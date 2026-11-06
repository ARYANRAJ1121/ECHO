"""
tests/test_policy.py -- Unit and Integration Tests for Policy Counterfactuals (F6)

Verifies:
1. Relative and fixed price caps clamp prices and calculate consumer savings.
2. Transparency delays accurately lag the observation history seen by firms.
3. Antitrust leniency bonuses reward defectors in supra-competitive regimes.
4. End-to-end simulation runs cleanly with policy evaluation in summary().
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from market.demand import LogitDemandModel
from market.policy import PolicyConfig
from market.engine import MarketEngine
from agents.heuristic_agent import FollowerAgent, SteadyAgent, UndercutAgent


def build_test_market():
    """Build a standard 5-firm test logit market."""
    model = LogitDemandModel(
        n_firms=5,
        marginal_cost=2.0,
        quality=[3.0] * 5,
        mu=0.5,
        market_size=1000.0,
    )
    benchmarks = model.get_benchmarks()
    return model, benchmarks


def test_price_cap_clamping_and_savings():
    """Verify price cap clamps supra-competitive prices and logs consumer savings."""
    model, benchmarks = build_test_market()
    span = benchmarks.monopoly_price - benchmarks.nash_price
    cap_fraction = 0.40
    expected_cap = benchmarks.nash_price + cap_fraction * span

    # All agents try to price at monopoly ceiling
    agents = [
        SteadyAgent(firm_id=i, target_price=benchmarks.monopoly_price)
        for i in range(5)
    ]

    policy = PolicyConfig.price_cap(fraction=cap_fraction)
    engine = MarketEngine(
        demand_model=model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=benchmarks.monopoly_price * 1.5,
        policy=policy,
    )

    records = engine.run(n_rounds=5)

    for rec in records:
        assert rec.is_policy_active is True
        for p in rec.prices:
            assert p <= expected_cap + 1e-4, f"Price {p} exceeded cap {expected_cap}"
        assert rec.consumer_savings > 0.0, "Consumer savings should be positive when capped"
        assert rec.collusion_index <= cap_fraction + 0.05

    summary = engine.summary()
    assert "policy" in summary
    assert summary["policy"]["capped_rounds_count"] == 5
    assert summary["policy"]["total_consumer_savings"] > 0.0


def test_delayed_transparency_lag():
    """Verify that transparency delay correctly hides recent market rounds."""
    model, benchmarks = build_test_market()
    delay = 3
    policy = PolicyConfig.delayed_transparency(delay=delay, active_from_round=1)

    # Inspect history lengths received by an agent
    observed_lengths = []

    class InspectingAgent(SteadyAgent):
        def choose_price(self, observation):
            observed_lengths.append(len(observation.price_history))
            return observation.price_floor + 1.0

    agents = [InspectingAgent(firm_id=i, target_price=3.0) for i in range(5)]
    engine = MarketEngine(
        demand_model=model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=10.0,
        policy=policy,
    )

    engine.run(n_rounds=6)

    # For delay=3:
    # Round 1: len = 0 (cutoff max(0, 0-3) = 0)
    # Round 2: len = 0 (cutoff max(0, 1-3) = 0)
    # Round 3: len = 0 (cutoff max(0, 2-3) = 0)
    # Round 4: len = 0 (cutoff max(0, 3-3) = 0)
    # Round 5: len = 1 (cutoff max(0, 4-3) = 1)
    # Round 6: len = 2 (cutoff max(0, 5-3) = 2)
    # Since 5 agents record per round, check agent 0's observation at each round:
    agent_0_obs = observed_lengths[0::5]
    assert agent_0_obs[0] == 0
    assert agent_0_obs[1] == 0
    assert agent_0_obs[2] == 0
    assert agent_0_obs[3] == 0
    assert agent_0_obs[4] == 1
    assert agent_0_obs[5] == 2


def test_leniency_program_rewards_defector():
    """Verify that an antitrust leniency bonus is awarded to an undercutting defector."""
    model, benchmarks = build_test_market()
    bonus_amount = 200.0
    policy = PolicyConfig.leniency_program(bonus=bonus_amount, active_from_round=1)

    # Firms 0-3 price high at monopoly, Firm 4 undercuts deeply
    agents = [
        SteadyAgent(firm_id=0, target_price=benchmarks.monopoly_price),
        SteadyAgent(firm_id=1, target_price=benchmarks.monopoly_price),
        SteadyAgent(firm_id=2, target_price=benchmarks.monopoly_price),
        SteadyAgent(firm_id=3, target_price=benchmarks.monopoly_price),
        SteadyAgent(firm_id=4, target_price=benchmarks.nash_price),
    ]

    engine = MarketEngine(
        demand_model=model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=10.0,
        policy=policy,
    )

    records = engine.run(n_rounds=3)
    for rec in records:
        assert 4 in rec.leniency_recipients, "Firm 4 should qualify for leniency bonus"
        # Firm 4 profit should reflect normal profit + bonus
        assert rec.profits[4] >= bonus_amount

    summary = engine.summary()
    assert summary["policy"]["total_leniency_awarded_count"] == 3


def test_split_run_counterfactual():
    """Verify A/B split run: rounds 1-5 unconstrained, rounds 6-10 capped."""
    model, benchmarks = build_test_market()
    policy = PolicyConfig.price_cap(fraction=0.20, active_from_round=6)

    agents = [
        SteadyAgent(firm_id=i, target_price=benchmarks.monopoly_price)
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=benchmarks.monopoly_price * 1.5,
        policy=policy,
    )

    records = engine.run(n_rounds=10)

    # Pre-policy (rounds 1-5): unconstrained monopoly
    for r in records[:5]:
        assert r.is_policy_active is False
        assert r.collusion_index > 0.95

    # Post-policy (rounds 6-10): capped near Nash
    for r in records[5:]:
        assert r.is_policy_active is True
        assert r.collusion_index <= 0.25

    summary = engine.summary()
    assert summary["policy"]["pre_policy_avg_lambda"] > 0.90
    assert summary["policy"]["post_policy_avg_lambda"] < 0.25
    assert summary["policy"]["lambda_reduction"] > 0.65


if __name__ == "__main__":
    test_price_cap_clamping_and_savings()
    test_delayed_transparency_lag()
    test_leniency_program_rewards_defector()
    test_split_run_counterfactual()
    print("\nAll Policy Counterfactual unit and integration tests PASSED!")
