"""
Tests for Batch Processor
=========================

Tests batch execution modes, error policies, and result aggregation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.simulation.batch_processor import (
    run_batch,
    _run_sequential,
    _run_parallel,
    _aggregate_results
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_profiles():
    """Sample equipment profiles for batch testing."""
    return [
        {
            "unit_id": 1,
            "time_cycle": 100,
            "sensor_values": {"s1": 100.0, "s2": 200.0},
            "profile_id": "profile_001"
        },
        {
            "unit_id": 2,
            "time_cycle": 200,
            "sensor_values": {"s1": 150.0, "s2": 250.0},
            "profile_id": "profile_002"
        },
        {
            "unit_id": 3,
            "time_cycle": 300,
            "sensor_values": {"s1": 200.0, "s2": 300.0},
            "profile_id": "profile_003"
        },
        {
            "unit_id": 4,
            "time_cycle": 400,
            "sensor_values": {"s1": 250.0, "s2": 350.0},
            "profile_id": "profile_004"
        },
        {
            "unit_id": 5,
            "time_cycle": 500,
            "sensor_values": {"s1": 300.0, "s2": 400.0},
            "profile_id": "profile_005"
        }
    ]


@pytest.fixture
def sample_results():
    """Sample simulation results for aggregation testing."""
    return [
        {
            "run_id": "run_001",
            "status": "success",
            "anomaly": True,
            "roi": 1500.0,
            "priority": "high",
            "similarity_hits": 2.0,
            "duration_sec": 1.5,
            "timestamp": "2025-01-15T10:00:00Z"
        },
        {
            "run_id": "run_002",
            "status": "success",
            "anomaly": True,
            "roi": 2000.0,
            "priority": "medium",
            "similarity_hits": 1.0,
            "duration_sec": 1.8,
            "timestamp": "2025-01-15T10:00:05Z"
        },
        {
            "run_id": "run_003",
            "status": "success",
            "anomaly": False,
            "roi": None,
            "priority": "none",
            "similarity_hits": 0.0,
            "duration_sec": 1.2,
            "timestamp": "2025-01-15T10:00:10Z"
        },
        {
            "run_id": "run_004",
            "status": "success",
            "anomaly": False,
            "roi": None,
            "priority": "none",
            "similarity_hits": 0.0,
            "duration_sec": 1.3,
            "timestamp": "2025-01-15T10:00:15Z"
        },
        {
            "run_id": "run_005",
            "status": "success",
            "anomaly": False,
            "roi": None,
            "priority": "none",
            "similarity_hits": 0.0,
            "duration_sec": 1.4,
            "timestamp": "2025-01-15T10:00:20Z"
        }
    ]


# ============================================================================
# Aggregation Tests
# ============================================================================

def test_aggregate_results_metrics_correctness(sample_results):
    """Test metrics aggregation correctness with known inputs."""
    metrics = _aggregate_results(sample_results)

    # Anomaly rate: 2 out of 5 = 0.4
    assert metrics["anomaly_rate"] == pytest.approx(0.4)

    # ROI distribution (only from 2 anomalies: 1500, 2000)
    assert metrics["roi_distribution"] is not None
    assert metrics["roi_distribution"]["mean"] == pytest.approx(1750.0)
    assert metrics["roi_distribution"]["median"] == pytest.approx(1750.0)
    assert metrics["roi_distribution"]["min"] == pytest.approx(1500.0)
    assert metrics["roi_distribution"]["max"] == pytest.approx(2000.0)

    # Priority distribution
    assert metrics["priority_distribution"]["high"] == 1
    assert metrics["priority_distribution"]["medium"] == 1
    assert metrics["priority_distribution"]["none"] == 3

    # Similarity hit rate (among anomalies with similarity_hits > 0)
    # 2 anomalies, both have similarity_hits > 0 = 100%
    assert metrics["similarity_hit_rate"] == pytest.approx(1.0)

    # Average duration
    expected_avg = (1.5 + 1.8 + 1.2 + 1.3 + 1.4) / 5
    assert metrics["avg_duration_sec"] == pytest.approx(expected_avg)


def test_aggregate_results_empty_batch():
    """Test aggregation with empty batch."""
    metrics = _aggregate_results([])

    assert metrics["anomaly_rate"] == 0.0
    assert metrics["roi_distribution"] is None
    assert metrics["similarity_hit_rate"] == 0.0
    assert metrics["avg_duration_sec"] == 0.0


def test_aggregate_results_float_precision():
    """Test that all metrics are float-typed."""
    results = [
        {
            "run_id": "run_001",
            "status": "success",
            "anomaly": True,
            "roi": 1500,  # int
            "priority": "high",
            "similarity_hits": 2,  # int
            "duration_sec": 1.5,
            "timestamp": "2025-01-15T10:00:00Z"
        }
    ]

    metrics = _aggregate_results(results)

    # Verify all numeric metrics are float
    assert isinstance(metrics["anomaly_rate"], float)
    assert isinstance(metrics["similarity_hit_rate"], float)
    assert isinstance(metrics["avg_duration_sec"], float)
    if metrics["roi_distribution"]:
        assert isinstance(metrics["roi_distribution"]["mean"], float)


# ============================================================================
# Sequential Execution Tests
# ============================================================================

@patch('src.simulation.batch_processor.run_single_simulation')
def test_batch_integrity_sequential(mock_run_single, sample_profiles):
    """Test batch integrity with sequential execution."""
    # Setup mock to return success results
    def mock_simulation(profile, run_id, random_seed, timeout_seconds):
        return {
            "run_id": run_id,
            "profile_id": profile["profile_id"],
            "unit_id": profile["unit_id"],
            "time_cycle": profile["time_cycle"],
            "status": "success",
            "anomaly": False,
            "roi": None,
            "priority": "none",
            "similarity_hits": 0.0,
            "timestamp": "2025-01-15T10:00:00Z",
            "duration_sec": 1.0,
            "random_seed": random_seed,
            "error_msg": None
        }

    mock_run_single.side_effect = mock_simulation

    # Run batch
    result = run_batch(
        profiles=sample_profiles,
        mode="sequential",
        error_policy="skip",
        base_random_seed=42
    )

    # Verify batch integrity
    assert result["total_runs"] == 5
    assert result["successful_runs"] == 5
    assert len(result["failed_runs"]) == 0
    assert len(result["runs"]) == 5

    # Verify sequential run IDs
    for idx, run in enumerate(result["runs"]):
        assert f"run_{idx:04d}" in run["run_id"]

    # Verify ISO timestamps
    assert "T" in result["timestamp"]
    assert isinstance(result["duration_sec"], float)


@patch('src.simulation.batch_processor.run_single_simulation')
def test_skip_error_policy(mock_run_single, sample_profiles):
    """Test skip error policy continues batch after failures."""
    # Setup mock: first and third profiles fail
    call_count = [0]

    def mock_simulation(profile, run_id, random_seed, timeout_seconds):
        call_count[0] += 1
        if call_count[0] in [1, 3]:  # Fail first and third
            return {
                "run_id": run_id,
                "profile_id": profile["profile_id"],
                "unit_id": profile["unit_id"],
                "time_cycle": profile["time_cycle"],
                "status": "error",
                "anomaly": False,
                "roi": None,
                "priority": "error",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 0.5,
                "random_seed": random_seed,
                "error_msg": "Test error"
            }
        else:
            return {
                "run_id": run_id,
                "profile_id": profile["profile_id"],
                "unit_id": profile["unit_id"],
                "time_cycle": profile["time_cycle"],
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 1.0,
                "random_seed": random_seed,
                "error_msg": None
            }

    mock_run_single.side_effect = mock_simulation

    # Run batch with skip policy
    result = run_batch(
        profiles=sample_profiles,
        mode="sequential",
        error_policy="skip",
        base_random_seed=42
    )

    # Verify batch continued despite failures
    assert result["total_runs"] == 5
    assert result["successful_runs"] == 3
    assert len(result["failed_runs"]) == 2

    # Verify failed runs are recorded
    assert all("error_msg" in failed for failed in result["failed_runs"])


@patch('src.simulation.batch_processor.run_single_simulation')
def test_failfast_error_policy(mock_run_single, sample_profiles):
    """Test fail-fast error policy aborts batch on first error."""
    # Setup mock: second profile fails
    call_count = [0]

    def mock_simulation(profile, run_id, random_seed, timeout_seconds):
        call_count[0] += 1
        if call_count[0] == 2:  # Fail second
            return {
                "run_id": run_id,
                "profile_id": profile["profile_id"],
                "unit_id": profile["unit_id"],
                "time_cycle": profile["time_cycle"],
                "status": "error",
                "anomaly": False,
                "roi": None,
                "priority": "error",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 0.5,
                "random_seed": random_seed,
                "error_msg": "Test error - fail fast"
            }
        else:
            return {
                "run_id": run_id,
                "profile_id": profile["profile_id"],
                "unit_id": profile["unit_id"],
                "time_cycle": profile["time_cycle"],
                "status": "success",
                "anomaly": False,
                "roi": None,
                "priority": "none",
                "similarity_hits": 0.0,
                "timestamp": "2025-01-15T10:00:00Z",
                "duration_sec": 1.0,
                "random_seed": random_seed,
                "error_msg": None
            }

    mock_run_single.side_effect = mock_simulation

    # Run batch with fail-fast policy - should raise exception
    with pytest.raises(RuntimeError) as exc_info:
        run_batch(
            profiles=sample_profiles,
            mode="sequential",
            error_policy="fail-fast",
            base_random_seed=42
        )

    assert "fail fast" in str(exc_info.value).lower()


# ============================================================================
# Parallel Execution Tests
# ============================================================================

@patch('src.simulation.batch_processor.run_single_simulation')
def test_parallel_mode_with_backoff(mock_run_single, sample_profiles):
    """Test parallel execution with backoff."""
    # Setup mock
    def mock_simulation(profile, run_id, random_seed, timeout_seconds):
        time.sleep(0.05)  # Simulate work
        return {
            "run_id": run_id,
            "profile_id": profile["profile_id"],
            "unit_id": profile["unit_id"],
            "time_cycle": profile["time_cycle"],
            "status": "success",
            "anomaly": False,
            "roi": None,
            "priority": "none",
            "similarity_hits": 0.0,
            "timestamp": "2025-01-15T10:00:00Z",
            "duration_sec": 0.05,
            "random_seed": random_seed,
            "error_msg": None
        }

    mock_run_single.side_effect = mock_simulation

    # Run batch in parallel mode
    start_time = time.time()
    result = run_batch(
        profiles=sample_profiles[:4],  # Use 4 profiles
        mode="parallel",
        error_policy="skip",
        max_workers=2,
        backoff_seconds=0.05,
        base_random_seed=42
    )
    duration = time.time() - start_time

    # Verify all runs completed
    assert result["total_runs"] == 4
    assert result["successful_runs"] == 4
    assert len(result["failed_runs"]) == 0

    # Parallel should be faster than sequential (with some tolerance)
    # Sequential would take: 4 * 0.05 = 0.2s + overhead
    # Parallel with 2 workers: 2 * 0.05 = 0.1s + overhead
    # We don't assert exact timing due to system variability


@patch('src.simulation.batch_processor.run_single_simulation')
def test_empty_batch_handling(mock_run_single):
    """Test empty profiles list."""
    result = run_batch(
        profiles=[],
        mode="sequential",
        error_policy="skip"
    )

    # Verify empty batch result
    assert result["total_runs"] == 0
    assert result["successful_runs"] == 0
    assert len(result["failed_runs"]) == 0
    assert len(result["runs"]) == 0

    # Verify metrics are zero
    assert result["summary_metrics"]["anomaly_rate"] == 0.0
    assert result["summary_metrics"]["roi_distribution"] is None
    assert result["summary_metrics"]["similarity_hit_rate"] == 0.0


# ============================================================================
# Input Validation Tests
# ============================================================================

def test_invalid_mode():
    """Test invalid execution mode."""
    with pytest.raises(ValueError) as exc_info:
        run_batch(
            profiles=[{"unit_id": 1, "time_cycle": 100, "sensor_values": {}}],
            mode="invalid_mode"
        )

    assert "Invalid mode" in str(exc_info.value)


def test_invalid_error_policy():
    """Test invalid error policy."""
    with pytest.raises(ValueError) as exc_info:
        run_batch(
            profiles=[{"unit_id": 1, "time_cycle": 100, "sensor_values": {}}],
            error_policy="invalid_policy"
        )

    assert "Invalid error_policy" in str(exc_info.value)
