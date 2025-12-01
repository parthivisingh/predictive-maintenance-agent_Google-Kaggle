"""
Tests for Simulation Runner
===========================

Tests deterministic execution, input validation, and RootAgent integration.
"""

import pytest
import jsonschema
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.simulation.simulation_runner import (
    run_single_simulation,
    _validate_input,
    _extract_metrics,
    _normalize_for_comparison
)
from agents.schemas import RootAgentOutput, FinalDecision, ExecutionMetadata, PipelineResults


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_profile():
    """Valid equipment profile."""
    return {
        "unit_id": 1,
        "time_cycle": 100,
        "sensor_values": {
            "s1": 100.5,
            "s2": 200.3,
            "s3": 50.1
        },
        "profile_id": "test_profile_001"
    }


@pytest.fixture
def mock_root_output_anomaly():
    """Mock RootAgentOutput with anomaly detected."""
    return {
        "success": True,
        "unit_id": 1,
        "time_cycle": 100,
        "pipeline_results": {
            "diagnostic": {
                "agent": "diagnostic_agent",
                "success": True,
                "anomaly_detected": True,
                "anomaly_score": 0.85,
                "severity": "high",
                "confidence": 0.9,
                "affected_sensors": ["s1", "s2"],
                "top_recommendation": "Check cooling system",
                "all_recommendations": ["Check cooling system", "Inspect sensors"],
                "method_used": "combined",
                "timestamp": "2025-01-15T10:00:00Z",
                "error": None
            },
            "research": {
                "agent": "research_agent",
                "success": True,
                "matches_found": 2,
                "similar_failures": [
                    {
                        "similarity_score": 0.92,
                        "failure_type": "cooling_failure",
                        "root_cause": "Fan malfunction",
                        "action_taken": "Replace fan",
                        "parts_replaced": ["cooling_fan"],
                        "avg_cost": 1500.0,
                        "avg_downtime": 4.0
                    }
                ],
                "timestamp": "2025-01-15T10:00:01Z",
                "error": None
            },
            "recommendation": {
                "agent": "recommendation_agent",
                "success": True,
                "roi_analysis": {
                    "estimated_preventive_cost": 1500.0,
                    "estimated_reactive_cost": 5000.0,
                    "expected_savings": 3500.0,
                    "roi_percentage": 233.33,
                    "recommendation": "preventive"
                },
                "work_order": {
                    "work_order_id": "WO-001",
                    "priority": "high",
                    "issue_summary": "Cooling system anomaly detected",
                    "recommended_actions": ["Replace cooling fan", "Test system"],
                    "estimated_cost": 1500.0,
                    "estimated_duration": 4.0
                },
                "timestamp": "2025-01-15T10:00:02Z",
                "error": None,
                "message": None
            }
        },
        "final_decision": {
            "action_required": True,
            "priority": "high",
            "work_order_id": "WO-001",
            "summary": "Cooling system anomaly detected",
            "estimated_cost": 1500.0,
            "recommended_actions": ["Replace cooling fan", "Test system"]
        },
        "execution_metadata": {
            "total_time_ms": 250.5,
            "agents_called": ["diagnostic_agent", "research_agent", "recommendation_agent"],
            "errors_encountered": []
        },
        "timestamp": "2025-01-15T10:00:02Z"
    }


@pytest.fixture
def mock_root_output_normal():
    """Mock RootAgentOutput with no anomaly."""
    return {
        "success": True,
        "unit_id": 1,
        "time_cycle": 100,
        "pipeline_results": {
            "diagnostic": {
                "agent": "diagnostic_agent",
                "success": True,
                "anomaly_detected": False,
                "anomaly_score": 0.1,
                "severity": "none",
                "confidence": 0.95,
                "affected_sensors": [],
                "top_recommendation": "Continue normal operation",
                "all_recommendations": [],
                "method_used": "combined",
                "timestamp": "2025-01-15T10:00:00Z",
                "error": None
            },
            "research": {
                "agent": "research_agent",
                "success": True,
                "matches_found": 0,
                "similar_failures": [],
                "timestamp": "2025-01-15T10:00:01Z",
                "error": None
            },
            "recommendation": {
                "agent": "recommendation_agent",
                "success": True,
                "roi_analysis": None,
                "work_order": None,
                "timestamp": "2025-01-15T10:00:02Z",
                "error": None,
                "message": "No action required"
            }
        },
        "final_decision": {
            "action_required": False,
            "priority": "none",
            "work_order_id": None,
            "summary": "Equipment operating normally. No maintenance required.",
            "estimated_cost": None,
            "recommended_actions": None
        },
        "execution_metadata": {
            "total_time_ms": 150.2,
            "agents_called": ["diagnostic_agent"],
            "errors_encountered": []
        },
        "timestamp": "2025-01-15T10:00:02Z"
    }


