"""
Unit tests for cost_calculator.py

Tests all cost calculation functions including:
- Cost data models
- Failure probability estimation
- ROI calculations
- Scenario analysis
"""

import unittest
from tools.cost_calculator import (
    MaintenanceCost,
    ROIAnalysis,
    estimate_failure_probability,
    calculate_maintenance_roi,
    run_scenario_analysis,
    DEFAULT_COSTS
)


class TestMaintenanceCost(unittest.TestCase):
    """Test MaintenanceCost data model."""

    def test_create_maintenance_cost(self):
        """Test creating maintenance cost object."""
        cost = MaintenanceCost(
            labor_cost=1000.0,
            parts_cost=2000.0,
            downtime_cost=5000.0,
            overhead_cost=300.0
        )

        self.assertEqual(cost.labor_cost, 1000.0)
        self.assertEqual(cost.parts_cost, 2000.0)
        self.assertEqual(cost.downtime_cost, 5000.0)
        self.assertEqual(cost.overhead_cost, 300.0)

    def test_total_cost_calculation(self):
        """Test total cost property."""
        cost = MaintenanceCost(
            labor_cost=1000.0,
            parts_cost=2000.0,
            downtime_cost=5000.0,
            overhead_cost=300.0
        )

        self.assertEqual(cost.total_cost, 8300.0)

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        cost = MaintenanceCost(
            labor_cost=1000.0,
            parts_cost=2000.0,
            downtime_cost=5000.0
        )

        cost_dict = cost.to_dict()

        self.assertIsInstance(cost_dict, dict)
        self.assertIn('labor_cost', cost_dict)
        self.assertIn('parts_cost', cost_dict)
        self.assertIn('total_cost', cost_dict)
        self.assertEqual(cost_dict['total_cost'], 8000.0)


class TestROIAnalysis(unittest.TestCase):
    """Test ROIAnalysis data model."""

    def test_create_roi_analysis(self):
        """Test creating ROI analysis object."""
        preventive = MaintenanceCost(1000, 2000, 3000)
        reactive = MaintenanceCost(2000, 5000, 10000)

        roi = ROIAnalysis(
            preventive_cost=preventive,
            reactive_cost=reactive,
            failure_probability=0.7,
            expected_reactive_cost=11900.0,
            savings=5900.0,
            roi_percentage=98.33,
            recommendation='preventive',
            confidence=0.85
        )

        self.assertEqual(roi.failure_probability, 0.7)
        self.assertEqual(roi.savings, 5900.0)
        self.assertEqual(roi.recommendation, 'preventive')

    def test_to_dict_conversion(self):
        """Test ROI analysis to_dict conversion."""
        preventive = MaintenanceCost(1000, 2000, 3000)
        reactive = MaintenanceCost(2000, 5000, 10000)

        roi = ROIAnalysis(
            preventive_cost=preventive,
            reactive_cost=reactive,
            failure_probability=0.7,
            expected_reactive_cost=11900.0,
            savings=5900.0,
            roi_percentage=98.33,
            recommendation='preventive',
            confidence=0.85
        )

        roi_dict = roi.to_dict()

        self.assertIsInstance(roi_dict, dict)
        self.assertIn('preventive_cost', roi_dict)
        self.assertIn('reactive_cost', roi_dict)
        self.assertIn('savings', roi_dict)
        self.assertIn('recommendation', roi_dict)


class TestEstimateFailureProbability(unittest.TestCase):
    """Test failure probability estimation."""

    def test_basic_probability_estimation(self):
        """Test basic probability calculation."""
        prob = estimate_failure_probability(
            anomaly_score=0.75,
            confidence=0.8
        )

        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
        # Should be approximately anomaly_score * confidence
        self.assertAlmostEqual(prob, 0.6, delta=0.05)

    def test_probability_with_low_rul(self):
        """Test probability with low remaining useful life."""
        prob = estimate_failure_probability(
            anomaly_score=0.5,
            rul_estimate=15,  # Very low RUL
            confidence=0.8
        )

        # Should be higher due to low RUL
        self.assertGreaterEqual(prob, 0.4)

    def test_probability_with_high_rul(self):
        """Test probability with high remaining useful life."""
        prob = estimate_failure_probability(
            anomaly_score=0.5,
            rul_estimate=100,  # High RUL
            confidence=0.8
        )

        # Should not be increased by RUL factor
        self.assertLessEqual(prob, 0.5)

    def test_probability_capped_at_95(self):
        """Test probability is capped at 0.95."""
        prob = estimate_failure_probability(
            anomaly_score=1.0,
            rul_estimate=10,  # Very low
            confidence=1.0
        )

        self.assertLessEqual(prob, 0.95)


