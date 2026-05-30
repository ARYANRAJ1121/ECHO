"""
database/db.py -- PostgreSQL Logger

=== WHY DOES THIS FILE EXIST? ===

Without this, simulation data prints to terminal and disappears.
This file saves EVERY round to PostgreSQL so you can:
- Run 10,000 rounds and analyze later with SQL
- Compare experiments (LLM vs RL vs heuristic)
- Feed data into Phase 7 plotting

=== HOW IT WORKS ===

1. At simulation START: insert a row into `simulations` table
2. After EACH round: insert rows into `rounds`, `firm_rounds`, `scratchpads`
3. At simulation END: update `simulations.ended_at`

=== CONNECTION ===

Uses psycopg2 (standard PostgreSQL driver for Python).
Connects to localhost:5432 by default (the Docker container).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any

import psycopg2
from psycopg2.extras import Json

from market.engine import RoundRecord


class DatabaseLogger:
    """
    Saves simulation data to PostgreSQL.

    Usage:
        logger = DatabaseLogger()
        sim_id = logger.start_simulation(config_dict)
        # ... after each round ...
        logger.log_round(sim_id, record, scratchpads)
        # ... at the end ...
        logger.end_simulation(sim_id)
        logger.close()

    Parameters
    ----------
    host : str
        PostgreSQL host. Default: localhost (Docker container).
    port : int
        PostgreSQL port. Default: 5432.
    dbname : str
        Database name. Default: echo.
    user : str
        Database user. Default: echo_user.
    password : str
        Database password. Default: echo_pass_2026.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        dbname: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        # Read from environment variables or use defaults
        self.conn = psycopg2.connect(
            host=host or os.getenv("ECHO_DB_HOST", "localhost"),
            port=port or int(os.getenv("ECHO_DB_PORT", "5433")),
            dbname=dbname or os.getenv("ECHO_DB_NAME", "echo"),
            user=user or os.getenv("ECHO_DB_USER", "echo_user"),
            password=password or os.getenv("ECHO_DB_PASSWORD", "echo_pass_2026"),
        )
        self.conn.autocommit = False  # we'll commit explicitly

    def start_simulation(self, config: dict[str, Any]) -> int:
        """
        Register a new simulation run. Returns the sim_id.

        Called ONCE at the beginning of a simulation.
        Stores the experiment config so it's fully reproducible.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO simulations
                (mode, n_firms, n_rounds, mu, marginal_cost,
                 nash_price, monopoly_price, config_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING sim_id
            """,
            (
                config.get("mode", "unknown"),
                config.get("n_firms", 5),
                config.get("n_rounds", 0),
                config.get("mu", 0.25),
                config.get("marginal_cost", 1.0),
                config.get("nash_price"),
                config.get("monopoly_price"),
                Json(config),
            ),
        )
        sim_id = cur.fetchone()[0]
        self.conn.commit()
        print(f"  [DB] Simulation registered: sim_id={sim_id}")
        return sim_id

    def log_round(
        self,
        sim_id: int,
        record: RoundRecord,
        scratchpads: dict[int, str] | None = None,
        response_times: dict[int, float] | None = None,
    ) -> None:
        """
        Save one round of data to the database.

        Called after EVERY round. Inserts into:
        - rounds (aggregate data: avg_price, Lambda)
        - firm_rounds (per-firm: price, profit, share)
        - scratchpads (LLM reasoning text, if available)
        """
        cur = self.conn.cursor()

        # Insert round summary
        cur.execute(
            """
            INSERT INTO rounds
                (sim_id, round_number, avg_price, total_profit,
                 outside_share, collusion_index)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING round_id
            """,
            (
                sim_id,
                record.round_number,
                record.avg_price,
                record.total_profit,
                record.outside_share,
                record.collusion_index,
            ),
        )
        round_id = cur.fetchone()[0]

        # Insert per-firm data
        for firm_id in range(len(record.prices)):
            cur.execute(
                """
                INSERT INTO firm_rounds
                    (round_id, sim_id, firm_id, price, profit, market_share)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    round_id,
                    sim_id,
                    firm_id,
                    record.prices[firm_id],
                    record.profits[firm_id],
                    record.shares[firm_id],
                ),
            )

        # Insert scratchpads (if LLM agents)
        if scratchpads:
            for firm_id, text in scratchpads.items():
                resp_time = response_times.get(firm_id) if response_times else None
                cur.execute(
                    """
                    INSERT INTO scratchpads
                        (round_id, sim_id, firm_id, scratchpad, response_time)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (round_id, sim_id, firm_id, text, resp_time),
                )

        self.conn.commit()

    def end_simulation(self, sim_id: int) -> None:
        """Mark simulation as complete. Called once at the end."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE simulations SET ended_at = NOW() WHERE sim_id = %s",
            (sim_id,),
        )
        self.conn.commit()
        print(f"  [DB] Simulation {sim_id} marked complete.")

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
