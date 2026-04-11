"""
Multi-step Bug Triage Environment.

Each episode:
  1) reset(task) → samples bugs from the pool, returns first bug observation
  2) step() loop: agent investigates OR submits triage per bug
  3) When all bugs are triaged, episode is done

The agent must decide *how much* to investigate each bug before triaging.
Investigating costs budget (medium/hard). Wasted investigation = lower score.
"""

from typing import Dict, List, Optional
import random, uuid

from openenv.core.env_server import Environment

from .models import (
    BugTriageAction,
    BugTriageObservation,
    BugTriageState,
    BugReport,
    InvestigationResult,
)
from .tasks import sample_bugs, TASK_CONFIG, VALID_INVESTIGATIONS, BugTemplate
from .grader import GRADERS


class BugTriageEnvironment(Environment):

    def _initial_observation(self) -> BugTriageObservation:
        """Return an empty observation (before reset)."""
        return BugTriageObservation(
            done=False,
            reward=0.01,
            feedback="Call reset with a task name to begin: easy, medium, or hard.",
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, *, task: str = "easy", seed: int | None = None) -> BugTriageObservation:
        self._task = task.strip().lower()
        if self._task not in TASK_CONFIG:
            return BugTriageObservation(
                done=True,
                reward=0.01,
                feedback=f"Invalid task '{task}'. Choose: easy, medium, hard.",
            )

        cfg = TASK_CONFIG[self._task]
        self._seed = seed if seed is not None else random.randint(0, 2**31)
        self._bugs: List[BugTemplate] = sample_bugs(self._task, self._seed)
        self._bug_count = cfg["sample_size"]
        self._investigation_budget = cfg["investigation_budget"]
        self._show_full_info = cfg["show_full_info"]

        # Per-episode tracking
        self._current_bug_idx = 0
        self._investigations_used_total = 0
        self._investigations_per_bug: List[int] = [0] * self._bug_count
        self._wasted_investigations: List[int] = [0] * self._bug_count
        self._revealed: List[Dict[str, str]] = [{} for _ in range(self._bug_count)]
        self._scores: List[float] = []
        self._episode_id = str(uuid.uuid4())[:8]

        return self._make_observation(feedback="Episode started. Triage the first bug.")

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------

    def step(self, action: BugTriageAction) -> BugTriageObservation:
        if not hasattr(self, "_bugs") or self._current_bug_idx >= self._bug_count:
            return BugTriageObservation(done=True, reward=0.01, feedback="Episode is done.")

        action_type = action.action_type.strip().lower()

        if action_type == "investigate":
            return self._handle_investigate(action)
        elif action_type == "triage":
            return self._handle_triage(action)
        else:
            return self._make_observation(
                feedback=f"Invalid action_type '{action.action_type}'. Use 'investigate' or 'triage'."
            )

    # ------------------------------------------------------------------
    # Investigation handler
    # ------------------------------------------------------------------

    def _handle_investigate(self, action: BugTriageAction) -> BugTriageObservation:
        target = action.investigate_target.strip().lower()
        idx = self._current_bug_idx

        # Validate
        if self._show_full_info:
            return self._make_observation(
                feedback="Investigation not needed for easy task — full info is already shown. Submit your triage."
            )

        if target not in VALID_INVESTIGATIONS:
            return self._make_observation(
                feedback=f"Invalid target '{action.investigate_target}'. Choose: {', '.join(VALID_INVESTIGATIONS)}."
            )

        if target in self._revealed[idx]:
            self._wasted_investigations[idx] += 1
            return self._make_observation(
                feedback=f"You already investigated '{target}' for this bug. Choose a different target or submit triage. (-0.05 penalty)"
            )

        if self._investigations_used_total >= self._investigation_budget:
            return self._make_observation(
                feedback=f"Investigation budget exhausted ({self._investigation_budget}/{self._investigation_budget}). You must submit triage."
            )

        # Reveal layer
        template = self._bugs[idx]
        content = getattr(template.layers, target, "No information available.")
        self._revealed[idx][target] = content
        self._investigations_per_bug[idx] += 1
        self._investigations_used_total += 1

        return self._make_observation(
            feedback=f"Investigation '{target}' revealed new information."
        )

    # ------------------------------------------------------------------
    # Triage handler
    # ------------------------------------------------------------------

    def _handle_triage(self, action: BugTriageAction) -> BugTriageObservation:
        idx = self._current_bug_idx
        template = self._bugs[idx]
        grader = GRADERS[self._task]

        score = grader(action, template.truth, self._investigations_per_bug[idx])
        # Penalty for wasted (repeated) investigation attempts
        waste_penalty = self._wasted_investigations[idx] * 0.05
        score = max(0.0, score - waste_penalty)
        score = min(max(score, 0.01), 0.99)  # clamp individual score strictly (0,1)
        self._scores.append(score)

        self._current_bug_idx += 1
        done = self._current_bug_idx >= self._bug_count
        avg_score = sum(self._scores) / len(self._scores) if self._scores else 0.0
        avg_score = min(max(avg_score, 0.01), 0.99)  # strictly between 0 and 1

        if done:
            return BugTriageObservation(
                done=True,
                reward=avg_score,
                task_name=self._task,
                current_bug_index=self._current_bug_idx,
                bugs_total=self._bug_count,
                investigations_used=self._investigations_used_total,
                investigation_budget=self._investigation_budget,
                phase="done",
                feedback=f"Episode complete. Average score: {avg_score:.3f}",
                step_score=score,
            )

        return self._make_observation(
            feedback=f"Bug {idx + 1} triaged (score: {score:.2f}). Moving to bug {idx + 2}/{self._bug_count}.",
            step_score=score,
        )

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> BugTriageState:
        scores = getattr(self, "_scores", [])
        avg = min(max(sum(scores) / len(scores), 0.01), 0.99) if scores else 0.01
        return BugTriageState(
            episode_id=getattr(self, "_episode_id", ""),
            step_count=len(scores),
            task_name=getattr(self, "_task", ""),
            total_bugs=getattr(self, "_bug_count", 0),
            bugs_processed=len(scores),
            cumulative_score=avg,
            investigations_used=getattr(self, "_investigations_used_total", 0),
            investigation_budget=getattr(self, "_investigation_budget", 0),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_observation(self, feedback: str, step_score: float = 0.01) -> BugTriageObservation:
        idx = self._current_bug_idx
        if idx >= self._bug_count:
            return BugTriageObservation(done=True, reward=min(max(sum(self._scores) / len(self._scores), 0.01), 0.99) if self._scores else 0.01, feedback=feedback)

        template = self._bugs[idx]
        bug = template.bug

        # Build investigation results already revealed for this bug
        investigations_done = [
            InvestigationResult(target=t, content=c)
            for t, c in self._revealed[idx].items()
        ]

        # Available investigations = not yet revealed
        available = [t for t in VALID_INVESTIGATIONS if t not in self._revealed[idx]]
        if self._show_full_info:
            # Show all layers for easy task
            investigations_done = [
                InvestigationResult(target="logs", content=template.layers.logs),
                InvestigationResult(target="related", content=template.layers.related),
                InvestigationResult(target="reporter", content=template.layers.reporter),
            ]
            available = []

        budget_remaining = self._investigation_budget - self._investigations_used_total

        return BugTriageObservation(
            done=False,
            reward=0.01,
            bug_report=bug,
            investigations_done=investigations_done,
            available_investigations=available if budget_remaining > 0 else [],
            task_name=self._task,
            current_bug_index=idx + 1,
            bugs_total=self._bug_count,
            investigations_used=self._investigations_used_total,
            investigation_budget=self._investigation_budget,
            phase="investigate" if (available and budget_remaining > 0 and not self._show_full_info) else "triage",
            feedback=feedback,
            step_score=step_score,
        )