class TestCalculateMaintenanceROI(unittest.TestCase):
    """Test ROI calculation."""

    def test_roi_with_high_failure_probability(self):
        """Test ROI with high failure probability."""
        roi = calculate_maintenance_roi(
            failure_type='bearing_degradation',
            failure_probability=0.8,
            preventive_parts_cost=3000.0,
            reactive_parts_cost=8000.0
        )

        self.assertIsInstance(roi, ROIAnalysis)
        self.assertEqual(roi.failure_probability, 0.8)
        # High probability should favor preventive
        self.assertGreater(roi.savings, 0)
        self.assertEqual(roi.recommendation, 'preventive')

    def test_roi_with_low_failure_probability(self):
        """Test ROI with low failure probability."""
        roi = calculate_maintenance_roi(
            failure_type='bearing_degradation',
            failure_probability=0.15,
            preventive_parts_cost=3000.0,
            reactive_parts_cost=8000.0
        )

        self.assertIsInstance(roi, ROIAnalysis)
        # Low probability should recommend monitor
        self.assertEqual(roi.recommendation, 'monitor')

    def test_roi_with_custom_costs(self):
        """Test ROI with custom cost parameters."""
        custom_costs = {
            'labor_rate_per_hour': 200.0,
            'downtime_cost_per_hour': 3000.0
        }

        roi = calculate_maintenance_roi(
            failure_type='bearing_degradation',
            failure_probability=0.6,
            preventive_parts_cost=2000.0,
            reactive_parts_cost=6000.0,
            custom_costs=custom_costs
        )

        self.assertIsInstance(roi, ROIAnalysis)
        # Custom costs should affect total cost
        self.assertGreater(roi.preventive_cost.labor_cost, DEFAULT_COSTS['preventive_labor_hours'] * 150)

    def test_roi_percentage_calculation(self):
        """Test ROI percentage calculation."""
        roi = calculate_maintenance_roi(
            failure_type='bearing_degradation',
            failure_probability=0.7,
            preventive_parts_cost=3500.0,
            reactive_parts_cost=8000.0
        )

        if roi.savings > 0:
            # ROI% = (savings / preventive_cost) * 100
            expected_roi = (roi.savings / roi.preventive_cost.total_cost) * 100
            self.assertAlmostEqual(roi.roi_percentage, expected_roi, places=1)

    def test_payback_period_calculation(self):
        """Test payback period calculation."""
        roi = calculate_maintenance_roi(
            failure_type='bearing_degradation',
            failure_probability=0.7,
            preventive_parts_cost=3000.0,
            reactive_parts_cost=8000.0,
            time_window_days=90
        )

        if roi.savings > 0:
            self.assertIsNotNone(roi.payback_period_days)
            self.assertGreater(roi.payback_period_days, 0)
        else:
            self.assertIsNone(roi.payback_period_days)


class TestRunScenarioAnalysis(unittest.TestCase):
    """Test scenario analysis."""

    def test_scenario_analysis_basic(self):
        """Test basic scenario analysis."""
        scenarios = run_scenario_analysis(
            failure_type='bearing_degradation',
            base_failure_probability=0.6,
            probability_range=(0.3, 0.9),
            num_scenarios=5
        )

        self.assertIsInstance(scenarios, dict)
        self.assertIn('base_case', scenarios)
        self.assertIn('scenarios', scenarios)
        self.assertIn('breakeven_probability', scenarios)
        self.assertIn('sensitivity', scenarios)

    def test_scenario_count(self):
        """Test correct number of scenarios generated."""
        scenarios = run_scenario_analysis(
            failure_type='bearing_degradation',
            base_failure_probability=0.5,
            num_scenarios=7
        )

        self.assertEqual(len(scenarios['scenarios']), 7)

    def test_scenario_probability_range(self):
        """Test scenarios cover probability range."""
        scenarios = run_scenario_analysis(
            failure_type='bearing_degradation',
            base_failure_probability=0.5,
            probability_range=(0.2, 0.8),
            num_scenarios=5
        )

        probabilities = [s['failure_probability'] for s in scenarios['scenarios']]

        self.assertAlmostEqual(min(probabilities), 0.2, places=2)
        self.assertAlmostEqual(max(probabilities), 0.8, places=2)

    def test_sensitivity_analysis(self):
        """Test sensitivity data."""
        scenarios = run_scenario_analysis(
            failure_type='bearing_degradation',
            base_failure_probability=0.6,
            num_scenarios=5
        )

        sensitivity = scenarios['sensitivity']

        self.assertIn('high_risk', sensitivity)
        self.assertIn('medium_risk', sensitivity)
        self.assertIn('low_risk', sensitivity)

        # High risk should have higher probability
        self.assertGreater(
            sensitivity['high_risk']['failure_probability'],
            sensitivity['low_risk']['failure_probability']
        )

    def test_breakeven_probability(self):
        """Test breakeven probability calculation."""
        scenarios = run_scenario_analysis(
            failure_type='bearing_degradation',
            base_failure_probability=0.5,
            probability_range=(0.1, 0.9),
            num_scenarios=10
        )

        breakeven = scenarios['breakeven_probability']

        # Breakeven may or may not exist depending on costs
        if breakeven is not None:
            self.assertGreaterEqual(breakeven, 0.0)
            self.assertLessEqual(breakeven, 1.0)


if __name__ == '__main__':
    unittest.main()
