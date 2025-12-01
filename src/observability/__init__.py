"""
Observability Module
===================

Provides log monitoring, metrics aggregation, and dashboard generation
for Phase 5 simulation outputs.
"""

from .log_monitor import parse_logs, aggregate_errors, detect_anomaly_trends
from .metrics_summary import load_metrics, compute_stability, generate_summary

__all__ = [
    'parse_logs',
    'aggregate_errors',
    'detect_anomaly_trends',
    'load_metrics',
    'compute_stability',
    'generate_summary',
]
