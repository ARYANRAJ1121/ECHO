"""
tests/test_info_structure.py -- Unit and integration tests for Information Structure variations (F4)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from market.demand import LogitDemandModel
from market.engine import MarketEngine
from market.info_structure import InfoConfig
from agents.heuristic_agent import FollowerAgent, SteadyAgent
from agents.base_agent import Observation, PricingAgent


def _make_demand() -> LogitDemandModel:
    return LogitDemandModel(
        n_firms=3,
        quality=[2.0, 2.0, 2.0],
        marginal_cost=1.0,
        mu=0.25,
        market_size=100.0,
    )


class MockCommunicatingAgent(PricingAgent):
    """Test agent that implements custom announcement and private message hooks."""

    def __init__(self, firm_id: int, base_price: float):
        super().__init__(firm_id=firm_id, name=f"MockAgent_{firm_id}")
        self.base_price = base_price
        self.received_announcements = None
        self.received_messages = None
        self.scratchpad_history = [f"Internal thought from firm {firm_id}"]

    def announce_intention(self, observation: Observation) -> float | None:
        return self.base_price + 0.10

    def send_private_message(self, observation: Observation, recipient_id: int) -> str | None:
        return f"Secret signal to firm {recipient_id}: target={self.base_price:.2f}"

    def choose_price(self, observation: Observation) -> float:
        self.received_announcements = observation.intended_prices
        self.received_messages = observation.private_messages
        # If rival announced a high price, match it
        if observation.intended_prices:
            return max(self.base_price, max(observation.intended_prices.values()))
        return self.base_price


def test_info_config_initialization():
    base = InfoConfig.baseline()
    assert base.is_tacit()
    assert not base.has_announcements()

    ann = InfoConfig.announcements(noise=0.02)
    assert not ann.is_tacit()
    assert ann.has_announcements()
    assert ann.announcement_noise == 0.02

    priv = InfoConfig.private_messages([(0, 1)])
    assert priv.has_private_channels()
    assert priv.private_pairs == [(0, 1)]

    sp = InfoConfig.shared_scratchpads()
    assert sp.has_shared_scratchpads()


def test_announcement_protocol():
    demand = _make_demand()
    agents = [
        MockCommunicatingAgent(0, 2.0),
        MockCommunicatingAgent(1, 2.2),
        MockCommunicatingAgent(2, 2.4),
    ]
    info = InfoConfig.announcements()
    engine = MarketEngine(demand, agents, info_config=info)
    records = engine.run(3)

    assert len(records) == 3
    rec = records[0]
    assert rec.info_telemetry is not None
    assert rec.info_telemetry["protocol"] == "announcements"
    assert "intended_prices" in rec.info_telemetry
    assert len(rec.info_telemetry["intended_prices"]) == 3
    # Check agent received intended prices in observation
    assert agents[0].received_announcements is not None
    assert len(agents[0].received_announcements) == 3


def test_private_messaging_protocol():
    demand = _make_demand()
    agents = [
        MockCommunicatingAgent(0, 2.0),
        MockCommunicatingAgent(1, 2.2),
        MockCommunicatingAgent(2, 2.4),
    ]
    info = InfoConfig.private_messages(pairs=[(0, 1)])
    engine = MarketEngine(demand, agents, info_config=info)
    records = engine.run(2)

    assert len(records) == 2
    rec = records[0]
    assert rec.info_telemetry is not None
    assert rec.info_telemetry["protocol"] == "private_messages"
    assert rec.info_telemetry["private_channels_count"] == 1

    # Firm 1 should have received message from firm 0
    assert agents[1].received_messages is not None
    assert 0 in agents[1].received_messages
    assert "Secret signal to firm 1" in agents[1].received_messages[0]


def test_shared_scratchpads_protocol():
    demand = _make_demand()
    agents = [
        MockCommunicatingAgent(0, 2.0),
        MockCommunicatingAgent(1, 2.2),
        MockCommunicatingAgent(2, 2.4),
    ]
    info = InfoConfig.shared_scratchpads()
    engine = MarketEngine(demand, agents, info_config=info)
    records = engine.run(2)

    assert len(records) == 2
    rec = records[0]
    assert rec.info_telemetry is not None
    assert rec.info_telemetry["protocol"] == "shared_scratchpads"
    assert rec.info_telemetry["shared_scratchpads_count"] == 3


def test_summary_info_structure():
    demand = _make_demand()
    agents = [
        SteadyAgent(0, target_price=2.0),
        SteadyAgent(1, target_price=2.0),
        SteadyAgent(2, target_price=2.0),
    ]
    info = InfoConfig.announcements()
    engine = MarketEngine(demand, agents, info_config=info)
    engine.run(2)
    summary = engine.summary()

    assert "info_structure" in summary
    assert summary["info_structure"]["protocol"] == "announcements"
