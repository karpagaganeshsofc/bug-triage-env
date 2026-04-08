"""
Deterministic graders for the upgraded Bug Triage environment.

Scoring combines ACCURACY and EFFICIENCY:
  - Easy:   accuracy only (no investigation)
  - Medium: 0.7 * accuracy + 0.3 * efficiency
  - Hard:   0.6 * accuracy + 0.4 * efficiency

Efficiency rewards agents that investigate wisely — gather enough info
to be accurate without wasting the limited budget.
"""

from .models import BugTriageAction, BugGroundTruth


VALID_BUG_TYPES = {"ui", "backend", "security"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def _match_bug_type(action: BugTriageAction, truth: BugGroundTruth) -> float:
    submitted = action.bug_type.strip().lower()
    if submitted not in VALID_BUG_TYPES:
        return 0.0
    return 1.0 if submitted == truth.bug_type else 0.0


def _match_severity(action: BugTriageAction, truth: BugGroundTruth) -> float:
    submitted = action.severity.strip().lower()
    if submitted not in VALID_SEVERITIES:
        return 0.0
    if submitted == truth.severity:
        return 1.0
    # Partial credit for adjacent severity
    order = ["low", "medium", "high", "critical"]
    if submitted in order and truth.severity in order:
        diff = abs(order.index(submitted) - order.index(truth.severity))
        if diff == 1:
            return 0.4  # One level off
    return 0.0


def _match_fix_keywords(action: BugTriageAction, truth: BugGroundTruth) -> float:
    if not truth.fix_keywords:
        return 1.0
    suggestion = action.fix_suggestion.strip().lower()
    if not suggestion:
        return 0.0
    matched = sum(1 for kw in truth.fix_keywords if kw.lower() in suggestion)
    return matched / len(truth.fix_keywords)


def _efficiency_score(investigations_for_bug: int, max_per_bug: int) -> float:
    """Reward efficient investigation. 0 investigations = 1.0, max = 0.3."""
    if max_per_bug <= 0:
        return 1.0
    efficiency = 1.0 - (investigations_for_bug / max_per_bug)
    return max(0.3, efficiency)


def grade_easy(action: BugTriageAction, truth: BugGroundTruth, investigations: int = 0) -> float:
    """Easy: bug_type classification only."""
    return _match_bug_type(action, truth)


def grade_medium(action: BugTriageAction, truth: BugGroundTruth, investigations: int = 0) -> float:
    """Medium: type + severity accuracy (0.7) + efficiency (0.3).
    Early-guess penalty: if agent triages with 0 investigations AND gets it wrong, score *= 0.7.
    """
    type_score = _match_bug_type(action, truth)
    sev_score = _match_severity(action, truth)
    accuracy = 0.5 * type_score + 0.5 * sev_score
    efficiency = _efficiency_score(investigations, 3)
    score = 0.7 * accuracy + 0.3 * efficiency
    # Penalize blind guessing: 0 investigations AND low accuracy
    if investigations == 0 and accuracy < 1.0:
        score *= 0.7
    return score


def grade_hard(action: BugTriageAction, truth: BugGroundTruth, investigations: int = 0) -> float:
    """Hard: type + severity + fix accuracy (0.6) + efficiency (0.4).
    Early-guess penalty: if agent triages with 0 investigations AND gets it wrong, score *= 0.7.
    """
    type_score = _match_bug_type(action, truth)
    sev_score = _match_severity(action, truth)
    fix_score = _match_fix_keywords(action, truth)
    accuracy = 0.3 * type_score + 0.3 * sev_score + 0.4 * fix_score
    efficiency = _efficiency_score(investigations, 3)
    score = 0.6 * accuracy + 0.4 * efficiency
    # Penalize blind guessing: 0 investigations AND low accuracy
    if investigations == 0 and accuracy < 1.0:
        score *= 0.7
    return score


GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}
