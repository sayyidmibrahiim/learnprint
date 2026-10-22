"""Learnprint scheduling subsystem (W4 of the mega plan).

Contract:
- `fixed_v1` reproduces the canonical evaluator's existing interval rule
  exactly (1/3/7/21 with fast retry after a failed delayed retrieval) so
  old courses never change unless adaptive_v2 is explicitly enabled.
- `adaptive_v2` is a deterministic, opt-in experiment. It is prefixed by
  policy_version in every output, is bounded (1..42 days), and a caller
  opts out simply by not asking for it. No update claims to be
  scientifically optimal; it is an experiment with measurable criteria.
- All datetimes must be timezone-aware; naive input fails closed (a pure
  UTC day-add on aware values avoids DST drifting errors).
- Scheduling is PRESENTATION ONLY: due dates never change competency
  status; the canonical evaluator in scripts/learnprint.py stays the
  single authority.

Python 3.9+ standard library only.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

FIXED_V1_INTERVALS = (1, 3, 7, 21)
ADAPTIVE_V2_BOUNDS = (1, 42)  # days
BURDEN_DEFAULT_MAX_PER_DAY = 7


class SchedulerError(ValueError):
    """Fail-closed scheduling rejection."""


def _aware(dt: datetime, field: str) -> datetime:
    if not isinstance(dt, datetime):
        raise SchedulerError(f"{field} must be a datetime")
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise SchedulerError(
            f"{field} must be timezone-aware; naive timestamps are rejected to fail closed"
        )
    return dt


def fixed_v1(passed_delayed: int, failed_latest: bool = False,
             intervals: Sequence[int] = FIXED_V1_INTERVALS) -> int:
    """Canonical fixed schedule. Mirrors the evaluator rule byte for byte:
    interval = 1 when the latest eligible delayed retrieval failed, else
    intervals[min(passed_delayed, len-1)]."""
    if not isinstance(passed_delayed, int) or isinstance(passed_delayed, bool) or passed_delayed < 0:
        raise SchedulerError("passed_delayed must be a non-negative integer")
    if not isinstance(failed_latest, bool):
        raise SchedulerError("failed_latest must be a boolean")
    if not intervals or not all(isinstance(i, int) and i > 0 for i in intervals):
        raise SchedulerError("intervals must be a nonempty list of positive day counts")
    if failed_latest:
        return 1
    return intervals[min(passed_delayed, len(intervals) - 1)]


def due_after(last_eligible: datetime, interval_days: int) -> datetime:
    """Due = instant + interval days, computed in UTC (DST-safe, deterministic)."""
    aware = _aware(last_eligible, "last_eligible").astimezone(timezone.utc)
    if not isinstance(interval_days, int) or isinstance(interval_days, bool) or interval_days != int(interval_days):
        raise SchedulerError("interval_days must be an integer")
    if interval_days <= 0:
        raise SchedulerError("interval_days must be positive")
    return aware + timedelta(days=interval_days)


def delayed_outcome(rubric: Dict[str, Any]) -> Optional[bool]:
    """True/False when a delayed retrieval outcome is scorable, else None.

    A delayed event passes only with concept==2 and application==2, exactly
    like the canonical evaluator. Unknown/missing outcomes are not passes
    and not fails -> None (incomplete history is tolerated for scheduling
    but never credited)."""
    if not isinstance(rubric, dict):
        raise SchedulerError("rubric must be an object")
    concept, application = rubric.get("concept"), rubric.get("application")
    if concept == 2 and application == 2:
        return True
    if concept is None or application is None:
        return None
    return False


def adaptive_v2(
    delayed_events: Sequence[Tuple[datetime, Dict[str, Any]]],
    floor_multiplier: float = 0.5,
) -> Dict[str, Any]:
    """Deterministic opt-in experiment: multiplier based on the two most
    recent eligible delayed outcomes.

    Returns {policy_version, interval_days, multiplier, evaluated, basis}.
    Determinism: identical inputs produce identical outputs; no clock or
    randomness. floor_multiplier/bounds keep it a bounded experiment.
    Callers MUST pre-filter events to eligible delayed retrievals (the
    canonical evaluator owns the retention floor), so this module neither
    duplicates nor bypasses that policy.
    """
    if not isinstance(floor_multiplier, (int, float)) or not (0.1 <= floor_multiplier <= 1.0):
        raise SchedulerError("floor_multiplier must be a number in [0.1, 1.0]")
    scored: List[bool] = []
    for entry in delayed_events:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise SchedulerError("delayed_events entries must be (datetime, rubric) tuples")
        event_date, rubric = entry
        _aware(event_date, "delayed event date")
        outcome = delayed_outcome(rubric)
        if outcome is not None:
            scored.append(outcome)
    recent = scored[-2:]
    if not recent:
        multiplier = 1.0
        basis = "no scorable delayed outcome; keep the fixed cadence"
    elif False in recent:
        multiplier = floor_multiplier
        basis = "recent scorable outcomes include a failure; compress toward retry"
    else:
        consecutive = 0
        for outcome in reversed(scored):
            if outcome:
                consecutive += 1
            else:
                break
        multiplier = min(2.0, 1.0 + 0.25 * consecutive)
        basis = f"{consecutive} consecutive eligible delayed passes in episode tail"
    fallback = fixed_v1(len([s for s in scored if s]), False in recent)
    raw_days = int(round(fallback * multiplier))
    lo, hi = ADAPTIVE_V2_BOUNDS
    interval_days = max(1, min(hi, raw_days))
    return {
        "policy_version": "adaptive_v2",
        "interval_days": interval_days,
        "multiplier": multiplier,
        "evaluated": len(scored),
        "basis": basis,
    }


def select_due(
    scheduled: Sequence[Tuple[datetime, str]],
    now: datetime,
    max_per_day: int = BURDEN_DEFAULT_MAX_PER_DAY,
) -> List[Tuple[datetime, str]]:
    """Deterministic review burden gate: order by (due, key), return the
    head that is due and fits the daily cap. Fail closed on naive times."""
    aware_now = _aware(now, "now")
    checked: List[Tuple[datetime, str]] = []
    for due, key in scheduled:
        if not isinstance(key, str) or not key:
            raise SchedulerError("scheduled key must be a nonempty string")
        checked.append((_aware(due, "due").astimezone(timezone.utc), key))
    if not isinstance(max_per_day, int) or max_per_day < 1:
        raise SchedulerError("max_per_day must be a positive integer")
    ordered = sorted(checked, key=lambda item: (item[0], item[1]))
    return [(due, key) for due, key in ordered if due <= aware_now][:max_per_day]


def schedule_from_policy(
    demonstrated: bool,
    last_eligible_date: Optional[datetime],
    passed_delayed: int,
    failed_latest: bool,
    policy_version: str = "fixed_v1",
    delayed_events: Optional[Sequence[Tuple[datetime, Dict[str, Any]]]] = None,
    intervals: Sequence[int] = FIXED_V1_INTERVALS,
) -> Dict[str, Any]:
    """Single entry point. fixed_v1 is the default and matches historical
    behavior; adaptive_v2 requires an explicit opt-in."""
    if not isinstance(policy_version, str):
        raise SchedulerError("policy_version must be a string")
    if policy_version == "fixed_v1":
        if not demonstrated:
            return {"policy_version": "fixed_v1", "interval_days": None, "due_at": None}
        if last_eligible_date is None:
            raise SchedulerError("demonstrated competencies require a last_eligible_date")
        days = fixed_v1(passed_delayed, failed_latest, intervals)
        due = due_after(last_eligible_date, days)
        return {
            "policy_version": "fixed_v1",
            "interval_days": days,
            "due_at": due.isoformat(),
        }
    if policy_version == "adaptive_v2":
        if not demonstrated:
            return {"policy_version": "adaptive_v2", "interval_days": None, "due_at": None}
        if last_eligible_date is None:
            raise SchedulerError("demonstrated competencies require a last_eligible_date")
        result = adaptive_v2(delayed_events or [])
        due = due_after(last_eligible_date, result["interval_days"])
        merged = dict(result)
        merged["due_at"] = due.isoformat()
        return merged
    raise SchedulerError(f"unsupported scheduling policy_version {policy_version!r}")
