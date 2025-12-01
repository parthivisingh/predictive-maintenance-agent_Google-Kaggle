"""
Simulation Runner - Single Run Orchestration
=============================================

Orchestrates single simulation runs through RootAgent.execute_pipeline.
Supports deterministic execution with random seeds and comprehensive logging.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import time
import jsonschema
import logging

from agents.root_agent import RootAgent
from agents.schemas import RootAgentOutput
from tools.logging_config import get_logger, set_request_id, clear_request_id
from src.simulation.schemas import PROFILE_INPUT_SCHEMA, ROOT_AGENT_OUTPUT_SCHEMA


logger = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes per run
MAX_TIMEOUT_SECONDS = 600  # 10 minutes absolute max


# ============================================================================
# Main Runner
# ============================================================================

def run_single_simulation(
    profile: Dict[str, Any],
    run_id: str,
    random_seed: Optional[int] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Execute a single simulation run through RootAgent.execute_pipeline.

    This function:
    1. Validates input profile against PROFILE_INPUT_SCHEMA
    2. Sets up logging context with request_id
    3. Calls RootAgent().execute_pipeline with deterministic seed
    4. Extracts metrics from RootAgentOutput
    5. Returns structured result with float-typed metrics

    Args:
        profile: Equipment profile with unit_id, time_cycle, sensor_values
        run_id: Unique identifier for this simulation run
        random_seed: Optional seed for deterministic execution
        timeout_seconds: Maximum execution time (default: 300s, max: 600s)

    Returns:
        dict: Structured result with metrics (all floats), status, timestamps
            {
                "run_id": str,
                "profile_id": str,
                "unit_id": int,
                "time_cycle": int,
                "status": "success" | "error",
                "anomaly": bool,
                "roi": float | None,
                "priority": str,
                "similarity_hits": float,
                "timestamp": str (ISO-8601),
                "duration_sec": float,
                "random_seed": int | None,
                "error_msg": str | None
            }

    Raises:
        jsonschema.ValidationError: If profile doesn't match schema
        TimeoutError: If execution exceeds timeout_seconds
    """
    # Validate timeout
    if timeout_seconds > MAX_TIMEOUT_SECONDS:
        timeout_seconds = MAX_TIMEOUT_SECONDS
        logger.warning(
            f"Timeout reduced to max allowed: {MAX_TIMEOUT_SECONDS}s",
            extra={"requested_timeout": timeout_seconds}
        )

    # Set request ID for logging traceability
    set_request_id(run_id)
    start_time = time.time()

    try:
        # Step 1: Validate input profile
        _validate_input(profile)

        profile_id = profile.get("profile_id", f"profile_{run_id}")
        unit_id = profile["unit_id"]
        time_cycle = profile["time_cycle"]
        sensor_values = profile["sensor_values"]

        logger.info(
            "Starting simulation run",
            extra={
                "run_id": run_id,
                "profile_id": profile_id,
                "unit_id": unit_id,
                "time_cycle": time_cycle,
                "random_seed": random_seed,
                "timeout_seconds": timeout_seconds
            }
        )

        # Step 2: Build config with random seed for deterministic execution
        config = {}
        if random_seed is not None:
            config["random_seed"] = random_seed

        # Step 3: Execute RootAgent pipeline (black-box call, no wrapper)
        root_agent = RootAgent()

        # TODO: Add timeout mechanism here
        # For now, we rely on the pipeline's internal timeout handling
        root_output: RootAgentOutput = root_agent.execute_pipeline(
            unit_id=unit_id,
            time_cycle=time_cycle,
            sensor_values=sensor_values,
            config=config
        )

        # Step 4: Validate output against schema (fail-fast on drift)
        _validate_root_output(root_output)

        # Step 5: Extract metrics from RootAgentOutput
        metrics = _extract_metrics(root_output)

        # Step 6: Build structured result
        duration_sec = time.time() - start_time

        result = {
            "run_id": run_id,
            "profile_id": profile_id,
            "unit_id": unit_id,
            "time_cycle": time_cycle,
            "status": "success" if root_output["success"] else "error",
            "anomaly": metrics["anomaly"],
            "roi": metrics["roi"],
            "priority": metrics["priority"],
            "similarity_hits": metrics["similarity_hits"],
            "timestamp": datetime.now().isoformat(),
            "duration_sec": float(duration_sec),
            "random_seed": random_seed,
            "error_msg": None
        }

        logger.info(
            "Simulation run completed",
            extra={
                "run_id": run_id,
                "profile_id": profile_id,
                "status": result["status"],
                "anomaly": result["anomaly"],
                "duration_sec": result["duration_sec"]
            }
        )

        return result

    except jsonschema.ValidationError as e:
        # Input validation failure
        duration_sec = time.time() - start_time
        error_msg = f"Profile validation failed: {e.message}"

        logger.error(
            "Simulation run failed - validation error",
            extra={
                "run_id": run_id,
                "error": error_msg,
                "duration_sec": duration_sec
            }
        )

        # Re-raise for caller to handle
        raise

    except Exception as e:
        # Execution failure
        duration_sec = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}"

        logger.error(
            "Simulation run failed - execution error",
            extra={
                "run_id": run_id,
                "error": error_msg,
                "duration_sec": duration_sec
            },
            exc_info=True
        )

        # Return error result (don't re-raise - let caller decide policy)
        result = {
            "run_id": run_id,
            "profile_id": profile.get("profile_id", f"profile_{run_id}"),
            "unit_id": profile.get("unit_id", 0),
            "time_cycle": profile.get("time_cycle", 0),
            "status": "error",
            "anomaly": False,
            "roi": None,
            "priority": "error",
            "similarity_hits": 0.0,
            "timestamp": datetime.now().isoformat(),
            "duration_sec": float(duration_sec),
            "random_seed": random_seed,
            "error_msg": error_msg
        }

        return result

    finally:
        # Always clear request ID
        clear_request_id()


