"""
Pydantic models for the Bug Triage & Fix Recommendation environment.

Upgraded: Multi-step investigation workflow with trade-offs.
The agent must decide WHAT to investigate and WHEN to commit to a triage decision.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from openenv.core.env_server import Action, Observation, State


# ---------------------------------------------------------------------------
# Bug data structures
# ---------------------------------------------------------------------------

class BugReport(BaseModel):
    """A bug report — initially brief, enriched through investigation."""

    id: str
    title: str
    brief_description: str
    affected_component: str
    reporter_role: str
    frequency: str


class InvestigationResult(BaseModel):
    """Information revealed by an investigation action."""

    target: str
    content: str


class BugGroundTruth(BaseModel):
    """Ground truth labels for deterministic grading."""

    bug_type: str  # "ui", "backend", "security"
    severity: str  # "low", "medium", "high", "critical"
    fix_keywords: List[str] = Field(default_factory=list)


class InvestigationLayers(BaseModel):
    """What each investigation action reveals about a bug."""

    logs: str = ""
    related: str = ""
    reporter: str = ""


# ---------------------------------------------------------------------------
# Action
# ---------------------------------------------------------------------------

class BugTriageAction(Action):
    """Agent's action: investigate further OR submit a triage decision.

    action_type="investigate": explore one aspect of the current bug.
    action_type="triage": submit classification and move to next bug.
    """

    action_type: str = "triage"  # "investigate" or "triage"

    # Investigation fields
    investigate_target: str = ""  # "logs", "related", "reporter"

    # Triage fields
    bug_type: str = ""
    severity: str = ""
    fix_suggestion: str = ""


# ---------------------------------------------------------------------------
# Observation
# ---------------------------------------------------------------------------

class BugTriageObservation(Observation):
    """What the agent observes each step.

    Inherits: done (bool), reward (Optional[float]).
    """

    bug_report: Optional[BugReport] = None
    investigations_done: List[InvestigationResult] = Field(default_factory=list)
    available_investigations: List[str] = Field(default_factory=list)

    task_name: str = ""
    current_bug_index: int = 0
    bugs_total: int = 0
    investigations_used: int = 0
    investigation_budget: int = 0
    phase: str = "investigate"
    feedback: str = ""
    step_score: float = 0.01


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class BugTriageState(State):
    """Episode metadata. Inherits: episode_id, step_count."""

    task_name: str = ""
    total_bugs: int = 0
    bugs_processed: int = 0
    cumulative_score: float = 0.01
    investigations_used: int = 0
    investigation_budget: int = 0
