"""EnvClient subclass for the Bug Triage environment."""

from typing import Any, Dict
from openenv import GenericEnvClient

from .models import BugTriageAction, BugTriageObservation, BugTriageState


class BugTriageClient(GenericEnvClient):
    """Client that communicates with the Bug Triage FastAPI server."""

    def _step_payload(self, action: BugTriageAction) -> Dict[str, Any]:
        return action.model_dump()

    def _parse_result(self, data: Dict[str, Any]) -> BugTriageObservation:
        return BugTriageObservation(**data)

    def _parse_state(self, data: Dict[str, Any]) -> BugTriageState:
        return BugTriageState(**data)
