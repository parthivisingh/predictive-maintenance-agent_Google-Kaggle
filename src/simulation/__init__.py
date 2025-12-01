"""
Simulation Package - Phase 5
============================

Orchestrates batch equipment simulations through RootAgent pipeline.
Provides deterministic execution, metrics aggregation, and reporting.
"""

from src.simulation.simulation_runner import run_single_simulation
from src.simulation.batch_processor import run_batch
from src.simulation.metrics_reporter import generate_report
from src.simulation import schemas


__all__ = [
    "run_single_simulation",
    "run_batch",
    "generate_report",
    "schemas"
]
