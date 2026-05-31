"""
agents/rag_agent.py -- RAG-Enhanced LLM Pricing Agent (Phase 4)

=== WHY DOES THIS FILE EXIST? ===

This extends the LLM agent with episodic memory. Before choosing a price,
the agent searches its past experiences for similar market conditions:

  "Last time all prices were above 3.0, I charged 2.8 and earned 0.015.
   But when I undercut to 2.5, I earned 0.020 -- so undercutting worked."

This retrieved context is injected into the LLM prompt, giving the agent
a form of long-term memory beyond the 5-round sliding window.

=== THE RESEARCH QUESTION ===

Does episodic memory accelerate tacit coordination?

Hypothesis: RAG agents collude FASTER because they can recall:
- "Last time I kept prices high, competitors followed"
- "Undercutting led to a price war that hurt everyone"

This is tested via A/B experiment:
  Run A: 5 RAG agents, 1000 rounds
  Run B: 5 vanilla LLM agents, 1000 rounds
  Compare: Lambda convergence speed

=== HOW IT WORKS ===

1. After each round: embed the market state and store in pgvector
2. Before each decision: search pgvector for top-3 similar past states
3. Inject retrieved context into the LLM prompt
4. LLM sees: current state + "here's what happened in similar situations"

The key insight: the agent doesn't just see recent history (last 5 rounds),
it sees the MOST RELEVANT history regardless of when it happened.
"""

from __future__ import annotations

from agents.llm_agent import LLMPricingAgent
from agents.base_agent import Observation
from database.memory import VectorMemory


class RAGPricingAgent(LLMPricingAgent):
    """
    LLM agent with retrieval-augmented episodic memory.

    Inherits all behavior from LLMPricingAgent, but overrides
    prompt construction to include retrieved past experiences.

    Parameters
    ----------
    firm_id : int
        Which firm this agent controls.
    memory : VectorMemory
        Shared vector memory store (connected to pgvector).
    sim_id : int
        Current simulation ID (for memory isolation).
    top_k : int
        How many similar past states to retrieve. Default: 3.
    **kwargs
        Passed to LLMPricingAgent (ollama_host, model, temperature, etc.)
    """

    def __init__(
        self,
        firm_id: int,
        memory: VectorMemory,
        sim_id: int,
        top_k: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(firm_id=firm_id, **kwargs)
        self.name = f"RAG_Firm_{firm_id}"
        self.memory = memory
        self.sim_id = sim_id
        self.top_k = top_k

        # Track what memories were retrieved each round
        self.retrieved_memories: list[list[dict]] = []

    def choose_price(self, observation: Observation) -> float:
        """
        Choose a price using RAG-enhanced reasoning.

        1. Build query from current market state
        2. Search pgvector for similar past states
        3. Build prompt with retrieved context
        4. Call LLM for price decision
        5. After decision: store this round's state for future retrieval
        """
        # Step 1-2: Retrieve similar past experiences
        memories = self._retrieve_memories(observation)
        self.retrieved_memories.append(memories)

        # Step 3-4: Build RAG-enhanced prompt and get price
        # We override _build_prompt temporarily
        self._current_memories = memories
        price = super().choose_price(observation)
        self._current_memories = None

        return price

    def store_round_memory(
        self,
        round_id: int,
        observation: Observation,
        prices: list[float],
        profits: list[float],
        shares: list[float],
        collusion_index: float,
    ) -> None:
        """
        Store this round's outcome in vector memory.

        Called by the engine AFTER the round completes, so the agent
        can recall this experience in future rounds.
        """
        description = VectorMemory.format_market_state(
            round_number=observation.round_number,
            firm_id=self.firm_id,
            prices=prices,
            profits=profits,
            shares=shares,
            collusion_index=collusion_index,
            marginal_cost=observation.marginal_cost,
        )
        self.memory.store_market_state(
            sim_id=self.sim_id,
            round_id=round_id,
            firm_id=self.firm_id,
            description=description,
        )

    def _retrieve_memories(self, obs: Observation) -> list[dict]:
        """
        Search for similar past market states.

        Builds a description of the CURRENT state and queries pgvector.
        Returns top-K most similar past experiences.
        """
        if not obs.price_history:
            return []  # first round, no memories to search

        # Describe the current state (what we're about to face)
        last_prices = obs.price_history[-1]
        last_profits = obs.profit_history[-1]
        avg_price = sum(last_prices) / len(last_prices)

        query = (
            f"Market with average price {avg_price:.3f}. "
            f"My last price: {last_prices[self.firm_id]:.3f}. "
            f"My last profit: {last_profits[self.firm_id]:.4f}. "
            f"Competitor prices: {[p for i, p in enumerate(last_prices) if i != self.firm_id]}."
        )

        try:
            results = self.memory.search_similar(
                query_text=query,
                sim_id=self.sim_id,
                firm_id=self.firm_id,
                top_k=self.top_k,
            )
            return results
        except Exception as e:
            print(f"  [RAG Firm {self.firm_id}] Memory search failed: {e}")
            return []

    def _build_prompt(self, obs: Observation) -> str:
        """
        Override LLM agent's prompt to include retrieved memories.

        Adds a "Past Experience" section between the system prompt
        and the user prompt.
        """
        # Get the base prompt from parent
        base_prompt = super()._build_prompt(obs)

        # If no memories retrieved, use base prompt as-is
        memories = getattr(self, "_current_memories", None)
        if not memories:
            return base_prompt

        # Build memory context section
        memory_lines = [
            "\n--- RELEVANT PAST EXPERIENCES ---",
            "You recall similar market situations from your history:",
        ]

        for i, mem in enumerate(memories, 1):
            similarity = mem.get("similarity", 0)
            description = mem.get("description", "")
            memory_lines.append(
                f"\n  Memory {i} (relevance: {similarity:.2f}):"
                f"\n    {description}"
            )

        memory_lines.append(
            "\nUse these past experiences to inform your pricing decision. "
            "Consider what worked and what didn't in similar situations."
            "\n--- END PAST EXPERIENCES ---\n"
        )

        memory_section = "\n".join(memory_lines)

        # Insert memory section before the "Based on the market history" line
        insert_point = "Based on the market history above"
        if insert_point in base_prompt:
            return base_prompt.replace(
                insert_point,
                memory_section + "\n" + insert_point,
            )
        else:
            # Fallback: append before the last section
            return base_prompt + "\n" + memory_section
