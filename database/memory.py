"""
database/memory.py -- Vector Memory Store (Phase 4: RAG)

=== WHY DOES THIS FILE EXIST? ===

This is the "brain" of the RAG system. It does two things:

1. STORE: After each round, convert the market state into text,
   embed it using nomic-embed-text (via Ollama), and save the
   768-dimensional vector + metadata into pgvector.

2. RETRIEVE: Before each pricing decision, the RAG agent asks:
   "What happened in rounds that looked like this one?"
   This file searches pgvector for the top-K most similar past
   states and returns them as context for the LLM prompt.

=== WHY IS THIS IMPORTANT FOR RESEARCH? ===

Standard LLM agents only see the last 5 rounds (their prompt window).
RAG agents can search their ENTIRE history. The research question:

"Does episodic memory accelerate tacit coordination?"

If RAG agents collude faster than vanilla LLM agents, it means
memory is a mechanism for coordination -- a novel finding.

=== HOW EMBEDDINGS WORK ===

nomic-embed-text converts text -> 768 numbers (a vector).
Similar text -> similar vectors (close in 768-dimensional space).

Example:
  "Round 47: all prices above 3.0, my profit 0.02" -> [0.12, -0.34, ...]
  "Round 91: all prices above 2.9, my profit 0.019" -> [0.11, -0.33, ...]

These two vectors are CLOSE because the market states are SIMILAR.
pgvector finds this with cosine similarity search.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import psycopg2


class VectorMemory:
    """
    Store and retrieve market state embeddings using pgvector.

    Parameters
    ----------
    ollama_host : str
        Ollama API URL for embedding model.
    embed_model : str
        Which Ollama model to use for embeddings.
    db_host, db_port, db_name, db_user, db_password : str/int
        PostgreSQL connection parameters.
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
        # Ollama returns {"embeddings": [[...768 floats...]]}
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

        Called after each round for each firm. The description is a
        natural-language summary of what happened:
          "Round 47: I charged 2.50, earned 0.015. Avg price was 2.80.
           Competitors: [2.50, 3.00, 2.90, 3.10]. Lambda = 0.45."

        Parameters
        ----------
        sim_id : int
            Simulation ID (for isolation between experiments).
        round_id : int
            Database round ID.
        firm_id : int
            Which firm's perspective this is from.
        description : str
            Natural-language market state summary.
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
    # Retrieve
    # ----------------------------------------------------------------

    def search_similar(
        self,
        query_text: str,
        sim_id: int,
        firm_id: int,
        top_k: int = 3,
        exclude_round_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find the top-K most similar past market states for a given firm.

        Uses cosine similarity search via pgvector's <=> operator.

        Parameters
        ----------
        query_text : str
            Description of the CURRENT market state.
        sim_id : int
            Only search within this simulation (no cross-contamination).
        firm_id : int
            Only search this firm's memories.
        top_k : int
            How many results to return. Default: 3.
        exclude_round_ids : list[int]
            Round IDs to exclude (e.g., current round).

        Returns
        -------
        list[dict]
            Each dict has: round_id, description, similarity_score
        """
        query_embedding = self.embed_text(query_text)

        cur = self.conn.cursor()

        exclude_clause = ""
        params: list[Any] = [str(query_embedding), sim_id, firm_id]

        if exclude_round_ids:
            placeholders = ", ".join(["%s"] * len(exclude_round_ids))
            exclude_clause = f"AND round_id NOT IN ({placeholders})"
            params.extend(exclude_round_ids)

        params.append(top_k)

        cur.execute(
            f"""
            SELECT round_id, description,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM embeddings
            WHERE sim_id = %s AND firm_id = %s
            {exclude_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            [str(query_embedding), sim_id, firm_id]
            + (exclude_round_ids or [])
            + [str(query_embedding), top_k],
        )

        results = []
        for row in cur.fetchall():
            results.append({
                "round_id": row[0],
                "description": row[1],
                "similarity": row[2],
            })

        return results

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

        This is what gets embedded and stored in pgvector.
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
