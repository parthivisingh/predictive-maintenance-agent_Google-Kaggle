"""
Diagnostic Agent - Sensor Anomaly Analysis

Wraps analyze_sensors() from tools.api_wrappers with agent-specific logic.
No direct imports from Phase 3.5 modules.
"""

from typing import Dict, Any
from datetime import datetime
from tools.api_wrappers import analyze_sensors
from agents.schemas import DiagnosticOutput


class DiagnosticAgent:
    """
    Diagnostic agent for analyzing sensor readings and detecting anomalies.

    This agent wraps the analyze_sensors() API wrapper and adds agent-specific
    metadata and error handling. It does not directly interact with Phase 3.5
    infrastructure.
    """

    def __init__(self):
        """Initialize the diagnostic agent."""
        self.agent_name = "diagnostic_agent"

    def analyze(self, context: Dict[str, Any], config: Dict[str, Any]) -> DiagnosticOutput:
        """
        Analyze sensor readings for anomalies.

        Args:
            context: Dictionary containing:
                - unit_id: int - Equipment unit identifier
                - time_cycle: int - Operational cycle number
                - sensor_values: Dict[str, float] - Sensor readings
            config: Dictionary containing:
                - diagnostic_method: str - Analysis method to use

        Returns:
            DiagnosticOutput dictionary with anomaly detection results
        """
        try:
            # Extract parameters from context
            unit_id = context.get("unit_id")
            time_cycle = context.get("time_cycle")
            sensor_values = context.get("sensor_values")

            # Get method from config (default to "combined")
            method = config.get("diagnostic_method", "combined")

            # Validate required parameters
            if unit_id is None or time_cycle is None or sensor_values is None:
                return self._error_response("Missing required parameters in context")

            # Call the API wrapper
            result = analyze_sensors(
                unit_id=unit_id,
                time_cycle=time_cycle,
                sensor_values=sensor_values,
                method=method
            )

            # Check if wrapper returned an error
            if not result.get("success", False):
                return self._error_response(
                    result.get("error_message", "Unknown error from analyze_sensors")
                )

            # Add agent metadata to successful result
            result["agent"] = self.agent_name

            # Ensure all required fields are present for DiagnosticOutput
            output: DiagnosticOutput = {
                "agent": result.get("agent", self.agent_name),
                "success": result.get("success", True),
                "anomaly_detected": result.get("anomaly_detected", False),
                "anomaly_score": result.get("anomaly_score", 0.0),
                "severity": result.get("severity", "none"),
                "confidence": result.get("confidence", 0.0),
                "affected_sensors": result.get("affected_sensors", []),
                "top_recommendation": result.get("top_recommendation", "No action required"),
                "all_recommendations": result.get("all_recommendations", []),
                "method_used": result.get("method_used", method),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "error": None
            }

            return output

        except Exception as e:
            # Catch any unexpected errors
            return self._error_response(str(e))

    def _error_response(self, error_message: str) -> DiagnosticOutput:
        """
        Create a standardized error response.

        Args:
            error_message: Description of the error

        Returns:
            DiagnosticOutput dictionary with error information
        """
        return {
            "agent": self.agent_name,
            "success": False,
            "anomaly_detected": False,
            "anomaly_score": 0.0,
            "severity": "none",
            "confidence": 0.0,
            "affected_sensors": [],
            "top_recommendation": "",
            "all_recommendations": [],
            "method_used": "none",
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }
