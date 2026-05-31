"""
agents/rag_agent.py -- Hybrid RAG Pricing Agent (Phase 4)

=== WHAT IS THIS? ===

An LLM pricing agent with Hybrid RAG episodic memory.

Before choosing a price, the agent searches its past experiences
using BOTH vector similarity AND SQL filters:

  Standard RAG:  "Find rounds that feel similar"
  Hybrid RAG:    "Find rounds that feel similar AND where I profited"

The agent automatically picks the right search strategy based on
its current situation (smart_search):

  - Profit low?  -> Search for rounds where I did well
  - Lambda high? -> Search for high-coordination rounds where I profited
  - Lambda low?  -> Search for profitable rounds in competitive markets

=== RESEARCH QUESTION ===

Does episodic memory with structured filtering accelerate tacit
coordination compared to vanilla LLM agents?

A/B Experiment:
  Run A: 5 Hybrid RAG agents, 1000 rounds
  Run B: 5 vanilla LLM agents, 1000 rounds
  Compare: Lambda convergence speed, profit trajectories
"""

from __future__ import annotations

from agents.llm_agent import LLMPricingAgent
from agents.base_agent import Observation
from database.memory import VectorMemory


class RAGPricingAgent(LLMPricingAgent):
    """
    LLM agent with hybrid retrieval-augmented episodic memory.

    Uses smart_search() which combines semantic similarity with
    SQL filters to retrieve the most relevant AND profitable
    past experiences.
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
        Choose a price using Hybrid RAG reasoning.

        1. Determine current context (profit, lambda)
        2. Smart search: semantic + structural filters
        3. Inject retrieved memories into LLM prompt
        4. Call LLM for price decision
        """
        # Step 1-2: Retrieve memories with hybrid search
        memories = self._retrieve_memories(observation)
        self.retrieved_memories.append(memories)

        # Step 3-4: Build RAG-enhanced prompt and get price
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
        Hybrid memory retrieval: semantic similarity + structural filters.

        Uses smart_search() which auto-selects the best filter strategy
        based on the agent's current profit and collusion index.
        """
        if not obs.price_history:
            return []  # first round, no memories to search

        # Current context for smart filtering
        last_prices = obs.price_history[-1]
        last_profits = obs.profit_history[-1]
        avg_price = sum(last_prices) / len(last_prices)

        current_profit = last_profits[self.firm_id]

        # Estimate current lambda from recent prices
        current_lambda = None  # smart_search uses profit-based heuristics

        # Build semantic query describing current state
        query = (
            f"Market with average price {avg_price:.3f}. "
            f"My last price: {last_prices[self.firm_id]:.3f}. "
            f"My last profit: {last_profits[self.firm_id]:.4f}. "
            f"Competitor prices: {[round(p, 3) for i, p in enumerate(last_prices) if i != self.firm_id]}."
        )

        try:
            # Use hybrid smart_search instead of basic search_similar
            results = self.memory.smart_search(
                query_text=query,
                sim_id=self.sim_id,
                firm_id=self.firm_id,
                current_profit=current_profit,
                current_lambda=current_lambda,
                top_k=self.top_k,
            )
            return results
        except Exception as e:
            # Fallback to standard search if hybrid fails
            print(f"  [RAG Firm {self.firm_id}] Hybrid search failed, falling back: {e}")
            try:
                return self.memory.search_similar(
                    query_text=query,
                    sim_id=self.sim_id,
                    firm_id=self.firm_id,
                    top_k=self.top_k,
                )
            except Exception as e2:
                print(f"  [RAG Firm {self.firm_id}] Fallback also failed: {e2}")
                return []

    def _build_prompt(self, obs: Observation) -> str:
        """
        Override LLM agent's prompt to include retrieved memories.

        Adds a structured "Past Experience" section with metadata
        (profit, lambda, similarity score) for each retrieved memory.
        """
        base_prompt = super()._build_prompt(obs)

        memories = getattr(self, "_current_memories", None)
        if not memories:
            return base_prompt

        # Build memory context section with rich metadata
        memory_lines = [
            "\n--- RELEVANT PAST EXPERIENCES (from your memory) ---",
            "You recall these similar market situations from your history.",
            "These are filtered to show the most useful experiences:",
        ]

        for i, mem in enumerate(memories, 1):
            similarity = mem.get("similarity", 0)
            description = mem.get("description", "")
            profit = mem.get("profit")
            collusion_index = mem.get("collusion_index")
            market_share = mem.get("market_share")

            # Build metadata string
            meta_parts = [f"relevance: {similarity:.2f}"]
            if profit is not None:
                meta_parts.append(f"profit: {profit:.4f}")
            if collusion_index is not None:
                meta_parts.append(f"lambda: {collusion_index:.3f}")
            if market_share is not None:
                meta_parts.append(f"share: {market_share:.1%}")

            meta_str = " | ".join(meta_parts)

            memory_lines.append(
                f"\n  Memory {i} ({meta_str}):"
                f"\n    {description}"
            )

        memory_lines.append(
            "\nLearn from these experiences. What pricing strategies led to "
            "good profits? What patterns do you notice?"
            "\n--- END PAST EXPERIENCES ---\n"
        )

        memory_section = "\n".join(memory_lines)

        # Insert memory section before the decision prompt
        insert_point = "Based on the market history above"
        if insert_point in base_prompt:
            return base_prompt.replace(
                insert_point,
                memory_section + "\n" + insert_point,
            )
        else:
            return base_prompt + "\n" + memory_section
