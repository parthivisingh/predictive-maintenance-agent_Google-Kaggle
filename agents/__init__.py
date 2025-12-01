"""
Multi-agent system for predictive maintenance.

This package contains specialized agents that work together to:
- Diagnose equipment anomalies
- Research similar historical failures
- Generate maintenance recommendations
- Orchestrate the entire pipeline

Each agent uses only the stable wrapper APIs from tools.api_wrappers.
"""

from agents.schemas import (
    DiagnosticInput,
    DiagnosticOutput,
    ResearchInput,
    ResearchOutput,
    RecommendationInput,
    RecommendationOutput,
    RootAgentInput,
    RootAgentOutput
)

__all__ = [
    "DiagnosticInput",
    "DiagnosticOutput",
    "ResearchInput",
    "ResearchOutput",
    "RecommendationInput",
    "RecommendationOutput",
    "RootAgentInput",
    "RootAgentOutput"
]
