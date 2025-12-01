"""
Metrics Reporter - Generate JSON and Markdown Reports
=====================================================

Calculates metrics from batch results and outputs structured reports.
Supports canonical JSON serialization for deterministic output.
"""

from typing import Dict, Any, List
from datetime import datetime
import json
import os
import logging

from tools.logging_config import get_logger


logger = get_logger(__name__)


# ============================================================================
# Main Report Generator
# ============================================================================

def generate_report(
    batch_result: Dict[str, Any],
    output_path: str,
    output_formats: List[str] = None
) -> None:
    """
    Generate metrics report from batch results.

    Outputs:
    - metrics.json: Canonical JSON with sorted keys and float serialization
    - metrics.md: Markdown summary with formatted tables

    Args:
        batch_result: Batch execution result from batch_processor.run_batch
        output_path: Directory path for output files
        output_formats: List of formats to generate (default: ["json", "markdown"])

    Raises:
        OSError: If output directory cannot be created or written to
    """
    if output_formats is None:
        output_formats = ["json", "markdown"]

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    logger.info(
        "Generating metrics report",
        extra={
            "batch_id": batch_result.get("batch_id"),
            "output_path": output_path,
            "formats": output_formats
        }
    )

    # Calculate detailed metrics
    metrics = _calculate_metrics(batch_result)

    # Generate JSON report
    if "json" in output_formats:
        json_path = os.path.join(output_path, "metrics.json")
        _write_json_report(metrics, json_path)
        logger.info(f"JSON report written to {json_path}")

    # Generate Markdown report
    if "markdown" in output_formats:
        md_path = os.path.join(output_path, "metrics.md")
        _write_markdown_report(metrics, batch_result, md_path)
        logger.info(f"Markdown report written to {md_path}")

    # Generate full batch result (for debugging/analysis)
    if "full" in output_formats:
        full_path = os.path.join(output_path, "batch_result.json")
        _write_full_result(batch_result, full_path)
        logger.info(f"Full batch result written to {full_path}")


# ============================================================================
# Metrics Calculation
# ============================================================================

