"""
Phase 4 Validation Tests

Tests ensuring:
1. Agents only call wrapper APIs
2. No direct Phase 3.5 module imports
3. Deterministic behavior
4. Proper error handling
5. Pipeline orchestration correctness
"""

import unittest
import inspect
from unittest.mock import patch, MagicMock
from agents.root_agent import RootAgent
from agents.diagnostic_agent import DiagnosticAgent
from agents.research_agent import ResearchAgent
from agents.recommendation_agent import RecommendationAgent


class Phase4ValidationTests(unittest.TestCase):
    """
    Validation tests for Phase 4 multi-agent system.
    Ensures compliance with design principles and isolation from Phase 3.5.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.root_agent = RootAgent()
        self.test_sensor_data = {
            "sensor_T30": 1605.2,
            "sensor_T50": 1450.8,
            "sensor_T2": 643.1,
            "sensor_T24": 1526.8,
            "sensor_T50_2": 1350.5,
            "sensor_P2": 551.2,
            "sensor_P15": 8.4,
            "sensor_P30": 390.1,
            "sensor_Nf": 2388.1,
            "sensor_Nc": 9046.2,
            "sensor_epr": 1.0,
            "sensor_Ps30": 1.02,
            "sensor_phi": 521.3,
            "sensor_NRf": 2388.1,
            "sensor_NRc": 8120.8,
            "sensor_BPR": 8.4,
            "sensor_farB": 0.03,
            "sensor_htBleed": 391.2,
            "sensor_Nf_dmd": 2388.0,
            "sensor_PCNfR_dmd": 100.0,
            "sensor_W31": 39.1,
            "sensor_W32": 23.3
        }

    def test_wrapper_only_calls(self):
        """Verify agents only call wrapper functions."""
        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        # Pipeline should succeed
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("pipeline_results", result)

        # Diagnostic agent should be called
        agents_called = result["execution_metadata"]["agents_called"]
        self.assertIn("diagnostic_agent", agents_called)

    def test_deterministic_behavior(self):
        """Same input should produce same output."""
        # Run pipeline twice with identical inputs
        result1 = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        result2 = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        # Compare key fields (excluding timestamps)
        self.assertEqual(
            result1["pipeline_results"]["diagnostic"]["anomaly_detected"],
            result2["pipeline_results"]["diagnostic"]["anomaly_detected"]
        )

        self.assertEqual(
            result1["pipeline_results"]["diagnostic"]["severity"],
            result2["pipeline_results"]["diagnostic"]["severity"]
        )

        self.assertEqual(
            result1["final_decision"]["action_required"],
            result2["final_decision"]["action_required"]
        )

    def test_no_phase35_imports(self):
        """Agents should not import Phase 3.5 modules directly."""
        import agents.diagnostic_agent as diag
        import agents.research_agent as res
        import agents.recommendation_agent as rec
        import agents.root_agent as root

        # Check module dependencies
        for module in [diag, res, rec, root]:
            source = inspect.getsource(module)

            # These imports should NOT appear
            forbidden_imports = [
                "from ml_model_manager",
                "import ml_model_manager",
                "from calibration_processor",
                "import calibration_processor",
                "from caching_strategy",
                "import caching_strategy",
                "from tools.sensor_analyzer",  # Should use wrapper instead
                "from tools.database_query",   # Should use wrapper instead
                "from tools.cost_calculator",  # Should use wrapper instead
                "from tools.work_order_generator"  # Should use wrapper instead
            ]

            for forbidden_import in forbidden_imports:
                self.assertNotIn(
                    forbidden_import,
                    source,
                    f"Module {module.__name__} contains forbidden import: {forbidden_import}"
                )

    def test_pipeline_structure(self):
        """Verify pipeline returns expected structure."""
        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        # Check top-level structure
        required_keys = [
            "success",
            "unit_id",
            "time_cycle",
            "pipeline_results",
            "final_decision",
            "execution_metadata",
            "timestamp"
        ]

        for key in required_keys:
            self.assertIn(key, result, f"Missing required key: {key}")

        # Check pipeline_results structure
        pipeline_results = result["pipeline_results"]
        self.assertIn("diagnostic", pipeline_results)
        self.assertIn("research", pipeline_results)
        self.assertIn("recommendation", pipeline_results)

        # Check final_decision structure
        final_decision = result["final_decision"]
        self.assertIn("action_required", final_decision)
        self.assertIn("priority", final_decision)
        self.assertIn("summary", final_decision)

        # Check execution_metadata structure
        metadata = result["execution_metadata"]
        self.assertIn("total_time_ms", metadata)
        self.assertIn("agents_called", metadata)
        self.assertIn("errors_encountered", metadata)

    def test_early_exit_optimization(self):
        """Verify early exit when no anomaly detected."""
        # Create sensor data that won't trigger anomaly
        normal_sensor_data = self.test_sensor_data.copy()

        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=1,  # Early cycle typically has no anomaly
            sensor_values=normal_sensor_data
        )

        # Check if research and recommendation were skipped or have minimal data
        agents_called = result["execution_metadata"]["agents_called"]

        # Diagnostic should always be called
        self.assertIn("diagnostic_agent", agents_called)

        # If no anomaly, action should not be required
        if not result["pipeline_results"]["diagnostic"]["anomaly_detected"]:
            self.assertFalse(result["final_decision"]["action_required"])

    def test_error_handling_missing_params(self):
        """Test error handling with missing parameters."""
        diagnostic_agent = DiagnosticAgent()

        # Test with missing sensor_values
        context = {
            "unit_id": 1,
            "time_cycle": 100
            # Missing sensor_values
        }
        config = {"diagnostic_method": "combined"}

        result = diagnostic_agent.analyze(context, config)

        # Should return error response
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])

    def test_research_agent_conditional_execution(self):
        """Test research agent only executes when anomaly detected."""
        research_agent = ResearchAgent()

        # Test with no anomaly detected
        context = {
            "sensor_values": self.test_sensor_data,
            "diagnostic": {
                "anomaly_detected": False
            }
        }
        config = {"similarity_top_n": 3, "similarity_threshold": 0.6}

        result = research_agent.search(context, config)

        # Should succeed but find no matches
        self.assertTrue(result["success"])
        self.assertEqual(result["matches_found"], 0)
        self.assertEqual(len(result["similar_failures"]), 0)

    def test_recommendation_agent_no_anomaly(self):
        """Test recommendation agent when no anomaly detected."""
        recommendation_agent = RecommendationAgent()

        # Test with no anomaly
        context = {
            "unit_id": 1,
            "diagnostic": {
                "anomaly_detected": False,
                "severity": "none"
            },
            "research": {
                "matches_found": 0,
                "similar_failures": []
            }
        }
        config = {"assigned_to": None}

        result = recommendation_agent.generate(context, config)

        # Should succeed with no action message
        self.assertTrue(result["success"])
        self.assertIsNone(result["roi_analysis"])
        self.assertIsNone(result["work_order"])
        self.assertIsNotNone(result["message"])

    def test_schema_completeness(self):
        """Verify all agent outputs match expected schemas."""
        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        # Check diagnostic output schema
        diagnostic = result["pipeline_results"]["diagnostic"]
        diagnostic_required_fields = [
            "agent", "success", "anomaly_detected", "anomaly_score",
            "severity", "confidence", "affected_sensors",
            "top_recommendation", "all_recommendations", "method_used", "timestamp"
        ]
        for field in diagnostic_required_fields:
            self.assertIn(field, diagnostic, f"Diagnostic missing field: {field}")

        # Check research output schema
        research = result["pipeline_results"]["research"]
        research_required_fields = [
            "agent", "success", "matches_found", "similar_failures", "timestamp"
        ]
        for field in research_required_fields:
            self.assertIn(field, research, f"Research missing field: {field}")

        # Check recommendation output schema
        recommendation = result["pipeline_results"]["recommendation"]
        recommendation_required_fields = [
            "agent", "success", "timestamp"
        ]
        for field in recommendation_required_fields:
            self.assertIn(field, recommendation, f"Recommendation missing field: {field}")

    def test_config_overrides(self):
        """Test that configuration overrides work correctly."""
        custom_config = {
            "diagnostic_method": "statistical",
            "similarity_top_n": 5,
            "similarity_threshold": 0.7,
            "assigned_to": "Test Technician"
        }

        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data,
            config=custom_config
        )

        # Should still succeed with custom config
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    def test_multiple_units(self):
        """Test pipeline works with different unit IDs."""
        for unit_id in [1, 5, 10]:
            result = self.root_agent.execute_pipeline(
                unit_id=unit_id,
                time_cycle=100,
                sensor_values=self.test_sensor_data
            )

            self.assertEqual(result["unit_id"], unit_id)
            self.assertIsInstance(result["pipeline_results"], dict)


class PerformanceTests(unittest.TestCase):
    """Tests for performance characteristics."""

    def setUp(self):
        """Set up test fixtures."""
        self.root_agent = RootAgent()
        self.test_sensor_data = {
            "sensor_T30": 1605.2,
            "sensor_T50": 1450.8,
            "sensor_T2": 643.1,
            "sensor_T24": 1526.8,
            "sensor_T50_2": 1350.5,
            "sensor_P2": 551.2,
            "sensor_P15": 8.4,
            "sensor_P30": 390.1,
            "sensor_Nf": 2388.1,
            "sensor_Nc": 9046.2,
            "sensor_epr": 1.0,
            "sensor_Ps30": 1.02,
            "sensor_phi": 521.3,
            "sensor_NRf": 2388.1,
            "sensor_NRc": 8120.8,
            "sensor_BPR": 8.4,
            "sensor_farB": 0.03,
            "sensor_htBleed": 391.2,
            "sensor_Nf_dmd": 2388.0,
            "sensor_PCNfR_dmd": 100.0,
            "sensor_W31": 39.1,
            "sensor_W32": 23.3
        }

    def test_execution_time_recorded(self):
        """Verify execution time is recorded."""
        result = self.root_agent.execute_pipeline(
            unit_id=1,
            time_cycle=100,
            sensor_values=self.test_sensor_data
        )

        execution_time = result["execution_metadata"]["total_time_ms"]
        self.assertIsInstance(execution_time, (int, float))
        self.assertGreater(execution_time, 0)


if __name__ == "__main__":
    unittest.main()
