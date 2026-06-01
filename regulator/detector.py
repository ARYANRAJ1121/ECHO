"""
regulator/detector.py -- Lambda Monitor (Method 1)

=== WHAT IS THIS? ===

The simplest collusion detector. Watches the Lambda (collusion index)
every round and raises alerts when it stays high for too long.

Lambda = (avg_price - nash_price) / (monopoly_price - nash_price)
  0.0 = competitive (Nash equilibrium)
  1.0 = full coordination (joint monopoly)
  >1.0 = prices exceeding even the monopoly benchmark

=== DETECTION LOGIC ===

Three alert levels:
  1. WATCH:    Lambda > 0.3 for 5+ consecutive rounds
  2. WARNING:  Lambda > 0.5 for 10+ consecutive rounds
  3. ALERT:    Lambda > 0.7 for 10+ consecutive rounds

Also computes:
  - Rolling average Lambda (configurable window, default 50 rounds)
  - Trend direction (is coordination increasing or decreasing?)
  - Time-to-threshold (how many rounds to reach Lambda > 0.7?)

=== WHY ISN'T LAMBDA ENOUGH? ===

Lambda CAN be noisy:
  - Round 1 always has high Lambda (random initial prices)
  - Temporary spikes from one agent experimenting
  - Does not distinguish INTENTIONAL coordination from accidental

That's why we need Methods 2 (NLP) and 3 (Demand Shocks) alongside.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Alert:
    """A single collusion alert raised by the detector."""
    round_number: int
    alert_type: str       # 'lambda_watch', 'lambda_warning', 'lambda_alert'
    severity: str         # 'low', 'medium', 'high'
    lambda_value: float
    rolling_avg: float
    streak: int           # how many consecutive rounds above threshold
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_number": self.round_number,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "lambda_value": self.lambda_value,
            "rolling_avg": self.rolling_avg,
            "streak": self.streak,
            "detail": self.detail,
        }


class LambdaMonitor:
    """
    Tracks Lambda (collusion index) over time and raises alerts.

    Usage:
        monitor = LambdaMonitor()
        for record in simulation_records:
            alerts = monitor.observe(record.round_number, record.collusion_index)
            for alert in alerts:
                print(alert)
        report = monitor.report()

    Parameters
    ----------
    watch_threshold : float
        Lambda level for "watch" status. Default: 0.3.
    warning_threshold : float
        Lambda level for "warning" status. Default: 0.5.
    alert_threshold : float
        Lambda level for "alert" status. Default: 0.7.
    watch_streak : int
        Consecutive rounds above watch_threshold to trigger. Default: 5.
    warning_streak : int
        Consecutive rounds above warning_threshold to trigger. Default: 10.
    alert_streak : int
        Consecutive rounds above alert_threshold to trigger. Default: 10.
    rolling_window : int
        Window size for rolling average. Default: 50.
    """

    def __init__(
        self,
        watch_threshold: float = 0.3,
        warning_threshold: float = 0.5,
        alert_threshold: float = 0.7,
        watch_streak: int = 5,
        warning_streak: int = 10,
        alert_streak: int = 10,
        rolling_window: int = 50,
    ) -> None:
        self.watch_threshold = watch_threshold
        self.warning_threshold = warning_threshold
        self.alert_threshold = alert_threshold
        self.watch_streak = watch_streak
        self.warning_streak = warning_streak
        self.alert_streak = alert_streak
        self.rolling_window = rolling_window

        # State
        self.lambda_history: list[float] = []
        self.alerts: list[Alert] = []

        # Streak counters
        self._watch_count = 0
        self._warning_count = 0
        self._alert_count = 0

        # Track if each level was already triggered (avoid spam)
        self._watch_triggered = False
        self._warning_triggered = False
        self._alert_triggered = False

        # First round where Lambda > alert_threshold
        self.first_alert_round: int | None = None

    def observe(self, round_number: int, lambda_value: float) -> list[Alert]:
        """
        Feed one round's Lambda value. Returns any new alerts.

        Called after EVERY round by the simulation engine.
        """
        self.lambda_history.append(lambda_value)
        new_alerts: list[Alert] = []
        rolling = self.rolling_average()

        # Update streak counters
        if lambda_value > self.alert_threshold:
            self._alert_count += 1
            self._warning_count += 1
            self._watch_count += 1
            if self.first_alert_round is None:
                self.first_alert_round = round_number
        elif lambda_value > self.warning_threshold:
            self._alert_count = 0
            self._warning_count += 1
            self._watch_count += 1
        elif lambda_value > self.watch_threshold:
            self._alert_count = 0
            self._warning_count = 0
            self._watch_count += 1
        else:
            self._alert_count = 0
            self._warning_count = 0
            self._watch_count = 0
            # Reset triggers when Lambda drops below all thresholds
            self._watch_triggered = False
            self._warning_triggered = False
            self._alert_triggered = False

        # Check for alert-level (highest priority first)
        if self._alert_count >= self.alert_streak and not self._alert_triggered:
            alert = Alert(
                round_number=round_number,
                alert_type="lambda_alert",
                severity="high",
                lambda_value=lambda_value,
                rolling_avg=rolling,
                streak=self._alert_count,
                detail=(
                    f"ALERT: Lambda > {self.alert_threshold} for "
                    f"{self._alert_count} consecutive rounds. "
                    f"Rolling avg: {rolling:.3f}. "
                    f"Strong evidence of supra-competitive pricing."
                ),
            )
            new_alerts.append(alert)
            self._alert_triggered = True

        elif self._warning_count >= self.warning_streak and not self._warning_triggered:
            alert = Alert(
                round_number=round_number,
                alert_type="lambda_warning",
                severity="medium",
                lambda_value=lambda_value,
                rolling_avg=rolling,
                streak=self._warning_count,
                detail=(
                    f"WARNING: Lambda > {self.warning_threshold} for "
                    f"{self._warning_count} consecutive rounds. "
                    f"Rolling avg: {rolling:.3f}. "
                    f"Moderate coordination detected."
                ),
            )
            new_alerts.append(alert)
            self._warning_triggered = True

        elif self._watch_count >= self.watch_streak and not self._watch_triggered:
            alert = Alert(
                round_number=round_number,
                alert_type="lambda_watch",
                severity="low",
                lambda_value=lambda_value,
                rolling_avg=rolling,
                streak=self._watch_count,
                detail=(
                    f"WATCH: Lambda > {self.watch_threshold} for "
                    f"{self._watch_count} consecutive rounds. "
                    f"Rolling avg: {rolling:.3f}. "
                    f"Possible coordination emerging."
                ),
            )
            new_alerts.append(alert)
            self._watch_triggered = True

        self.alerts.extend(new_alerts)
        return new_alerts

    def rolling_average(self, window: int | None = None) -> float:
        """Compute rolling average Lambda over the last `window` rounds."""
        w = window or self.rolling_window
        if not self.lambda_history:
            return 0.0
        recent = self.lambda_history[-w:]
        return sum(recent) / len(recent)

    def trend(self, window: int = 20) -> str:
        """
        Compute Lambda trend direction.

        Returns 'rising', 'falling', or 'stable' based on comparing
        the first half vs second half of the last `window` rounds.
        """
        if len(self.lambda_history) < window:
            return "insufficient_data"

        recent = self.lambda_history[-window:]
        half = window // 2
        first_half = sum(recent[:half]) / half
        second_half = sum(recent[half:]) / half

        diff = second_half - first_half
        if diff > 0.05:
            return "rising"
        elif diff < -0.05:
            return "falling"
        else:
            return "stable"

    def report(self) -> dict[str, Any]:
        """
        Generate a summary report of all Lambda monitoring.

        Returns a dict with key metrics for the paper.
        """
        if not self.lambda_history:
            return {"error": "No data observed"}

        return {
            "total_rounds": len(self.lambda_history),
            "final_lambda": self.lambda_history[-1],
            "peak_lambda": max(self.lambda_history),
            "mean_lambda": sum(self.lambda_history) / len(self.lambda_history),
            "rolling_avg": self.rolling_average(),
            "trend": self.trend(),
            "total_alerts": len(self.alerts),
            "alert_breakdown": {
                "watch": sum(1 for a in self.alerts if a.severity == "low"),
                "warning": sum(1 for a in self.alerts if a.severity == "medium"),
                "alert": sum(1 for a in self.alerts if a.severity == "high"),
            },
            "first_alert_round": self.first_alert_round,
            "alerts": [a.to_dict() for a in self.alerts],
        }
