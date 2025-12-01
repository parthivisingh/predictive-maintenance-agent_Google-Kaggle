"""
Tests for API Wrappers
=======================

Comprehensive test suite for all API wrapper functions.
"""

import pytest
import json
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)


class TestSensorAnalysisWrapper:
    """Test sensor analysis API wrapper."""

    def test_analyze_sensors_success(self):
        """Test successful sensor analysis."""
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0, "sensor_Nc": 9080.0}
        )

        assert result["success"] == True
        assert "anomaly_score" in result
        assert 0 <= result["anomaly_score"] <= 1
        assert result["severity"] in ["none", "low", "medium", "high", "critical"]
        assert isinstance(result["affected_sensors"], list)
        assert "top_recommendation" in result
        assert "method_used" in result

    def test_analyze_sensors_validation_error_negative_unit_id(self):
        """Test input validation for negative unit ID."""
        result = analyze_sensors(
            unit_id=-1,  # Invalid
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        assert result["success"] == False
        assert "error_type" in result
        assert "error_message" in result

    def test_analyze_sensors_validation_error_invalid_method(self):
        """Test input validation for invalid method."""
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0},
            method="invalid_method"  # Invalid
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_analyze_sensors_empty_sensor_values(self):
        """Test with empty sensor values."""
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={}  # Empty
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_analyze_sensors_extreme_values(self):
        """Test with extreme sensor values."""
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1e15}  # Extreme value
        )

        assert result["success"] == False
        assert "range" in result["error_message"].lower() or "validation" in result["error_message"].lower()

    def test_analyze_sensors_json_serializable(self):
        """Test that output is JSON serializable."""
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert deserialized["success"] == result["success"]


class TestSimilaritySearchWrapper:
    """Test similarity search API wrapper."""

    def test_search_similar_failures_success(self):
        """Test successful similarity search."""
        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0, "sensor_Nc": 9080.0},
            top_n=3,
            similarity_threshold=0.5
        )

        assert result["success"] == True
        assert "matches_found" in result
        assert "similar_failures" in result
        assert isinstance(result["similar_failures"], list)
        assert result["matches_found"] == len(result["similar_failures"])

    def test_search_similar_failures_validation_top_n_too_large(self):
        """Test validation for top_n too large."""
        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=20,  # Too large
            similarity_threshold=0.5
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_search_similar_failures_validation_threshold_out_of_range(self):
        """Test validation for similarity threshold out of range."""
        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=3,
            similarity_threshold=1.5  # Out of range
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_search_similar_failures_response_structure(self):
        """Test response structure for similarity search."""
        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=3
        )

        if result["success"] and result["matches_found"] > 0:
            failure = result["similar_failures"][0]
            assert "similarity_score" in failure
            assert "failure_type" in failure
            assert "root_cause" in failure
            assert "action_taken" in failure
            assert "parts_replaced" in failure
            assert isinstance(failure["parts_replaced"], list)

    def test_search_similar_failures_json_serializable(self):
        """Test that output is JSON serializable."""
        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0}
        )

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0


class TestROICalculationWrapper:
    """Test ROI calculation API wrapper."""

    def test_calculate_roi_success(self):
        """Test successful ROI calculation."""
        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7,
            preventive_labor_hours=4.0
        )

        assert result["success"] == True
        assert "estimated_preventive_cost" in result
        assert "estimated_reactive_cost" in result
        assert "expected_savings" in result
        assert "roi_percentage" in result
        assert "recommendation" in result
        assert isinstance(result["estimated_preventive_cost"], (int, float))

    def test_calculate_roi_validation_probability_out_of_range(self):
        """Test validation for probability out of range."""
        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=1.5,  # Out of range
            preventive_labor_hours=4.0
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_calculate_roi_validation_negative_labor_hours(self):
        """Test validation for negative labor hours."""
        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7,
            preventive_labor_hours=-1.0  # Negative
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_calculate_roi_with_custom_costs(self):
        """Test ROI calculation with custom costs."""
        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7,
            preventive_labor_hours=4.0,
            custom_costs={"labor_rate": 100.0, "part_cost": 500.0}
        )

        assert result["success"] == True
        assert result["estimated_preventive_cost"] > 0

    def test_calculate_roi_json_serializable(self):
        """Test that output is JSON serializable."""
        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0


