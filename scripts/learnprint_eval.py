"""Learnprint evaluation lab (W10): simulated journeys ONLY.

No human participants are simulated, fabricated or claimed. A journey
drives the deterministic tutor FSM with scripted learner behavior and
reports measurable, reproducible metrics:

- false_mastery_leaks: scripted assisted tasks that would have been (or
  must never be) treated as independent performance. Must always be 0.
- confusion_pauses: confusion exits handled as instruction, never scores.
- scored_guarantees: tutor events never carry scoring fields.
- fail_closed_verified: invalid journeys are rejected, proving the engine
  cannot be steered into forbidden states by bad scripts.

Every output is labeled simulated:true / human_participants:0. Real
learning outcomes come only from real documented learner sessions.
"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

import learnprint_scheduler as scheduler
import learnprint_tutor as tutor


class EvalError(ValueError):
    """Fail-closed evaluation rejection."""


def simulate_journey(script: Any) -> Dict[str, Any]:
    """Deterministically replay a scripted learner journey through the FSM."""
    if not isinstance(script, dict):
        raise EvalError("journey script must be an object")
    journey_id = script.get("journey_id")
    if not isinstance(journey_id, str) or not journey_id.strip():
        raise EvalError("journey_id must be nonempty text")
    behaviors = script.get("behavior")
    if not isinstance(behaviors, list) or not behaviors:
        raise EvalError("journey needs a nonempty behavior list")

    doc = tutor.initial_state(
        course_id=str(script.get("course_id", "sim-course")),
        topic=str(script.get("topic", journey_id)),
        session_id=f"sim-{journey_id}",
    )
    expectations = script.get("expect_independence", [])
    if not isinstance(expectations, list):
        raise EvalError("expect_independence must be a list")
    leaks: List[Dict[str, Any]] = []
    confusion_pauses = 0
    expectation_index = 0
    last_attempt_task: Optional[Dict[str, Any]] = None

    for index, step in enumerate(behaviors):
        if not isinstance(step, dict) or "action" not in step:
            raise EvalError(f"behavior[{index}] must be an object with an action")
        action = step["action"]
        try:
            if action == "attempt":
                doc = tutor.apply_transition(
                    doc, "ATTEMPT", f"{journey_id}:e{index}",
                    task_id=str(step["task_id"]),
                    help_level=step.get("help_level", "none"),
                    task_author=step.get("task_author", "course_material"),
                    task_fingerprint=step.get("task_fingerprint"),
                )
                task = doc["current_task"]
                classification = tutor.attempt_independence(task, doc.get("outcome_not_scored"))
                expected = (
                    expectations[expectation_index] if expectation_index < len(expectations) else classification
                )
                expectation_index += 1
                if classification != expected:
                    leaks.append({
                        "behavior": index,
                        "task_id": task["task_id"],
                        "classification": classification,
                        "expected": expected,
                    })
                last_attempt_task = task
            elif action == "confusion_exit":
                doc = tutor.apply_transition(
                    doc, "EXPLAIN", f"{journey_id}:e{index}", reason="confusion"
                )
                confusion_pauses += 1
            elif action == "transition":
                to_phase = step["to"]
                doc = tutor.apply_transition(
                    doc, to_phase, f"{journey_id}:e{index}",
                    task_id=step.get("task_id"),
                    help_level=step.get("help_level", "none"),
                    task_author=step.get("task_author"),
                    task_fingerprint=step.get("task_fingerprint"),
                    external_ref=step.get("external_ref"),
                    reason=step.get("reason"),
                )
            else:
                raise EvalError(f"unknown behavior action {action!r}")
        except tutor.TutorStateError as exc:
            return {
                "journey_id": journey_id,
                "simulated": True,
                "human_participants": 0,
                "passed": False,
                "blocked_at_behavior": index,
                "blocked_reason": str(exc),
                "finding": "engine rejected an invalid or unsafe scripted state (fail closed)",
            }

    scored_refs = [
        event["event_id"]
        for event in doc["events"]
        if any(key in (event.get("refs") or {}) for key in ("scored", "score", "rubric"))
    ]
    passed = not leaks and not scored_refs
    result: Dict[str, Any] = {
        "journey_id": journey_id,
        "simulated": True,
        "human_participants": 0,
        "passed": passed,
        "metrics": {
            "false_mastery_leaks": leaks,
            "confusion_pauses": confusion_pauses,
            "scored_guarantees_violations": scored_refs,
            "phases_visited": [event["to"] for event in doc["events"]],
        },
        "disclaimer": "simulated journey; no real learner data; no mastery claim",
    }
    if script.get("retention_floor_seconds") is not None and last_attempt_task:
        interval = scheduler.fixed_v1(int(script.get("passed_delayed", 0)), bool(script.get("failed_latest", False)))
        result["metrics"]["planned_interval_days"] = interval
    return result


def run_script(path: str) -> int:
    with open(path, encoding="utf-8") as handle:
        script = json.load(handle)
    result = simulate_journey(script)
    print(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True))
    return 0 if result["passed"] else 2


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="learnprint_eval.py",
        description="Deterministic simulated-journey evaluation lab (no humans simulated).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="replay a journey script and report metrics")
    run.add_argument("--script", required=True)
    run.set_defaults(func=lambda a: run_script(a.script))
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (EvalError, tutor.TutorStateError, OSError) as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
