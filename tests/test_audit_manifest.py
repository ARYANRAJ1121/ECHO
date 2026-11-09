"""
tests/test_audit_manifest.py -- Unit and integration tests for Reproducibility Manifests & Regulatory Audit Pack (F12)
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from market.demand import LogitDemandModel
from market.engine import MarketEngine
from agents.heuristic_agent import SteadyAgent, FollowerAgent
from regulator.audit_manifest import (
    compute_consumer_surplus,
    compute_gini,
    compute_welfare_audit,
    build_experiment_manifest,
    generate_regulatory_dossier_markdown,
    export_audit_pack,
    WelfareAuditReport,
)


def _make_test_engine(high_prices: bool = True) -> MarketEngine:
    model = LogitDemandModel(
        n_firms=4,
        marginal_cost=2.0,
        quality=[3.0] * 4,
        mu=0.5,
        market_size=1000.0,
    )
    b = model.get_benchmarks()
    target_p = b.monopoly_price if high_prices else b.nash_price
    agents = [
        SteadyAgent(firm_id=i, target_price=target_p + i * 0.05)
        for i in range(4)
    ]
    engine = MarketEngine(
        demand_model=model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=10.0,
    )
    engine.run(10)
    return engine


def test_consumer_surplus_and_gini():
    model = LogitDemandModel(
        n_firms=3,
        marginal_cost=1.0,
        quality=[2.0] * 3,
        mu=0.5,
        market_size=100.0,
    )
    # Higher prices must strictly reduce consumer surplus
    low_prices = np.array([1.5, 1.5, 1.5])
    high_prices = np.array([3.5, 3.5, 3.5])

    cs_low = compute_consumer_surplus(model, low_prices)
    cs_high = compute_consumer_surplus(model, high_prices)
    assert cs_low > cs_high

    # Gini coefficient test
    equal_profits = [10.0, 10.0, 10.0, 10.0]
    assert compute_gini(equal_profits) < 1e-4

    unequal_profits = [0.0, 0.0, 0.0, 100.0]
    assert compute_gini(unequal_profits) > 0.60


def test_welfare_audit_calculations():
    engine = _make_test_engine(high_prices=True)
    report: WelfareAuditReport = compute_welfare_audit(engine)

    assert report.total_rounds == 10
    assert report.total_consumer_welfare_loss > 0.0
    assert report.direct_overcharge_loss > 0.0
    assert report.total_deadweight_loss >= 0.0
    assert report.mean_lambda >= 0.70
    assert report.cartel_persistence_rounds > 0
    assert report.max_consecutive_cartel_streak > 0
    assert report.mean_markup_pct > 0.0


def test_manifest_generation_and_export():
    engine = _make_test_engine(high_prices=True)
    manifest = build_experiment_manifest(engine, seed=42)

    assert manifest.manifest_version == "1.0.0"
    assert "commit_hash" in manifest.git_provenance
    assert "python_version" in manifest.system_environment
    assert manifest.simulation_setup["n_rounds"] == 10
    assert manifest.simulation_setup["random_seed"] == 42
    assert "ACTIONABLE_TACIT_COLLUSION" in manifest.regulatory_verdict

    # Test export to temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        network_rep = {"ring_leader": "Firm 0", "network_density": 0.75}
        shap_rep = {"global_importance": {"price_vs_nash": 0.45, "is_cheapest": 0.22}}

        paths = export_audit_pack(
            engine,
            output_dir=tmpdir,
            seed=42,
            network_report=network_rep,
            shap_report=shap_rep,
        )

        assert os.path.isfile(paths["manifest_json"])
        assert os.path.isfile(paths["regulatory_dossier_md"])

        # Validate JSON parseability
        with open(paths["manifest_json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["simulation_setup"]["n_rounds"] == 10
            assert "welfare_audit" in data

        # Validate Markdown content
        with open(paths["regulatory_dossier_md"], "r", encoding="utf-8") as f:
            md_text = f.read()
            assert "# ANTITRUST REGULATORY AUDIT & COMPLIANCE DOSSIER" in md_text
            assert "Firm 0" in md_text
            assert "0.75" in md_text
            assert "price_vs_nash" in md_text

