"""Antitrust regulator — collusion detection pipeline."""

from .detector import LambdaMonitor, Alert
from .network_detector import CollusionNetworkDetector, NetworkAnalysisResult
