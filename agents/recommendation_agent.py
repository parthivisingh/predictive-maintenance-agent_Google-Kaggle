"""
Recommendation Agent - ROI Analysis & Work Order Generation

Chains calculate_roi_simple() and generate_work_order_simple() from tools.api_wrappers.
No direct imports from Phase 3.5 modules.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from tools.api_wrappers import calculate_roi_simple, generate_work_order_simple
from agents.schemas import RecommendationOutput, ROIAnalysis, WorkOrder


class RecommendationAgent:
    """
    Recommendation agent for generating maintenance recommendations and work orders.

    This agent chains two operations:
    1. Calculate ROI for preventive maintenance
    2. Generate a work order with recommended actions

    It only executes if an anomaly has been detected.
    """

    def __init__(self):
        """Initialize the recommendation agent."""
        self.agent_name = "recommendation_agent"

    def generate(self, context: Dict[str, Any], config: Dict[str, Any]) -> RecommendationOutput:
        """
        Generate maintenance recommendations and work orders.

        Args:
            context: Dictionary containing:
                - unit_id: int - Equipment identifier
                - diagnostic: Dict - Results from diagnostic_agent
                - research: Dict - Results from research_agent
            config: Dictionary containing:
                - assigned_to: Optional[str] - Technician to assign work order to

        Returns:
            RecommendationOutput dictionary with ROI analysis and work order
        """
        try:
            # Extract diagnostic and research results
            diagnostic = context.get("diagnostic", {})
            research = context.get("research", {})

            # Early exit if no anomaly detected
            if not diagnostic.get("anomaly_detected", False):
                return self._no_action_response()

            # Get equipment ID
            equipment_id = context.get("unit_id")
            if equipment_id is None:
                return self._error_response("Missing unit_id in context")

            # Step 1: Calculate ROI
            roi_result = self._calculate_roi(diagnostic, research)

            # Step 2: Generate work order
            work_order_result = self._generate_work_order(
                equipment_id,
                diagnostic,
                roi_result,
                config
            )

            # Build final response
            output: RecommendationOutput = {
                "agent": self.agent_name,
                "success": True,
                "roi_analysis": roi_result if roi_result else None,
                "work_order": work_order_result if work_order_result else None,
                "timestamp": datetime.now().isoformat(),
                "error": None,
                "message": None
            }

            return output

        except Exception as e:
            # Catch any unexpected errors
            return self._error_response(str(e))

    def _calculate_roi(
        self,
        diagnostic: Dict[str, Any],
        research: Dict[str, Any]
    ) -> Optional[ROIAnalysis]:
        """
        Calculate ROI for preventive maintenance.

        Args:
            diagnostic: Diagnostic results
            research: Research results

        Returns:
            ROIAnalysis dictionary or None if calculation fails
        """
        try:
            # Extract failure type from research results
            failure_type = self._extract_failure_type(research)

            # Get failure probability from diagnostic
            failure_probability = diagnostic.get("anomaly_score", 0.5)

            # Calculate ROI using wrapper
            roi_result = calculate_roi_simple(
                failure_type=failure_type,
                failure_probability=failure_probability,
                preventive_labor_hours=4.0
            )

            # Check if calculation was successful
            if not roi_result.get("success", False):
                return None

            # Build ROI analysis
            roi_analysis: ROIAnalysis = {
                "estimated_preventive_cost": roi_result.get("estimated_preventive_cost", 0.0),
                "estimated_reactive_cost": roi_result.get("estimated_reactive_cost", 0.0),
                "expected_savings": roi_result.get("expected_savings", 0.0),
                "roi_percentage": roi_result.get("roi_percentage", 0.0),
                "recommendation": roi_result.get("recommendation", "monitor")
            }

            return roi_analysis

        except Exception:
            # If ROI calculation fails, return None (non-critical error)
            return None

    def _generate_work_order(
        self,
        equipment_id: int,
        diagnostic: Dict[str, Any],
        roi_result: Optional[ROIAnalysis],
        config: Dict[str, Any]
    ) -> Optional[WorkOrder]:
        """
        Generate a work order for maintenance.

        Args:
            equipment_id: Equipment unit ID
            diagnostic: Diagnostic results
            roi_result: ROI analysis results (optional)
            config: Configuration including assigned_to

        Returns:
            WorkOrder dictionary or None if generation fails
        """
        try:
            # Prepare anomaly data for work order generation
            anomaly_data = {
                "anomaly_detected": diagnostic.get("anomaly_detected", False),
                "severity": diagnostic.get("severity", "medium"),
                "confidence": diagnostic.get("confidence", 0.0),
                "affected_sensors": diagnostic.get("affected_sensors", []),
                "top_recommendation": diagnostic.get("top_recommendation", "")
            }

            # Convert ROI analysis to dict format expected by wrapper
            roi_data = None
            if roi_result:
                roi_data = {
                    "estimated_preventive_cost": roi_result["estimated_preventive_cost"],
                    "estimated_reactive_cost": roi_result["estimated_reactive_cost"],
                    "expected_savings": roi_result["expected_savings"],
                    "roi_percentage": roi_result["roi_percentage"],
                    "recommendation": roi_result["recommendation"]
                }

            # Get assigned_to from config
            assigned_to = config.get("assigned_to")

            # Generate work order using wrapper
            wo_result = generate_work_order_simple(
                equipment_id=equipment_id,
                anomaly_data=anomaly_data,
                roi_data=roi_data,
                assigned_to=assigned_to
            )

            # Check if generation was successful
            if not wo_result.get("success", False):
                return None

            # Build work order
            work_order: WorkOrder = {
                "work_order_id": wo_result.get("work_order_id", ""),
                "priority": wo_result.get("priority", "medium"),
                "issue_summary": wo_result.get("issue_summary", ""),
                "recommended_actions": wo_result.get("recommended_actions", []),
                "estimated_cost": wo_result.get("estimated_cost", 0.0),
                "estimated_duration": wo_result.get("estimated_duration", 0.0)
            }

            return work_order

        except Exception:
            # If work order generation fails, return None (non-critical error)
            return None

    def _extract_failure_type(self, research: Dict[str, Any]) -> str:
        """
        Extract the most likely failure type from research results.

        Args:
            research: Research agent results

        Returns:
            Failure type string
        """
        if research.get("matches_found", 0) > 0:
            similar_failures = research.get("similar_failures", [])
            if similar_failures and len(similar_failures) > 0:
                return similar_failures[0].get("failure_type", "Unknown")
        return "Unknown"

    def _no_action_response(self) -> RecommendationOutput:
        """
        Create response when no action is required.

        Returns:
            RecommendationOutput indicating no maintenance needed
        """
        return {
            "agent": self.agent_name,
            "success": True,
            "roi_analysis": None,
            "work_order": None,
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "message": "No action required - equipment operating normally"
        }

    def _error_response(self, error_message: str) -> RecommendationOutput:
        """
        Create a standardized error response.

        Args:
            error_message: Description of the error

        Returns:
            RecommendationOutput with error information
        """
        return {
            "agent": self.agent_name,
            "success": False,
            "roi_analysis": None,
            "work_order": None,
            "timestamp": datetime.now().isoformat(),
            "error": error_message,
            "message": None
        }
