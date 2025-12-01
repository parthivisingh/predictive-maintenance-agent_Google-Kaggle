"""
Batch Processor - Sequential and Parallel Execution
===================================================

Runs batch simulations with configurable execution modes and error policies.
Aggregates results and provides comprehensive metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import time
import uuid
import jsonschema
import numpy as np
import logging

from src.simulation.simulation_runner import run_single_simulation
from src.simulation.schemas import SIMULATION_OUTPUT_SCHEMA
from tools.logging_config import get_logger


logger = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

DEFAULT_MAX_WORKERS = 4
DEFAULT_BACKOFF_SECONDS = 0.1
DEFAULT_TIMEOUT_PER_RUN = 300  # 5 minutes


# ============================================================================
# Main Batch Runner
# ============================================================================

def run_batch(
    profiles: List[Dict[str, Any]],
    mode: str = "sequential",
    error_policy: str = "skip",
    max_workers: int = DEFAULT_MAX_WORKERS,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
    base_random_seed: Optional[int] = None,
    timeout_per_run: int = DEFAULT_TIMEOUT_PER_RUN
) -> Dict[str, Any]:
    """
    Execute batch of simulation profiles.

    Modes:
    - "sequential": Run profiles one-by-one (safer, default)
    - "parallel": Use ThreadPoolExecutor with max_workers and backoff
                  (only if RootAgent is I/O-bound)

    Error Policies:
    - "skip": Log error, append to failed_runs, continue batch
    - "fail-fast": Raise exception on first error, abort batch

    Args:
        profiles: List of equipment profiles to simulate
        mode: Execution mode ("sequential" | "parallel")
        error_policy: Error handling policy ("skip" | "fail-fast")
        max_workers: Max parallel workers (only for parallel mode)
        backoff_seconds: Delay between parallel submits to avoid races
        base_random_seed: Base seed for deterministic runs (incremented per run)
        timeout_per_run: Timeout in seconds for each individual run

    Returns:
        dict: Batch results with aggregated metrics
            {
                "batch_id": str,
                "total_runs": int,
                "successful_runs": int,
                "failed_runs": list[dict],
                "runs": list[dict],
                "summary_metrics": dict,
                "timestamp": str,
                "duration_sec": float,
                "mode": str,
                "error_policy": str
            }

    Raises:
        ValueError: If invalid mode or error_policy
        Exception: If error_policy="fail-fast" and run fails
    """
    # Validate parameters
    if mode not in ["sequential", "parallel"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'sequential' or 'parallel'")

    if error_policy not in ["skip", "fail-fast"]:
        raise ValueError(f"Invalid error_policy: {error_policy}. Must be 'skip' or 'fail-fast'")

    # Generate batch ID
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    logger.info(
        "Starting batch execution",
        extra={
            "batch_id": batch_id,
            "total_profiles": len(profiles),
            "mode": mode,
            "error_policy": error_policy,
            "max_workers": max_workers if mode == "parallel" else None,
            "backoff_seconds": backoff_seconds if mode == "parallel" else None
        }
    )

    # Execute batch based on mode
    if mode == "sequential":
        runs, failed_runs = _run_sequential(
            profiles=profiles,
            batch_id=batch_id,
            error_policy=error_policy,
            base_random_seed=base_random_seed,
            timeout_per_run=timeout_per_run
        )
    else:  # parallel
        runs, failed_runs = _run_parallel(
            profiles=profiles,
            batch_id=batch_id,
            error_policy=error_policy,
            max_workers=max_workers,
            backoff_seconds=backoff_seconds,
            base_random_seed=base_random_seed,
            timeout_per_run=timeout_per_run
        )

    # Aggregate results
    duration_sec = time.time() - start_time
    summary_metrics = _aggregate_results(runs)

    # Build batch result
    batch_result = {
        "batch_id": batch_id,
        "total_runs": len(profiles),
        "successful_runs": len(runs),
        "failed_runs": failed_runs,
        "runs": runs,
        "summary_metrics": summary_metrics,
        "timestamp": datetime.now().isoformat(),
        "duration_sec": float(duration_sec),
        "mode": mode,
        "error_policy": error_policy
    }

    logger.info(
        "Batch execution completed",
        extra={
            "batch_id": batch_id,
            "total_runs": len(profiles),
            "successful_runs": len(runs),
            "failed_count": len(failed_runs),
            "duration_sec": duration_sec
        }
    )

    return batch_result


# ============================================================================
# Execution Modes
# ============================================================================

def _run_sequential(
    profiles: List[Dict[str, Any]],
    batch_id: str,
    error_policy: str,
    base_random_seed: Optional[int],
    timeout_per_run: int
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run profiles sequentially (one-by-one).

    Safer than parallel mode - avoids concurrency issues.

    Args:
        profiles: List of profiles to run
        batch_id: Batch identifier
        error_policy: Error handling policy
        base_random_seed: Base random seed
        timeout_per_run: Timeout per run in seconds

    Returns:
        tuple: (successful_runs, failed_runs)
    """
    successful_runs = []
    failed_runs = []

    for idx, profile in enumerate(profiles):
        run_id = f"{batch_id}_run_{idx:04d}"
        random_seed = base_random_seed + idx if base_random_seed is not None else None

        try:
            result = run_single_simulation(
                profile=profile,
                run_id=run_id,
                random_seed=random_seed,
                timeout_seconds=timeout_per_run
            )

            # Validate output
            _validate_output(result)

            if result["status"] == "success":
                successful_runs.append(result)
            else:
                # Run returned error status
                if error_policy == "fail-fast":
                    raise RuntimeError(f"Run {run_id} failed: {result.get('error_msg', 'Unknown error')}")
                else:  # skip
                    failed_runs.append({
                        "profile_id": profile.get("profile_id", f"profile_{idx}"),
                        "run_id": run_id,
                        "error_msg": result.get("error_msg", "Unknown error"),
                        "timestamp": result["timestamp"]
                    })

        except jsonschema.ValidationError as e:
            # Input validation error
            error_msg = f"Profile validation failed: {e.message}"
            logger.error(
                "Profile validation error",
                extra={"run_id": run_id, "error": error_msg}
            )

            if error_policy == "fail-fast":
                raise
            else:  # skip
                failed_runs.append({
                    "profile_id": profile.get("profile_id", f"profile_{idx}"),
                    "run_id": run_id,
                    "error_msg": error_msg,
                    "timestamp": datetime.now().isoformat()
                })

        except Exception as e:
            # Unexpected error
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(
                "Unexpected error in run",
                extra={"run_id": run_id, "error": error_msg},
                exc_info=True
            )

            if error_policy == "fail-fast":
                raise
            else:  # skip
                failed_runs.append({
                    "profile_id": profile.get("profile_id", f"profile_{idx}"),
                    "run_id": run_id,
                    "error_msg": error_msg,
                    "timestamp": datetime.now().isoformat()
                })

    return successful_runs, failed_runs