def _calculate_metrics(batch_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive metrics from batch result.

    Reuses patterns from tools/metrics.py for consistency.
    All numeric metrics are float-typed with ISO timestamps.

    Args:
        batch_result: Batch result from run_batch

    Returns:
        dict: Comprehensive metrics dictionary
    """
    runs = batch_result.get("runs", [])
    failed_runs = batch_result.get("failed_runs", [])
    summary_metrics = batch_result.get("summary_metrics", {})

    # Basic counts
    total_runs = batch_result.get("total_runs", 0)
    successful_runs = len(runs)
    failed_count = len(failed_runs)

    # Success rate
    success_rate = float(successful_runs) / float(total_runs) if total_runs > 0 else 0.0

    # Extract from summary_metrics (already calculated)
    anomaly_rate = summary_metrics.get("anomaly_rate", 0.0)
    roi_distribution = summary_metrics.get("roi_distribution")
    priority_distribution = summary_metrics.get("priority_distribution", {})
    similarity_hit_rate = summary_metrics.get("similarity_hit_rate", 0.0)
    avg_duration_sec = summary_metrics.get("avg_duration_sec", 0.0)

    # Build comprehensive metrics
    metrics = {
        "batch_id": batch_result.get("batch_id"),
        "timestamp": datetime.now().isoformat(),
        "execution": {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_count,
            "success_rate": success_rate,
            "mode": batch_result.get("mode", "sequential"),
            "error_policy": batch_result.get("error_policy", "skip"),
            "duration_sec": batch_result.get("duration_sec", 0.0)
        },
        "anomaly_metrics": {
            "anomaly_rate": anomaly_rate,
            "total_anomalies": sum(1 for r in runs if r.get("anomaly", False)),
            "total_normal": sum(1 for r in runs if not r.get("anomaly", False))
        },
        "roi_metrics": roi_distribution,
        "priority_metrics": priority_distribution,
        "research_metrics": {
            "similarity_hit_rate": similarity_hit_rate,
            "avg_similarity_hits": float(sum(r.get("similarity_hits", 0) for r in runs)) / float(len(runs)) if runs else 0.0
        },
        "performance_metrics": {
            "avg_duration_sec": avg_duration_sec,
            "min_duration_sec": float(min(r.get("duration_sec", 0) for r in runs)) if runs else 0.0,
            "max_duration_sec": float(max(r.get("duration_sec", 0) for r in runs)) if runs else 0.0
        }
    }

    return metrics


# ============================================================================
# JSON Output
# ============================================================================

def _write_json_report(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write metrics as canonical JSON.

    Uses deterministic serialization:
    - sort_keys=True for consistent ordering
    - separators=(',', ':') for compact output
    - default=float for consistent numeric typing

    Args:
        metrics: Metrics dictionary
        output_path: Output file path
    """
    json_str = _serialize_json_canonical(metrics)

    with open(output_path, 'w') as f:
        f.write(json_str)


def _serialize_json_canonical(data: Dict[str, Any]) -> str:
    """
    Serialize data to canonical JSON string.

    Deterministic serialization for byte-identical comparison.

    Args:
        data: Data to serialize

    Returns:
        str: Canonical JSON string
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(',', ':'),
        default=_json_serializer,
        indent=2  # Pretty-print for readability
    )


def _json_serializer(obj):
    """
    Custom JSON serializer for non-standard types.

    Coerces numeric types to float for consistency.
    """
    # Handle numpy types
    if hasattr(obj, 'item'):  # numpy scalar
        return float(obj.item())

    # Handle Decimal
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # Default to float for any numeric type
    if isinstance(obj, (int, float)):
        return float(obj)

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ============================================================================
# Markdown Output
# ============================================================================

def _write_markdown_report(
    metrics: Dict[str, Any],
    batch_result: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write metrics as formatted Markdown report.

    Args:
        metrics: Metrics dictionary
        batch_result: Full batch result
        output_path: Output file path
    """
    lines = []

    # Header
    lines.append("# Simulation Metrics Report")
    lines.append("")
    lines.append(f"**Batch ID:** `{metrics.get('batch_id')}`")
    lines.append(f"**Generated:** {metrics.get('timestamp')}")
    lines.append("")

    # Execution Summary
    lines.append("## Execution Summary")
    lines.append("")
    exec_metrics = metrics.get("execution", {})
    lines.append(f"- **Mode:** {exec_metrics.get('mode')}")
    lines.append(f"- **Error Policy:** {exec_metrics.get('error_policy')}")
    lines.append(f"- **Total Runs:** {exec_metrics.get('total_runs')}")
    lines.append(f"- **Successful:** {exec_metrics.get('successful_runs')}")
    lines.append(f"- **Failed:** {exec_metrics.get('failed_runs')}")
    lines.append(f"- **Success Rate:** {exec_metrics.get('success_rate', 0.0):.2%}")
    lines.append(f"- **Duration:** {exec_metrics.get('duration_sec', 0.0):.2f}s")
    lines.append("")

    # Anomaly Metrics
    lines.append("## Anomaly Detection")
    lines.append("")
    anomaly_metrics = metrics.get("anomaly_metrics", {})
    lines.append(f"- **Anomaly Rate:** {anomaly_metrics.get('anomaly_rate', 0.0):.2%}")
    lines.append(f"- **Total Anomalies:** {anomaly_metrics.get('total_anomalies', 0)}")
    lines.append(f"- **Total Normal:** {anomaly_metrics.get('total_normal', 0)}")
    lines.append("")

    # ROI Metrics
    lines.append("## ROI Distribution")
    lines.append("")
    roi_metrics = metrics.get("roi_metrics")
    if roi_metrics:
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Mean | ${roi_metrics.get('mean', 0.0):.2f} |")
        lines.append(f"| Median | ${roi_metrics.get('median', 0.0):.2f} |")
        lines.append(f"| Std Dev | ${roi_metrics.get('std', 0.0):.2f} |")
        lines.append(f"| Min | ${roi_metrics.get('min', 0.0):.2f} |")
        lines.append(f"| Max | ${roi_metrics.get('max', 0.0):.2f} |")
    else:
        lines.append("*No ROI data available*")
    lines.append("")

    # Priority Distribution
    lines.append("## Priority Distribution")
    lines.append("")
    priority_metrics = metrics.get("priority_metrics", {})
    lines.append("| Priority | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Critical | {priority_metrics.get('critical', 0)} |")
    lines.append(f"| High | {priority_metrics.get('high', 0)} |")
    lines.append(f"| Medium | {priority_metrics.get('medium', 0)} |")
    lines.append(f"| Low | {priority_metrics.get('low', 0)} |")
    lines.append(f"| None | {priority_metrics.get('none', 0)} |")
    lines.append(f"| Error | {priority_metrics.get('error', 0)} |")
    lines.append("")

    # Research Metrics
    lines.append("## Research Similarity")
    lines.append("")
    research_metrics = metrics.get("research_metrics", {})
    lines.append(f"- **Similarity Hit Rate:** {research_metrics.get('similarity_hit_rate', 0.0):.2%}")
    lines.append(f"- **Avg Similarity Hits:** {research_metrics.get('avg_similarity_hits', 0.0):.2f}")
    lines.append("")

    # Performance Metrics
    lines.append("## Performance")
    lines.append("")
    perf_metrics = metrics.get("performance_metrics", {})
    lines.append(f"- **Avg Duration:** {perf_metrics.get('avg_duration_sec', 0.0):.2f}s")
    lines.append(f"- **Min Duration:** {perf_metrics.get('min_duration_sec', 0.0):.2f}s")
    lines.append(f"- **Max Duration:** {perf_metrics.get('max_duration_sec', 0.0):.2f}s")
    lines.append("")

    # Failed Runs
    failed_runs = batch_result.get("failed_runs", [])
    if failed_runs:
        lines.append("## Failed Runs")
        lines.append("")
        lines.append("| Profile ID | Run ID | Error |")
        lines.append("|------------|--------|-------|")
        for failed in failed_runs:
            profile_id = failed.get("profile_id", "N/A")
            run_id = failed.get("run_id", "N/A")
            error_msg = failed.get("error_msg", "Unknown error")
            # Truncate long error messages
            if len(error_msg) > 50:
                error_msg = error_msg[:47] + "..."
            lines.append(f"| {profile_id} | {run_id} | {error_msg} |")
        lines.append("")

    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


# ============================================================================
# Full Result Output
# ============================================================================

def _write_full_result(batch_result: Dict[str, Any], output_path: str) -> None:
    """
    Write full batch result as JSON (for debugging/analysis).

    Args:
        batch_result: Full batch result
        output_path: Output file path
    """
    json_str = _serialize_json_canonical(batch_result)

    with open(output_path, 'w') as f:
        f.write(json_str)
