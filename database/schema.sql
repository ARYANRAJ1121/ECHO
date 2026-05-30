-- =============================================================
-- ECHO -- PostgreSQL Schema
-- =============================================================
--
-- WHY THIS FILE?
-- Defines ALL tables that store simulation data.
-- Auto-runs when PostgreSQL container starts for the first time.
--
-- TABLE DESIGN:
-- simulations  -> one row per experiment run
-- rounds       -> one row per round (linked to simulation)
-- firm_rounds  -> one row per firm per round (prices, profits, shares)
-- scratchpads  -> LLM reasoning text (one per firm per round)
-- collusion_metrics -> Lambda + detection alerts per round
--
-- LATER (Phase 4): embeddings table for RAG vector search
-- =============================================================

-- Enable pgvector extension (for RAG memory in Phase 4)
CREATE EXTENSION IF NOT EXISTS vector;

-- ----- Table 1: Simulations -----
-- Each experiment run (e.g., "5 LLM agents, 1000 rounds, mu=0.5")
CREATE TABLE simulations (
    sim_id        SERIAL PRIMARY KEY,
    started_at    TIMESTAMP DEFAULT NOW(),
    ended_at      TIMESTAMP,
    mode          VARCHAR(20) NOT NULL,          -- 'llm', 'dummy', 'rl', 'rag'
    n_firms       INTEGER NOT NULL,
    n_rounds      INTEGER NOT NULL,
    mu            FLOAT NOT NULL,                -- price sensitivity
    marginal_cost FLOAT NOT NULL,
    nash_price    FLOAT,                         -- computed benchmark
    monopoly_price FLOAT,                        -- computed benchmark
    config_json   JSONB                          -- full config dump for reproducibility
);

-- ----- Table 2: Rounds -----
-- One row per round of the game
CREATE TABLE rounds (
    round_id      SERIAL PRIMARY KEY,
    sim_id        INTEGER NOT NULL REFERENCES simulations(sim_id),
    round_number  INTEGER NOT NULL,
    avg_price     FLOAT NOT NULL,
    total_profit  FLOAT NOT NULL,
    outside_share FLOAT,
    collusion_index FLOAT NOT NULL,              -- Lambda
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(sim_id, round_number)
);

-- ----- Table 3: Firm Rounds -----
-- Per-firm data for each round (the core data table)
CREATE TABLE firm_rounds (
    id            SERIAL PRIMARY KEY,
    round_id      INTEGER NOT NULL REFERENCES rounds(round_id),
    sim_id        INTEGER NOT NULL REFERENCES simulations(sim_id),
    firm_id       INTEGER NOT NULL,              -- 0-4
    price         FLOAT NOT NULL,
    profit        FLOAT NOT NULL,
    market_share  FLOAT NOT NULL,
    UNIQUE(round_id, firm_id)
);

-- ----- Table 4: Scratchpads -----
-- LLM reasoning text (Phase 3 agents write these)
CREATE TABLE scratchpads (
    id            SERIAL PRIMARY KEY,
    round_id      INTEGER NOT NULL REFERENCES rounds(round_id),
    sim_id        INTEGER NOT NULL REFERENCES simulations(sim_id),
    firm_id       INTEGER NOT NULL,
    scratchpad    TEXT NOT NULL,                  -- the LLM's private reasoning
    response_time FLOAT,                         -- how long Ollama took (seconds)
    created_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE(round_id, firm_id)
);

-- ----- Table 5: Collusion Alerts -----
-- Raised by the Antitrust Regulator (Phase 5)
CREATE TABLE collusion_alerts (
    id            SERIAL PRIMARY KEY,
    sim_id        INTEGER NOT NULL REFERENCES simulations(sim_id),
    round_number  INTEGER NOT NULL,
    alert_type    VARCHAR(30) NOT NULL,          -- 'lambda_threshold', 'nlp_similarity', 'shock_response'
    severity      VARCHAR(10) NOT NULL,          -- 'low', 'medium', 'high'
    detail        JSONB,                         -- evidence payload
    created_at    TIMESTAMP DEFAULT NOW()
);

-- ----- Table 6: Embeddings (Phase 4 RAG) -----
-- Vector embeddings of market states for similarity search
CREATE TABLE embeddings (
    id            SERIAL PRIMARY KEY,
    sim_id        INTEGER NOT NULL REFERENCES simulations(sim_id),
    round_id      INTEGER NOT NULL REFERENCES rounds(round_id),
    firm_id       INTEGER NOT NULL,
    description   TEXT NOT NULL,                  -- text that was embedded
    embedding     vector(768),                   -- nomic-embed-text outputs 768 dims
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_rounds_sim ON rounds(sim_id);
CREATE INDEX idx_firm_rounds_sim ON firm_rounds(sim_id);
CREATE INDEX idx_firm_rounds_round ON firm_rounds(round_id);
CREATE INDEX idx_scratchpads_sim ON scratchpads(sim_id);
CREATE INDEX idx_scratchpads_round ON scratchpads(round_id);

-- Vector similarity index (for Phase 4 RAG -- cosine distance)
CREATE INDEX idx_embeddings_vector ON embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
