"""
Async Wrappers for Tool APIs
=============================

Provides async versions of all tools for:
- Concurrent request handling
- Non-blocking I/O
- Better scalability
"""

import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from tools.api_wrappers import (
    analyze_sensors as _analyze_sensors_sync,
    search_similar_failures_simple as _search_similar_failures_sync,
    calculate_roi_simple as _calculate_roi_sync,
    generate_work_order_simple as _generate_work_order_sync
)

# Thread pool for running sync functions
executor = ThreadPoolExecutor(max_workers=10)


async def analyze_sensors_async(
    unit_id: int,
    time_cycle: int,
    sensor_values: Dict[str, float],
    method: str = "combined"
) -> Dict[str, Any]:
    """
    Async version of analyze_sensors.

    Parameters:
    -----------
    unit_id : int
        Equipment unit identifier
    time_cycle : int
        Operational cycle number
    sensor_values : Dict[str, float]
        Sensor readings
    method : str
        Detection method

    Returns:
    --------
    Dict[str, Any]
        Analysis results
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        _analyze_sensors_sync,
        unit_id,
        time_cycle,
        sensor_values,
        method
    )
    return result


async def search_similar_failures_async(
    sensor_values: Dict[str, float],
    top_n: int = 3,
    similarity_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Async version of similarity search.

    Parameters:
    -----------
    sensor_values : Dict[str, float]
        Current sensor readings
    top_n : int
        Number of similar cases to return
    similarity_threshold : float
        Minimum similarity score

    Returns:
    --------
    Dict[str, Any]
        Similar failures
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        _search_similar_failures_sync,
        sensor_values,
        top_n,
        similarity_threshold
    )
    return result


async def calculate_roi_async(
    failure_type: str,
    failure_probability: float,
    preventive_labor_hours: float = 4.0,
    custom_costs: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Async version of ROI calculation.

    Parameters:
    -----------
    failure_type : str
        Type of failure
    failure_probability : float
        Probability of failure (0-1)
    preventive_labor_hours : float
        Expected labor hours
    custom_costs : Dict[str, float], optional
        Custom cost overrides

    Returns:
    --------
    Dict[str, Any]
        ROI analysis
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        _calculate_roi_sync,
        failure_type,
        failure_probability,
        preventive_labor_hours,
        custom_costs
    )
    return result


async def generate_work_order_async(
    equipment_id: int,
    anomaly_data: Dict[str, Any],
    roi_data: Optional[Dict[str, Any]] = None,
    assigned_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async version of work order generation.

    Parameters:
    -----------
    equipment_id : int
        Equipment unit ID
    anomaly_data : Dict[str, Any]
        Anomaly detection results
    roi_data : Dict[str, Any], optional
        ROI calculation results
    assigned_to : str, optional
        Technician name

    Returns:
    --------
    Dict[str, Any]
        Work order
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        _generate_work_order_sync,
        equipment_id,
        anomaly_data,
        roi_data,
        assigned_to
    )
    return result


# ============================================================================
# Concurrent Processing Utilities
# ============================================================================

async def process_multiple_units_concurrent(unit_configs):
    """
    Process multiple units in parallel.

    Parameters:
    -----------
    unit_configs : List[Dict]
        List of configuration dicts for each unit

    Returns:
    --------
    List[Dict]
        Results for each unit
    """
    tasks = [
        analyze_sensors_async(**config)
        for config in unit_configs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


async def complete_workflow_async(
    unit_id: int,
    time_cycle: int,
    sensor_values: Dict[str, float]
) -> Dict[str, Any]:
    """
    Run complete diagnostic workflow asynchronously.

    Parameters:
    -----------
    unit_id : int
        Equipment unit ID
    time_cycle : int
        Operational cycle
    sensor_values : Dict[str, float]
        Sensor readings

    Returns:
    --------
    Dict[str, Any]
        Complete workflow results
    """
    # Step 1: Analyze sensors
    sensor_result = await analyze_sensors_async(
        unit_id=unit_id,
        time_cycle=time_cycle,
        sensor_values=sensor_values
    )

    if not sensor_result["success"] or not sensor_result.get("anomaly_detected"):
        return {
            "success": True,
            "anomaly_detected": False,
            "sensor_analysis": sensor_result
        }

    # Step 2 & 3: Run similarity search and ROI calculation in parallel
    similarity_task = search_similar_failures_async(
        sensor_values=sensor_values,
        top_n=3
    )

    # Get failure type for ROI calculation
    # For now, use a default or wait for similarity results
    similarity_result, = await asyncio.gather(similarity_task)

    if not similarity_result["success"] or similarity_result["matches_found"] == 0:
        # No similar failures, but can still generate work order
        work_order = await generate_work_order_async(
            equipment_id=unit_id,
            anomaly_data=sensor_result
        )

        return {
            "success": True,
            "anomaly_detected": True,
            "sensor_analysis": sensor_result,
            "similar_failures": similarity_result,
            "work_order": work_order
        }

    # Step 3: Calculate ROI
    failure_type = similarity_result["similar_failures"][0]["failure_type"]
    roi_result = await calculate_roi_async(
        failure_type=failure_type,
        failure_probability=sensor_result["anomaly_score"]
    )

    # Step 4: Generate work order
    work_order = await generate_work_order_async(
        equipment_id=unit_id,
        anomaly_data=sensor_result,
        roi_data=roi_result
    )

    return {
        "success": True,
        "anomaly_detected": True,
        "sensor_analysis": sensor_result,
        "similar_failures": similarity_result,
        "roi_analysis": roi_result,
        "work_order": work_order
    }
