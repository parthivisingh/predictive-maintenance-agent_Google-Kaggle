"""
Tests for LLM tool integration and serialization.

Validates that:
1. All tool outputs are JSON-serializable
2. Outputs can be deserialized by LLM agents
3. Schema stability (no breaking changes)
4. No numpy types in outputs
"""

import json
import pytest
import numpy as np
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)


class TestLLMSerialization:
    """Test serialization for LLM consumption."""

    def test_all_outputs_json_serializable(self):
        """All wrapper outputs must be JSON-serializable."""

        # Test sensor analysis
        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0, "sensor_Nc": 9080.0}
        )

        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert deserialized["success"] == result["success"]

        # Test similarity search
        result2 = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0}
        )
        json_str2 = json.dumps(result2)
        assert len(json_str2) > 0

        # Test ROI calculation
        result3 = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )
        json_str3 = json.dumps(result3)
        assert len(json_str3) > 0

        # Test work order
        result4 = generate_work_order_simple(
            equipment_id=1,
            anomaly_data={"anomaly_detected": True, "severity": "high"}
        )
        json_str4 = json.dumps(result4)
        assert len(json_str4) > 0

    def test_no_numpy_types_in_output(self):
        """Outputs should not contain numpy types (not JSON-serializable)."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0, "sensor_Nc": 9080.0}
        )

        # Recursively check for numpy types
        def check_types(obj, path="root"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    check_types(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_types(item, f"{path}[{i}]")
            else:
                # Check if it's a numpy type
                if isinstance(obj, (np.integer, np.floating, np.ndarray)):
                    pytest.fail(f"Found numpy type at {path}: {type(obj)}")

        check_types(result)

    def test_schema_stability_sensor_analysis(self):
        """Response schemas should remain stable (no unexpected fields)."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # Define expected schema
        if result["success"]:
            required_fields = {
                "success", "anomaly_detected", "anomaly_score",
                "severity", "confidence", "affected_sensors",
                "top_recommendation", "all_recommendations", "method_used", "timestamp"
            }
            assert required_fields.issubset(set(result.keys())), \
                f"Missing fields: {required_fields - set(result.keys())}"
        else:
            required_fields = {"success", "error_type", "error_message", "timestamp"}
            assert required_fields.issubset(set(result.keys())), \
                f"Missing fields: {required_fields - set(result.keys())}"

    def test_schema_stability_similarity_search(self):
        """Similarity search response schema stability."""

        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0}
        )

        if result["success"]:
            required_fields = {"success", "matches_found", "similar_failures", "timestamp"}
            assert required_fields.issubset(set(result.keys()))

            # Check structure of similar_failures
            if result["matches_found"] > 0:
                failure = result["similar_failures"][0]
                failure_fields = {
                    "similarity_score", "failure_type", "root_cause",
                    "action_taken", "parts_replaced", "avg_cost", "avg_downtime"
                }
                assert failure_fields.issubset(set(failure.keys()))

    def test_schema_stability_roi_calculation(self):
        """ROI calculation response schema stability."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )

        if result["success"]:
            required_fields = {
                "success", "estimated_preventive_cost", "estimated_reactive_cost",
                "expected_savings", "roi_percentage", "recommendation", "timestamp"
            }
            assert required_fields.issubset(set(result.keys()))

    def test_schema_stability_work_order(self):
        """Work order response schema stability."""

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data={"anomaly_detected": True, "severity": "high"}
        )

        if result["success"]:
            required_fields = {
                "success", "work_order_id", "priority", "issue_summary",
                "recommended_actions", "estimated_cost", "estimated_duration", "timestamp"
            }
            assert required_fields.issubset(set(result.keys()))

    def test_llm_prompt_integration(self):
        """Test that outputs can be embedded in LLM prompts."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1650.0, "sensor_Nc": 9100.0}
        )

        # Simulate LLM prompt
        prompt = f"""
        Based on the following sensor analysis:

        {json.dumps(result, indent=2)}

        Provide maintenance recommendations.
        """

        assert len(prompt) > 0
        assert "anomaly_score" in prompt or "error" in prompt.lower()

    def test_nested_json_serialization(self):
        """Test that complex nested structures serialize properly."""

        # Create complex anomaly data
        anomaly_data = {
            "anomaly_detected": True,
            "severity": "high",
            "anomaly_score": 0.85,
            "affected_sensors": ["sensor_T30", "sensor_Nc"],
            "sensor_values": {
                "sensor_T30": 1650.0,
                "sensor_Nc": 9100.0
            },
            "recommendations": [
                "Check temperature sensors",
                "Inspect cooling system"
            ]
        }

        roi_data = {
            "estimated_preventive_cost": 2500.0,
            "expected_savings": 10000.0,
            "breakdown": {
                "labor": 1000.0,
                "parts": 1500.0
            }
        }

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data=anomaly_data,
            roi_data=roi_data
        )

        # Should serialize completely
        json_str = json.dumps(result, indent=2)
        assert len(json_str) > 0

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert deserialized["success"] == result["success"]

    def test_numeric_precision_maintained(self):
        """Test that numeric values maintain appropriate precision."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation",
            failure_probability=0.7
        )

        if result["success"]:
            # Check that values are rounded appropriately
            assert isinstance(result["estimated_preventive_cost"], (int, float))
            assert isinstance(result["expected_savings"], (int, float))
            assert isinstance(result["roi_percentage"], (int, float))

            # Values should be rounded to 2 decimal places
            # (when serialized as JSON, precision is maintained)
            json_str = json.dumps(result)
            parsed = json.loads(json_str)
            assert parsed["estimated_preventive_cost"] == result["estimated_preventive_cost"]

    def test_unicode_handling(self):
        """Test that unicode characters are handled properly."""

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data={
                "anomaly_detected": True,
                "severity": "high",
                "description": "Temperature ≥ 1650°C detected"  # Unicode chars
            },
            assigned_to="José García"  # Unicode name
        )

        # Should serialize with unicode
        json_str = json.dumps(result, ensure_ascii=False)
        assert len(json_str) > 0

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert deserialized["success"] == result["success"]

    def test_special_characters_in_strings(self):
        """Test handling of special characters in strings."""

        result = calculate_roi_simple(
            failure_type="HPC_degradation \"critical\"",  # Quotes
            failure_probability=0.7
        )

        # Should handle escaping properly
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should deserialize correctly
        deserialized = json.loads(json_str)
        assert deserialized["success"] == result["success"]


class TestLLMResponseParsing:
    """Test that LLM agents can easily parse responses."""

    def test_simple_field_access(self):
        """Test that common fields are easily accessible."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # LLM can check success directly
        if result["success"]:
            # Easy access to key fields
            _ = result["anomaly_detected"]
            _ = result["severity"]
            _ = result["top_recommendation"]

        # No exceptions should be raised

    def test_array_iteration(self):
        """Test that arrays can be easily iterated."""

        result = search_similar_failures_simple(
            sensor_values={"sensor_T30": 1620.0}
        )

        if result["success"] and result["matches_found"] > 0:
            # LLM can iterate over failures
            for failure in result["similar_failures"]:
                assert "failure_type" in failure
                assert "similarity_score" in failure

    def test_conditional_field_handling(self):
        """Test that optional fields are handled properly."""

        result = generate_work_order_simple(
            equipment_id=1,
            anomaly_data={"anomaly_detected": True, "severity": "high"}
            # No roi_data
        )

        # Should succeed without roi_data
        assert result["success"] == True
        # Required fields should be present
        assert "work_order_id" in result

    def test_error_response_parsing(self):
        """Test that error responses are easily parsable."""

        result = analyze_sensors(
            unit_id=-1,  # Invalid
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # LLM can easily check for errors
        assert result["success"] == False
        assert "error_type" in result
        assert "error_message" in result

        # Can format error message for user
        error_msg = f"Error ({result['error_type']}): {result['error_message']}"
        assert len(error_msg) > 0


class TestBackwardsCompatibility:
    """Test that API changes don't break existing integrations."""

    def test_additional_fields_dont_break_parsing(self):
        """New fields can be added without breaking existing code."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        # Existing code that only checks specific fields should still work
        assert "success" in result
        assert "timestamp" in result

        # Even if new fields are added in the future, these should remain

    def test_field_types_remain_consistent(self):
        """Field types should remain consistent across versions."""

        result = analyze_sensors(
            unit_id=1,
            time_cycle=100,
            sensor_values={"sensor_T30": 1620.0}
        )

        if result["success"]:
            # These types should never change
            assert isinstance(result["success"], bool)
            assert isinstance(result["anomaly_detected"], bool)
            assert isinstance(result["anomaly_score"], (int, float))
            assert isinstance(result["severity"], str)
            assert isinstance(result["affected_sensors"], list)
            assert isinstance(result["all_recommendations"], list)
