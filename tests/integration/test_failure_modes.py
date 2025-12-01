"""
Tests for system behavior under failure conditions.

Scenarios:
1. Database unavailable
2. Corrupted database
3. Missing historical data
4. ML model errors
5. Invalid sensor data
6. Network timeouts (future)
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)


class TestDatabaseFailures:
    """Test behavior when database is unavailable."""

    def test_similarity_search_with_missing_database(self):
        """Should return error but not crash."""

        # Patch the database path to nonexistent file
        with patch('tools.database_query.DEFAULT_DB_PATH', 'nonexistent_database_xyz.db'):
            result = search_similar_failures_simple(
                sensor_values={"sensor_T30": 1620.0}
            )

            # Should fail gracefully
            assert result["success"] == False
            assert "error_type" in result
            assert "error_message" in result
            assert len(result["error_message"]) > 0

    def test_roi_calculation_with_database_error(self):
        """Should use fallback defaults when database fails."""

        # ROI calculation should work even without database
        # (uses default costs)
        result = calculate_roi_simple(
            failure_type="nonexistent_failure_type_xyz",
            failure_probability=0.7
        )

        # Should succeed with defaults
        assert result["success"] == True
        assert result["estimated_preventive_cost"] > 0
        assert result["estimated_reactive_cost"] > 0

    def test_work_order_generation_without_database(self):
        """Work order should generate without database dependency."""

        anomaly_data = {
            "anomaly_detected": True,
            "severity": "high",
            "anomaly_score": 0.85
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data
        )

        # Should succeed
        assert result["success"] == True
        assert "work_order_id" in result


class TestMLModelFailures:
    """Test ML model error handling."""

    def test_ml_detection_with_insufficient_data(self):
        """Should fall back to statistical methods."""

        # Use a unit with very little history
        result = analyze_sensors(
            unit_id=999,  # Unit likely has no or minimal history
            time_cycle=1,
            sensor_values={"sensor_T30": 1620.0},
            method="ml"
        )

        # Should succeed (falls back to statistical or handles gracefully)
        assert result["success"] == True
        # Method used might be statistical if ML failed
        assert result["method_used"] in ["statistical", "ml", "combined"]

    def test_ml_model_with_single_sensor(self):
        """Test ML detection with minimal sensor data."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0},  # Single sensor
            method="ml"
        )

        # Should handle gracefully
        assert result["success"] == True

    def test_combined_method_fallback(self):
        """Combined method should fall back gracefully."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0},
            method="combined"
        )

        # Should always succeed
        assert result["success"] == True
        assert "method_used" in result


class TestInvalidInputHandling:
    """Test handling of invalid inputs."""

    @pytest.mark.parametrize("invalid_sensor_value", [
        float('inf'),
        float('-inf'),
        1e15,  # Unreasonably large
        -1e15  # Unreasonably small
    ])
    def test_invalid_sensor_values(self, invalid_sensor_value):
        """Should reject invalid sensor values."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": invalid_sensor_value}
        )

        assert result["success"] == False
        error_msg_lower = result["error_message"].lower()
        assert ("validation" in error_msg_lower or
                "range" in error_msg_lower or
                "invalid" in error_msg_lower)

    def test_empty_sensor_values(self):
        """Should reject empty sensor dict."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={}
        )

        assert result["success"] == False
        assert "error_type" in result

    def test_negative_unit_id(self):
        """Should reject negative unit ID."""

        result = analyze_sensors(
            unit_id=-1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        assert result["success"] == False

    def test_zero_unit_id(self):
        """Should reject zero unit ID."""

        result = analyze_sensors(
            unit_id=0,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        assert result["success"] == False

    def test_negative_time_cycle(self):
        """Should reject negative time cycle."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=-100,
            sensor_values={"sensor_T30": 1620.0}
        )

        assert result["success"] == False

    def test_invalid_method(self):
        """Should reject invalid method."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0},
            method="invalid_method"
        )

        assert result["success"] == False

    def test_invalid_probability(self):
        """Should reject invalid probability values."""

        # Test probability > 1
        result1 = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=1.5
        )
        assert result1["success"] == False

        # Test negative probability
        result2 = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=-0.5
        )
        assert result2["success"] == False

    def test_invalid_top_n(self):
        """Should reject invalid top_n values."""

        # Test top_n too large
        result1 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=100
        )
        assert result1["success"] == False

        # Test top_n zero
        result2 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=0
        )
        assert result2["success"] == False

    def test_invalid_similarity_threshold(self):
        """Should reject invalid similarity threshold."""

        # Test threshold > 1
        result1 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            similarity_threshold=1.5
        )
        assert result1["success"] == False

        # Test negative threshold
        result2 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            similarity_threshold=-0.5
        )
        assert result2["success"] == False


class TestMissingDataHandling:
    """Test handling of missing or incomplete data."""

    def test_sensor_analysis_with_minimal_sensors(self):
        """Test with only one sensor."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # Should handle gracefully
        assert result["success"] == True

    def test_work_order_with_minimal_anomaly_data(self):
        """Test work order with minimal anomaly data."""

        minimal_anomaly_data = {
            "anomaly_detected": True,
            "severity": "medium"
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=minimal_anomaly_data
        )

        # Should succeed
        assert result["success"] == True

    def test_work_order_missing_required_fields(self):
        """Test work order with missing required fields."""

        incomplete_anomaly_data = {
            "anomaly_detected": True
            # Missing severity
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=incomplete_anomaly_data
        )

        # Should fail validation
        assert result["success"] == False
        assert "error_type" in result


