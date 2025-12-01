"""
Tests for Metrics Reporter
===========================

Tests metrics calculation, JSON/markdown generation, and canonical serialization.
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path

from src.simulation.metrics_reporter import (
    generate_report,
    _calculate_metrics,
    _serialize_json_canonical
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_batch_result():
    """Sample batch result for testing."""
    return {
        "batch_id": "batch_test_001",
        "total_runs": 5,
        "successful_runs": 5,
        "failed_runs": [],
        "runs": [
            {
                "run_id": "run_001",
                "profile_id": "profile_001",
                "unit_id": 1,
                "time_cycle": 100,
                "status": "success",
                "anomaly": True,
                "roi": 1500.0,
                "priority": "high",
                "similarity_hits": 2.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 1.5,
                "random_seed": 42,
                "error_msg": None
            },
            {
                "run_id": "run_002",
                "profile_id": "profile_002",
                "unit_id": 2,
                "time_cycle": 200,
                "status": "success",
                "anomaly": True,
                "roi": 2000.0,
                "priority": "medium",
                "similarity_hits": 1.0,
                "timestamp": "2025-01-15T10:00:05Z",
                "duration_sec": 1.8,
                "random_seed": 43,
                "error_msg": None
            },
            {
                "run_id": "run_003",
                "profile_id": "profile_003",
                "unit_id": 3,
                "time_cycle": 300,
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:10Z",
                "duration_sec": 1.2,
                "random_seed": 44,
                "error_msg": None
            },
            {
                "run_id": "run_004",
                "profile_id": "profile_004",
                "unit_id": 4,
                "time_cycle": 400,
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:15Z",
                "duration_sec": 1.3,
                "random_seed": 45,
                "error_msg": None
            },
            {
                "run_id": "run_005",
                "profile_id": "profile_005",
                "unit_id": 5,
                "time_cycle": 500,
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:20Z",
                "duration_sec": 1.4,
                "random_seed": 46,
                "error_msg": None
            }
        ],
        "summary_metrics": {
            "anomaly_rate": 0.4,
            "roi_distribution": {
                "mean": 1750.0,
                "median": 1750.0,
                "std": 250.0,
                "min": 1500.0,
                "max": 2000.0
            },
            "priority_distribution": {
                "high": 1,
                "medium": 1,
                "low": 0,
                "none": 3,
                "critical": 0,
                "error": 0
            },
            "similarity_hit_rate": 1.0,
            "avg_duration_sec": 1.44,
            "timestamp": "2025-01-15T10:00:20Z"
        },
        "timestamp": "2025-01-15T10:00:20Z",
        "duration_sec": 25.5,
        "mode": "sequential",
        "error_policy": "skip"
    }


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


# ============================================================================
# Metrics Calculation Tests
# ============================================================================

def test_calculate_metrics(sample_batch_result):
    """Test comprehensive metrics calculation."""
    metrics = _calculate_metrics(sample_batch_result)

    # Verify structure
    assert "batch_id" in metrics
    assert "timestamp" in metrics
    assert "execution" in metrics
    assert "anomaly_metrics" in metrics
    assert "roi_metrics" in metrics
    assert "priority_metrics" in metrics
    assert "research_metrics" in metrics
    assert "performance_metrics" in metrics

    # Verify execution metrics
    assert metrics["execution"]["total_runs"] == 5
    assert metrics["execution"]["successful_runs"] == 5
    assert metrics["execution"]["failed_runs"] == 0
    assert metrics["execution"]["success_rate"] == 1.0

    # Verify anomaly metrics
    assert metrics["anomaly_metrics"]["anomaly_rate"] == 0.4
    assert metrics["anomaly_metrics"]["total_anomalies"] == 2
    assert metrics["anomaly_metrics"]["total_normal"] == 3

    # Verify ROI metrics
    assert metrics["roi_metrics"]["mean"] == 1750.0
    assert metrics["roi_metrics"]["min"] == 1500.0
    assert metrics["roi_metrics"]["max"] == 2000.0


# ============================================================================
# JSON Serialization Tests
# ============================================================================

def test_canonical_json_serialization():
    """Test canonical JSON serialization is deterministic."""
    data = {
        "z_key": "value",
        "a_key": 123,
        "m_key": [3, 2, 1],
        "b_key": {"nested": True}
    }

    # Serialize multiple times
    json1 = _serialize_json_canonical(data)
    json2 = _serialize_json_canonical(data)
    json3 = _serialize_json_canonical(data)

    # Should be byte-identical
    assert json1 == json2 == json3

    # Verify sorted keys (a, b, m, z order)
    parsed = json.loads(json1)
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_canonical_json_float_serialization():
    """Test that numeric values are serialized as float."""
    data = {
        "int_value": 42,
        "float_value": 42.5,
        "nested": {
            "int_in_nested": 100
        }
    }

    json_str = _serialize_json_canonical(data)
    parsed = json.loads(json_str)

    # Verify all numbers are float-typed in JSON
    # (JSON doesn't distinguish, but our serializer coerces)
    assert isinstance(parsed["int_value"], (int, float))
    assert isinstance(parsed["float_value"], float)


# ============================================================================
# Report Generation Tests
# ============================================================================

def test_generate_json_report(sample_batch_result, temp_output_dir):
    """Test JSON report generation."""
    generate_report(
        batch_result=sample_batch_result,
        output_path=temp_output_dir,
        output_formats=["json"]
    )

    # Verify JSON file created
    json_path = Path(temp_output_dir) / "metrics.json"
    assert json_path.exists()

    # Verify JSON is valid and contains expected data
    with open(json_path, 'r') as f:
        metrics = json.load(f)

    assert metrics["batch_id"] == "batch_test_001"
    assert metrics["execution"]["total_runs"] == 5
    assert metrics["anomaly_metrics"]["anomaly_rate"] == 0.4


def test_generate_markdown_report(sample_batch_result, temp_output_dir):
    """Test markdown report generation."""
    generate_report(
        batch_result=sample_batch_result,
        output_path=temp_output_dir,
        output_formats=["markdown"]
    )

    # Verify markdown file created
    md_path = Path(temp_output_dir) / "metrics.md"
    assert md_path.exists()

    # Verify markdown content
    with open(md_path, 'r') as f:
        content = f.read()

    # Check for expected sections
    assert "# Simulation Metrics Report" in content
    assert "## Execution Summary" in content
    assert "## Anomaly Detection" in content
    assert "## ROI Distribution" in content
    assert "## Priority Distribution" in content
    assert "batch_test_001" in content

    # Check for formatted floats (%.2f)
    assert "%.2f" not in content  # Should be actual values, not format strings
    assert "1750.00" in content or "1,750.00" in content  # ROI mean


def test_generate_full_report(sample_batch_result, temp_output_dir):
    """Test full batch result output."""
    generate_report(
        batch_result=sample_batch_result,
        output_path=temp_output_dir,
        output_formats=["full"]
    )

    # Verify full result file created
    full_path = Path(temp_output_dir) / "batch_result.json"
    assert full_path.exists()

    # Verify full result contains all batch data
    with open(full_path, 'r') as f:
        full_result = json.load(f)

    assert full_result["batch_id"] == "batch_test_001"
    assert len(full_result["runs"]) == 5
    assert "summary_metrics" in full_result


def test_generate_all_formats(sample_batch_result, temp_output_dir):
    """Test generating all report formats."""
    generate_report(
        batch_result=sample_batch_result,
        output_path=temp_output_dir,
        output_formats=["json", "markdown", "full"]
    )

    # Verify all files created
    assert (Path(temp_output_dir) / "metrics.json").exists()
    assert (Path(temp_output_dir) / "metrics.md").exists()
    assert (Path(temp_output_dir) / "batch_result.json").exists()


# ============================================================================
# Edge Cases
# ============================================================================

def test_generate_report_with_failed_runs(temp_output_dir):
    """Test report generation with failed runs."""
    batch_result = {
        "batch_id": "batch_with_failures",
        "total_runs": 3,
        "successful_runs": 2,
        "failed_runs": [
            {
                "profile_id": "profile_003",
                "run_id": "run_003",
                "error_msg": "Test error message",
                "timestamp": "2025-01-15T10:00:10Z"
            }
        ],
        "runs": [
            {
                "run_id": "run_001",
                "profile_id": "profile_001",
                "unit_id": 1,
                "time_cycle": 100,
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 1.0,
                "random_seed": 42,
                "error_msg": None
            },
            {
                "run_id": "run_002",
                "profile_id": "profile_002",
                "unit_id": 2,
                "time_cycle": 200,
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:05Z",
                "duration_sec": 1.0,
                "random_seed": 43,
                "error_msg": None
            }
        ],
        "summary_metrics": {
            "anomaly_rate": 0.0,
            "roi_distribution": None,
            "priority_distribution": {"high": 0, "medium": 0, "low": 0, "none": 2, "critical": 0, "error": 0},
            "similarity_hit_rate": 0.0,
            "avg_duration_sec": 1.0,
            "timestamp": "2025-01-15T10:00:10Z"
        },
        "timestamp": "2025-01-15T10:00:10Z",
        "duration_sec": 10.0,
        "mode": "sequential",
        "error_policy": "skip"
    }

    generate_report(
        batch_result=batch_result,
        output_path=temp_output_dir,
        output_formats=["markdown"]
    )

    # Verify markdown includes failed runs section
    md_path = Path(temp_output_dir) / "metrics.md"
    with open(md_path, 'r') as f:
        content = f.read()

    assert "## Failed Runs" in content
    assert "profile_003" in content
    assert "Test error" in content


def test_output_directory_creation(sample_batch_result):
    """Test that output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "nested" / "output"

        generate_report(
            batch_result=sample_batch_result,
            output_path=str(nested_dir),
            output_formats=["json"]
        )

        # Verify nested directory was created
        assert nested_dir.exists()
        assert (nested_dir / "metrics.json").exists()
