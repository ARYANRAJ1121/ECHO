"""
tests/test_network_detector.py -- Unit and Integration Tests for Graph-Based Detection (F7)

Verifies:
1. Network detector initialization and fallback handling.
2. High density & clustering detected on coordinated price series.
3. Lead-lag cross-correlation accurately pinpoints the intentional Price Leader.
4. Competitive independent prices produce low network density.
5. Publication network plot generation (09_collusion_network.png).
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from regulator.network_detector import CollusionNetworkDetector, NetworkAnalysisResult


def test_empty_and_short_history():
    """Verify detector safely returns default fallback on insufficient rounds."""
    detector = CollusionNetworkDetector(n_firms=5)
    short_history = [[3.5, 3.5, 3.5, 3.5, 3.5], [3.6, 3.6, 3.6, 3.6, 3.6]]
    res = detector.analyze(short_history)

    assert isinstance(res, NetworkAnalysisResult)
    assert res.density == 0.0
    assert res.verdict == "insufficient_data"


def test_competitive_pricing_network():
    """Independent uncoordinated prices produce low network density and competitive verdict."""
    detector = CollusionNetworkDetector(n_firms=5)
    rng = np.random.default_rng(42)

    # 30 rounds of random independent noise
    comp_prices = rng.normal(loc=3.5, scale=0.2, size=(30, 5)).tolist()
    res = detector.analyze(comp_prices)

    assert isinstance(res, NetworkAnalysisResult)
    assert res.density < 0.35
    assert res.verdict == "decentralized_competitive"


def test_collusive_price_leadership():
    """Firm 0 leads price hikes and firms 1-4 follow, verifying leader identification."""
    detector = CollusionNetworkDetector(
        n_firms=5,
        firm_names=["Alpha Leader", "Beta Follower", "Gamma Follower", "Delta Follower", "Epsilon Follower"],
    )

    n_rounds = 40
    prices = np.zeros((n_rounds, 5))
    prices[0, :] = 3.60

    # Firm 0 leads, Firms 1-4 lag by 1 round
    for t in range(1, n_rounds):
        # Leader sets new trend
        prices[t, 0] = prices[t - 1, 0] + 0.02 * (1 if (t % 4 < 2) else -0.5)
        # Followers copy leader's previous round
        for j in range(1, 5):
            prices[t, j] = prices[t - 1, 0] + 0.005 * (j - 2)

    res = detector.analyze(prices.tolist())

    assert isinstance(res, NetworkAnalysisResult)
    assert res.density >= 0.35
    # Firm 0 should be identified as the leader
    assert res.price_leader == "Alpha Leader"
    assert res.leader_firm_id == 0
    assert res.leader_score > 0.20


def test_network_plot_generation():
    """Verify generate_network_plot creates 09_collusion_network.png."""
    detector = CollusionNetworkDetector(n_firms=5)
    prices = np.ones((20, 5)) * 4.0 + np.random.randn(20, 5) * 0.05
    res = detector.analyze(prices.tolist())

    out_dir = os.path.join("analysis", "test_net_output")
    out_fig = os.path.join(out_dir, "09_collusion_network.png")

    try:
        plot_path = detector.generate_network_plot(res, output_path=out_fig)
        assert plot_path == out_fig
        assert os.path.isfile(out_fig)
        assert os.path.getsize(out_fig) > 1000
    finally:
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)


if __name__ == "__main__":
    test_empty_and_short_history()
    test_competitive_pricing_network()
    test_collusive_price_leadership()
    test_network_plot_generation()
    print("All Graph-Based Collusion Detection unit tests PASSED!")

