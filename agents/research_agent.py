"""
Research Agent - Historical Failure Analysis

Wraps search_similar_failures_simple() from tools.api_wrappers with conditional logic.
No direct imports from Phase 3.5 modules.
"""

from typing import Dict, Any
from datetime import datetime
from tools.api_wrappers import search_similar_failures_simple
from agents.schemas import ResearchOutput


class ResearchAgent:
    """
    Research agent for finding similar historical failures.

    This agent searches the failure database for similar sensor patterns
    and provides insights from past maintenance actions. It only executes
    if an anomaly has been detected.
    """

    def __init__(self):
        """Initialize the research agent."""
        self.agent_name = "research_agent"

    def search(self, context: Dict[str, Any], config: Dict[str, Any]) -> ResearchOutput:
        """
        Search for similar historical failures.

        Args:
            context: Dictionary containing:
                - sensor_values: Dict[str, float] - Current sensor readings
                - diagnostic: Dict - Results from diagnostic_agent
            config: Dictionary containing:
                - similarity_top_n: int - Number of matches to return
                - similarity_threshold: float - Minimum similarity score

        Returns:
            ResearchOutput dictionary with similar failure matches
        """
        try:
            # Extract diagnostic results
            diagnostic = context.get("diagnostic", {})

            # Early exit if no anomaly detected
            if not diagnostic.get("anomaly_detected", False):
                return self._no_anomaly_response()

            # Extract parameters
            sensor_values = context.get("sensor_values")
            if sensor_values is None:
                return self._error_response("Missing sensor_values in context")

            # Get search parameters from config
            top_n = config.get("similarity_top_n", 3)
            similarity_threshold = config.get("similarity_threshold", 0.6)

            # Call the API wrapper
            result = search_similar_failures_simple(
                sensor_values=sensor_values,
                top_n=top_n,
                similarity_threshold=similarity_threshold
            )

            # Check if wrapper returned an error
            if not result.get("success", False):
                return self._error_response(
                    result.get("error_message", "Unknown error from search_similar_failures_simple")
                )

            # Add agent metadata
            result["agent"] = self.agent_name

            # Ensure all required fields are present for ResearchOutput
            output: ResearchOutput = {
                "agent": result.get("agent", self.agent_name),
                "success": result.get("success", True),
                "matches_found": result.get("matches_found", 0),
                "similar_failures": result.get("similar_failures", []),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "error": None
            }

            return output

        except Exception as e:
            # Catch any unexpected errors
            return self._error_response(str(e))

    def _no_anomaly_response(self) -> ResearchOutput:
        """
        Create response when no anomaly is detected.

        Returns:
            ResearchOutput dictionary indicating no search was performed
        """
        return {
            "agent": self.agent_name,
            "success": True,
            "matches_found": 0,
            "similar_failures": [],
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

    def _error_response(self, error_message: str) -> ResearchOutput:
        """
        Create a standardized error response.

        Args:
            error_message: Description of the error

        Returns:
            ResearchOutput dictionary with error information
        """
        return {
            "agent": self.agent_name,
            "success": False,
            "matches_found": 0,
            "similar_failures": [],
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }
