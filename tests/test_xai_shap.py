"""
tests/test_xai_shap.py -- Unit and Integration Tests for Explainable AI (XAI) & SHAP Attributions (F10)

Verifies:
1. Feature extraction and Random Forest model training with SHAP TreeExplainer.
2. Local per-round SHAP attribution computation across classes.
3. Natural-language explanation generator explaining why an agent is classified as cooperative/competitive.
4. Heuristic attribution fallback when model is untrained.
5. Publication-quality SHAP summary plot generation (08_xai_shap.png).
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from analysis.strategy_classifier import AgentStrategyClassifier, FEATURE_NAMES, StrategyPrediction


def test_heuristic_attribution_fallback():
    """Verify untrained classifier still outputs structured attributions and clear explanations."""
    classifier = AgentStrategyClassifier(nash_price=3.50, monopoly_price=4.20, n_firms=5)
    assert not classifier.is_trained

    # Firm pricing above Nash and stable -> Cooperative
    pred = classifier.predict_round(
        firm_id=0,
        round_number=5,
        prices=[4.00, 3.98, 4.02, 3.99, 4.01],
        prev_prices=[3.99, 3.98, 4.01, 3.98, 4.00],
        profits=[120.0, 118.0, 122.0, 119.0, 121.0],
        cost=3.00,
        price_history_window=[[4.00, 3.98, 4.02, 3.99, 4.01]] * 5,
    )

    assert isinstance(pred, StrategyPrediction)
    assert pred.predicted_strategy in ("cooperative", "competitive", "exploratory", "predatory")
    assert pred.attributions is not None
    assert len(pred.attributions) == len(FEATURE_NAMES)
    assert "price_vs_nash" in pred.attributions
    assert pred.explanation is not None
    assert len(pred.explanation) > 10


def test_shap_training_and_attributions():
    """Verify scikit-learn training initializes SHAP TreeExplainer and computes real SHAP values."""
    classifier = AgentStrategyClassifier(nash_price=3.50, monopoly_price=4.20, n_firms=5)

    # Synthetic 20-round price & profit history
    price_hist = []
    profit_hist = []
    for r in range(25):
        base_p = 3.60 + (r / 25.0) * 0.45
        noise = (np.arange(5) - 2) * 0.02
        prices = (base_p + noise).tolist()
        profits = [max(0.1, (p - 3.0) * 20.0) for p in prices]
        price_hist.append(prices)
        profit_hist.append(profits)

    X, y = classifier.extract_features(price_hist, profit_hist, cost=3.0)
    assert len(X) >= 20
    assert len(y) == len(X)

    train_res = classifier.train(X, y)
    assert classifier.is_trained
    assert train_res["training_accuracy"] > 0.70

    # Predict with trained model + SHAP TreeExplainer
    pred = classifier.predict_round(
        firm_id=0,
        round_number=26,
        prices=price_hist[-1],
        prev_prices=price_hist[-2],
        profits=profit_hist[-1],
        cost=3.00,
        price_history_window=price_hist[-5:],
    )

    assert pred.predicted_strategy in ("cooperative", "competitive", "exploratory", "predatory")
    assert pred.attributions is not None
    for name in FEATURE_NAMES:
        assert name in pred.attributions
        assert isinstance(pred.attributions[name], float)

    assert pred.explanation is not None
    assert "Driven by" in pred.explanation


def test_shap_summary_plot_generation():
    """Verify generate_shap_summary_plot writes 08_xai_shap.png."""
    classifier = AgentStrategyClassifier(nash_price=3.50, monopoly_price=4.20, n_firms=5)

    price_hist = []
    profit_hist = []
    for r in range(25):
        base_p = 3.60 + (r / 25.0) * 0.45
        noise = (np.arange(5) - 2) * 0.02
        prices = (base_p + noise).tolist()
        profits = [max(0.1, (p - 3.0) * 20.0) for p in prices]
        price_hist.append(prices)
        profit_hist.append(profits)

    X, y = classifier.extract_features(price_hist, profit_hist, cost=3.0)
    out_dir = os.path.join("analysis", "test_xai_output")
    out_fig = os.path.join(out_dir, "08_xai_shap.png")

    try:
        res_path = classifier.generate_shap_summary_plot(X, y, output_path=out_fig)
        assert res_path == out_fig
        assert os.path.isfile(out_fig)
        assert os.path.getsize(out_fig) > 1000
    finally:
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)


if __name__ == "__main__":
    test_heuristic_attribution_fallback()
    test_shap_training_and_attributions()
    test_shap_summary_plot_generation()
    print("All Explainable AI (SHAP) unit tests PASSED!")

