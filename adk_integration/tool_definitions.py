"""
Google ADK Tool Definitions
===========================

Production-ready tool wrappers for ADK agents.

Usage with Google ADK:
----------------------
from google.generativeai import configure, GenerativeModel
from adk_integration.tool_definitions import all_maintenance_tools

configure(api_key=os.getenv('GOOGLE_API_KEY'))

model = GenerativeModel(
    model_name='gemini-2.0-flash-exp',
    tools=all_maintenance_tools
)

response = model.generate_content("Analyze sensor data for unit 1...")
"""

from google.generativeai.types import Tool, FunctionDeclaration
from tools.api_wrappers import (
    analyze_sensors,
    search_similar_failures_simple,
    calculate_roi_simple,
    generate_work_order_simple
)

# ============================================================================
# Tool Definitions for ADK
# ============================================================================

# Sensor Analyzer Tool
sensor_analyzer_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="analyze_sensors",
            description=(
                "Analyzes sensor readings to detect equipment anomalies. "
                "Returns anomaly score (0-1), severity level (none/low/medium/high/critical), "
                "confidence score, affected sensors, and specific recommendations. "
                "Use this when you need to determine if equipment sensors show abnormal behavior "
                "or if there are signs of potential failure."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "unit_id": {
                        "type": "integer",
                        "description": "Equipment unit identifier (must be >= 1)"
                    },
                    "time_cycle": {
                        "type": "integer",
                        "description": "Operational cycle number (must be >= 1)"
                    },
                    "sensor_values": {
                        "type": "object",
                        "description": "Sensor readings as key-value pairs, e.g., {'sensor_T30': 1620.0, 'sensor_Nc': 9080.0}"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["statistical", "ml", "combined"],
                        "description": "Detection method: 'statistical' uses statistical analysis, 'ml' uses machine learning, 'combined' uses both (recommended, default)"
                    }
                },
                "required": ["unit_id", "time_cycle", "sensor_values"]
            }
        )
    ]
)

# Similarity Search Tool
similarity_search_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="search_similar_failures",
            description=(
                "Searches historical maintenance database for similar failure patterns. "
                "Returns past failures with similar sensor signatures, including failure types, "
                "root causes, actions taken, parts replaced, costs, and downtime. "
                "Use this to find precedent cases and learn from past maintenance events. "
                "Helps identify likely failure modes based on historical data."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "sensor_values": {
                        "type": "object",
                        "description": "Current sensor readings to match against historical patterns"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of similar cases to return (1-10, default: 3)"
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score 0-1 to include results (default: 0.6, higher = more similar required)"
                    }
                },
                "required": ["sensor_values"]
            }
        )
    ]
)

# ROI Calculator Tool
roi_calculator_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="calculate_roi",
            description=(
                "Calculates return on investment for preventive vs reactive maintenance. "
                "Compares estimated costs of preventive action now versus reactive repair later, "
                "accounting for failure probability. Returns cost estimates, expected savings, "
                "ROI percentage, and clear recommendation (preventive/reactive/monitor). "
                "Use this to make data-driven maintenance decisions based on cost-benefit analysis."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "failure_type": {
                        "type": "string",
                        "description": "Type of failure to analyze (e.g., 'HPC_degradation', 'turbine_overheating')"
                    },
                    "failure_probability": {
                        "type": "number",
                        "description": "Estimated probability of failure occurring (0-1, where 1.0 = certain)"
                    },
                    "preventive_labor_hours": {
                        "type": "number",
                        "description": "Expected labor hours for preventive maintenance (default: 4.0 hours)"
                    },
                    "custom_costs": {
                        "type": "object",
                        "description": "Optional custom cost overrides (e.g., {'labor_rate': 125.0, 'part_cost': 2000.0})"
                    }
                },
                "required": ["failure_type", "failure_probability"]
            }
        )
    ]
)

# Work Order Generator Tool
work_order_generator_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="generate_work_order",
            description=(
                "Generates a comprehensive maintenance work order based on anomaly analysis. "
                "Includes work order ID, priority level (critical/high/medium/low), "
                "issue summary, detailed recommended actions, estimated cost, duration, "
                "safety notes, and due date. Use this as the final step to create "
                "actionable maintenance tasks that technicians can execute."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "equipment_id": {
                        "type": "integer",
                        "description": "Equipment unit identifier"
                    },
                    "anomaly_data": {
                        "type": "object",
                        "description": "Output from analyze_sensors function (must include 'anomaly_detected' and 'severity' fields)"
                    },
                    "roi_data": {
                        "type": "object",
                        "description": "Optional output from calculate_roi function (enhances work order with cost justification)"
                    },
                    "assigned_to": {
                        "type": "string",
                        "description": "Optional technician name to assign the work order to"
                    }
                },
                "required": ["equipment_id", "anomaly_data"]
            }
        )
    ]
)


# ============================================================================
# Combined Tool List
# ============================================================================

all_maintenance_tools = [
    sensor_analyzer_tool,
    similarity_search_tool,
    roi_calculator_tool,
    work_order_generator_tool
]


# ============================================================================
# Function Mapping (for ADK function calling)
# ============================================================================

FUNCTION_MAP = {
    "analyze_sensors": analyze_sensors,
    "search_similar_failures": search_similar_failures_simple,
    "calculate_roi": calculate_roi_simple,
    "generate_work_order": generate_work_order_simple
}


def execute_function_call(function_name: str, **kwargs):
    """
    Execute a function call from ADK.

    Parameters:
    -----------
    function_name : str
        Name of function to call
    **kwargs
        Function arguments

    Returns:
    --------
    Any
        Function result
    """
    if function_name not in FUNCTION_MAP:
        return {
            "success": False,
            "error_type": "UnknownFunction",
            "error_message": f"Function '{function_name}' not found"
        }

    func = FUNCTION_MAP[function_name]
    return func(**kwargs)