# ============================================================================
# Input Validation Tests
# ============================================================================

def test_validate_input_valid(valid_profile):
    """Test validation passes for valid profile."""
    # Should not raise
    _validate_input(valid_profile)


def test_validate_input_missing_unit_id():
    """Test validation fails for missing unit_id."""
    profile = {
        "time_cycle": 100,
        "sensor_values": {"s1": 100.0}
    }

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        _validate_input(profile)

    assert "unit_id" in str(exc_info.value)


def test_validate_input_invalid_unit_id():
    """Test validation fails for invalid unit_id."""
    profile = {
        "unit_id": -1,  # Must be >= 1
        "time_cycle": 100,
        "sensor_values": {"s1": 100.0}
    }

    with pytest.raises(jsonschema.ValidationError):
        _validate_input(profile)


def test_validate_input_empty_sensor_values():
    """Test validation fails for empty sensor_values."""
    profile = {
        "unit_id": 1,
        "time_cycle": 100,
        "sensor_values": {}  # Must have at least 1 entry
    }

    with pytest.raises(jsonschema.ValidationError):
        _validate_input(profile)


# ============================================================================
# Metrics Extraction Tests
# ============================================================================

def test_extract_metrics_anomaly(mock_root_output_anomaly):
    """Test metrics extraction from anomaly output."""
    metrics = _extract_metrics(mock_root_output_anomaly)

    assert metrics["anomaly"] is True
    assert metrics["roi"] == 1500.0
    assert isinstance(metrics["roi"], float)
    assert metrics["priority"] == "high"
    assert metrics["similarity_hits"] == 2.0
    assert isinstance(metrics["similarity_hits"], float)


def test_extract_metrics_normal(mock_root_output_normal):
    """Test metrics extraction from normal output."""
    metrics = _extract_metrics(mock_root_output_normal)

    assert metrics["anomaly"] is False
    assert metrics["roi"] is None
    assert metrics["priority"] == "none"
    assert metrics["similarity_hits"] == 0.0
    assert isinstance(metrics["similarity_hits"], float)


def test_extract_metrics_float_coercion(mock_root_output_anomaly):
    """Test that all numeric metrics are coerced to float."""
    metrics = _extract_metrics(mock_root_output_anomaly)

    # Verify float types
    assert isinstance(metrics["similarity_hits"], float)
    if metrics["roi"] is not None:
        assert isinstance(metrics["roi"], float)


# ============================================================================
# Deterministic Execution Tests
# ============================================================================

@patch('src.simulation.simulation_runner.RootAgent')
def test_deterministic_content_equivalence(mock_root_agent_class, valid_profile, mock_root_output_anomaly):
    """Test that same profile + seed yields content-equivalent metrics."""
    # Setup mock
    mock_agent = Mock()
    mock_agent.execute_pipeline.return_value = mock_root_output_anomaly
    mock_root_agent_class.return_value = mock_agent

    # Run 3 times with same seed
    results = []
    for i in range(3):
        result = run_single_simulation(
            profile=valid_profile,
            run_id=f"test_run_{i}",
            random_seed=42
        )
        results.append(result)

    # Normalize for comparison (freeze timestamps)
    normalized = [_normalize_for_comparison(r) for r in results]

    # Check content equivalence (excluding timestamps)
    assert normalized[0]["anomaly"] == normalized[1]["anomaly"] == normalized[2]["anomaly"]
    assert normalized[0]["roi"] == normalized[1]["roi"] == normalized[2]["roi"]
    assert normalized[0]["priority"] == normalized[1]["priority"] == normalized[2]["priority"]
    assert normalized[0]["similarity_hits"] == normalized[1]["similarity_hits"] == normalized[2]["similarity_hits"]

    # Verify seed was passed correctly
    for call in mock_agent.execute_pipeline.call_args_list:
        assert call[1]["config"]["random_seed"] == 42


