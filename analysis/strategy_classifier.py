"""
analysis/strategy_classifier.py -- ML-Based Agent Strategy Classifier

=== WHAT IS THIS? ===

A scikit-learn Random Forest classifier that automatically labels each
agent's pricing behavior on a per-round basis as one of:

  - 'competitive':   undercutting rivals, seeking market share
  - 'cooperative':   maintaining high prices, matching rivals
  - 'predatory':     pricing below cost to eliminate competitors
  - 'exploratory':   volatile/random pricing with no clear strategy

=== HOW IT WORKS ===

1. FEATURE EXTRACTION: For each (agent, round) pair, we compute:
   - price_vs_nash: how far above/below the Nash equilibrium
   - price_vs_avg:  how far above/below the market average
   - price_change:  direction and magnitude of price change from last round
   - profit_trend:  is profit rising or falling
   - market_share:  current market share
   - price_volatility: standard deviation of last 5 prices

2. LABELING (Rule-Based Heuristics):
   Since we don't have human-labeled training data, we use
   economic theory to auto-label the training set:
   - price < cost → predatory
   - price < avg - 0.3 → competitive
   - |price_change| > 0.5 and low consistency → exploratory
   - price > avg and stable → cooperative

3. TRAINING: Fit a Random Forest on the auto-labeled data.

4. PREDICTION: Classify new rounds in real-time.

=== WHY IS THIS USEFUL? ===

Instead of just saying "prices are high" (lambda), we can say
"Agent 2 shifted from COMPETITIVE to COOPERATIVE at round 47."

This gives temporal, per-agent behavioral profiles — much richer
than aggregate metrics.

=== AI TECHNIQUES ===
- Feature engineering from time-series pricing data
- Random Forest classification (sklearn)
- Auto-labeling via domain heuristics
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# Try sklearn, fall back gracefully
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


STRATEGY_LABELS = ["competitive", "cooperative", "predatory", "exploratory"]


@dataclass
class StrategyPrediction:
    """Strategy classification for one agent in one round."""
    firm_id: int
    round_number: int
    predicted_strategy: str
    confidence: float
    features: dict[str, float]


class AgentStrategyClassifier:
    """
    Classifies agent pricing behavior using a Random Forest model.

    The classifier is trained on auto-labeled data derived from
    economic heuristics (price vs Nash, volatility, etc.) and then
    used to classify agent behavior in real-time.

    Usage:
        classifier = AgentStrategyClassifier(nash_price=1.52, n_firms=5)

        # Extract features from simulation data
        features, labels = classifier.extract_features(
            price_history, profit_history, cost=1.0
        )

        # Train the model
        classifier.train(features, labels)

        # Classify a new round
        prediction = classifier.predict_round(
            firm_id=2, round_number=100,
            prices=current_prices, prev_prices=last_prices,
            profits=current_profits, cost=1.0,
            price_history_window=last_5_prices
        )
    """

    def __init__(
        self,
        nash_price: float = 1.52,
        monopoly_price: float = 1.60,
        n_firms: int = 5,
    ) -> None:
        self.nash_price = nash_price
        self.monopoly_price = monopoly_price
        self.n_firms = n_firms
        self.model = None
        self.label_encoder = LabelEncoder() if HAS_SKLEARN else None
        self.is_trained = False

    # ────────────────────────────────────────
    # Feature Extraction
    # ────────────────────────────────────────

    def compute_features(
        self,
        firm_id: int,
        prices: list[float],
        prev_prices: list[float] | None,
        profits: list[float],
        cost: float,
        price_history_window: list[list[float]] | None = None,
    ) -> dict[str, float]:
        """
        Compute features for one (agent, round) pair.

        Features:
        - price_vs_nash: (my_price - nash) / nash
        - price_vs_avg: (my_price - avg_price) / avg_price
        - price_vs_cost: (my_price - cost) / cost  (markup ratio)
        - price_change: change from last round (0 if first round)
        - profit_rank: rank among all firms (1=best, 5=worst)
        - market_share: my_profit / total_profit
        - price_volatility: std of my last N prices
        - is_cheapest: 1 if lowest price, 0 otherwise
        - is_most_expensive: 1 if highest price, 0 otherwise
        """
        my_price = prices[firm_id]
        avg_price = sum(prices) / len(prices)
        total_profit = sum(profits) if sum(profits) > 0 else 1e-9

        # Price change
        price_change = 0.0
        if prev_prices is not None:
            price_change = my_price - prev_prices[firm_id]

        # Profit rank
        sorted_profits = sorted(enumerate(profits), key=lambda x: -x[1])
        profit_rank = next(i + 1 for i, (fid, _) in enumerate(sorted_profits) if fid == firm_id)

        # Volatility (std of last N prices)
        volatility = 0.0
        if price_history_window:
            my_prices = [round_prices[firm_id] for round_prices in price_history_window]
            volatility = float(np.std(my_prices)) if len(my_prices) > 1 else 0.0

        return {
            "price_vs_nash": (my_price - self.nash_price) / max(self.nash_price, 0.01),
            "price_vs_avg": (my_price - avg_price) / max(avg_price, 0.01),
            "price_vs_cost": (my_price - cost) / max(cost, 0.01),
            "price_change": price_change,
            "profit_rank": profit_rank / self.n_firms,
            "market_share": profits[firm_id] / total_profit,
            "price_volatility": volatility,
            "is_cheapest": 1.0 if my_price == min(prices) else 0.0,
            "is_most_expensive": 1.0 if my_price == max(prices) else 0.0,
        }

    def _auto_label(self, features: dict[str, float], cost: float, my_price: float) -> str:
        """
        Auto-label a round using economic heuristics.

        Rules:
        - price < cost → predatory
        - price significantly below average → competitive
        - high volatility + no clear direction → exploratory
        - price above average + stable → cooperative
        """
        if my_price < cost:
            return "predatory"

        if features["price_vs_avg"] < -0.1 and features["is_cheapest"] > 0.5:
            return "competitive"

        if features["price_volatility"] > 0.3 and abs(features["price_change"]) > 0.2:
            return "exploratory"

        if features["price_vs_nash"] > 0.05 and features["price_volatility"] < 0.2:
            return "cooperative"

        # Default to competitive if none of the above
        return "competitive"

    # ────────────────────────────────────────
    # Training
    # ────────────────────────────────────────

    def extract_features(
        self,
        price_history: list[list[float]],
        profit_history: list[list[float]],
        cost: float = 1.0,
    ) -> tuple[list[list[float]], list[str]]:
        """
        Extract features and auto-labels from full simulation history.

        Returns (X, y) where X is feature matrix, y is label vector.
        """
        X = []
        y = []

        for round_idx in range(1, len(price_history)):
            prices = price_history[round_idx]
            prev_prices = price_history[round_idx - 1]
            profits = profit_history[round_idx]

            # Window of last 5 rounds
            window_start = max(0, round_idx - 5)
            window = price_history[window_start:round_idx + 1]

            for firm_id in range(len(prices)):
                feats = self.compute_features(
                    firm_id=firm_id,
                    prices=prices,
                    prev_prices=prev_prices,
                    profits=profits,
                    cost=cost,
                    price_history_window=window,
                )

                label = self._auto_label(feats, cost, prices[firm_id])

                X.append(list(feats.values()))
                y.append(label)

        return X, y

    def train(self, X: list[list[float]], y: list[str]) -> dict[str, Any]:
        """
        Train the Random Forest classifier.

        Returns training summary with class distribution and accuracy.
        """
        if not HAS_SKLEARN:
            return {"error": "scikit-learn not installed. Run: pip install scikit-learn"}

        X_arr = np.array(X)
        y_encoded = self.label_encoder.fit_transform(y)

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight="balanced",  # handle imbalanced classes
        )
        self.model.fit(X_arr, y_encoded)
        self.is_trained = True

        # Training accuracy
        train_preds = self.model.predict(X_arr)
        accuracy = float(np.mean(train_preds == y_encoded))

        # Class distribution
        unique, counts = np.unique(y, return_counts=True)
        distribution = {label: int(count) for label, count in zip(unique, counts)}

        # Feature importances
        feature_names = [
            "price_vs_nash", "price_vs_avg", "price_vs_cost", "price_change",
            "profit_rank", "market_share", "price_volatility", "is_cheapest",
            "is_most_expensive",
        ]
        importances = {
            name: float(imp)
            for name, imp in zip(feature_names, self.model.feature_importances_)
        }

        return {
            "training_samples": len(X),
            "training_accuracy": accuracy,
            "class_distribution": distribution,
            "feature_importances": importances,
        }

    # ────────────────────────────────────────
    # Prediction
    # ────────────────────────────────────────

    def predict_round(
        self,
        firm_id: int,
        round_number: int,
        prices: list[float],
        prev_prices: list[float] | None,
        profits: list[float],
        cost: float,
        price_history_window: list[list[float]] | None = None,
    ) -> StrategyPrediction:
        """
        Classify one agent's strategy for one round.

        Returns a StrategyPrediction with the label and confidence.
        """
        feats = self.compute_features(
            firm_id, prices, prev_prices, profits, cost, price_history_window
        )

        if self.is_trained and self.model is not None:
            X = np.array([list(feats.values())])
            pred_encoded = self.model.predict(X)[0]
            proba = self.model.predict_proba(X)[0]
            label = self.label_encoder.inverse_transform([pred_encoded])[0]
            confidence = float(max(proba))
        else:
            # Fallback to heuristic if model not trained
            label = self._auto_label(feats, cost, prices[firm_id])
            confidence = 0.7  # heuristic confidence

        return StrategyPrediction(
            firm_id=firm_id,
            round_number=round_number,
            predicted_strategy=label,
            confidence=confidence,
            features=feats,
        )

    def classify_simulation(
        self,
        price_history: list[list[float]],
        profit_history: list[list[float]],
        cost: float = 1.0,
    ) -> list[StrategyPrediction]:
        """
        Classify ALL agents across ALL rounds of a simulation.

        Returns a flat list of StrategyPrediction objects.
        """
        predictions = []

        for round_idx in range(1, len(price_history)):
            prices = price_history[round_idx]
            prev_prices = price_history[round_idx - 1]
            profits = profit_history[round_idx]

            window_start = max(0, round_idx - 5)
            window = price_history[window_start:round_idx + 1]

            for firm_id in range(len(prices)):
                pred = self.predict_round(
                    firm_id=firm_id,
                    round_number=round_idx + 1,
                    prices=prices,
                    prev_prices=prev_prices,
                    profits=profits,
                    cost=cost,
                    price_history_window=window,
                )
                predictions.append(pred)

        return predictions

    def report(
        self,
        predictions: list[StrategyPrediction],
    ) -> dict[str, Any]:
        """Generate a summary report of strategy classifications."""
        if not predictions:
            return {"error": "No predictions to report"}

        # Per-agent strategy distribution
        per_agent: dict[int, dict[str, int]] = {}
        for p in predictions:
            if p.firm_id not in per_agent:
                per_agent[p.firm_id] = {s: 0 for s in STRATEGY_LABELS}
            per_agent[p.firm_id][p.predicted_strategy] += 1

        # Overall distribution
        overall = {s: 0 for s in STRATEGY_LABELS}
        for p in predictions:
            overall[p.predicted_strategy] += 1

        # Strategy transitions: how many times did each agent switch?
        transitions = {}
        sorted_preds = sorted(predictions, key=lambda p: (p.firm_id, p.round_number))
        for i in range(1, len(sorted_preds)):
            curr = sorted_preds[i]
            prev = sorted_preds[i - 1]
            if curr.firm_id == prev.firm_id and curr.predicted_strategy != prev.predicted_strategy:
                key = f"{prev.predicted_strategy}→{curr.predicted_strategy}"
                transitions[key] = transitions.get(key, 0) + 1

        return {
            "total_predictions": len(predictions),
            "overall_distribution": overall,
            "per_agent_distribution": per_agent,
            "strategy_transitions": transitions,
        }
