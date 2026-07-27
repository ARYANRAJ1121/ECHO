"""
api_server.py -- ECHO Phase 8: Full API + Live Dashboard Server

Serves the real-time dashboard and provides:
  - WebSocket /ws/simulate: streams rounds in real-time
  - REST endpoints for status, history, scratchpads
  - POST /api/simulation/shock/{firm_id}: demand shock trigger

Run:
    python api_server.py
    Open http://localhost:8000
"""

import asyncio
import json
import os
import time
from typing import Any

import requests as http_requests

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from run_simulation import (
    build_dummy_simulation,
    build_rl_simulation,
    build_llm_simulation,
    build_dqn_simulation,
)
from regulator.detector import LambdaMonitor
from regulator.sentiment import ScratchpadSentimentAnalyzer
from analysis.strategy_classifier import AgentStrategyClassifier
from analysis.forecaster import PriceForecaster

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────

# n8n webhook endpoint for collusion alert automation
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/echo-alert")
N8N_COMPLETE_URL = os.getenv("N8N_COMPLETE_URL", "http://localhost:5678/webhook/echo-simulation-complete")

app = FastAPI(title="ECHO Antitrust Simulation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Simulation State (module-level singleton)
# ──────────────────────────────────────────────

class SimulationState:
    """Tracks the current simulation so REST endpoints can query it."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.running: bool = False
        self.mode: str = ""
        self.total_rounds: int = 0
        self.current_round: int = 0
        self.engine: Any = None
        self.monitor: LambdaMonitor | None = None
        self.records: list[dict] = []
        self.scratchpads: dict[int, list[str]] = {}  # firm_id -> list of texts
        self.shock_events: list[dict] = []
        self.start_time: float = 0
        self.benchmarks: dict = {}
        self.sentiment_analyzer: ScratchpadSentimentAnalyzer | None = None
        self.strategy_classifier: AgentStrategyClassifier | None = None
        self.forecaster: PriceForecaster | None = None


sim_state = SimulationState()


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard/index.html")


app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")


# ──────────────────────────────────────────────
# REST Endpoints
# ──────────────────────────────────────────────

@app.get("/api/simulation/status")
def get_simulation_status():
    """Current simulation state snapshot."""
    return {
        "running": sim_state.running,
        "mode": sim_state.mode,
        "current_round": sim_state.current_round,
        "total_rounds": sim_state.total_rounds,
        "lambda": sim_state.records[-1]["lambda"] if sim_state.records else 0,
        "avg_price": sim_state.records[-1]["avg_price"] if sim_state.records else 0,
        "benchmarks": sim_state.benchmarks,
        "shock_events": sim_state.shock_events,
        "elapsed_seconds": round(time.time() - sim_state.start_time, 1) if sim_state.running else 0,
    }


@app.get("/api/simulation/history")
def get_simulation_history():
    """Full round history (for reconnecting clients)."""
    return {
        "mode": sim_state.mode,
        "total_rounds": sim_state.total_rounds,
        "benchmarks": sim_state.benchmarks,
        "records": sim_state.records,
        "shock_events": sim_state.shock_events,
    }


@app.get("/api/agents/{firm_id}/scratchpad")
def get_agent_scratchpad(firm_id: int):
    """Latest scratchpad reasoning for a specific firm."""
    history = sim_state.scratchpads.get(firm_id, [])
    if not history:
        return {"firm_id": firm_id, "scratchpad": None, "total_entries": 0}
    return {
        "firm_id": firm_id,
        "scratchpad": history[-1],
        "total_entries": len(history),
    }


@app.get("/api/validation")
def get_validation_data():
    report_path = os.path.join("analysis", "data", "validation_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r") as f:
            return json.load(f)
    return {"error": "Validation report not found. Run: python run_simulation.py --mode dummy --rounds 50 --validate"}


# ──────────────────────────────────────────────
# Demand Shock Endpoint
# ──────────────────────────────────────────────

class ShockRequest(BaseModel):
    intensity: float = 0.3  # default 30% quality reduction


@app.post("/api/simulation/shock/{firm_id}")
def trigger_demand_shock(firm_id: int, req: ShockRequest = ShockRequest()):
    """
    Trigger a demand shock on a specific firm mid-simulation.

    Reduces the firm's quality parameter by `intensity` (default 30%).
    Other firms' quality stays the same. This is how we test whether
    competitors respond to the shock — a sign of coordination.
    """
    if not sim_state.running:
        return JSONResponse(
            status_code=400,
            content={"error": "No simulation is running."},
        )
    if sim_state.engine is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Engine not initialized."},
        )
    if firm_id < 0 or firm_id >= sim_state.engine.demand_model.n_firms:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid firm_id. Must be 0-{sim_state.engine.demand_model.n_firms - 1}."},
        )

    # Apply the shock: reduce quality for this firm
    dm = sim_state.engine.demand_model
    old_quality = float(dm.quality[firm_id])
    dm.quality[firm_id] -= req.intensity
    new_quality = float(dm.quality[firm_id])

    shock_event = {
        "firm_id": firm_id,
        "round": sim_state.current_round,
        "intensity": req.intensity,
        "old_quality": round(old_quality, 4),
        "new_quality": round(new_quality, 4),
        "timestamp": time.time(),
    }
    sim_state.shock_events.append(shock_event)

    print(f"  *** SHOCK: Firm {firm_id} quality {old_quality:.3f} -> {new_quality:.3f} at round {sim_state.current_round}")

    return {"status": "shock_applied", "event": shock_event}

# ──────────────────────────────────────────────
# n8n Webhook Helper
# ──────────────────────────────────────────────

async def _notify_n8n(
    round_num: int,
    lambda_val: float,
    avg_price: float,
    mode: str,
    alerts: list[dict],
) -> None:
    """
    Fire-and-forget webhook to n8n when collusion is detected.

    Runs in a background asyncio task so it never blocks the
    simulation loop. Silently fails if n8n is not running.
    """
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: http_requests.post(
            N8N_WEBHOOK_URL,
            json={
                "event": "collusion_alert",
                "round": round_num,
                "lambda": round(lambda_val, 4),
                "avg_price": round(avg_price, 4),
                "mode": mode,
                "alerts": alerts,
                "timestamp": time.time(),
            },
            timeout=3,
        ))
    except Exception:
        pass  # n8n not running — no problem


async def _notify_n8n_complete(
    mode: str,
    total_rounds: int,
    regulator: dict,
    sentiment_report: dict | None,
    forecast: list | None,
) -> None:
    """Fire-and-forget webhook when simulation completes."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: http_requests.post(
            N8N_COMPLETE_URL,
            json={
                "event": "simulation_complete",
                "mode": mode,
                "total_rounds": total_rounds,
                "regulator": regulator,
                "sentiment_report": sentiment_report,
                "forecast": forecast,
                "timestamp": time.time(),
            },
            timeout=3,
        ))
    except Exception:
        pass


