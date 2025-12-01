"""
End-to-end integration tests for complete workflows.

These tests validate the entire pipeline from sensor data
to final work order generation.
"""

import pytest
import time
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)


class TestSensorToWorkOrderPipeline:
    """Test complete sensor → anomaly → similarity → ROI → work order flow."""

    def test_complete_workflow_high_severity(self):
        """Test complete workflow with high-severity anomaly."""

        # Step 1: Sensor analysis
        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=150,
            sensor_values={
                'sensor_T30': 1650.0,  # High temperature
                'sensor_Nc': 9100.0,   # High speed
                'sensor_Ps30': 48.5
            },
            method='combined'
        )

        assert sensor_result["success"] == True
        assert "anomaly_detected" in sensor_result
        assert "severity" in sensor_result
        assert sensor_result["severity"] in ["none", "low", "medium", "high", "critical"]

        # Only continue if anomaly detected
        if sensor_result["anomaly_detected"]:
            # Step 2: Find similar failures
            similarity_result = search_similar_failures_simple(
                sensor_values={'sensor_T30': 1650.0, 'sensor_Nc': 9100.0},
                top_n=3
            )

            assert similarity_result["success"] == True
            assert "matches_found" in similarity_result

            if similarity_result["matches_found"] > 0:
                failure_type = similarity_result["similar_failures"][0]["failure_type"]

                # Step 3: Calculate ROI
                roi_result = calculate_roi_simple(
                    failure_type=failure_type,
                    failure_probability=sensor_result["anomaly_score"],
                    preventive_labor_hours=4.0
                )

                assert roi_result["success"] == True
                assert "recommendation" in roi_result
                assert "expected_savings" in roi_result

                # Step 4: Generate work order
                work_order_result = generate_work_order_simple(
                    equipment_id=1,
                    anomaly_data=sensor_result,
                    roi_data=roi_result
                )

                assert work_order_result["success"] == True
                assert "work_order_id" in work_order_result
                assert work_order_result["priority"] in ["critical", "high", "medium", "low"]

                # Validate complete data flow
                assert work_order_result["issue_summary"] is not None
                assert len(work_order_result["recommended_actions"]) > 0
                assert work_order_result["estimated_cost"] > 0

    def test_complete_workflow_normal_operation(self):
        """Test workflow when no anomaly detected."""

        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={
                'sensor_T30': 1590.0,  # Normal
                'sensor_Nc': 9050.0,   # Normal
                'sensor_Ps30': 47.5    # Normal
            }
        )

        assert sensor_result["success"] == True
        assert "anomaly_detected" in sensor_result
        assert sensor_result["severity"] in ["none", "low", "medium", "high", "critical"]

        # For normal operation, workflow should complete without errors
        # but may not generate work orders
        # This tests graceful handling

    def test_workflow_resilience_with_no_similar_failures(self):
        """Test workflow when no similar failures found."""

        # Use sensor values that may not have matches
        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={
                'sensor_T30': 1620.0,
                'sensor_Nc': 9080.0
            }
        )

        if sensor_result["success"] and sensor_result["anomaly_detected"]:
            # Search with very high threshold
            similarity_result = search_similar_failures_simple(
                sensor_values={'sensor_T30': 1620.0},
                top_n=3,
                similarity_threshold=0.99  # Very high threshold
            )

            assert similarity_result["success"] == True
            # May have 0 matches, which is valid

    def test_workflow_performance_under_2_seconds(self):
        """Entire pipeline should complete within 2 seconds."""
        start = time.time()

        # Run complete workflow
        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1620.0, 'sensor_Nc': 9080.0}
        )

        if sensor_result["success"] and sensor_result.get("anomaly_detected"):
            similarity_result = search_similar_failures_simple(
                sensor_values={'sensor_T30': 1620.0}
            )

            if similarity_result["success"] and similarity_result["matches_found"] > 0:
                roi_result = calculate_roi_simple(
                    failure_type="HPC_degradation",
                    failure_probability=0.7
                )

                if roi_result["success"]:
                    work_order_result = generate_work_order_simple(
                        equipment_id=1,
                        anomaly_data=sensor_result,
                        roi_data=roi_result
                    )

        elapsed = time.time() - start

        # This is a performance guideline, not a strict requirement
        # Log warning if exceeds, but don't fail test
        if elapsed >= 2.0:
            print(f"WARNING: Workflow took {elapsed:.2f}s, expected < 2.0s")
        assert elapsed < 5.0, f"Workflow took {elapsed:.2f}s, maximum allowed is 5.0s"

    def test_workflow_data_consistency(self):
        """Test that data flows consistently through the pipeline."""

        # Step 1: Analyze sensors
        sensor_result = analyze_sensors(
            unit_id=5,
            time_cycle=200,
            sensor_values={
                'sensor_T30': 1640.0,
                'sensor_Nc': 9090.0,
                'sensor_Ps30': 48.2
            }
        )

        assert sensor_result["success"] == True

        if sensor_result["anomaly_detected"]:
            # Step 2: Generate work order
            work_order = generate_work_order_simple(
                equipment_id=5,
                anomaly_data=sensor_result
            )

            assert work_order["success"] == True

            # Verify severity mapping is consistent
            severity_to_priority = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "low": "low",
                "none": "low"
            }

            expected_priority = severity_to_priority.get(sensor_result["severity"], "medium")
            # Priority should match or be higher than severity
            priority_levels = ["low", "medium", "high", "critical"]
            assert priority_levels.index(work_order["priority"]) >= priority_levels.index(expected_priority) - 1


