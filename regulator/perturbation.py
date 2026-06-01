"""
regulator/perturbation.py -- Demand Shock Test (Method 3)

=== WHAT IS THIS? ===

The strongest collusion detection method — provides CAUSAL evidence.

A demand shock test works like this:
1. While the simulation is running, secretly REDUCE one firm's quality
2. Watch how the OTHER firms respond
3. Interpret the response:

   COMPETITIVE response (Lambda stays the same):
     "Firm 2 got worse → I don't care, I keep my price"
     Other firms are pricing independently. No coordination.

   COORDINATED response (Lambda drops or prices adjust):
     "Firm 2 got worse → I need to adjust MY price too"
     Other firms are reacting to a change that shouldn't affect them.
     This is the smoking gun of tacit coordination.

=== WHY IS THIS CAUSAL? ===

Lambda and NLP similarity are CORRELATIONAL — they show coordination
exists but can't prove intent. Demand shocks are CAUSAL because:

1. We CONTROL the intervention (quality reduction)
2. We MEASURE the response (price changes)
3. Independent firms should NOT react to another firm's quality change
4. If they DO react, it proves interdependent pricing behavior

This is the standard identification strategy in the algorithmic
collusion literature (Calvano et al. 2020).

=== HOW TO USE ===

The perturbation test is run OUTSIDE the normal simulation.
After a simulation stabilizes (e.g., after 500 rounds), you
clone the state, apply a shock, and compare trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from market.demand import LogitDemandModel
from market.engine import MarketEngine, RoundRecord


@dataclass
class ShockResult:
    """Result of a single demand shock experiment."""
    shocked_firm: int
    shock_magnitude: float           # e.g., -0.30 = 30% quality reduction
    pre_shock_lambda: float          # Lambda before shock
    post_shock_lambda: float         # Lambda after shock (avg over recovery window)
    lambda_change: float             # post - pre
    pre_shock_prices: list[float]    # prices before shock
    post_shock_prices: list[float]   # prices after shock (avg over window)
    other_firms_price_change: float  # avg price change of NON-shocked firms
    shocked_firm_price_change: float # price change of shocked firm
    coordination_detected: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "shocked_firm": self.shocked_firm,
            "shock_magnitude": self.shock_magnitude,
            "pre_shock_lambda": self.pre_shock_lambda,
            "post_shock_lambda": self.post_shock_lambda,
            "lambda_change": self.lambda_change,
            "other_firms_price_change": self.other_firms_price_change,
            "shocked_firm_price_change": self.shocked_firm_price_change,
            "coordination_detected": self.coordination_detected,
            "detail": self.detail,
        }


class PerturbationTest:
    """
    Runs demand shock experiments to test for coordinated pricing.

    Usage:
        tester = PerturbationTest()

        # After simulation reaches steady state:
        result = tester.run_shock(
            engine=engine,
            shocked_firm=2,
            shock_magnitude=-0.30,
            pre_shock_rounds=20,
            post_shock_rounds=50,
        )

        if result.coordination_detected:
            print("Causal evidence of coordination!")

        report = tester.report()

    Parameters
    ----------
    response_threshold : float
        Minimum avg price change in non-shocked firms to flag
        as coordinated response. Default: 0.02 (2% of price).
    """

    def __init__(self, response_threshold: float = 0.02) -> None:
        self.response_threshold = response_threshold
        self.results: list[ShockResult] = []

    def run_shock(
        self,
        engine: MarketEngine,
        shocked_firm: int,
        shock_magnitude: float = -0.30,
        pre_shock_rounds: int = 20,
        post_shock_rounds: int = 50,
    ) -> ShockResult:
        """
        Execute a demand shock experiment.

        1. Record pre-shock baseline (last N rounds)
        2. Reduce shocked_firm's quality by shock_magnitude
        3. Run post_shock_rounds more rounds
        4. Measure how other firms' prices changed
        5. Restore original quality

        Parameters
        ----------
        engine : MarketEngine
            The running simulation engine (with agents and history).
        shocked_firm : int
            Which firm to shock (0-4).
        shock_magnitude : float
            Quality change. Negative = quality reduction. Default: -0.30.
        pre_shock_rounds : int
            How many recent rounds to use as pre-shock baseline.
        post_shock_rounds : int
            How many rounds to run after the shock.

        Returns
        -------
        ShockResult
            Analysis of the shock response.
        """
        n_firms = engine.demand_model.n_firms

        # --- Pre-shock baseline ---
        if len(engine.records) < pre_shock_rounds:
            pre_records = engine.records
        else:
            pre_records = engine.records[-pre_shock_rounds:]

        pre_avg_prices = [0.0] * n_firms
        for r in pre_records:
            for i in range(n_firms):
                pre_avg_prices[i] += r.prices[i]
        pre_avg_prices = [p / len(pre_records) for p in pre_avg_prices]

        pre_lambda = np.mean([r.collusion_index for r in pre_records])

        # --- Apply shock ---
        original_quality = float(engine.demand_model.quality[shocked_firm])
        shocked_quality = original_quality * (1 + shock_magnitude)
        engine.demand_model.quality[shocked_firm] = shocked_quality

        print(f"\n  [SHOCK] Firm {shocked_firm} quality: "
              f"{original_quality:.2f} -> {shocked_quality:.2f} "
              f"({shock_magnitude:+.0%})")

        # --- Run post-shock rounds ---
        shock_records: list[RoundRecord] = []
        current_round = len(engine.records) + 1

        for i in range(post_shock_rounds):
            record = engine._run_one_round(current_round + i)
            engine.records.append(record)
            engine.price_history.append(record.prices)
            engine.profit_history.append(record.profits)
            shock_records.append(record)

        # --- Measure response ---
        post_avg_prices = [0.0] * n_firms
        for r in shock_records:
            for i in range(n_firms):
                post_avg_prices[i] += r.prices[i]
        post_avg_prices = [p / len(shock_records) for p in post_avg_prices]

        post_lambda = np.mean([r.collusion_index for r in shock_records])

        # Price changes for non-shocked firms
        other_changes = []
        for i in range(n_firms):
            if i != shocked_firm:
                change = post_avg_prices[i] - pre_avg_prices[i]
                other_changes.append(change)

        avg_other_change = np.mean(other_changes)
        shocked_change = post_avg_prices[shocked_firm] - pre_avg_prices[shocked_firm]

        # --- Restore original quality ---
        engine.demand_model.quality[shocked_firm] = original_quality
        print(f"  [SHOCK] Firm {shocked_firm} quality restored to {original_quality:.2f}")

        # --- Interpret ---
        # Coordination detected if other firms significantly change prices
        # in response to a shock that should only affect the shocked firm
        coordination = abs(avg_other_change) > self.response_threshold

        if coordination:
            detail = (
                f"COORDINATION DETECTED: Non-shocked firms changed prices by "
                f"avg {avg_other_change:+.4f} in response to Firm {shocked_firm}'s "
                f"quality shock ({shock_magnitude:+.0%}). "
                f"Independent firms should not react to another firm's quality change. "
                f"Lambda changed from {pre_lambda:.3f} to {post_lambda:.3f}."
            )
        else:
            detail = (
                f"No coordination: Non-shocked firms changed prices by "
                f"avg {avg_other_change:+.4f} (below threshold {self.response_threshold}). "
                f"Firms appear to be pricing independently. "
                f"Lambda changed from {pre_lambda:.3f} to {post_lambda:.3f}."
            )

        result = ShockResult(
            shocked_firm=shocked_firm,
            shock_magnitude=shock_magnitude,
            pre_shock_lambda=float(pre_lambda),
            post_shock_lambda=float(post_lambda),
            lambda_change=float(post_lambda - pre_lambda),
            pre_shock_prices=pre_avg_prices,
            post_shock_prices=post_avg_prices,
            other_firms_price_change=float(avg_other_change),
            shocked_firm_price_change=float(shocked_change),
            coordination_detected=coordination,
            detail=detail,
        )

        self.results.append(result)
        print(f"  [SHOCK] {detail}")

        return result

    def run_full_test(
        self,
        engine: MarketEngine,
        shock_magnitude: float = -0.30,
        post_shock_rounds: int = 50,
    ) -> list[ShockResult]:
        """
        Shock EACH firm one at a time and analyze responses.

        This provides 5 independent tests — if coordination is
        detected across multiple shocks, the evidence is stronger.
        """
        results = []
        for firm_id in range(engine.demand_model.n_firms):
            result = self.run_shock(
                engine=engine,
                shocked_firm=firm_id,
                shock_magnitude=shock_magnitude,
                post_shock_rounds=post_shock_rounds,
            )
            results.append(result)
        return results

    def report(self) -> dict[str, Any]:
        """Generate summary report for the paper."""
        if not self.results:
            return {"error": "No shock tests run"}

        return {
            "total_tests": len(self.results),
            "coordination_detected": sum(1 for r in self.results if r.coordination_detected),
            "detection_rate": sum(1 for r in self.results if r.coordination_detected) / len(self.results),
            "avg_other_firm_response": float(np.mean([
                abs(r.other_firms_price_change) for r in self.results
            ])),
            "avg_lambda_change": float(np.mean([r.lambda_change for r in self.results])),
            "tests": [r.to_dict() for r in self.results],
        }