class TestWorkOrderGenerationWrapper:
    """Test work order generation API wrapper."""

    def test_generate_work_order_success(self):
        """Test successful work order generation."""
        anomaly_data = {
            "anomaly_detected": True,
            "severity": "high",
            "anomaly_score": 0.85,
            "affected_sensors": ["sensor_T30"],
            "recommendations": ["Inspect for overheating"]
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data
        )

        assert result["success"] == True
        assert "work_order_id" in result
        assert "priority" in result
        assert "issue_summary" in result
        assert "recommended_actions" in result
        assert "estimated_cost" in result
        assert isinstance(result["recommended_actions"], list)

    def test_generate_work_order_validation_missing_fields(self):
        """Test validation for missing required fields in anomaly_data."""
        anomaly_data = {
            "anomaly_detected": True
            # Missing 'severity'
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_generate_work_order_with_roi_data(self):
        """Test work order generation with ROI data."""
        anomaly_data = {
            "anomaly_detected": True,
            "severity": "high",
            "anomaly_score": 0.85
        }

        roi_data = {
            "expected_savings": 5000.0,
            "roi_percentage": 250.0
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data,
            roi_data=roi_data
        )

        assert result["success"] == True

    def test_generate_work_order_json_serializable(self):
        """Test that output is JSON serializable."""
        anomaly_data = {
            "anomaly_detected": True,
            "severity": "high"
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data
        )

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0


class TestAPIWrapperConsistency:
    """Test consistency across all API wrappers."""

    def test_all_wrappers_have_success_field(self):
        """All wrappers must include 'success' field in response."""
        # Sensor analysis
        result1 = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )
        assert "success" in result1
        assert isinstance(result1["success"], bool)

        # Similarity search
        result2 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0}
        )
        assert "success" in result2
        assert isinstance(result2["success"], bool)

        # ROI calculation
        result3 = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )
        assert "success" in result3
        assert isinstance(result3["success"], bool)

        # Work order
        result4 = generate_work_order_simple(
            equipment_id=1,
            anomaly_data={"anomaly_detected": True, "severity": "high"}
        )
        assert "success" in result4
        assert isinstance(result4["success"], bool)

    def test_all_wrappers_have_timestamp(self):
        """All wrappers must include 'timestamp' field."""
        result1 = analyze_sensors(1, 100, {"sensor_T30": 1620.0})
        assert "timestamp" in result1

        result2 = search_similar_failures_simple({"sensor_T30": 1620.0})
        assert "timestamp" in result2

        result3 = calculate_roi_simple("HPC_degradation", 0.7)
        assert "timestamp" in result3

        result4 = generate_work_order_simple(1, {"anomaly_detected": True, "severity": "high"})
        assert "timestamp" in result4

    def test_error_responses_have_standard_structure(self):
        """Error responses must have consistent structure."""
        # Trigger validation error
        result = analyze_sensors(
            unit_id=-1,  # Invalid
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        assert result["success"] == False
        assert "error_type" in result
        assert "error_message" in result
        assert "timestamp" in result

    def test_no_exceptions_raised_from_wrappers(self):
        """No wrapper should raise exceptions."""
        # All these should return error dicts, not raise exceptions
        try:
            analyze_sensors(-1, 100, {"sensor_T30": 1620.0})
            search_similar_failures_simple({}, top_n=100)
            calculate_roi_simple("HPC_degradation", 2.0)
            generate_work_order_simple(1, {})
        except Exception as e:
            pytest.fail(f"Wrapper raised exception: {e}")
