"""
analysis/forecaster.py -- Time-Series Price Forecasting Model

=== WHAT IS THIS? ===

A machine learning module that predicts future market prices based
on historical price trajectories. Given the last N rounds of pricing
data, it forecasts where prices are heading.

=== WHY IS THIS USEFUL? ===

1. EARLY WARNING: If the forecaster predicts prices will converge
   upward, the regulator can intervene BEFORE collusion solidifies.

2. COUNTERFACTUAL ANALYSIS: "If the simulation keeps running for
   1000 more rounds, will prices stabilize at the monopoly level?"

3. PAPER CONTRIBUTION: Demonstrates predictive modeling on top
   of the simulation framework.

=== AI TECHNIQUES ===

1. Moving Average baseline (simple, interpretable)
2. Linear Regression with sliding window features (sklearn)
3. Feature engineering from time-series data:
   - Lagged prices (t-1, t-2, ..., t-W)
   - Rolling mean and std
   - Price momentum (rate of change)

=== HOW IT WORKS ===

Training data: [round_1_prices, round_2_prices, ..., round_N_prices]

For each round t, features are:
  X = [avg_price(t-1), avg_price(t-2), ..., avg_price(t-W),
       rolling_mean, rolling_std, momentum]

  y = avg_price(t)

The model learns: given the last W rounds, what will the next price be?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class Forecast:
    """A price forecast for one future round."""
    target_round: int
    predicted_avg_price: float
    confidence_interval: tuple[float, float]  # (lower, upper)
    method: str  # 'linear_regression' or 'moving_average'


class PriceForecaster:
    """
    Predicts future market prices using time-series regression.

    Uses a sliding window of past prices as features to predict
    the next round's average price. Supports both a simple moving
    average baseline and a trained Linear Regression model.

    Usage:
        forecaster = PriceForecaster(window_size=10)

        # Train on historical data
        summary = forecaster.train(price_history)

        # Predict next N rounds
        forecasts = forecaster.forecast(price_history, n_steps=5)
    """

    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self.model = None
        self.is_trained = False
        self.training_residuals: list[float] = []

    # ────────────────────────────────────────
    # Feature Engineering
    # ────────────────────────────────────────

    def _extract_features(
        self,
        avg_prices: list[float],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Build feature matrix from average price time series.

        For each round t (where t >= window_size):
          Features:
            - Lagged avg prices: [p(t-1), p(t-2), ..., p(t-W)]
            - Rolling mean of the window
            - Rolling std of the window
            - Momentum: p(t-1) - p(t-W) (price direction over the window)

          Target: p(t)

        Returns (X, y) numpy arrays.
        """
        W = self.window_size
        if len(avg_prices) <= W:
            return np.array([]), np.array([])

        X = []
        y = []

        for t in range(W, len(avg_prices)):
            window = avg_prices[t - W:t]

            features = list(window)  # lagged prices
            features.append(float(np.mean(window)))      # rolling mean
            features.append(float(np.std(window)))        # rolling std
            features.append(window[-1] - window[0])       # momentum

            X.append(features)
            y.append(avg_prices[t])

        return np.array(X), np.array(y)

    def _avg_prices_from_history(
        self,
        price_history: list[list[float]],
    ) -> list[float]:
        """Convert per-firm price history to average price series."""
        return [sum(prices) / len(prices) for prices in price_history]

    # ────────────────────────────────────────
    # Moving Average Baseline
    # ────────────────────────────────────────

    def moving_average_forecast(
        self,
        price_history: list[list[float]],
        n_steps: int = 5,
    ) -> list[Forecast]:
        """
        Simple moving average forecast (baseline).

        Predicts the next price as the average of the last W prices.
        """
        avg_prices = self._avg_prices_from_history(price_history)

        forecasts = []
        extended = list(avg_prices)

        for step in range(n_steps):
            window = extended[-self.window_size:]
            pred = float(np.mean(window))
            std = float(np.std(window))

            forecasts.append(Forecast(
                target_round=len(price_history) + step + 1,
                predicted_avg_price=pred,
                confidence_interval=(pred - 2 * std, pred + 2 * std),
                method="moving_average",
            ))
            extended.append(pred)

        return forecasts

    # ────────────────────────────────────────
    # Linear Regression Model
    # ────────────────────────────────────────

    def train(
        self,
        price_history: list[list[float]],
    ) -> dict[str, Any]:
        """
        Train the Linear Regression forecasting model.

        Returns training summary with R², MAE, and feature count.
        """
        if not HAS_SKLEARN:
            return {"error": "scikit-learn not installed. Run: pip install scikit-learn"}

        avg_prices = self._avg_prices_from_history(price_history)
        X, y = self._extract_features(avg_prices)

        if len(X) < 5:
            return {"error": "Not enough data to train (need at least window_size + 5 rounds)"}

        # Train/test split: last 20% for validation
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]

        self.model = LinearRegression()
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)

        self.training_residuals = (y_train - y_pred_train).tolist()

        return {
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "train_r2": float(r2_score(y_train, y_pred_train)),
            "test_r2": float(r2_score(y_test, y_pred_test)) if len(X_test) > 1 else None,
            "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
            "test_mae": float(mean_absolute_error(y_test, y_pred_test)) if len(X_test) > 1 else None,
            "window_size": self.window_size,
            "n_features": X.shape[1],
        }

    def forecast(
        self,
        price_history: list[list[float]],
        n_steps: int = 5,
    ) -> list[Forecast]:
        """
        Forecast the next n_steps rounds using the trained model.

        Uses autoregressive forecasting: each prediction feeds into
        the next step's features.
        """
        if not self.is_trained or self.model is None:
            return self.moving_average_forecast(price_history, n_steps)

        avg_prices = self._avg_prices_from_history(price_history)

        # Compute confidence interval width from training residuals
        residual_std = float(np.std(self.training_residuals)) if self.training_residuals else 0.1

        forecasts = []
        extended = list(avg_prices)

        for step in range(n_steps):
            window = extended[-self.window_size:]

            features = list(window)
            features.append(float(np.mean(window)))
            features.append(float(np.std(window)))
            features.append(window[-1] - window[0])

            X = np.array([features])
            pred = float(self.model.predict(X)[0])

            # Confidence interval widens with each step
            ci_width = residual_std * (1 + step * 0.5)

            forecasts.append(Forecast(
                target_round=len(price_history) + step + 1,
                predicted_avg_price=pred,
                confidence_interval=(pred - 2 * ci_width, pred + 2 * ci_width),
                method="linear_regression",
            ))
            extended.append(pred)

        return forecasts

    def report(
        self,
        price_history: list[list[float]],
        n_forecast_steps: int = 10,
    ) -> dict[str, Any]:
        """Generate a complete forecasting report."""
        avg_prices = self._avg_prices_from_history(price_history)

        # Train if not already
        train_summary = {}
        if not self.is_trained:
            train_summary = self.train(price_history)

        # Generate forecasts
        lr_forecasts = self.forecast(price_history, n_forecast_steps)
        ma_forecasts = self.moving_average_forecast(price_history, n_forecast_steps)

        # Price trend assessment
        if len(avg_prices) >= 20:
            first_half = np.mean(avg_prices[:len(avg_prices) // 2])
            second_half = np.mean(avg_prices[len(avg_prices) // 2:])
            trend = "rising" if second_half > first_half + 0.05 else (
                "falling" if second_half < first_half - 0.05 else "stable"
            )
        else:
            trend = "insufficient_data"

        return {
            "historical_rounds": len(avg_prices),
            "current_avg_price": avg_prices[-1] if avg_prices else None,
            "price_trend": trend,
            "training_summary": train_summary,
            "lr_forecasts": [
                {
                    "round": f.target_round,
                    "predicted_price": round(f.predicted_avg_price, 4),
                    "ci_lower": round(f.confidence_interval[0], 4),
                    "ci_upper": round(f.confidence_interval[1], 4),
                }
                for f in lr_forecasts
            ],
            "ma_forecasts": [
                {
                    "round": f.target_round,
                    "predicted_price": round(f.predicted_avg_price, 4),
                }
                for f in ma_forecasts
            ],
        }
