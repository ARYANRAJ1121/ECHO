"""Antitrust regulator — collusion detection pipeline."""

from .detector import LambdaMonitor, Alert
from .network_detector import CollusionNetworkDetector, NetworkAnalysisResult
from .audit_manifest import (
    WelfareAuditReport,
    ExperimentManifest,
    compute_welfare_audit,
    build_experiment_manifest,
    export_audit_pack,
    generate_regulatory_dossier_markdown,
)