@patch('src.simulation.simulation_runner.RootAgent')
def test_run_single_simulation_success(mock_root_agent_class, valid_profile, mock_root_output_anomaly):
    """Test successful single simulation run."""
    # Setup mock
    mock_agent = Mock()
    mock_agent.execute_pipeline.return_value = mock_root_output_anomaly
    mock_root_agent_class.return_value = mock_agent

    result = run_single_simulation(
        profile=valid_profile,
        run_id="test_run_001",
        random_seed=42
    )

    # Verify result structure
    assert result["run_id"] == "test_run_001"
    assert result["profile_id"] == "test_profile_001"
    assert result["unit_id"] == 1
    assert result["time_cycle"] == 100
    assert result["status"] == "success"
    assert result["anomaly"] is True
    assert result["roi"] == 1500.0
    assert result["priority"] == "high"
    assert result["similarity_hits"] == 2.0
    assert result["random_seed"] == 42
    assert result["error_msg"] is None
    assert isinstance(result["duration_sec"], float)
    assert isinstance(result["timestamp"], str)


@patch('src.simulation.simulation_runner.RootAgent')
def test_run_single_simulation_error_handling(mock_root_agent_class, valid_profile):
    """Test error handling in simulation run."""
    # Setup mock to raise exception
    mock_agent = Mock()
    mock_agent.execute_pipeline.side_effect = RuntimeError("Test error")
    mock_root_agent_class.return_value = mock_agent

    result = run_single_simulation(
        profile=valid_profile,
        run_id="test_run_error",
        random_seed=42
    )

    # Verify error result
    assert result["status"] == "error"
    assert result["error_msg"] is not None
    assert "RuntimeError" in result["error_msg"]
    assert result["anomaly"] is False
    assert result["roi"] is None
    assert result["priority"] == "error"


# ============================================================================
# Normalization Tests
# ============================================================================

def test_normalize_for_comparison():
    """Test result normalization for deterministic comparison."""
    result = {
        "run_id": "test_001",
        "timestamp": "2025-01-15T10:30:45.123456",
        "duration_sec": 1.2345678,
        "anomaly": True,
        "roi": 1500.0
    }

    normalized = _normalize_for_comparison(result)

    # Verify timestamp is frozen
    assert normalized["timestamp"] == "2025-01-01T00:00:00.000000"

    # Verify duration is rounded
    assert normalized["duration_sec"] == 1.235

    # Verify other fields unchanged
    assert normalized["anomaly"] is True
    assert normalized["roi"] == 1500.0


# ============================================================================
# Integration Test (Real RootAgent)
# ============================================================================

@pytest.mark.integration
def test_real_rootagent_integration_smoke(valid_profile):
    """Smoke test with real RootAgent integration."""
    # This test uses the real RootAgent (no mocking)
    # Only run in controlled environments with proper setup

    result = run_single_simulation(
        profile=valid_profile,
        run_id="integration_test_001",
        random_seed=42
    )

    # Verify result structure (don't assert specific values)
    assert "run_id" in result
    assert "status" in result
    assert "anomaly" in result
    assert "roi" in result
    assert "priority" in result
    assert "similarity_hits" in result
    assert "timestamp" in result
    assert "duration_sec" in result

    # Verify types
    assert isinstance(result["anomaly"], bool)
    assert isinstance(result["priority"], str)
    assert isinstance(result["similarity_hits"], float)
    assert isinstance(result["duration_sec"], float)

    if result["roi"] is not None:
        assert isinstance(result["roi"], float)