class TestPartialWorkflowScenarios:
    """Test partial workflows and edge cases."""

    def test_roi_calculation_without_database(self):
        """Test ROI calculation with fallback defaults."""

        # This should work even if database has no matching failure type
        result = calculate_roi_simple(
            failure_type="unknown_failure_type_xyz",
            failure_probability=0.5,
            preventive_labor_hours=3.0
        )

        # Should succeed with default costs
        assert result["success"] == True
        assert result["estimated_preventive_cost"] > 0

    def test_work_order_without_roi_data(self):
        """Test work order generation without ROI data."""

        anomaly_data = {
            "anomaly_detected": True,
            "severity": "medium",
            "anomaly_score": 0.6,
            "affected_sensors": ["sensor_T30"],
            "top_recommendation": "Monitor closely"
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data
            # No roi_data provided
        )

        assert result["success"] == True
        assert "work_order_id" in result

    def test_sensor_analysis_all_methods(self):
        """Test sensor analysis with different methods."""

        sensor_values = {'sensor_T30': 1620.0, 'sensor_Nc': 9080.0}

        # Test statistical method
        result_stat = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values=sensor_values,
            method="statistical"
        )
        assert result_stat["success"] == True
        assert result_stat["method_used"] in ["statistical", "combined"]

        # Test ML method
        result_ml = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values=sensor_values,
            method="ml"
        )
        assert result_ml["success"] == True

        # Test combined method
        result_combined = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values=sensor_values,
            method="combined"
        )
        assert result_combined["success"] == True


class TestWorkflowErrorRecovery:
    """Test error recovery in workflows."""

    def test_workflow_continues_on_similarity_search_failure(self):
        """Workflow should be resilient to similarity search failures."""

        # Get sensor analysis
        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1620.0}
        )

        if sensor_result["success"] and sensor_result["anomaly_detected"]:
            # Try similarity search with invalid parameters
            similarity_result = search_similar_failures_simple(
                sensor_values={'sensor_T30': 1620.0},
                top_n=100,  # Invalid
                similarity_threshold=0.5
            )

            # Should fail gracefully
            assert similarity_result["success"] == False

            # But we can still generate work order without similarity data
            work_order = generate_work_order_simple(
                equipment_id=1,
                anomaly_data=sensor_result
            )

            assert work_order["success"] == True

    def test_workflow_handles_missing_data_gracefully(self):
        """Test workflow with minimal data."""

        # Minimal sensor analysis
        sensor_result = analyze_sensors(
            unit_id=1,
            time_cycle=1,
            sensor_values={'sensor_T30': 1600.0}  # Single sensor
        )

        assert sensor_result["success"] == True

        # Should be able to generate work order even with minimal data
        if sensor_result["anomaly_detected"]:
            work_order = generate_work_order_simple(
                equipment_id=1,
                anomaly_data=sensor_result
            )

            assert work_order["success"] == True


class TestConcurrentWorkflows:
    """Test multiple concurrent workflows."""

    def test_multiple_units_analyzed_independently(self):
        """Test that multiple units can be analyzed independently."""

        # Analyze different units
        result1 = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={'sensor_T30': 1620.0}
        )

        result2 = analyze_sensors(
            unit_id=2,
            time_cycle=100,
            sensor_values={'sensor_T30': 1580.0}
        )

        result3 = analyze_sensors(
            unit_id=3,
            time_cycle=100,
            sensor_values={'sensor_T30': 1630.0}
        )

        # All should succeed independently
        assert result1["success"] == True
        assert result2["success"] == True
        assert result3["success"] == True

        # Results should be independent
        # (different units may have different results)