class TestDataTypeErrors:
    """Test handling of wrong data types."""

    def test_sensor_values_wrong_type(self):
        """Test with non-numeric sensor values."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": "invalid"}  # String instead of float
        )

        assert result["success"] == False

    def test_non_dict_sensor_values(self):
        """Test with non-dictionary sensor values."""

        with pytest.raises(Exception):
            # This should raise a validation error at the Python level
            analyze_sensors(
                unit_id=1,
                time_cycle=100,
                sensor_values=[1620.0, 9080.0]  # List instead of dict
            )

    def test_string_as_numeric_parameter(self):
        """Test with string where number expected."""

        with pytest.raises(Exception):
            analyze_sensors(
                unit_id="one",  # String instead of int
                time_cycle=100,
                sensor_values={"sensor_T30": 1620.0}
            )


class TestConcurrentFailures:
    """Test behavior when multiple components fail."""

    def test_multiple_validation_errors(self):
        """Test with multiple invalid parameters."""

        result = analyze_sensors(
            unit_id=-1,  # Invalid
            time_cycle=-100,  # Invalid
            sensor_values={}  # Invalid
        )

        # Should report at least one error
        assert result["success"] == False
        assert "error_type" in result

    def test_sensor_analysis_with_all_invalid_sensors(self):
        """Test with all sensor values invalid."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={
                "sensor_T30": float('inf'),
                "sensor_Nc": float('-inf')
            }
        )

        assert result["success"] == False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_failure_probability(self):
        """Test ROI with zero failure probability."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.0
        )

        # Should succeed
        assert result["success"] == True
        # With zero probability, expected savings should be zero or negative
        assert result["expected_savings"] <= 0

    def test_full_failure_probability(self):
        """Test ROI with 100% failure probability."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=1.0
        )

        # Should succeed
        assert result["success"] == True
        # With 100% probability, should strongly recommend preventive
        assert result["expected_savings"] > 0

    def test_minimum_labor_hours(self):
        """Test with minimum labor hours."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7,
            preventive_labor_hours=0.1  # Minimum allowed
        )

        assert result["success"] == True

    def test_maximum_labor_hours(self):
        """Test with maximum labor hours."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7,
            preventive_labor_hours=100.0  # Maximum allowed
        )

        assert result["success"] == True

    def test_similarity_search_with_single_match(self):
        """Test similarity search requesting single match."""

        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            top_n=1
        )

        assert result["success"] == True
        if result["matches_found"] > 0:
            assert len(result["similar_failures"]) == 1

    def test_very_high_similarity_threshold(self):
        """Test with very high similarity threshold."""

        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0},
            similarity_threshold=0.99  # Very high
        )

        # Should succeed but may find no matches
        assert result["success"] == True
        # matches_found could be 0


class TestRecoveryMechanisms:
    """Test that systems recover gracefully from errors."""

    def test_subsequent_calls_after_error(self):
        """Test that system recovers after an error."""

        # First call with error
        result1 = analyze_sensors(
            unit_id=-1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )
        assert result1["success"] == False

        # Second call should work normally
        result2 = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )
        assert result2["success"] == True

    def test_error_does_not_affect_other_functions(self):
        """Test that error in one function doesn't affect others."""

        # Error in sensor analysis
        result1 = analyze_sensors(
            unit_id=-1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )
        assert result1["success"] == False

        # Other functions should still work
        result2 = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )
        assert result2["success"] == True