def _run_parallel(
    profiles: List[Dict[str, Any]],
    batch_id: str,
    error_policy: str,
    max_workers: int,
    backoff_seconds: float,
    base_random_seed: Optional[int],
    timeout_per_run: int
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run profiles in parallel using ThreadPoolExecutor.

    NOTE: Only use parallel mode if RootAgent is I/O-bound.
    Sequential mode is safer to avoid race conditions.

    Args:
        profiles: List of profiles to run
        batch_id: Batch identifier
        error_policy: Error handling policy
        max_workers: Maximum parallel workers
        backoff_seconds: Delay between submits
        base_random_seed: Base random seed
        timeout_per_run: Timeout per run in seconds

    Returns:
        tuple: (successful_runs, failed_runs)
    """
    successful_runs = []
    failed_runs = []

    # Map futures to profile metadata for error handling
    future_to_meta: Dict[Future, Dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all profiles with backoff
        for idx, profile in enumerate(profiles):
            run_id = f"{batch_id}_run_{idx:04d}"
            random_seed = base_random_seed + idx if base_random_seed is not None else None

            future = executor.submit(
                run_single_simulation,
                profile=profile,
                run_id=run_id,
                random_seed=random_seed,
                timeout_seconds=timeout_per_run
            )

            future_to_meta[future] = {
                "profile": profile,
                "run_id": run_id,
                "profile_id": profile.get("profile_id", f"profile_{idx}")
            }

            # Backoff to avoid overwhelming the system
            if backoff_seconds > 0 and idx < len(profiles) - 1:
                time.sleep(backoff_seconds)

        # Collect results as they complete
        for future in as_completed(future_to_meta):
            meta = future_to_meta[future]
            run_id = meta["run_id"]
            profile_id = meta["profile_id"]

            try:
                result = future.result()

                # Validate output
                _validate_output(result)

                if result["status"] == "success":
                    successful_runs.append(result)
                else:
                    # Run returned error status
                    if error_policy == "fail-fast":
                        # Cancel remaining futures
                        for f in future_to_meta:
                            f.cancel()
                        raise RuntimeError(f"Run {run_id} failed: {result.get('error_msg', 'Unknown error')}")
                    else:  # skip
                        failed_runs.append({
                            "profile_id": profile_id,
                            "run_id": run_id,
                            "error_msg": result.get("error_msg", "Unknown error"),
                            "timestamp": result["timestamp"]
                        })

            except Exception as e:
                # Future execution error
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.error(
                    "Error in parallel run",
                    extra={"run_id": run_id, "error": error_msg},
                    exc_info=True
                )

                if error_policy == "fail-fast":
                    # Cancel remaining futures
                    for f in future_to_meta:
                        f.cancel()
                    raise
                else:  # skip
                    failed_runs.append({
                        "profile_id": profile_id,
                        "run_id": run_id,
                        "error_msg": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })

    return successful_runs, failed_runs


# ============================================================================
# Aggregation
# ============================================================================

def _aggregate_results(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate metrics from successful runs.

    Computes mean/median/std for float metrics, distributions for categoricals.
    All numeric outputs coerced to float for consistent JSON serialization.

    Args:
        runs: List of successful run results

    Returns:
        dict: Aggregated metrics
            {
                "anomaly_rate": float,
                "roi_distribution": {mean, median, std, min, max},
                "priority_distribution": {high, medium, low, none, error},
                "similarity_hit_rate": float,
                "avg_duration_sec": float,
                "timestamp": str
            }
    """
    if not runs:
        # Empty batch - return zero metrics
        return {
            "anomaly_rate": 0.0,
            "roi_distribution": None,
            "priority_distribution": {"high": 0, "medium": 0, "low": 0, "none": 0, "critical": 0, "error": 0},
            "similarity_hit_rate": 0.0,
            "avg_duration_sec": 0.0,
            "timestamp": datetime.now().isoformat()
        }

    # Extract metric arrays
    anomalies = [r["anomaly"] for r in runs]
    rois = [r["roi"] for r in runs if r["roi"] is not None]
    priorities = [r["priority"] for r in runs]
    similarity_hits = [r["similarity_hits"] for r in runs]
    durations = [r["duration_sec"] for r in runs]

    # Anomaly rate
    anomaly_rate = float(sum(anomalies)) / float(len(runs))

    # ROI distribution
    if rois:
        roi_distribution = {
            "mean": float(np.mean(rois)),
            "median": float(np.median(rois)),
            "std": float(np.std(rois)),
            "min": float(np.min(rois)),
            "max": float(np.max(rois))
        }
    else:
        roi_distribution = None

    # Priority distribution
    from collections import Counter
    priority_counts = Counter(priorities)
    priority_distribution = {
        "high": priority_counts.get("high", 0),
        "medium": priority_counts.get("medium", 0),
        "low": priority_counts.get("low", 0),
        "none": priority_counts.get("none", 0),
        "critical": priority_counts.get("critical", 0),
        "error": priority_counts.get("error", 0)
    }

    # Similarity hit rate (runs with similarity_hits > 0 among anomalies)
    anomaly_runs = [r for r in runs if r["anomaly"]]
    if anomaly_runs:
        hits_with_similarity = sum(1 for r in anomaly_runs if r["similarity_hits"] > 0)
        similarity_hit_rate = float(hits_with_similarity) / float(len(anomaly_runs))
    else:
        similarity_hit_rate = 0.0

    # Average duration
    avg_duration_sec = float(np.mean(durations))

    return {
        "anomaly_rate": anomaly_rate,
        "roi_distribution": roi_distribution,
        "priority_distribution": priority_distribution,
        "similarity_hit_rate": similarity_hit_rate,
        "avg_duration_sec": avg_duration_sec,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Validation
# ============================================================================

def _validate_output(result: Dict[str, Any]) -> None:
    """
    Validate simulation result against SIMULATION_OUTPUT_SCHEMA.

    Fail-fast on schema drift.

    Args:
        result: Simulation result to validate

    Raises:
        jsonschema.ValidationError: If result doesn't match schema
    """
    jsonschema.validate(instance=result, schema=SIMULATION_OUTPUT_SCHEMA)
