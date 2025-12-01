"""
JSON Schemas for Simulation Input/Output Validation
====================================================

Lightweight schemas matching agents.schemas TypedDict structures exactly.
Used for fail-fast validation via jsonschema.validate.
"""

from typing import Dict, Any

# ============================================================================
# Profile Input Schema (matches RootAgent.execute_pipeline parameters)
# ============================================================================

PROFILE_INPUT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["unit_id", "time_cycle", "sensor_values"],
    "properties": {
        "unit_id": {
            "type": "integer",
            "minimum": 1,
            "description": "Equipment unit identifier"
        },
        "time_cycle": {
            "type": "integer",
            "minimum": 1,
            "description": "Operational cycle number"
        },
        "sensor_values": {
            "type": "object",
            "minProperties": 1,
            "patternProperties": {
                "^.*$": {
                    "type": "number"
                }
            },
            "description": "Dictionary of sensor readings (sensor_name: value)"
        },
        "profile_id": {
            "type": "string",
            "description": "Optional profile identifier for tracking"
        }
    },
    "additionalProperties": False
}


# ============================================================================
# Simulation Output Schema (single run result)
# ============================================================================

SIMULATION_OUTPUT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["run_id", "status", "timestamp"],
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Unique run identifier"
        },
        "profile_id": {
            "type": "string",
            "description": "Profile identifier"
        },
        "unit_id": {
            "type": "integer",
            "minimum": 1
        },
        "time_cycle": {
            "type": "integer",
            "minimum": 1
        },
        "status": {
            "type": "string",
            "enum": ["success", "error"],
            "description": "Run execution status"
        },
        "anomaly": {
            "type": "boolean",
            "description": "Anomaly detected flag"
        },
        "roi": {
            "type": ["number", "null"],
            "description": "Estimated cost/ROI as float"
        },
        "priority": {
            "type": "string",
            "enum": ["none", "low", "medium", "high", "critical", "error"],
            "description": "Priority level"
        },
        "similarity_hits": {
            "type": "number",
            "description": "Number of similar failures found (coerced to float)"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO-8601 timestamp"
        },
        "duration_sec": {
            "type": "number",
            "description": "Execution duration in seconds"
        },
        "random_seed": {
            "type": ["integer", "null"],
            "description": "Random seed used for deterministic execution"
        },
        "error_msg": {
            "type": ["string", "null"],
            "description": "Error message if status=error"
        }
    },
    "additionalProperties": True  # Allow extra fields from RootAgentOutput
}


# ============================================================================
# Root Agent Output Schema (lightweight validation)
# ============================================================================

ROOT_AGENT_OUTPUT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["success", "unit_id", "time_cycle", "pipeline_results", "final_decision", "execution_metadata", "timestamp"],
    "properties": {
        "success": {
            "type": "boolean"
        },
        "unit_id": {
            "type": "integer",
            "minimum": 1
        },
        "time_cycle": {
            "type": "integer",
            "minimum": 1
        },
        "pipeline_results": {
            "type": "object",
            "required": ["diagnostic", "research", "recommendation"],
            "properties": {
                "diagnostic": {"type": "object"},
                "research": {"type": "object"},
                "recommendation": {"type": "object"}
            }
        },
        "final_decision": {
            "type": "object",
            "required": ["action_required", "summary"],
            "properties": {
                "action_required": {"type": "boolean"},
                "priority": {
                    "type": "string",
                    "description": "Priority level (accepts enum string representations)"
                },
                "work_order_id": {"type": ["string", "null"]},
                "summary": {"type": "string"},
                "estimated_cost": {"type": ["number", "null"]},
                "recommended_actions": {
                    "type": ["array", "null"],
                    "items": {"type": "string"}
                }
            }
        },
        "execution_metadata": {
            "type": "object",
            "required": ["total_time_ms", "agents_called", "errors_encountered"],
            "properties": {
                "total_time_ms": {"type": "number"},
                "agents_called": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "errors_encountered": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        }
    },
    "additionalProperties": False
}


# ============================================================================
# Batch Result Schema
# ============================================================================

BATCH_RESULT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["batch_id", "total_runs", "successful_runs", "failed_runs", "runs", "timestamp"],
    "properties": {
        "batch_id": {
            "type": "string",
            "description": "Unique batch identifier"
        },
        "total_runs": {
            "type": "integer",
            "minimum": 0
        },
        "successful_runs": {
            "type": "integer",
            "minimum": 0
        },
        "failed_runs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["profile_id", "error_msg"],
                "properties": {
                    "profile_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "error_msg": {"type": "string"},
                    "timestamp": {"type": "string"}
                }
            }
        },
        "runs": {
            "type": "array",
            "items": SIMULATION_OUTPUT_SCHEMA
        },
        "summary_metrics": {
            "type": "object",
            "description": "Aggregated metrics across all runs"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "duration_sec": {
            "type": "number",
            "description": "Total batch execution duration"
        }
    },
    "additionalProperties": True
}
