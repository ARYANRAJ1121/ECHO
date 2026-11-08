"""
tests/test_macro.py -- Unit tests for Non-Stationary Markets & Macro Cycles (F5)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from market.demand import LogitDemandModel
from market.macro import MacroConfig
from market.engine import MarketEngine
from agents.heuristic_agent import SteadyAgent


def _make_demand() -> LogitDemandModel:
    return LogitDemandModel(
        n_firms=3,
        quality=[2.0, 2.0, 2.0],
        marginal_cost=1.0,
        mu=0.25,
        market_size=100.0,
    )


def test_macro_config_factories():
    none_cfg = MacroConfig.none()
    assert none_cfg.seasonality_amp == 0.0
    assert none_cfg.cost_trend == 0.0

    seasonal_cfg = MacroConfig.seasonal(amp=0.35, period=12)
    assert seasonal_cfg.seasonality_amp == 0.35
    assert seasonal_cfg.seasonality_period == 12

    recession_cfg = MacroConfig.recession(shock_round=15, intensity=-0.50, duration=4)
    assert recession_cfg.shock_round == 15
    assert recession_cfg.shock_intensity == -0.50
    assert recession_cfg.shock_duration == 4

    inflation_cfg = MacroConfig.inflation(cost_trend=0.02)
    assert inflation_cfg.cost_trend == 0.02


def test_macro_seasonal_oscillation():
    demand = _make_demand()
    cfg = MacroConfig.seasonal(amp=0.30, period=20)

    # Round 0 (or 20): phase 0 -> sin(0) = 0 -> market_size == 100.0
    t0 = cfg.apply(demand, 20)
    assert abs(t0["market_size"] - 100.0) < 1e-4

    # Round 5 (period 20): phase pi/2 -> sin(pi/2) = 1 -> peak (130.0)
    t5 = cfg.apply(demand, 5)
    assert abs(t5["market_size"] - 130.0) < 1e-3

    # Round 15: phase 3pi/2 -> sin(3pi/2) = -1 -> trough (70.0)
    t15 = cfg.apply(demand, 15)
    assert abs(t15["market_size"] - 70.0) < 1e-3


def test_macro_recession_shock():
    demand = _make_demand()
    cfg = MacroConfig.recession(shock_round=10, intensity=-0.40, duration=3)

    # Before shock
    assert not cfg.is_shock_active(9)
    t9 = cfg.apply(demand, 9)
    assert not t9["is_shock"]
    assert abs(t9["market_size"] - 100.0) < 1e-3

    # During shock
    assert cfg.is_shock_active(10)
    assert cfg.is_shock_active(12)
    t10 = cfg.apply(demand, 10)
    assert t10["is_shock"]
    assert abs(t10["market_size"] - 60.0) < 1e-3

    # After shock
    assert not cfg.is_shock_active(13)
    t13 = cfg.apply(demand, 13)
    assert not t13["is_shock"]
    assert abs(t13["market_size"] - 100.0) < 1e-3


def test_macro_cost_inflation():
    demand = _make_demand()
    cfg = MacroConfig.inflation(cost_trend=0.01)

    t1 = cfg.apply(demand, 1)
    assert abs(t1["cost_multiplier"] - 1.0) < 1e-4
    assert np.allclose(demand.costs, np.array([1.0, 1.0, 1.0]))

    t11 = cfg.apply(demand, 11)  # 10 rounds later -> +10%
    assert abs(t11["cost_multiplier"] - 1.10) < 1e-3
    assert np.allclose(demand.costs, np.array([1.10, 1.10, 1.10]))


def test_market_engine_with_macro():
    demand = _make_demand()
    agents = [
        SteadyAgent(firm_id=i, target_price=2.0)
        for i in range(3)
    ]
    macro = MacroConfig.recession(shock_round=5, intensity=-0.40, duration=3)
    engine = MarketEngine(demand, agents, macro=macro)

    rounds = engine.run(10)
    assert len(rounds) == 10
    
    # Check telemetry
    assert rounds[4].macro_telemetry is not None
    assert rounds[4].macro_telemetry["is_shock"] is True
    assert rounds[4].macro_telemetry["market_size"] < 100.0
    assert rounds[0].macro_telemetry["is_shock"] is False

    summary = engine.summary()
    assert "macro" in summary
    assert summary["macro"]["is_active"] is True
