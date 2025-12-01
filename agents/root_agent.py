"""
Root Agent - Pipeline Orchestrator

Orchestrates the sequential multi-agent pipeline.
No direct wrapper calls - delegates to specialized agents.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import time

from agents.diagnostic_agent import DiagnosticAgent
from agents.research_agent import ResearchAgent
from agents.recommendation_agent import RecommendationAgent
from agents.schemas import RootAgentOutput, PipelineResults, FinalDecision, ExecutionMetadata


class RootAgent:
    """
    Root agent that orchestrates the sequential maintenance analysis pipeline.

    Pipeline flow:
    1. Diagnostic Agent - Analyze sensor data for anomalies
    2. Research Agent - Find similar historical failures (if anomaly detected)
    3. Recommendation Agent - Generate ROI and work orders (if anomaly detected)

    The pipeline uses early exit optimization: if no anomaly is detected,
    research and recommendation agents are skipped.
    """

    def __init__(self):
        """Initialize the root agent and all specialized agents."""
        self.diagnostic_agent = DiagnosticAgent()
        self.research_agent = ResearchAgent()
        self.recommendation_agent = RecommendationAgent()

    def execute_pipeline(
        self,
        unit_id: int,
        time_cycle: int,
        sensor_values: Dict[str, float],
        config: Optional[Dict[str, Any]] = None
    ) -> RootAgentOutput:
        """
        Execute the full maintenance analysis pipeline.

        Args:
            unit_id: Equipment unit identifier (>= 1)
            time_cycle: Operational cycle number (>= 1)
            sensor_values: Dictionary of sensor readings
            config: Optional configuration overrides

        Returns:
            RootAgentOutput with complete pipeline results and final decision
        """
        start_time = time.time()
        config = config or self._default_config()

        # Initialize context that will be passed through the pipeline
        context = {
            "unit_id": unit_id,
            "time_cycle": time_cycle,
            "sensor_values": sensor_values
        }

        errors = []
        agents_called = []

        # ====================================================================
        # Step 1: Diagnostic Analysis
        # ====================================================================
        diagnostic_result = self.diagnostic_agent.analyze(context, config)
        context["diagnostic"] = diagnostic_result
        agents_called.append("diagnostic_agent")

        if not diagnostic_result.get("success", False):
            # Critical failure - cannot continue pipeline
            error_msg = diagnostic_result.get("error", "Unknown diagnostic error")
            errors.append(f"Diagnostic failed: {error_msg}")
            return self._build_error_response(context, errors, agents_called, start_time)

        # ====================================================================
        # Step 2: Research Similar Failures (Conditional)
        # ====================================================================
        if diagnostic_result.get("anomaly_detected", False):
            # Anomaly detected - search for similar failures
            research_result = self.research_agent.search(context, config)
            context["research"] = research_result
            agents_called.append("research_agent")

            if not research_result.get("success", False):
                # Non-critical error - log and continue
                error_msg = research_result.get("error", "Unknown research error")
                errors.append(f"Research failed: {error_msg}")
        else:
            # No anomaly - skip research
            context["research"] = {
                "agent": "research_agent",
                "success": True,
                "matches_found": 0,
                "similar_failures": [],
                "timestamp": datetime.now().isoformat(),
                "error": None
            }

        # ====================================================================
        # Step 3: Generate Recommendations (Conditional)
        # ====================================================================
        if diagnostic_result.get("anomaly_detected", False):
            # Anomaly detected - generate recommendations
            recommendation_result = self.recommendation_agent.generate(context, config)
            context["recommendation"] = recommendation_result
            agents_called.append("recommendation_agent")

            if not recommendation_result.get("success", False):
                # Non-critical error - log and continue
                error_msg = recommendation_result.get("error", "Unknown recommendation error")
                errors.append(f"Recommendation failed: {error_msg}")
        else:
            # No anomaly - skip recommendations
            context["recommendation"] = {
                "agent": "recommendation_agent",
                "success": True,
                "roi_analysis": None,
                "work_order": None,
                "message": "No action required",
                "timestamp": datetime.now().isoformat(),
                "error": None
            }

        # ====================================================================
        # Step 4: Build Final Response
        # ====================================================================
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Determine overall success
        # Pipeline succeeds if diagnostic succeeds, even if research/recommendations fail
        overall_success = diagnostic_result.get("success", False)

        # Build pipeline results
        pipeline_results: PipelineResults = {
            "diagnostic": context["diagnostic"],
            "research": context.get("research", {}),
            "recommendation": context.get("recommendation", {})
        }

        # Build final decision
        final_decision = self._make_final_decision(context)

        # Build execution metadata
        execution_metadata: ExecutionMetadata = {
            "total_time_ms": round(execution_time, 2),
            "agents_called": agents_called,
            "errors_encountered": errors
        }

        # Build final output
        output: RootAgentOutput = {
            "success": overall_success,
            "unit_id": unit_id,
            "time_cycle": time_cycle,
            "pipeline_results": pipeline_results,
            "final_decision": final_decision,
            "execution_metadata": execution_metadata,
            "timestamp": datetime.now().isoformat()
        }

        return output

    def _make_final_decision(self, context: Dict[str, Any]) -> FinalDecision:
        """
        Aggregate pipeline results into a final decision.

        Args:
            context: Full pipeline context with all agent results

        Returns:
            FinalDecision dictionary with action recommendations
        """
        diagnostic = context.get("diagnostic", {})
        recommendation = context.get("recommendation", {})

        anomaly_detected = diagnostic.get("anomaly_detected", False)
        severity = diagnostic.get("severity", "none")

        # No anomaly case
        if not anomaly_detected:
            decision: FinalDecision = {
                "action_required": False,
                "priority": "none",
                "work_order_id": None,
                "summary": "Equipment operating normally. No maintenance required.",
                "estimated_cost": None,
                "recommended_actions": None
            }
            return decision

        # Anomaly detected - extract work order details
        work_order = recommendation.get("work_order", {})

        if work_order:
            decision: FinalDecision = {
                "action_required": True,
                "priority": work_order.get("priority", severity),
                "work_order_id": work_order.get("work_order_id"),
                "summary": work_order.get("issue_summary", f"Anomaly detected: {severity} severity"),
                "estimated_cost": work_order.get("estimated_cost"),
                "recommended_actions": work_order.get("recommended_actions", [])
            }
        else:
            # Anomaly detected but no work order generated
            decision: FinalDecision = {
                "action_required": True,
                "priority": severity,
                "work_order_id": None,
                "summary": f"Anomaly detected: {severity} severity. Manual review required.",
                "estimated_cost": None,
                "recommended_actions": diagnostic.get("all_recommendations", [])
            }

        return decision

    def _build_error_response(
        self,
        context: Dict[str, Any],
        errors: list,
        agents_called: list,
        start_time: float
    ) -> RootAgentOutput:
        """
        Build response when critical error occurs.

        Args:
            context: Current pipeline context
            errors: List of error messages
            agents_called: List of agents that were called
            start_time: Pipeline start time

        Returns:
            RootAgentOutput with error information
        """
        execution_time = (time.time() - start_time) * 1000

        # Build error decision
        final_decision: FinalDecision = {
            "action_required": False,
            "priority": "error",
            "work_order_id": None,
            "summary": "Pipeline execution failed. Manual inspection required.",
            "estimated_cost": None,
            "recommended_actions": None
        }

        # Build execution metadata
        execution_metadata: ExecutionMetadata = {
            "total_time_ms": round(execution_time, 2),
            "agents_called": agents_called,
            "errors_encountered": errors
        }

        # Build minimal pipeline results from context
        pipeline_results: PipelineResults = {
            "diagnostic": context.get("diagnostic", {}),
            "research": context.get("research", {}),
            "recommendation": context.get("recommendation", {})
        }

        # Build error output
        output: RootAgentOutput = {
            "success": False,
            "unit_id": context.get("unit_id", 0),
            "time_cycle": context.get("time_cycle", 0),
            "pipeline_results": pipeline_results,
            "final_decision": final_decision,
            "execution_metadata": execution_metadata,
            "timestamp": datetime.now().isoformat()
        }

        return output

    def _default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for the pipeline.

        Returns:
            Dictionary with default configuration values
        """
        return {
            "diagnostic_method": "combined",
            "similarity_top_n": 3,
            "similarity_threshold": 0.6,
            "assigned_to": None
        }
