"""
run_simulation.py -- ECHO Orchestrator

=== HOW TO RUN ===

    python run_simulation.py --dataset gasoline --mode dummy --rounds 50
    python run_simulation.py --dataset crypto   --mode llm   --rounds 10
    python run_simulation.py --dataset amazon   --mode rag   --rounds 10 --db
    python run_simulation.py --dataset airlines  --mode rl    --rounds 5000
    python run_simulation.py --dataset rideshare --mode dqn   --rounds 500

Datasets: gasoline (FRED API), crypto (CoinGecko), amazon (CSV),
          airlines (Indian carriers), rideshare (Uber/Lyft)

=== n8n AUTOMATION PIPELINE ===
  Real-time collusion alerts and summaries are dispatched to n8n webhooks:
    - Alert Webhook:             http://localhost:5678/webhook/echo-alert
    - Complete Summary Webhook:  http://localhost:5678/webhook/echo-simulation-complete
"""

from __future__ import annotations
import argparse

from market.demand import LogitDemandModel
from market.engine import MarketEngine


def build_demand_model(market_ctx) -> LogitDemandModel:
    """Build the demand model for a dataset. Shared by every mode."""
    return LogitDemandModel(
        n_firms=5,
        mu=market_ctx.mu,
        marginal_costs=market_ctx.marginal_costs,
        quality=[market_ctx.base_quality] * 5,
        outside_quality=0.0,
        market_size=1.0,
    )


# How far outside the Nash-monopoly range agents are allowed to price, as a
# fraction of that range. This bounds Lambda to roughly [-0.3, 1.3].
BAND_MARGIN = 0.30


def resolve_price_band(market_ctx, demand_model: LogitDemandModel) -> tuple[float, float]:
    """Return the trading band, derived from this market's own benchmarks.

    The band has to bracket the Nash and monopoly prices for Lambda to mean
    anything, and it has to stay close to them for the discretized RL and DQN
    action grids to have any resolution where it matters.

    Using the loader's "realistic price range" directly fails both ways. On
    rideshare the monopoly price sat at $26/mile against an $8 ceiling, so a
    perfect cartel capped out at Lambda = 0.21. On gasoline the ceiling was
    $7.50 against a Nash-monopoly range of only $0.41, so almost every point
    on the 15-level price grid was above monopoly and Lambda ran past 5.
    """
    benchmarks = demand_model.get_benchmarks()
    span = max(benchmarks.monopoly_price - benchmarks.nash_price, 1e-9)

    floor = max(
        min(market_ctx.marginal_costs) * 0.9,
        benchmarks.nash_price - BAND_MARGIN * span,
    )
    ceiling = benchmarks.monopoly_price + BAND_MARGIN * span

    print(
        f"  [Calibration] Trading band [{floor:.4f}, {ceiling:.4f}] "
        f"around Nash {benchmarks.nash_price:.4f} / monopoly {benchmarks.monopoly_price:.4f}"
    )
    return floor, ceiling


