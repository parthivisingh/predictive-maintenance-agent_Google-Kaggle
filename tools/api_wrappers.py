"""
Lightweight API Wrappers for ADK Agent Integration
===================================================

This module provides minimal, well-typed wrapper functions that simplify
the interface to all Phase 3 tools. Each wrapper:

1. Accepts simple, JSON-serializable inputs
2. Returns flattened, typed dictionaries
3. Handles errors with standard error schemas
4. Validates inputs using Pydantic
5. Logs all invocations for observability

DESIGN PRINCIPLES:
- Functions under 50 lines
- Single responsibility
- Type hints on all parameters and returns
- No complex objects in return values
- Errors return structured dicts (never raise)
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import logging

# Configure structured logging
logger = logging.getLogger(__name__)


# ============================================================================
# Standard Response Schemas
# ============================================================================

class APIError(BaseModel):
    """Standard error response schema."""
    success: bool = False
    error_type: str
    error_message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class APIResponse(BaseModel):
    """Standard success response schema."""
    success: bool = True
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Input Validation Schemas
# ============================================================================

class SensorAnalysisRequest(BaseModel):
    """Request schema for sensor analysis."""
    unit_id: int = Field(..., ge=1, description="Equipment unit ID")
    time_cycle: int = Field(..., ge=1, description="Operational cycle number")
    sensor_values: Dict[str, float] = Field(..., min_length=1)
    method: str = Field(default="combined", pattern="^(statistical|ml|combined)$")

    @field_validator('sensor_values')
    @classmethod
    def validate_sensors(cls, v):
        """Validate sensor values are numeric and not NaN."""
        for sensor, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Sensor {sensor} value must be numeric")
            if not (-1e10 < value < 1e10):  # Sanity check
                raise ValueError(f"Sensor {sensor} value {value} out of reasonable range")
        return v


class SimilaritySearchRequest(BaseModel):
    """Request schema for similarity search."""
    sensor_values: Dict[str, float] = Field(..., min_length=1)
    top_n: int = Field(default=3, ge=1, le=10)
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0)

    @field_validator('sensor_values')
    @classmethod
    def validate_sensors(cls, v):
        """Validate sensor values are numeric and not NaN."""
        for sensor, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Sensor {sensor} value must be numeric")
        return v


class ROICalculationRequest(BaseModel):
    """Request schema for ROI calculation."""
    failure_type: str
    failure_probability: float = Field(..., ge=0.0, le=1.0)
    preventive_labor_hours: float = Field(default=4.0, ge=0.1, le=100.0)
    custom_costs: Optional[Dict[str, float]] = None

    @field_validator('custom_costs')
    @classmethod
    def validate_custom_costs(cls, v):
        """Validate custom costs if provided."""
        if v is not None:
            for key, value in v.items():
                if not isinstance(value, (int, float)) or value < 0:
                    raise ValueError(f"Custom cost {key} must be a non-negative number")
        return v


class WorkOrderRequest(BaseModel):
    """Request schema for work order generation."""
    equipment_id: int = Field(..., ge=1)
    anomaly_data: Dict[str, Any]
    roi_data: Optional[Dict[str, Any]] = None
    assigned_to: Optional[str] = None

    @field_validator('anomaly_data')
    @classmethod
    def validate_anomaly_data(cls, v):
        """Validate anomaly data structure."""
        required_fields = {'anomaly_detected', 'severity'}
        if not required_fields.issubset(set(v.keys())):
            raise ValueError(f"Anomaly data must contain: {required_fields}")
        return v


# ============================================================================
# API Wrapper Functions
# ============================================================================

def analyze_sensors(
    unit_id: int,
    time_cycle: int,
    sensor_values: Dict[str, float],
    method: str = "combined"
) -> Dict[str, Any]:
    """
    Lightweight wrapper for sensor anomaly analysis.

    Parameters:
    -----------
    unit_id : int
        Equipment unit identifier (>= 1)
    time_cycle : int
        Operational cycle number (>= 1)
    sensor_values : Dict[str, float]
        Sensor readings (e.g., {"sensor_T30": 1605.2})
    method : str
        Detection method: "statistical", "ml", or "combined"

    Returns:
    --------
    Dict[str, Any]
        Flattened response:
        {
            "success": true,
            "anomaly_detected": bool,
            "anomaly_score": float (0-1),
            "severity": str (none|low|medium|high|critical),
            "confidence": float (0-1),
            "affected_sensors": List[str],
            "top_recommendation": str,
            "all_recommendations": List[str],
            "method_used": str
        }

        OR on error:
        {
            "success": false,
            "error_type": str,
            "error_message": str
        }
    """
    try:
        # Validate input
        request = SensorAnalysisRequest(
            unit_id=unit_id,
            time_cycle=time_cycle,
            sensor_values=sensor_values,
            method=method
        )

        logger.info(f"Analyzing sensors for unit {unit_id}, cycle {time_cycle}")

        # Call underlying tool
        from tools.sensor_analyzer import analyze_sensor_data

        result = analyze_sensor_data(
            sensor_readings={
                'unit_id': request.unit_id,
                'time_cycle': request.time_cycle,
                'sensor_values': request.sensor_values
            },
            method=request.method
        )

        # Flatten response
        return {
            "success": True,
            "anomaly_detected": result.anomaly_detected,
            "anomaly_score": round(result.anomaly_score, 4),
            "severity": result.severity,
            "confidence": round(result.confidence, 4),
            "affected_sensors": result.affected_sensors,
            "top_recommendation": result.recommendations[0] if result.recommendations else "No action required",
            "all_recommendations": result.recommendations,
            "method_used": result.method_used,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Sensor analysis failed: {e}", exc_info=True)
        return {
            "success": False,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }


def search_similar_failures_simple(
    sensor_values: Dict[str, float],
    top_n: int = 3,
    similarity_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Find similar historical failures.

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Current sensor readings
    top_n : int
        Number of similar failures to return (1-10)
    similarity_threshold : float
        Minimum similarity score (0.0-1.0)

    Returns:
    --------
    Dict[str, Any]
        {
            "success": true,
            "matches_found": int,
            "similar_failures": [
                {
                    "similarity_score": float,
                    "failure_type": str,
                    "root_cause": str,
                    "action_taken": str,
                    "parts_replaced": List[str],
                    "avg_cost": float,
                    "avg_downtime": float
                },
                ...
            ]
        }
    """
    try:
        request = SimilaritySearchRequest(
            sensor_values=sensor_values,
            top_n=top_n,
            similarity_threshold=similarity_threshold
        )

        from tools.database_query import search_similar_failures

        results = search_similar_failures(
            request.sensor_values,
            request.top_n,
            request.similarity_threshold
        )

        # Flatten and simplify
        simplified = []
        for r in results:
            simplified.append({
                "similarity_score": round(r["similarity_score"], 4),
                "failure_type": r["failure_type"],
                "root_cause": r["root_cause"],
                "action_taken": r["action_taken"],
                "parts_replaced": r.get("parts_replaced", "").split(",") if r.get("parts_replaced") else [],
                "avg_cost": r["total_cost"],
                "avg_downtime": r["downtime_hours"]
            })

        return {
            "success": True,
            "matches_found": len(simplified),
            "similar_failures": simplified,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Similarity search failed: {e}", exc_info=True)
        return {
            "success": False,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }


def calculate_roi_simple(
    failure_type: str,
    failure_probability: float,
    preventive_labor_hours: float = 4.0,
    custom_costs: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate ROI for preventive maintenance.

    Parameters:
    -----------
    failure_type : str
        Type of failure (e.g., "HPC_degradation")
    failure_probability : float
        Probability of failure (0.0-1.0)
    preventive_labor_hours : float
        Hours required for preventive maintenance
    custom_costs : Dict[str, float], optional
        Custom cost overrides

    Returns:
    --------
    Dict[str, Any]
        {
            "success": true,
            "estimated_preventive_cost": float,
            "estimated_reactive_cost": float,
            "expected_savings": float,
            "roi_percentage": float,
            "recommendation": str
        }
    """
    try:
        request = ROICalculationRequest(
            failure_type=failure_type,
            failure_probability=failure_probability,
            preventive_labor_hours=preventive_labor_hours,
            custom_costs=custom_costs
        )

        from tools.cost_calculator import calculate_maintenance_roi

        # Adapt parameters to actual function signature
        cost_overrides = request.custom_costs or {}
        # Add labor hours to custom costs if not already specified
        if 'labor_hours_preventive' not in cost_overrides:
            cost_overrides['labor_hours_preventive'] = request.preventive_labor_hours

        result = calculate_maintenance_roi(
            failure_type=request.failure_type,
            failure_probability=request.failure_probability,
            custom_costs=cost_overrides
        )

        return {
            "success": True,
            "estimated_preventive_cost": round(result.preventive_cost, 2),
            "estimated_reactive_cost": round(result.expected_reactive_cost, 2),
            "expected_savings": round(result.savings, 2),
            "roi_percentage": round(result.roi_percentage, 2),
            "recommendation": result.recommendation,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"ROI calculation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }


def generate_work_order_simple(
    equipment_id: int,
    anomaly_data: Dict[str, Any],
    roi_data: Optional[Dict[str, Any]] = None,
    assigned_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate work order for maintenance.

    Parameters:
    -----------
    equipment_id : int
        Equipment unit ID
    anomaly_data : Dict[str, Any]
        Anomaly detection results
    roi_data : Dict[str, Any], optional
        ROI calculation results
    assigned_to : str, optional
        Technician to assign work order to

    Returns:
    --------
    Dict[str, Any]
        {
            "success": true,
            "work_order_id": str,
            "priority": str,
            "issue_summary": str,
            "recommended_actions": List[str],
            "estimated_cost": float,
            "estimated_duration": float
        }
    """
    try:
        request = WorkOrderRequest(
            equipment_id=equipment_id,
            anomaly_data=anomaly_data,
            roi_data=roi_data,
            assigned_to=assigned_to
        )

        from tools.work_order_generator import generate_work_order

        # Adapt parameters to actual function signature
        # The function expects anomaly_result, roi_analysis, similar_failures
        result = generate_work_order(
            equipment_id=request.equipment_id,
            anomaly_result=request.anomaly_data,
            roi_analysis=request.roi_data or {},
            similar_failures=[],  # Empty list if not provided
            assigned_to=request.assigned_to
        )

        return {
            "success": True,
            "work_order_id": result.work_order_id,
            "priority": str(result.priority),  # Convert enum to string for JSON
            "issue_summary": result.issue_detected,
            "recommended_actions": result.recommended_actions,
            "estimated_cost": round(result.estimated_cost, 2),
            "estimated_duration": round(result.estimated_duration_hours, 2),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Work order generation failed: {e}", exc_info=True)
        return {
            "success": False,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }
