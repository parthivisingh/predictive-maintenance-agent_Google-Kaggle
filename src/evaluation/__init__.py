"""
Evaluation Module
=================

Provides model quality evaluation and system health checks for
Phase 5 simulation outputs.
"""

from .model_quality import evaluate_accuracy, evaluate_stability, evaluate_similarity_quality
from .system_health import check_success_rate, detect_timeouts, analyze_performance

__all__ = [
    'evaluate_accuracy',
    'evaluate_stability',
    'evaluate_similarity_quality',
    'check_success_rate',
    'detect_timeouts',
    'analyze_performance',
]
