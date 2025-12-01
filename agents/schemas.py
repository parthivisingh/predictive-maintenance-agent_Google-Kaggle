"""
Agent schemas for Phase 4 multi-agent system.

All schemas use TypedDict for JSON-safe serialization.
These schemas define the contract between agents in the pipeline.
"""

from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict


# ============================================================================
# Diagnostic Agent Schemas
# ============================================================================

class DiagnosticInput(TypedDict):
    """Input schema for diagnostic agent."""
    unit_id: int              # >= 1
    time_cycle: int           # >= 1
    sensor_values: Dict[str, float]  # Dict of sensor readings
    method: str              # "statistical" | "ml" | "combined"


class DiagnosticOutput(TypedDict):
    """Output schema for diagnostic agent."""
    agent: str               # Always "diagnostic_agent"
    success: bool
    anomaly_detected: bool
    anomaly_score: float     # 0-1
    severity: str           # "none|low|medium|high|critical"
    confidence: float        # 0-1
    affected_sensors: List[str]
    top_recommendation: str
    all_recommendations: List[str]
    method_used: str
    timestamp: str
    error: Optional[str]     # Only if success=false


# ============================================================================
# Research Agent Schemas
# ============================================================================

class ResearchInput(TypedDict):
    """Input schema for research agent."""
    sensor_values: Dict[str, float]
    anomaly_detected: bool
    severity: str
    top_n: int              # 1-10
    similarity_threshold: float  # 0.0-1.0


class SimilarFailure(TypedDict):
    """Schema for a single similar failure match."""
    similarity_score: float
    failure_type: str
    root_cause: str
    action_taken: str
    parts_replaced: List[str]
    avg_cost: float
    avg_downtime: float


class ResearchOutput(TypedDict):
    """Output schema for research agent."""
    agent: str               # Always "research_agent"
    success: bool
    matches_found: int
    similar_failures: List[SimilarFailure]
    timestamp: str
    error: Optional[str]


# ============================================================================
# Recommendation Agent Schemas
# ============================================================================

class RecommendationInput(TypedDict):
    """Input schema for recommendation agent."""
    equipment_id: int
    diagnostic_data: DiagnosticOutput
    research_data: ResearchOutput
    assigned_to: Optional[str]


class ROIAnalysis(TypedDict):
    """ROI analysis results."""
    estimated_preventive_cost: float
    estimated_reactive_cost: float
    expected_savings: float
    roi_percentage: float
    recommendation: str  # "preventive|reactive|monitor"


class WorkOrder(TypedDict):
    """Work order details."""
    work_order_id: str
    priority: str
    issue_summary: str
    recommended_actions: List[str]
    estimated_cost: float
    estimated_duration: float


class RecommendationOutput(TypedDict):
    """Output schema for recommendation agent."""
    agent: str               # Always "recommendation_agent"
    success: bool
    roi_analysis: Optional[ROIAnalysis]
    work_order: Optional[WorkOrder]
    timestamp: str
    error: Optional[str]
    message: Optional[str]   # For no-action cases


# ============================================================================
# Root Agent Schemas
# ============================================================================

class RootAgentConfig(TypedDict, total=False):
    """Configuration for root agent pipeline."""
    diagnostic_method: str
    similarity_top_n: int
    similarity_threshold: float
    assigned_to: Optional[str]


class RootAgentInput(TypedDict):
    """Input schema for root agent."""
    unit_id: int
    time_cycle: int
    sensor_values: Dict[str, float]
    assigned_to: Optional[str]
    config: RootAgentConfig


class PipelineResults(TypedDict):
    """Results from all agents in the pipeline."""
    diagnostic: DiagnosticOutput
    research: ResearchOutput
    recommendation: RecommendationOutput


class FinalDecision(TypedDict):
    """Final decision from the pipeline."""
    action_required: bool
    priority: str
    work_order_id: Optional[str]
    summary: str
    estimated_cost: Optional[float]
    recommended_actions: Optional[List[str]]


class ExecutionMetadata(TypedDict):
    """Metadata about pipeline execution."""
    total_time_ms: float
    agents_called: List[str]
    errors_encountered: List[str]


class RootAgentOutput(TypedDict):
    """Output schema for root agent."""
    success: bool
    unit_id: int
    time_cycle: int
    pipeline_results: PipelineResults
    final_decision: FinalDecision
    execution_metadata: ExecutionMetadata
    timestamp: str


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_sensor_values(sensor_values: Dict[str, float]) -> bool:
    """Validate sensor values dictionary."""
    if not isinstance(sensor_values, dict):
        return False
    if len(sensor_values) == 0:
        return False
    for key, value in sensor_values.items():
        if not isinstance(key, str) or not isinstance(value, (int, float)):
            return False
    return True


def validate_unit_id(unit_id: int) -> bool:
    """Validate unit ID."""
    return isinstance(unit_id, int) and unit_id >= 1


def validate_time_cycle(time_cycle: int) -> bool:
    """Validate time cycle."""
    return isinstance(time_cycle, int) and time_cycle >= 1