# ──────────────────────────────────────────────
# WebSocket: Live Simulation Stream
# ──────────────────────────────────────────────


@app.websocket("/ws/simulate")
async def simulate_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        config_text = await websocket.receive_text()
        config = json.loads(config_text)
        mode = config.get("mode", "dummy")
        n_rounds = config.get("rounds", 50)

        print(f"\n{'='*60}")
        print(f"Starting {mode.upper()} simulation for {n_rounds} rounds")
        print(f"{'='*60}")

        # Reset state
        sim_state.reset()
        sim_state.mode = mode
        sim_state.total_rounds = n_rounds
        sim_state.running = True
        sim_state.start_time = time.time()

        # Build the right simulation
        if mode == "rl":
            engine, _ = build_rl_simulation(n_rounds)
        elif mode == "dqn":
            engine, _ = build_dqn_simulation(n_rounds)
        elif mode == "llm":
            engine, _ = build_llm_simulation(n_rounds)
        else:
            engine, _ = build_dummy_simulation(n_rounds)

        sim_state.engine = engine
        monitor = LambdaMonitor()
        sim_state.monitor = monitor

        # Initialize AI analysis modules
        sentiment_analyzer = ScratchpadSentimentAnalyzer()
        sim_state.sentiment_analyzer = sentiment_analyzer

        strategy_classifier = AgentStrategyClassifier(
            nash_price=engine.benchmarks.nash_price,
            monopoly_price=engine.benchmarks.monopoly_price,
            n_firms=engine.demand_model.n_firms,
        )
        sim_state.strategy_classifier = strategy_classifier

        forecaster = PriceForecaster(window_size=10)
        sim_state.forecaster = forecaster

        # Send benchmarks
        benchmarks = {
            "type": "benchmarks",
            "nash_price": engine.benchmarks.nash_price,
            "monopoly_price": engine.benchmarks.monopoly_price,
            "price_floor": engine.price_floor,
            "price_ceiling": engine.price_ceiling,
        }
        sim_state.benchmarks = {
            "nash_price": engine.benchmarks.nash_price,
            "monopoly_price": engine.benchmarks.monopoly_price,
        }
        await websocket.send_text(json.dumps(benchmarks))

        # Run round by round
        for round_num in range(1, n_rounds + 1):
            sim_state.current_round = round_num

            record = engine._run_one_round(round_num)
            engine.records.append(record)
            engine.price_history.append(record.prices)
            engine.profit_history.append(record.profits)

            # RL/DQN learning step
            if mode in ("rl", "dqn"):
                from agents.base_agent import Observation
                for i, agent in enumerate(engine.agents):
                    if hasattr(agent, "learn"):
                        obs = Observation(
                            round_number=round_num,
                            firm_id=agent.firm_id,
                            marginal_cost=float(engine.demand_model.costs[0]),
                            price_floor=engine.price_floor,
                            price_ceiling=engine.price_ceiling,
                            price_history=engine.price_history,
                            profit_history=engine.profit_history,
                        )
                        agent.learn(obs, record.prices, record.profits[i])

            # Lambda monitoring
            alerts = monitor.observe(record.round_number, record.collusion_index)

            # n8n webhook: fire-and-forget when collusion alerts trigger
            if alerts:
                asyncio.create_task(_notify_n8n(
                    round_num=round_num,
                    lambda_val=record.collusion_index,
                    avg_price=record.avg_price,
                    mode=mode,
                    alerts=[{"type": a.alert_type, "severity": a.severity, "detail": a.detail} for a in alerts],
                ))

            # Collect scratchpads for LLM/RAG agents
            scratchpads = {}
            if mode in ("llm", "rag"):
                for agent in engine.agents:
                    if hasattr(agent, "scratchpad_history") and agent.scratchpad_history:
                        text = agent.scratchpad_history[-1]
                        scratchpads[agent.firm_id] = text
                        # Store in state
                        if agent.firm_id not in sim_state.scratchpads:
                            sim_state.scratchpads[agent.firm_id] = []
                        sim_state.scratchpads[agent.firm_id].append(text)

            # Build payload
            payload = {
                "type": "round",
                "round": record.round_number,
                "prices": record.prices,
                "shares": record.shares,
                "profits": record.profits,
                "avg_price": record.avg_price,
                "total_profit": record.total_profit,
                "lambda": record.collusion_index,
                "alerts": [
                    {"type": a.alert_type.replace("lambda_", ""), "detail": a.detail}
                    for a in alerts
                ],
            }

            # --- AI Analysis: Strategy Classification ---
            strategy_labels = {}
            if len(engine.price_history) >= 2:
                prev_prices = engine.price_history[-2]
                window_start = max(0, len(engine.price_history) - 6)
                window = engine.price_history[window_start:]
                for i in range(len(record.prices)):
                    pred = strategy_classifier.predict_round(
                        firm_id=i,
                        round_number=round_num,
                        prices=record.prices,
                        prev_prices=prev_prices,
                        profits=record.profits,
                        cost=float(engine.demand_model.costs[0]),
                        price_history_window=window,
                    )
                    strategy_labels[i] = {
                        "strategy": pred.predicted_strategy,
                        "confidence": round(pred.confidence, 3),
                    }
                payload["strategies"] = strategy_labels

            # --- AI Analysis: Sentiment (LLM/RAG modes) ---
            if scratchpads and len(scratchpads) > 0:
                snapshot = sentiment_analyzer.analyze_round(round_num, scratchpads)
                payload["sentiment"] = {
                    "mean_cooperative": round(snapshot.mean_cooperative, 3),
                    "mean_competitive": round(snapshot.mean_competitive, 3),
                    "cooperative_majority": snapshot.cooperative_majority,
                    "is_suspicious": snapshot.is_suspicious,
                    "agents": {
                        r.firm_id: {
                            "intent": r.dominant_intent,
                            "cooperative": round(r.cooperative_score, 3),
                            "competitive": round(r.competitive_score, 3),
                        }
                        for r in snapshot.results
                    },
                }

            # Include scratchpads if present
            if scratchpads:
                payload["scratchpads"] = scratchpads

            # Include shock events that happened this round
            round_shocks = [
                s for s in sim_state.shock_events
                if s["round"] == round_num
            ]
            if round_shocks:
                payload["shocks"] = round_shocks

            # Store in state for REST queries
            sim_state.records.append({
                "round": record.round_number,
                "prices": record.prices,
                "avg_price": record.avg_price,
                "lambda": record.collusion_index,
                "profits": record.profits,
                "shares": record.shares,
            })

            # Send — batch for long RL simulations
            if mode == "rl" and n_rounds >= 1000:
                if round_num % 10 == 0 or round_num == n_rounds:
                    await websocket.send_text(json.dumps(payload))
                    await asyncio.sleep(0.001)
            elif mode == "llm":
                # LLM is already slow, send every round without delay
                await websocket.send_text(json.dumps(payload))
            else:
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.05)

        # Simulation complete
        summary = engine.summary()
        report = monitor.report()

        # --- AI Analysis: Price Forecast ---
        forecast_data = None
        if len(engine.price_history) > 15:
            try:
                forecaster.train(engine.price_history)
                forecasts = forecaster.forecast(engine.price_history, n_steps=10)
                forecast_data = [
                    {
                        "round": f.target_round,
                        "price": round(f.predicted_avg_price, 4),
                        "ci_lower": round(f.confidence_interval[0], 4),
                        "ci_upper": round(f.confidence_interval[1], 4),
                    }
                    for f in forecasts
                ]
            except Exception as e:
                print(f"Forecast error: {e}")

        # --- AI Analysis: Sentiment Report ---
        sentiment_report = None
        if sentiment_analyzer.snapshots:
            sr = sentiment_analyzer.report()
            sentiment_report = {
                "suspicious_rate": round(sr.get("suspicious_rate", 0), 3),
                "intent_drift": sr.get("intent_drift", "n/a"),
                "mean_cooperative": round(sr.get("mean_cooperative_score", 0), 3),
            }

        await websocket.send_text(json.dumps({
            "type": "summary",
            "data": summary,
            "regulator": {
                "mean_lambda": report["mean_lambda"],
                "peak_lambda": report["peak_lambda"],
                "total_alerts": report["total_alerts"],
                "trend": report["trend"],
                "convergence_round": summary.get("convergence_round"),
            },
            "forecast": forecast_data,
            "sentiment_report": sentiment_report,
        }))

        # n8n webhook: notify simulation complete
        asyncio.create_task(_notify_n8n_complete(
            mode=mode,
            total_rounds=n_rounds,
            regulator={
                "mean_lambda": report["mean_lambda"],
                "peak_lambda": report["peak_lambda"],
                "total_alerts": report["total_alerts"],
                "trend": report["trend"],
                "convergence_round": summary.get("convergence_round"),
            },
            sentiment_report=sentiment_report,
            forecast=forecast_data,
        ))

        sim_state.running = False
        elapsed = round(time.time() - sim_state.start_time, 1)
        print(f"\nSimulation complete in {elapsed}s.")

    except WebSocketDisconnect:
        print("Client disconnected.")
        sim_state.running = False
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
        sim_state.running = False


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("ECHO — Antitrust Simulation Dashboard")
    print("Open http://localhost:8000 in your browser")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
