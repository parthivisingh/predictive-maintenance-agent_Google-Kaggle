"""
ADK Agent Connector - Bridge between Root Agent and Google Gemini ADK

Connects the root agent to Google Gemini ADK for LLM-powered orchestration.
Allows natural language interaction with the multi-agent maintenance system.
"""

import os
from typing import Dict, Any, Optional, List
from google.generativeai import configure, GenerativeModel
from agents.root_agent import RootAgent
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)


class ADKAgentConnector:
    """
    Bridges RootAgent with Google Gemini ADK.

    This connector allows LLM-powered orchestration of maintenance tools
    through natural language. The LLM can call individual tools or trigger
    the complete multi-agent pipeline.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp", api_key: Optional[str] = None):
        """
        Initialize the ADK agent connector.

        Args:
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
            api_key: Google API key (if not provided, uses GOOGLE_API_KEY env var)
        """
        # Initialize root agent
        self.root_agent = RootAgent()

        # Configure Google Generative AI
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        configure(api_key=api_key)

        # Import tool definitions
        from adk_integration.tool_definitions import all_maintenance_tools

        # Initialize Gemini model with tools
        self.model = GenerativeModel(
            model_name=model_name,
            tools=all_maintenance_tools
        )

        # Function mapping for tool execution
        self.function_map = {
            "analyze_sensors": analyze_sensors,
            "search_similar_failures": search_similar_failures_simple,
            "calculate_roi": calculate_roi_simple,
            "generate_work_order": generate_work_order_simple
        }

    def execute_with_llm(
        self,
        user_prompt: str,
        sensor_data: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Allow LLM to orchestrate tool calls through natural language.

        Args:
            user_prompt: Natural language request from user
            sensor_data: Optional equipment context (unit_id, time_cycle, sensor_values)
            max_iterations: Maximum number of function call iterations (default: 10)

        Returns:
            Dictionary containing:
                - llm_response: Final text response from LLM
                - function_calls_executed: Number of tool calls made
                - tool_results: List of tool execution results
                - conversation_history: Full conversation turns
        """
        # Build context-enhanced prompt
        enhanced_prompt = self._build_context_prompt(user_prompt, sensor_data)

        # Start chat session
        chat = self.model.start_chat()

        # Send initial message
        response = chat.send_message(enhanced_prompt)

        # Track execution
        tool_results = []
        conversation_history = []
        iterations = 0

        # Handle function calling loop
        while iterations < max_iterations:
            iterations += 1

            # Check if response has function calls
            if not response.parts:
                break

            has_function_call = any(
                hasattr(part, 'function_call') for part in response.parts
            )

            if not has_function_call:
                # No more function calls - we're done
                break

            # Execute all function calls in this response
            function_responses = []
            for part in response.parts:
                if hasattr(part, 'function_call'):
                    # Execute the function call
                    result = self._execute_function(part.function_call)
                    tool_results.append({
                        "function_name": part.function_call.name,
                        "arguments": dict(part.function_call.args),
                        "result": result
                    })

                    # Prepare function response for LLM
                    function_responses.append({
                        "name": part.function_call.name,
                        "response": result
                    })

            # If we executed functions, send results back to LLM
            if function_responses:
                # Send function results back to continue the conversation
                response = chat.send_message(
                    self._format_function_responses(function_responses)
                )
            else:
                break

        # Extract final text response
        final_text = None
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    final_text = part.text
                    break

        return {
            "llm_response": final_text,
            "function_calls_executed": len(tool_results),
            "tool_results": tool_results,
            "iterations": iterations,
            "success": final_text is not None
        }

    def execute_pipeline_direct(
        self,
        unit_id: int,
        time_cycle: int,
        sensor_values: Dict[str, float],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the multi-agent pipeline directly without LLM orchestration.

        This bypasses the LLM and calls the root agent directly,
        which is faster and deterministic.

        Args:
            unit_id: Equipment unit identifier
            time_cycle: Operational cycle number
            sensor_values: Dictionary of sensor readings
            config: Optional pipeline configuration

        Returns:
            RootAgentOutput from the pipeline
        """
        return self.root_agent.execute_pipeline(
            unit_id=unit_id,
            time_cycle=time_cycle,
            sensor_values=sensor_values,
            config=config
        )

    def _build_context_prompt(
        self,
        user_prompt: str,
        sensor_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build enhanced prompt with sensor context.

        Args:
            user_prompt: User's natural language request
            sensor_data: Optional sensor data context

        Returns:
            Enhanced prompt string
        """
        if not sensor_data:
            return user_prompt

        context_info = f"""
{user_prompt}

Equipment Context:
- Unit ID: {sensor_data.get('unit_id', 'N/A')}
- Time Cycle: {sensor_data.get('time_cycle', 'N/A')}
- Sensors: {len(sensor_data.get('sensor_values', {}))} readings available

Use the available maintenance tools to analyze this equipment and provide recommendations.
"""
        return context_info.strip()

    def _execute_function(self, function_call) -> Dict[str, Any]:
        """
        Execute a function call from the LLM.

        Args:
            function_call: FunctionCall object from Gemini

        Returns:
            Function execution result
        """
        function_name = function_call.name
        kwargs = dict(function_call.args)

        # Map function name (handle both versions)
        if function_name == "search_similar_failures":
            # ADK tool name differs from wrapper name
            actual_function = self.function_map.get("search_similar_failures")
        elif function_name == "calculate_roi":
            actual_function = self.function_map.get("calculate_roi")
        elif function_name == "generate_work_order":
            actual_function = self.function_map.get("generate_work_order")
        else:
            actual_function = self.function_map.get(function_name)

        if actual_function:
            try:
                return actual_function(**kwargs)
            except Exception as e:
                return {
                    "success": False,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
        else:
            return {
                "success": False,
                "error_type": "UnknownFunction",
                "error_message": f"Unknown function: {function_name}"
            }

    def _format_function_responses(self, function_responses: List[Dict]) -> str:
        """
        Format function responses for sending back to LLM.

        Args:
            function_responses: List of function response dictionaries

        Returns:
            Formatted string for LLM
        """
        formatted = "Function execution results:\n\n"
        for i, resp in enumerate(function_responses, 1):
            formatted += f"{i}. {resp['name']}:\n"
            formatted += f"   Result: {resp['response']}\n\n"
        return formatted
