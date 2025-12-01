"""
Cost-Benefit Calculator Tool
=============================

Calculate ROI for preventive vs. reactive maintenance decisions.

USAGE FOR PHASE 4 AGENTS:
-------------------------

Basic usage (calculate ROI):
>>> from tools.cost_calculator import calculate_maintenance_roi
>>>
>>> roi = calculate_maintenance_roi(
>>>     failure_type='bearing_degradation',
>>>     failure_probability=0.7,
>>>     preventive_parts_cost=3500.0,
>>>     reactive_parts_cost=8000.0
>>> )
>>> print(f"Savings: ${roi.savings:.2f}")
>>> print(f"ROI: {roi.roi_percentage:.1f}%")
>>> print(f"Recommendation: {roi.recommendation}")

Estimate failure probability:
>>> from tools.cost_calculator import estimate_failure_probability
>>>
>>> prob = estimate_failure_probability(
>>>     anomaly_score=0.75,
>>>     rul_estimate=25,
>>>     confidence=0.85
>>> )
>>> print(f"Failure probability: {prob:.2%}")

Run scenario analysis:
>>> from tools.cost_calculator import run_scenario_analysis
>>>
>>> scenarios = run_scenario_analysis(
>>>     failure_type='bearing_degradation',
>>>     base_failure_probability=0.6,
>>>     probability_range=(0.3, 0.9)
>>> )
>>> print(f"Breakeven probability: {scenarios['breakeven_probability']}")

INTEGRATION WITH GOOGLE ADK:
-----------------------------
To use as an ADK tool in Phase 4:

from google.adk import Tool
from tools.cost_calculator import calculate_maintenance_roi

cost_tool = Tool(
    name="calculate_roi",
    description="Calculates ROI for preventive vs reactive maintenance",
    func=calculate_maintenance_roi
)
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np


@dataclass
class MaintenanceCost:
    """
    Represents costs for a maintenance action.

    Attributes:
    -----------
    labor_cost : float
        Cost of labor (USD)
    parts_cost : float
        Cost of replacement parts (USD)
    downtime_cost : float
        Cost of production downtime (USD)
    overhead_cost : float
        Overhead and administrative costs (USD)
    total_cost : float
        Total cost (computed)
    """
    labor_cost: float
    parts_cost: float
    downtime_cost: float
    overhead_cost: float = 0.0

    @property
    def total_cost(self) -> float:
        """Calculate total cost."""
        return (self.labor_cost + self.parts_cost +
                self.downtime_cost + self.overhead_cost)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'labor_cost': round(self.labor_cost, 2),
            'parts_cost': round(self.parts_cost, 2),
            'downtime_cost': round(self.downtime_cost, 2),
            'overhead_cost': round(self.overhead_cost, 2),
            'total_cost': round(self.total_cost, 2)
        }


@dataclass
class ROIAnalysis:
    """
    Results of ROI analysis comparing preventive vs. reactive maintenance.

    Attributes:
    -----------
    preventive_cost : MaintenanceCost
        Cost of preventive maintenance
    reactive_cost : MaintenanceCost
        Cost if failure occurs (reactive)
    failure_probability : float
        Probability of failure (0-1)
    expected_reactive_cost : float
        Expected cost of reactive approach (probability-weighted)
    savings : float
        Expected savings from preventive maintenance
    roi_percentage : float
        Return on investment percentage
    recommendation : str
        'preventive', 'reactive', or 'monitor'
    confidence : float
        Confidence in recommendation (0-1)
    payback_period_days : Optional[int]
        Days to recover preventive maintenance cost
    """
    preventive_cost: MaintenanceCost
    reactive_cost: MaintenanceCost
    failure_probability: float
    expected_reactive_cost: float
    savings: float
    roi_percentage: float
    recommendation: str
    confidence: float
    payback_period_days: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'preventive_cost': self.preventive_cost.to_dict(),
            'reactive_cost': self.reactive_cost.to_dict(),
            'failure_probability': round(self.failure_probability, 3),
            'expected_reactive_cost': round(self.expected_reactive_cost, 2),
            'savings': round(self.savings, 2),
            'roi_percentage': round(self.roi_percentage, 2),
            'recommendation': self.recommendation,
            'confidence': round(self.confidence, 3),
            'payback_period_days': self.payback_period_days
        }


# Default cost parameters (can be overridden)
DEFAULT_COSTS = {
    'labor_rate_per_hour': 150.0,  # USD per hour
    'downtime_cost_per_hour': 2000.0,  # Production loss
    'overhead_rate': 0.15,  # 15% overhead on labor+parts
    'preventive_labor_hours': 6.0,
    'reactive_labor_hours': 12.0,
    'preventive_downtime_hours': 4.0,
    'reactive_downtime_hours': 24.0
}


def estimate_failure_probability(
    anomaly_score: float,
    rul_estimate: Optional[int] = None,
    confidence: float = 0.7
) -> float:
    """
    Estimate probability of failure based on anomaly data.

    Parameters:
    -----------
    anomaly_score : float
        Anomaly score from sensor_analyzer (0-1)
    rul_estimate : int, optional
        Estimated remaining useful life (cycles)
    confidence : float
        Confidence in anomaly detection

    Returns:
    --------
    float
        Failure probability (0-1)
    """
    # Base probability from anomaly score
    base_prob = anomaly_score * confidence

    # Adjust based on RUL if available
    if rul_estimate is not None:
        if rul_estimate <= 20:
            rul_factor = 1.5  # High risk
        elif rul_estimate <= 50:
            rul_factor = 1.2  # Medium risk
        else:
            rul_factor = 1.0  # Lower risk

        base_prob = min(base_prob * rul_factor, 0.95)

    return base_prob


def calculate_maintenance_roi(
    failure_type: str,
    failure_probability: float,
    preventive_parts_cost: Optional[float] = None,
    reactive_parts_cost: Optional[float] = None,
    time_window_days: int = 90,
    custom_costs: Optional[Dict] = None
) -> ROIAnalysis:
    """
    Calculate ROI for preventive maintenance vs. reactive maintenance.

    Parameters:
    -----------
    failure_type : str
        Type of failure (e.g., 'bearing_degradation')
    failure_probability : float
        Probability of failure occurring (0-1)
    preventive_parts_cost : float, optional
        Cost of parts for preventive maintenance
        If None, uses database lookup
    reactive_parts_cost : float, optional
        Cost of parts if failure occurs
        If None, uses database lookup
    time_window_days : int
        Time window for analysis (default: 90 days)
    custom_costs : Dict, optional
        Override default cost parameters

    Returns:
    --------
    ROIAnalysis
        Comprehensive ROI analysis
    """
    # Merge custom costs with defaults
    costs = DEFAULT_COSTS.copy()
    if custom_costs:
        costs.update(custom_costs)

    # Look up parts costs from database if not provided
    if preventive_parts_cost is None or reactive_parts_cost is None:
        try:
            from tools.database_query import find_parts_replaced
            parts_info = find_parts_replaced(failure_type)

            if 'error' not in parts_info:
                if preventive_parts_cost is None:
                    preventive_parts_cost = parts_info.get('preventive_cost', 3000.0)
                if reactive_parts_cost is None:
                    reactive_parts_cost = parts_info.get('average_cost', 5000.0)
            else:
                # Fallback defaults
                preventive_parts_cost = preventive_parts_cost or 3000.0
                reactive_parts_cost = reactive_parts_cost or 8000.0
        except:
            # Fallback if database not available
            preventive_parts_cost = preventive_parts_cost or 3000.0
            reactive_parts_cost = reactive_parts_cost or 8000.0

    # Calculate preventive maintenance cost
    preventive_labor = costs['preventive_labor_hours'] * costs['labor_rate_per_hour']
    preventive_downtime = costs['preventive_downtime_hours'] * costs['downtime_cost_per_hour']
    preventive_overhead = (preventive_labor + preventive_parts_cost) * costs['overhead_rate']

    preventive_cost_obj = MaintenanceCost(
        labor_cost=preventive_labor,
        parts_cost=preventive_parts_cost,
        downtime_cost=preventive_downtime,
        overhead_cost=preventive_overhead
    )

    # Calculate reactive maintenance cost (if failure occurs)
    reactive_labor = costs['reactive_labor_hours'] * costs['labor_rate_per_hour']
    reactive_downtime = costs['reactive_downtime_hours'] * costs['downtime_cost_per_hour']
    reactive_overhead = (reactive_labor + reactive_parts_cost) * costs['overhead_rate']

    reactive_cost_obj = MaintenanceCost(
        labor_cost=reactive_labor,
        parts_cost=reactive_parts_cost,
        downtime_cost=reactive_downtime,
        overhead_cost=reactive_overhead
    )

    # Calculate expected reactive cost (probability-weighted)
    expected_reactive = reactive_cost_obj.total_cost * failure_probability

    # Calculate savings
    savings = expected_reactive - preventive_cost_obj.total_cost

    # Calculate ROI percentage
    if preventive_cost_obj.total_cost > 0:
        roi_percentage = (savings / preventive_cost_obj.total_cost) * 100
    else:
        roi_percentage = 0.0

    # Determine recommendation
    if savings > 0 and failure_probability > 0.3:
        recommendation = 'preventive'
        confidence = min(0.6 + (failure_probability * 0.4), 0.95)
    elif failure_probability < 0.2:
        recommendation = 'monitor'
        confidence = 0.7
    else:
        recommendation = 'reactive'
        confidence = 0.6

    # Calculate payback period (days to recover investment)
    if savings > 0:
        # Assume savings accrue over time window
        daily_savings = savings / time_window_days
        payback_period = int(preventive_cost_obj.total_cost / daily_savings) if daily_savings > 0 else None
    else:
        payback_period = None

    return ROIAnalysis(
        preventive_cost=preventive_cost_obj,
        reactive_cost=reactive_cost_obj,
        failure_probability=failure_probability,
        expected_reactive_cost=expected_reactive,
        savings=savings,
        roi_percentage=roi_percentage,
        recommendation=recommendation,
        confidence=confidence,
        payback_period_days=payback_period
    )


def run_scenario_analysis(
    failure_type: str,
    base_failure_probability: float,
    probability_range: Tuple[float, float] = (0.3, 0.9),
    num_scenarios: int = 5
) -> Dict:
    """
    Run multiple scenarios with varying failure probabilities.

    Parameters:
    -----------
    failure_type : str
        Failure type to analyze
    base_failure_probability : float
        Base case failure probability
    probability_range : Tuple[float, float]
        (min, max) probabilities to test
    num_scenarios : int
        Number of scenarios to generate

    Returns:
    --------
    Dict
        Scenario analysis results with breakeven point
    """
    scenarios = []

    # Generate probability values
    probabilities = np.linspace(probability_range[0], probability_range[1], num_scenarios)

    for prob in probabilities:
        roi = calculate_maintenance_roi(failure_type, prob)
        scenarios.append({
            'failure_probability': round(prob, 3),
            'preventive_cost': roi.preventive_cost.total_cost,
            'expected_reactive_cost': roi.expected_reactive_cost,
            'savings': roi.savings,
            'roi_percentage': roi.roi_percentage,
            'recommendation': roi.recommendation
        })

    # Find breakeven probability (where savings = 0)
    breakeven = None
    for i in range(len(scenarios) - 1):
        if scenarios[i]['savings'] <= 0 < scenarios[i + 1]['savings']:
            # Linear interpolation
            p1, s1 = scenarios[i]['failure_probability'], scenarios[i]['savings']
            p2, s2 = scenarios[i + 1]['failure_probability'], scenarios[i + 1]['savings']
            breakeven = p1 + (0 - s1) * (p2 - p1) / (s2 - s1)
            break

    # Calculate base case
    base_roi = calculate_maintenance_roi(failure_type, base_failure_probability)

    return {
        'base_case': {
            'failure_probability': base_failure_probability,
            'savings': base_roi.savings,
            'roi_percentage': base_roi.roi_percentage,
            'recommendation': base_roi.recommendation
        },
        'scenarios': scenarios,
        'breakeven_probability': round(breakeven, 3) if breakeven else None,
        'sensitivity': {
            'high_risk': scenarios[-1],
            'medium_risk': scenarios[len(scenarios) // 2],
            'low_risk': scenarios[0]
        }
    }