def build_llm_simulation(
    n_rounds: int,
    market_ctx,
    provider: str = "groq",
    model: str | None = None,
) -> tuple[MarketEngine, int]:
    """Wire up 5 LLM agents talking to Groq, Gemini, or Ollama."""
    from agents.llm_agent import LLMPricingAgent

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)
    agents = [
        LLMPricingAgent(
            firm_id=i,
            provider=provider,
            model=model,
            temperature=0.7,
            identity_name=market_ctx.firm_names[i],
            market_description=market_ctx.description,
            competitors=[name for j, name in enumerate(market_ctx.firm_names) if j != i],
            currency=market_ctx.currency,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def build_gemini_simulation(
    n_rounds: int,
    market_ctx,
    model: str = "gemini-flash-lite-latest",
) -> tuple[MarketEngine, int]:
    """Wire up 5 LLM agents talking to Google Gemini API."""
    return build_llm_simulation(n_rounds, market_ctx, provider="gemini", model=model)


def build_rag_simulation(n_rounds: int, sim_id: int, market_ctx) -> tuple[MarketEngine, int]:
    """
    Wire up 5 RAG-enhanced LLM agents.

    Requires PostgreSQL running (for pgvector) and Ollama running
    (for nomic-embed-text embeddings). LLM inference uses Groq API.
    """
    from agents.rag_agent import RAGPricingAgent
    from database.memory import VectorMemory

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)

    # Shared memory store (all agents write/read from same pgvector)
    memory = VectorMemory()

    agents = [
        RAGPricingAgent(
            firm_id=i,
            memory=memory,
            sim_id=sim_id,
            top_k=3,
            model="allam-2-7b",
            temperature=0.7,
            identity_name=market_ctx.firm_names[i],
            market_description=market_ctx.description,
            competitors=[name for j, name in enumerate(market_ctx.firm_names) if j != i],
            currency=market_ctx.currency,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def build_dummy_simulation(n_rounds: int, market_ctx) -> tuple[MarketEngine, int]:
    """Wire up 5 heuristic agents (fast, no LLM needed)."""
    from agents.heuristic_agent import SteadyAgent, FollowerAgent, UndercutAgent

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)

    # Anchor each rule to this market's own benchmarks. A fraction f means
    # "price f of the way from Nash to monopoly", so the control group sits
    # just above the competitive benchmark on every dataset regardless of
    # whether a unit costs $3 or $64,000.
    benchmarks = demand_model.get_benchmarks()
    span = benchmarks.monopoly_price - benchmarks.nash_price

    def anchored(fraction: float) -> float:
        return benchmarks.nash_price + fraction * span

    agents = [
        SteadyAgent(
            firm_id=0, target_price=anchored(0.10),
            identity_name=market_ctx.firm_names[0],
        ),
        FollowerAgent(
            firm_id=1, target_price=anchored(0.25), adjustment_speed=0.5,
            identity_name=market_ctx.firm_names[1],
        ),
        UndercutAgent(
            firm_id=2, undercut_frac=0.005, floor_price=anchored(-0.05),
            identity_name=market_ctx.firm_names[2],
        ),
        FollowerAgent(
            firm_id=3, target_price=anchored(0.05), adjustment_speed=0.3,
            identity_name=market_ctx.firm_names[3],
        ),
        SteadyAgent(
            firm_id=4, target_price=anchored(0.30),
            identity_name=market_ctx.firm_names[4],
        ),
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def build_rl_simulation(n_rounds: int, market_ctx) -> tuple[MarketEngine, int]:
    """
    Wire up 5 Q-Learning agents (Calvano 2020 replication).
    """
    from agents.rl_agent import QLearningAgent

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)

    agents = [
        QLearningAgent(
            firm_id=i,
            identity_name=market_ctx.firm_names[i],
            n_prices=15,
            alpha=0.15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.99995,
            price_floor=price_floor,
            price_ceiling=price_ceiling,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def build_dqn_simulation(n_rounds: int, market_ctx) -> tuple[MarketEngine, int]:
    """
    Wire up 5 DQN agents (Deep RL).
    """
    from agents.dqn_agent import DQNPricingAgent

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)

    agents = [
        DQNPricingAgent(
            firm_id=i,
            identity_name=market_ctx.firm_names[i],
            n_prices=15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
            price_floor=price_floor,
            price_ceiling=price_ceiling,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def build_mixed_simulation(n_rounds: int, market_ctx) -> tuple[MarketEngine, int]:
    """
    Wire up a Mixed-Agent Oligopoly:
    - Firms 0 & 1: DQNPricingAgent (Deep RL learners)
    - Firm 2: QLearningAgent (Tabular RL learner)
    - Firm 3: FollowerAgent (Heuristic follower that accommodates high prices)
    - Firm 4: UndercutAgent (The 'Maverick' competitive discounter pricing near Nash)

    Models real-world market asymmetry (e.g. 2 legacy carriers + 1 mid-tier + 1 follower
    vs 1 aggressive ultra-low-cost maverick like Akasa or Ryanair).
    Tests whether a single non-cooperative firm can prevent tacit collusion (F2).
    """
    from agents.dqn_agent import DQNPricingAgent
    from agents.rl_agent import QLearningAgent
    from agents.heuristic_agent import FollowerAgent, UndercutAgent

    demand_model = build_demand_model(market_ctx)
    price_floor, price_ceiling = resolve_price_band(market_ctx, demand_model)
    benchmarks = demand_model.get_benchmarks()
    span = benchmarks.monopoly_price - benchmarks.nash_price

    def anchored(frac):
        return round(float(benchmarks.nash_price + frac * span), 4)

    agents = [
        DQNPricingAgent(
            firm_id=0,
            identity_name=f"{market_ctx.firm_names[0]} (DQN)",
            n_prices=15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
            price_floor=price_floor,
            price_ceiling=price_ceiling,
        ),
        DQNPricingAgent(
            firm_id=1,
            identity_name=f"{market_ctx.firm_names[1]} (DQN)",
            n_prices=15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
            price_floor=price_floor,
            price_ceiling=price_ceiling,
        ),
        QLearningAgent(
            firm_id=2,
            identity_name=f"{market_ctx.firm_names[2]} (Q-Learn)",
            n_prices=15,
            alpha=0.15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.9995,
            price_floor=price_floor,
            price_ceiling=price_ceiling,
        ),
        FollowerAgent(
            firm_id=3,
            target_price=anchored(0.20),
            adjustment_speed=0.35,
            identity_name=f"{market_ctx.firm_names[3]} (Follower)",
        ),
        UndercutAgent(
            firm_id=4,
            undercut_frac=0.015,
            floor_price=anchored(-0.02),
            identity_name=f"{market_ctx.firm_names[4]} (Maverick)",
        ),
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=price_floor,
        price_ceiling=price_ceiling,
    )
    return engine, n_rounds


def print_results(engine: MarketEngine, show_scratchpads: bool = False) -> None:
    """Print simulation results."""
    records = engine.records
    summary = engine.summary()

    # Per-round table
    print("\n" + "=" * 80)
    print("ROUND-BY-ROUND RESULTS")
    print("=" * 80)
    print(f"{'Round':>5}  {'AvgPrice':>9}  {'Lambda':>7}  {'TotProfit':>10}  Prices")
    print("-" * 80)

    for r in records:
        price_str = ", ".join(f"{p:.3f}" for p in r.prices)
        print(
            f"{r.round_number:>5}  "
            f"{r.avg_price:>9.4f}  "
            f"{r.collusion_index:>7.4f}  "
            f"{r.total_profit:>10.6f}  "
            f"[{price_str}]"
        )

    # Summary
    print("\n" + "=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)
    print(f"  Rounds completed:         {summary['rounds_completed']}")
    print(f"  Nash benchmark price:     {summary['nash_price']:.4f}")
    print(f"  Monopoly benchmark:       {summary['monopoly_price']:.4f}")
    print(f"  Final avg price:          {summary['final_avg_price']:.4f}")
    print(f"  Final Lambda:             {summary['final_collusion_index']:.4f}")
    print(f"  Converged Lambda (last 20%): {summary['converged_collusion_index']:.4f}")
    print(f"  Peak Lambda:              {summary['peak_collusion_index']:.4f}")
    print(f"  Convergence round (>0.7): {summary['convergence_round']}")
    print("=" * 80)

    # Show last round's scratchpads for LLM/RAG agents
    if show_scratchpads:
        print("\n" + "=" * 80)
        print("LAST ROUND SCRATCHPADS (Agent reasoning)")
        print("=" * 80)
        for agent in engine.agents:
            if hasattr(agent, "scratchpad_history") and agent.scratchpad_history:
                print(f"\n--- {agent.name} ---")
                print(agent.scratchpad_history[-1])
        print("=" * 80)

    # Show RL agent stats if applicable
    rl_agents = [a for a in engine.agents if hasattr(a, "stats")]
    if rl_agents:
        print("\n" + "=" * 80)
        print("RL AGENT STATS")
        print("=" * 80)
        for agent in rl_agents:
            stats = agent.stats()
            if "total_q_updates" in stats:
                # Tabular Q-Learning agent
                print(f"  {agent.name}: {stats['total_q_updates']} updates | "
                      f"{stats['q_table_size']} states discovered | "
                      f"final epsilon: {stats['final_epsilon']:.4f}")
            elif "training_steps" in stats:
                # DQN agent
                avg_loss = f"{stats['avg_loss']:.6f}" if stats.get('avg_loss') else "N/A"
                print(f"  {agent.name}: {stats['training_steps']} training steps | "
                      f"{stats['replay_buffer_size']} experiences | "
                      f"avg loss: {avg_loss} | "
                      f"final epsilon: {stats['final_epsilon']:.4f} | "
                      f"params: {stats['network_params']}")
            else:
                print(f"  {agent.name}: {stats}")
        print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ECHO Simulation")
    parser.add_argument("--mode", choices=["llm", "dummy", "rag", "rl", "dqn", "mixed", "gemini"], default="dummy",
                        help="Agent type: 'llm', 'gemini', 'rag', 'rl', 'dqn', 'mixed', or 'dummy'")
    parser.add_argument("--llm-provider", choices=["groq", "gemini", "ollama"], default="groq",
                        help="LLM provider for --mode llm (default: groq)")
    parser.add_argument("--llm-model", type=str, default=None,
                        help="Custom model name for LLM provider (e.g. 'gemini-2.5-flash', 'allam-2-7b')")
    parser.add_argument("--rounds", type=int, default=50,
                        help="Number of rounds to simulate (use 5000+ for RL)")
    parser.add_argument("--db", action="store_true",
                        help="Save results to PostgreSQL (required for --mode rag)")
    parser.add_argument("--validate", action="store_true",
                        help="Run Phase 1.5 empirical validation after simulation")
    parser.add_argument("--dataset", type=str,
                        choices=["gasoline", "crypto", "amazon", "rideshare", "airlines"],
                        default="gasoline",
                        help="Real-world dataset to use (default: gasoline)")
    # Policy Counterfactuals (F6)
    parser.add_argument("--policy-cap-frac", type=float, default=None,
                        help="Regulatory price cap as fraction of Nash-Monopoly span (e.g., 0.50)")
    parser.add_argument("--fixed-price-cap", type=float, default=None,
                        help="Hard absolute price ceiling imposed by regulator")
    parser.add_argument("--transparency-delay", type=int, default=0,
                        help="Lag rival price visibility by k rounds to disrupt punishment (default: 0)")
    parser.add_argument("--leniency-bonus", type=float, default=0.0,
                        help="Antitrust whistleblower bonus awarded to defectors undercutting cartel")
    parser.add_argument("--policy-start-round", type=int, default=1,
                        help="Round at which regulatory policy begins (enables A/B split comparisons)")

    # Macroeconomic & Non-Stationary Environments (F5)
    parser.add_argument("--seasonality-amp", type=float, default=0.0,
                        help="Seasonal demand swing amplitude (e.g., 0.30 for ±30%)")
    parser.add_argument("--seasonality-period", type=int, default=20,
                        help="Rounds per seasonal demand cycle (default: 20)")
    parser.add_argument("--macro-shock-round", type=int, default=None,
                        help="Round at which an acute recession / demand collapse occurs")
    parser.add_argument("--macro-shock-intensity", type=float, default=-0.40,
                        help="Fractional demand shift during macro shock (default: -0.40)")
    parser.add_argument("--cost-inflation", type=float, default=0.0,
                        help="Per-round input cost inflation rate (e.g., 0.005 for +0.5%/rd)")
    args = parser.parse_args()

    # RAG mode requires database
    if args.mode == "rag" and not args.db:
        print("RAG mode requires --db flag (needs PostgreSQL for pgvector).")
        print("Usage: python run_simulation.py --mode rag --rounds 10 --db --dataset gasoline")
        exit(1)

    print("=" * 80)
    print("ECHO -- Emergent Collusion in Heterogeneous Oligopolies")
    print(f"Mode: {args.mode.upper()} agents | Rounds: {args.rounds} | DB: {'ON' if args.db else 'OFF'}")

    # Dataset Loading — always load a real-world dataset
    from data_loaders import get_data_loader
    market_ctx = get_data_loader(args.dataset).load()
    print(f"Dataset: {market_ctx.describe()}")
    if market_ctx.is_fallback:
        print("!" * 80)
        print("WARNING: live data unavailable. Running on synthetic parameters.")
        print("Do not report these results as empirical validation.")
        print("!" * 80)
    real_lambda = market_ctx.observed_dispersion_lambda()
    if real_lambda is not None:
        print(f"Observed real-world price convergence proxy: {real_lambda:.4f}")
    print("=" * 80)

    # Database logging (optional, required for RAG)
    db_logger = None
    sim_id = None

    if args.db:
        from database.db import DatabaseLogger
        db_logger = DatabaseLogger()

    # Build simulation
    if args.mode == "rag":
        # RAG needs sim_id upfront (agents need it for memory isolation)
        sim_id = db_logger.start_simulation({
            "mode": "rag",
            "n_firms": 5,
            "n_rounds": args.rounds,
            "mu": market_ctx.mu,
            "marginal_cost": market_ctx.marginal_costs[0],
            "dataset": args.dataset
        })
        engine, n_rounds = build_rag_simulation(args.rounds, sim_id=sim_id, market_ctx=market_ctx)
        # Update benchmarks after engine is created
        db_logger.conn.cursor().execute(
            "UPDATE simulations SET nash_price=%s, monopoly_price=%s WHERE sim_id=%s",
            (engine.benchmarks.nash_price, engine.benchmarks.monopoly_price, sim_id),
        )
        db_logger.conn.commit()
    elif args.mode == "gemini":
        engine, n_rounds = build_gemini_simulation(args.rounds, market_ctx=market_ctx, model=args.llm_model or "gemini-flash-lite-latest")
    elif args.mode == "llm":
        engine, n_rounds = build_llm_simulation(args.rounds, market_ctx=market_ctx, provider=args.llm_provider, model=args.llm_model)
    elif args.mode == "rl":
        engine, n_rounds = build_rl_simulation(args.rounds, market_ctx=market_ctx)
    elif args.mode == "dqn":
        engine, n_rounds = build_dqn_simulation(args.rounds, market_ctx=market_ctx)
    elif args.mode == "mixed":
        engine, n_rounds = build_mixed_simulation(args.rounds, market_ctx=market_ctx)
    else:
        engine, n_rounds = build_dummy_simulation(args.rounds, market_ctx=market_ctx)

    # Configure Antitrust Policy Counterfactual (F6) if specified
    from market.policy import PolicyConfig
    policy = None
    if any([
        args.policy_cap_frac is not None,
        args.fixed_price_cap is not None,
        args.transparency_delay > 0,
        args.leniency_bonus > 0.0,
    ]):
        parts = []
        if args.policy_cap_frac is not None:
            parts.append(f"Cap({int(args.policy_cap_frac*100)}%)")
        if args.fixed_price_cap is not None:
            parts.append(f"FixedCap({args.fixed_price_cap})")
        if args.transparency_delay > 0:
            parts.append(f"Delay({args.transparency_delay}r)")
        if args.leniency_bonus > 0.0:
            parts.append(f"Leniency({args.leniency_bonus:.1f})")
        policy_name = " + ".join(parts) if parts else "Antitrust Remedy"

        policy = PolicyConfig(
            name=policy_name,
            price_cap_fraction=args.policy_cap_frac,
            fixed_price_cap=args.fixed_price_cap,
            transparency_delay=args.transparency_delay,
            leniency_bonus=args.leniency_bonus,
            active_from_round=args.policy_start_round,
        )
        engine.policy = policy
        print(f"\n[Antitrust Policy] Enforcing '{policy_name}' starting at round {args.policy_start_round}")

    # Configure Non-Stationary Macro Environment (F5) if specified
    from market.macro import MacroConfig
    macro = None
    if any([
        args.seasonality_amp > 0.0,
        args.macro_shock_round is not None,
        args.cost_inflation != 0.0,
    ]):
        macro_name_parts = []
        if args.seasonality_amp > 0.0:
            macro_name_parts.append(f"Seasonal(±{int(args.seasonality_amp*100)}%)")
        if args.macro_shock_round is not None:
            macro_name_parts.append(f"Recession(R{args.macro_shock_round})")
        if args.cost_inflation != 0.0:
            macro_name_parts.append(f"Inflation(+{args.cost_inflation*100:.1f}%)")

        macro = MacroConfig(
            name=" + ".join(macro_name_parts),
            seasonality_amp=args.seasonality_amp,
            seasonality_period=args.seasonality_period,
            shock_round=args.macro_shock_round,
            shock_intensity=args.macro_shock_intensity,
            cost_trend=args.cost_inflation,
        )
        engine.macro = macro
        print(f"\n[Macro Environment] Active regime: '{macro.name}'")

    # Start sim in DB (for non-RAG modes)
    if args.db and sim_id is None:
        sim_id = db_logger.start_simulation({
            "mode": args.mode,
            "n_firms": 5,
            "n_rounds": args.rounds,
            "mu": market_ctx.mu,
            "marginal_cost": market_ctx.marginal_costs[0],
            "dataset": args.dataset,
            "nash_price": engine.benchmarks.nash_price,
            "monopoly_price": engine.benchmarks.monopoly_price,
        })

    engine.run(n_rounds=n_rounds, db_logger=db_logger, sim_id=sim_id)

    if db_logger:
        db_logger.end_simulation(sim_id)
        db_logger.close()

    print_results(engine, show_scratchpads=(args.mode in ("llm", "rag", "gemini")))

    # --- Antitrust Regulator: Lambda Monitor ---
    from regulator.detector import LambdaMonitor

    monitor = LambdaMonitor()
    for record in engine.records:
        alerts = monitor.observe(record.round_number, record.collusion_index)
        for alert in alerts:
            print(f"  *** {alert.detail}")

    report = monitor.report()
    print("\n" + "=" * 80)
    print("REGULATOR REPORT (Lambda Monitor)")
    print("=" * 80)
    print(f"  Rounds analyzed:     {report['total_rounds']}")
    print(f"  Mean Lambda:         {report['mean_lambda']:.4f}")
    print(f"  Peak Lambda:         {report['peak_lambda']:.4f}")
    print(f"  Final Lambda:        {report['final_lambda']:.4f}")
    print(f"  Rolling avg (50r):   {report['rolling_avg']:.4f}")
    print(f"  Trend:               {report['trend']}")
    print(f"  Total alerts:        {report['total_alerts']}")
    print(f"    Watch (low):       {report['alert_breakdown']['watch']}")
    print(f"    Warning (medium):  {report['alert_breakdown']['warning']}")
    print(f"    Alert (high):      {report['alert_breakdown']['alert']}")
    if report['first_alert_round']:
        print(f"  First alert round:   {report['first_alert_round']}")
    print("=" * 80)

    # --- Policy Counterfactual Evaluation (F6) ---
    engine_summary = engine.summary()
    if "policy" in engine_summary:
        pol = engine_summary["policy"]
        print("\n" + "=" * 80)
        print(f"ANTITRUST POLICY INTERVENTION REPORT: {pol['name'].upper()}")
        print("=" * 80)
        print(f"  Policy Regime:               {pol['name']}")
        print(f"  Active from Round:           {pol['config']['active_from_round']}")
        print(f"  Active Rounds Evaluated:     {pol['active_rounds_count']}")
        if pol['pre_policy_avg_lambda'] is not None:
            print(f"  Pre-Intervention Mean Lambda:{pol['pre_policy_avg_lambda']:.4f}")
        if pol['post_policy_avg_lambda'] is not None:
            print(f"  Post-Intervention Mean Lambda:{pol['post_policy_avg_lambda']:.4f}")
        if pol['lambda_reduction'] is not None:
            direction = "REDUCED (Collusion Disrupted)" if pol['lambda_reduction'] > 0 else "INCREASED/FLAT"
            print(f"  Net Lambda Impact:           {pol['lambda_reduction']:+.4f} [{direction}]")
        print(f"  Total Consumer Savings:      {market_ctx.currency} {pol['total_consumer_savings']:,.2f}")
        print(f"  Rounds Price Cap Clamped:    {pol['capped_rounds_count']}")
        print(f"  Leniency Awards Granted:     {pol['total_leniency_awarded_count']}")
        print("=" * 80)

    # One-run figure pack (wipes previous latest_run/)
    from analysis.run_pack import build_run_pack
    build_run_pack(
        dataset=args.dataset,
        mode=args.mode,
        records=[
            {
                "round": rec.round_number,
                "prices": rec.prices,
                "avg_price": rec.avg_price,
                "lambda": rec.collusion_index,
                "profits": rec.profits,
                "shares": rec.shares,
            }
            for rec in engine.records
        ],
        firm_names=market_ctx.firm_names,
        nash=float(engine.benchmarks.nash_price),
        monopoly=float(engine.benchmarks.monopoly_price),
        currency=market_ctx.currency,
        real_avg_series=market_ctx.observed_market_average(n=300),
        regulator=report,
        data_source=market_ctx.source,
    )

    # --- Phase 1.5: Empirical Validation ---
    if args.validate:
        from analysis.real_data import run_validation
        summary = engine.summary()
        sim_lambda = summary['converged_collusion_index']
        run_validation(sim_lambda=sim_lambda)
