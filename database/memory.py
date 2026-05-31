"""
database/memory.py -- Hybrid Vector Memory Store (Phase 4: RAG)

=== WHAT IS HYBRID RAG? ===

Standard RAG: "Find past rounds that FEEL similar" (vector search only)
Hybrid RAG:   "Find past rounds that FEEL similar AND meet specific criteria"

It combines two search strategies in one query:
  1. SEMANTIC (pgvector): cosine similarity on text embeddings
  2. STRUCTURAL (SQL WHERE): filter on actual data columns

Example hybrid search:
  "Find rounds similar to now, WHERE:
   - my profit was above the simulation average
   - AND collusion index was > 0.3
   - AND I was not the cheapest firm"

This gives the agent SMARTER memories -- not just similar situations,
but similar situations where specific outcomes occurred.

=== WHY HYBRID > STANDARD FOR ECHO? ===

Standard RAG might return:
  "Round 47: similar prices, but you lost money"
  "Round 91: similar prices, but you lost money"
  "Round 120: similar prices, and you actually profited"

Hybrid RAG filters to only return:
  "Round 120: similar prices, and you actually profited"
  "Round 250: similar prices, and your profit was highest"
  "Round 310: similar prices, and coordination held for 20 rounds"

The agent learns from SUCCESS, not just similarity.

=== HOW IT WORKS TECHNICALLY ===

Single PostgreSQL query that:
  1. JOINs embeddings table with rounds + firm_rounds tables
  2. Applies SQL WHERE filters (profit, lambda, share thresholds)
  3. Orders by cosine similarity (pgvector <=> operator)
  4. Returns top-K results

No extra calls, no extra GPU usage. Just a smarter SQL query.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import psycopg2


class VectorMemory:
    """
    Hybrid RAG memory store using pgvector + SQL filtering.

    Combines semantic similarity (embeddings) with structural
    filtering (SQL WHERE on profit, lambda, market share) to
    retrieve the most relevant AND useful past experiences.
    """

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text",
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_user: str | None = None,
        db_password: str | None = None,
    ) -> None:
        self.ollama_host = ollama_host.rstrip("/")
        self.embed_model = embed_model

        self.conn = psycopg2.connect(
            host=db_host or os.getenv("ECHO_DB_HOST", "localhost"),
            port=db_port or int(os.getenv("ECHO_DB_PORT", "5433")),
            dbname=db_name or os.getenv("ECHO_DB_NAME", "echo"),
            user=db_user or os.getenv("ECHO_DB_USER", "echo_user"),
            password=db_password or os.getenv("ECHO_DB_PASSWORD", "echo_pass_2026"),
        )
        self.conn.autocommit = False

    # ----------------------------------------------------------------
    # Embedding
    # ----------------------------------------------------------------

    def embed_text(self, text: str) -> list[float]:
        """
        Convert text to a 768-dimensional vector using nomic-embed-text.

        Calls Ollama's /api/embed endpoint.
        Returns a list of 768 floats.
        """
        url = f"{self.ollama_host}/api/embed"
        payload = {
            "model": self.embed_model,
            "input": text,
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["embeddings"][0]

    # ----------------------------------------------------------------
    # Store
    # ----------------------------------------------------------------

    def store_market_state(
        self,
        sim_id: int,
        round_id: int,
        firm_id: int,
        description: str,
    ) -> None:
        """
        Embed a market state description and store it in pgvector.

        Called after each round for each firm.
        """
        embedding = self.embed_text(description)

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO embeddings
                (sim_id, round_id, firm_id, description, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            """,
            (sim_id, round_id, firm_id, description, str(embedding)),
        )
        self.conn.commit()

    # ----------------------------------------------------------------
    # Retrieve: Standard (semantic only)
    # ----------------------------------------------------------------

    def search_similar(
        self,
        query_text: str,
        sim_id: int,
        firm_id: int,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Standard RAG: find top-K similar past states using vector search only.

        This is the baseline. Use hybrid_search() for better results.
        """
        query_embedding = self.embed_text(query_text)
        emb_str = str(query_embedding)

        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT round_id, description,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM embeddings
            WHERE sim_id = %s AND firm_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (emb_str, sim_id, firm_id, emb_str, top_k),
        )

        return [
            {"round_id": row[0], "description": row[1], "similarity": row[2]}
            for row in cur.fetchall()
        ]

    # ----------------------------------------------------------------
    # Retrieve: Hybrid (semantic + structural)
    # ----------------------------------------------------------------

    def hybrid_search(
        self,
        query_text: str,
        sim_id: int,
        firm_id: int,
        top_k: int = 3,
        min_profit: float | None = None,
        max_profit: float | None = None,
        min_lambda: float | None = None,
        max_lambda: float | None = None,
        min_share: float | None = None,
        was_cheapest: bool | None = None,
        was_most_expensive: bool | None = None,
        profit_above_average: bool | None = None,
    ) -> list[dict[str, Any]]:
        """
        Hybrid RAG: semantic similarity + SQL structural filters.

        Combines pgvector cosine search with SQL WHERE clauses that
        filter on actual simulation data (profit, lambda, share).

        This is the KEY UPGRADE over standard RAG. The agent doesn't
        just recall similar situations -- it recalls similar situations
        where specific outcomes occurred.

        Parameters
        ----------
        query_text : str
            Description of current market state (will be embedded).
        sim_id : int
            Simulation to search within.
        firm_id : int
            Firm whose memories to search.
        top_k : int
            Number of results to return.
        min_profit : float, optional
            Only return rounds where firm profit >= this value.
        max_profit : float, optional
            Only return rounds where firm profit <= this value.
        min_lambda : float, optional
            Only return rounds where collusion index >= this value.
        max_lambda : float, optional
            Only return rounds where collusion index <= this value.
        min_share : float, optional
            Only return rounds where firm market share >= this value.
        was_cheapest : bool, optional
            If True, only rounds where this firm had the lowest price.
            If False, only rounds where this firm was NOT the cheapest.
        was_most_expensive : bool, optional
            If True, only rounds where this firm had the highest price.
        profit_above_average : bool, optional
            If True, only rounds where firm profit > avg profit across firms.

        Returns
        -------
        list[dict]
            Each dict has: round_id, description, similarity, profit,
            collusion_index, market_share
        """
        query_embedding = self.embed_text(query_text)
        emb_str = str(query_embedding)

        # Build dynamic WHERE clause
        conditions = ["e.sim_id = %s", "e.firm_id = %s"]
        params: list[Any] = [emb_str, sim_id, firm_id]

        if min_profit is not None:
            conditions.append("fr.profit >= %s")
            params.append(min_profit)

        if max_profit is not None:
            conditions.append("fr.profit <= %s")
            params.append(max_profit)

        if min_lambda is not None:
            conditions.append("r.collusion_index >= %s")
            params.append(min_lambda)

        if max_lambda is not None:
            conditions.append("r.collusion_index <= %s")
            params.append(max_lambda)

        if min_share is not None:
            conditions.append("fr.market_share >= %s")
            params.append(min_share)

        if profit_above_average is True:
            # Subquery: this firm's profit > average profit across all firms that round
            conditions.append("""
                fr.profit > (
                    SELECT AVG(fr2.profit)
                    FROM firm_rounds fr2
                    WHERE fr2.round_id = fr.round_id
                )
            """)

        if was_cheapest is True:
            conditions.append("""
                fr.price = (
                    SELECT MIN(fr2.price)
                    FROM firm_rounds fr2
                    WHERE fr2.round_id = fr.round_id
                )
            """)
        elif was_cheapest is False:
            conditions.append("""
                fr.price > (
                    SELECT MIN(fr2.price)
                    FROM firm_rounds fr2
                    WHERE fr2.round_id = fr.round_id
                )
            """)

        if was_most_expensive is True:
            conditions.append("""
                fr.price = (
                    SELECT MAX(fr2.price)
                    FROM firm_rounds fr2
                    WHERE fr2.round_id = fr.round_id
                )
            """)

        where_clause = " AND ".join(conditions)
        params.extend([emb_str, top_k])

        cur = self.conn.cursor()
        cur.execute(
            f"""
            SELECT e.round_id,
                   e.description,
                   1 - (e.embedding <=> %s::vector) AS similarity,
                   fr.profit,
                   fr.market_share,
                   r.collusion_index
            FROM embeddings e
            JOIN rounds r ON e.round_id = r.round_number AND e.sim_id = r.sim_id
            JOIN firm_rounds fr ON r.round_id = fr.round_id AND fr.firm_id = e.firm_id
            WHERE {where_clause}
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
            """,
            params,
        )

        return [
            {
                "round_id": row[0],
                "description": row[1],
                "similarity": row[2],
                "profit": row[3],
                "market_share": row[4],
                "collusion_index": row[5],
            }
            for row in cur.fetchall()
        ]

    # ----------------------------------------------------------------
    # Smart search (auto-selects filters based on context)
    # ----------------------------------------------------------------

    def smart_search(
        self,
        query_text: str,
        sim_id: int,
        firm_id: int,
        current_profit: float | None = None,
        current_lambda: float | None = None,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Intelligent hybrid search that auto-selects filters based on
        the agent's current situation.

        Strategy:
        - If profit is LOW:  search for rounds where profit was HIGH
          ("what should I do differently?")
        - If lambda is HIGH: search for rounds where lambda was also high
          AND profit was good ("is coordination working for me?")
        - If lambda is LOW:  search for any profitable rounds
          ("how do I make money in competitive markets?")

        This is what the RAG agent calls by default.
        """
        # Fallback to standard search if no context
        if current_profit is None and current_lambda is None:
            return self.search_similar(query_text, sim_id, firm_id, top_k)

        # Strategy 1: Profit is low → find rounds where I did well
        if current_profit is not None and current_profit < 0.01:
            return self.hybrid_search(
                query_text=query_text,
                sim_id=sim_id,
                firm_id=firm_id,
                top_k=top_k,
                profit_above_average=True,
            )

        # Strategy 2: High lambda → find high-lambda rounds where I profited
        if current_lambda is not None and current_lambda > 0.5:
            return self.hybrid_search(
                query_text=query_text,
                sim_id=sim_id,
                firm_id=firm_id,
                top_k=top_k,
                min_lambda=0.3,
                profit_above_average=True,
            )

        # Strategy 3: Low lambda → find any profitable similar rounds
        if current_lambda is not None and current_lambda < 0.3:
            return self.hybrid_search(
                query_text=query_text,
                sim_id=sim_id,
                firm_id=firm_id,
                top_k=top_k,
                profit_above_average=True,
            )

        # Default: standard semantic search
        return self.search_similar(query_text, sim_id, firm_id, top_k)

    # ----------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------

    @staticmethod
    def format_market_state(
        round_number: int,
        firm_id: int,
        prices: list[float],
        profits: list[float],
        shares: list[float],
        collusion_index: float,
        marginal_cost: float,
    ) -> str:
        """
        Convert raw round data into a natural-language description
        suitable for embedding.
        """
        my_price = prices[firm_id]
        my_profit = profits[firm_id]
        my_share = shares[firm_id]
        avg_price = sum(prices) / len(prices)

        other_prices = [p for i, p in enumerate(prices) if i != firm_id]
        other_str = ", ".join(f"{p:.3f}" for p in other_prices)

        return (
            f"Round {round_number}: "
            f"I (Firm {firm_id}) charged {my_price:.3f}, "
            f"earned profit {my_profit:.4f}, "
            f"captured {my_share:.1%} market share. "
            f"Competitor prices: [{other_str}]. "
            f"Average market price: {avg_price:.3f}. "
            f"Collusion index: {collusion_index:.3f}. "
            f"My markup over cost: {my_price - marginal_cost:.3f}."
        )

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
