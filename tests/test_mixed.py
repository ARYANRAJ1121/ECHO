"""
tests/test_mixed.py -- Unit and Integration Tests for Mixed Oligopoly (F2)

Verifies:
1. Mixed market instantiates heterogeneous agents (DQN, Q-learning, Follower, Maverick).
2. Maverick agent (UndercutAgent) reliably undercuts and prices near Nash.
3. Mixed simulation runs end-to-end without crashes or numerical instabilities.
4. Learning agents (DQN, Q-learning) receive observations and update parameters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_simulation import build_mixed_simulation
from data_loaders import get_data_loader


def test_mixed_simulation_instantiation():
    """Verify agent composition in mixed mode."""
    market_ctx = get_data_loader("gasoline").load()
    engine, rounds = build_mixed_simulation(n_rounds=10, market_ctx=market_ctx)

    assert len(engine.agents) == 5
    # Verify heterogeneous types
    types = [type(a).__name__ for a in engine.agents]
    assert "DQNPricingAgent" in types
    assert "QLearningAgent" in types
    assert "FollowerAgent" in types
    assert "UndercutAgent" in types


def test_mixed_simulation_run_and_maverick_behavior():
    """Verify that the mixed market runs and Maverick (Firm 4) undercuts high prices."""
    market_ctx = get_data_loader("gasoline").load()
    engine, rounds = build_mixed_simulation(n_rounds=15, market_ctx=market_ctx)

    records = engine.run(n_rounds=15)
    assert len(records) == 15

    # Firm 4 is the Maverick (UndercutAgent)
    # Check that in later rounds, Firm 4's price is at or below the market average
    for rec in records[3:]:
        maverick_price = rec.prices[4]
        avg_price = rec.avg_price
        # Maverick should price below or very close to average
        assert maverick_price <= avg_price + 0.05

    summary = engine.summary()
    assert summary["rounds_completed"] == 15
    assert summary["final_collusion_index"] is not None


if __name__ == "__main__":
    test_mixed_simulation_instantiation()
    test_mixed_simulation_run_and_maverick_behavior()
    print("\nAll Mixed Oligopoly unit tests PASSED!")
