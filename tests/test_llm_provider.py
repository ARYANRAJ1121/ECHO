"""
tests/test_llm_provider.py -- Unit and Integration Tests for Pluggable Cross-Model LLM Agents (F1)

Verifies:
1. Multi-provider instantiation (Groq, Gemini, Ollama) with correct default models.
2. Provider routing dispatches prompt to the appropriate backend.
3. Robust regex extraction of <scratchpad> and <price> XML tags.
4. Fallback numerical price extraction when LLM omits formal tags.
5. End-to-end engine builder for Gemini simulation.
"""

import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.llm_agent import LLMPricingAgent
from agents.base_agent import Observation
from run_simulation import build_gemini_simulation, build_llm_simulation
from data_loaders.gasoline import GasolineDataLoader


def test_provider_initialization():
    """Verify default models and provider routing attributes."""
    # Groq
    with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_groq_key"}):
        agent_groq = LLMPricingAgent(firm_id=0, provider="groq")
        assert agent_groq.provider == "groq"
        assert agent_groq.model == "allam-2-7b"

    # Gemini
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_gemini_key"}):
        agent_gemini = LLMPricingAgent(firm_id=1, provider="gemini")
        assert agent_gemini.provider == "gemini"
        assert agent_gemini.model == "gemini-3.5-flash-lite"

    # Custom model Gemini
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_gemini_key"}):
        agent_custom = LLMPricingAgent(firm_id=2, provider="gemini", model="gemini-2.5-pro")
        assert agent_custom.model == "gemini-2.5-pro"

    # Ollama
    agent_ollama = LLMPricingAgent(firm_id=3, provider="ollama")
    assert agent_ollama.provider == "ollama"
    assert agent_ollama.model == "llama3"


def test_provider_dispatch():
    """Verify that _call_llm routes calls to the appropriate provider method."""
    agent_gemini = LLMPricingAgent(firm_id=0, provider="gemini")
    agent_gemini._call_gemini = MagicMock(return_value="<scratchpad>test</scratchpad><price>3.85</price>")
    agent_gemini._call_groq = MagicMock()
    agent_gemini._call_ollama = MagicMock()

    res = agent_gemini._call_llm("System prompt\n\nUser prompt")
    assert "<price>3.85</price>" in res
    agent_gemini._call_gemini.assert_called_once()
    agent_gemini._call_groq.assert_not_called()
    agent_gemini._call_ollama.assert_not_called()

    # Ollama dispatch
    agent_ollama = LLMPricingAgent(firm_id=1, provider="ollama")
    agent_ollama._call_ollama = MagicMock(return_value="<scratchpad>test ollama</scratchpad><price>3.90</price>")
    res_ollama = agent_ollama._call_llm("System\n\nUser")
    assert "<price>3.90</price>" in res_ollama
    agent_ollama._call_ollama.assert_called_once()


def test_tag_parsing_and_fallback():
    """Verify parsing handles both well-formed XML tags and informal prose."""
    agent = LLMPricingAgent(firm_id=0, provider="gemini")
    obs = Observation(
        round_number=1,
        firm_id=0,
        marginal_cost=2.0,
        price_floor=3.0,
        price_ceiling=4.5,
        price_history=[[3.50] * 5],
        profit_history=[[100.0] * 5],
    )

    # 1. Clean XML
    xml_resp = "<scratchpad>Market is coordinating.</scratchpad>\n<price>3.75</price>"
    price, scratchpad = agent._parse_response(xml_resp, obs)
    assert price == 3.75
    assert scratchpad == "Market is coordinating."

    # 2. Informative fallback without tags
    informal_resp = "I think setting price to 3.82 is optimal to maximize margin."
    price2, scratchpad2 = agent._parse_response(informal_resp, obs)
    assert price2 == 3.82
    assert scratchpad2 == "[no scratchpad]"

    # 3. Clamping to bounds
    high_resp = "<scratchpad>Going high</scratchpad><price>99.99</price>"
    price3, scratchpad3 = agent._parse_response(high_resp, obs)
    assert price3 == 4.50
    assert scratchpad3 == "Going high"


def test_build_gemini_simulation_wiring():
    """Verify build_gemini_simulation configures 5 Gemini agents with legal price bands."""
    market_ctx = GasolineDataLoader().load()
    engine, rounds = build_gemini_simulation(n_rounds=10, market_ctx=market_ctx)

    assert rounds == 10
    assert len(engine.agents) == 5
    for a in engine.agents:
        assert isinstance(a, LLMPricingAgent)
        assert a.provider == "gemini"
        assert a.model == "gemini-3.5-flash-lite"


if __name__ == "__main__":
    test_provider_initialization()
    test_provider_dispatch()
    test_tag_parsing_and_fallback()
    test_build_gemini_simulation_wiring()
    print("All LLM Provider unit tests PASSED!")