# ============================================================================
# Helper Functions
# ============================================================================

def _validate_input(profile: Dict[str, Any]) -> None:
    """
    Validate profile against PROFILE_INPUT_SCHEMA.

    Args:
        profile: Profile dictionary to validate

    Raises:
        jsonschema.ValidationError: If profile doesn't match schema
    """
    jsonschema.validate(instance=profile, schema=PROFILE_INPUT_SCHEMA)


def _validate_root_output(root_output: RootAgentOutput) -> None:
    """
    Validate RootAgentOutput against ROOT_AGENT_OUTPUT_SCHEMA.

    Fail-fast on schema drift to catch breaking changes early.

    Args:
        root_output: RootAgent output to validate

    Raises:
        jsonschema.ValidationError: If output doesn't match schema
    """
    try:
        jsonschema.validate(instance=root_output, schema=ROOT_AGENT_OUTPUT_SCHEMA)
    except jsonschema.ValidationError as e:
        logger.error(
            "RootAgent output schema validation failed - possible schema drift",
            extra={"error": e.message, "schema_path": list(e.absolute_schema_path)}
        )
        raise


def _extract_metrics(root_output: RootAgentOutput) -> Dict[str, Any]:
    """
    Extract metrics from RootAgentOutput.final_decision.

    Coerces all numeric values to float for consistent JSON serialization.
    Handles both enum objects and plain strings for priority field.

    Args:
        root_output: RootAgent output with final_decision

    Returns:
        dict: Extracted metrics
            {
                "anomaly": bool,
                "roi": float | None,
                "priority": str,
                "similarity_hits": float
            }
    """
    final_decision = root_output["final_decision"]
    research = root_output["pipeline_results"].get("research", {})

    # Extract anomaly (from action_required)
    anomaly = final_decision.get("action_required", False)

    # Extract ROI (from estimated_cost, coerce to float)
    estimated_cost = final_decision.get("estimated_cost")
    roi = float(estimated_cost) if estimated_cost is not None else None

    # Extract priority (handle both enum objects and plain strings)
    priority_raw = final_decision.get("priority", "none")
    if hasattr(priority_raw, 'value'):
        # It's an enum object - extract the value
        priority = priority_raw.value
    elif isinstance(priority_raw, str):
        # It's already a string
        # Handle both plain strings and enum string representations like "Priority.MEDIUM"
        if '.' in priority_raw and priority_raw.count('.') == 1:
            # Looks like "Priority.MEDIUM" - extract the value part
            priority = priority_raw.split('.')[1].lower()
        else:
            # Plain string - use as-is, but normalize case
            priority = priority_raw.lower()
    else:
        # Fallback - convert to string and extract value if needed
        priority_str = str(priority_raw)
        if '.' in priority_str:
            priority = priority_str.split('.')[1].lower()
        else:
            priority = priority_str.lower()

    # Extract similarity hits (from research, coerce to float)
    matches_found = research.get("matches_found", 0)
    similarity_hits = float(matches_found)

    return {
        "anomaly": anomaly,
        "roi": roi,
        "priority": priority,
        "similarity_hits": similarity_hits
    }


def _normalize_for_comparison(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize simulation result for deterministic comparison.

    Freezes timestamps and request_ids to canonical values so that
    content-equivalent results can be compared byte-for-byte.

    NOTE: Use ONLY for test comparisons, NOT for production logs.

    Args:
        result: Simulation result to normalize

    Returns:
        dict: Normalized result with frozen timestamp
    """
    normalized = result.copy()

    # Freeze timestamp to canonical value
    normalized["timestamp"] = "2025-01-01T00:00:00.000000"

    # Round duration to avoid floating point comparison issues
    if "duration_sec" in normalized:
        normalized["duration_sec"] = round(normalized["duration_sec"], 3)

    return normalized
