"""Learnprint tutor FSM: deterministic instructional phases with durable,
idempotent sessions (W2 of the mega plan).

Design contract:
- The FSM owns ONLY the instructional phase and task provenance. It never
  grades, never invents evidence, and never writes the canonical ledger.
- Transitions are explicit and table-driven (plan phase ORIENT -> ... ->
  COMPLETE, compressible for advanced learners per the teaching protocol).
- State persists as a single versioned JSON document written atomically
  (same-dir temp file, fsync, os.replace), so a crash never corrupts state.
- Every appended event carries a caller-supplied unique event_id; replays of
  the same request are no-ops; conflicting reuse is an error (idempotency).
- Stale writes are rejected via an optimistic revision check.
- Fail closed on malformed/unexpected input: unknown phase, invalid
  transition, invalid task metadata, wrong schema_version.

Python 3.9+ standard library only. No implicit writes: callers pass explicit
paths; nothing here touches Courses/ by default.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1
ENGINE = "learnprint_tutor/1"

PHASES = (
    "ORIENT",
    "EXPLAIN",
    "GUIDED",
    "ATTEMPT",
    "FEEDBACK",
    "TEACH_BACK",
    "TRANSFER",
    "DELAYED_RETRIEVAL",
    "COMPLETE",
)

ALLOWED_TRANSITIONS: Dict[str, set] = {
    "ORIENT": {"EXPLAIN", "GUIDED", "ATTEMPT"},
    "EXPLAIN": {"GUIDED", "ATTEMPT"},
    "GUIDED": {"GUIDED", "ATTEMPT", "EXPLAIN"},
    "ATTEMPT": {"FEEDBACK", "EXPLAIN"},
    "FEEDBACK": {
        "EXPLAIN",
        "TEACH_BACK",
        "ATTEMPT",
        "TRANSFER",
        "DELAYED_RETRIEVAL",
        "COMPLETE",
    },
    "TEACH_BACK": {"TRANSFER", "ATTEMPT", "EXPLAIN"},
    "TRANSFER": {"FEEDBACK"},
    "DELAYED_RETRIEVAL": {"FEEDBACK", "COMPLETE"},
    "COMPLETE": set(),
}

HELP_LEVELS = ("none", "hint", "worked_example", "solution")
TASK_AUTHORS = ("tutor_model", "human_authored", "course_material")
EXITS_SCORED_SAFELY = ("FEEDBACK",)
TASK_REQUIRED_FOR = ("ATTEMPT", "TRANSFER")


class TutorStateError(ValueError):
    """Base error for every deterministic FSM rejection."""


class InvalidTransition(TutorStateError):
    """Requested phase change is not in the transition table."""


class DuplicateEventId(TutorStateError):
    """event_id reuse with a different payload."""


class StaleRevision(TutorStateError):
    """Caller expected an older revision than the stored one."""


class CorruptState(TutorStateError):
    """Document failed schema validation or replay agreement."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initial_state(course_id: str, topic: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a fresh validated session document starting in ORIENT."""
    if not course_id or not isinstance(course_id, str):
        raise TutorStateError("course_id must be a nonempty string")
    if not topic or not isinstance(topic, str):
        raise TutorStateError("topic must be a nonempty string")
    sid = session_id or str(uuid.uuid4())
    now = _now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "session_id": sid,
        "course_id": course_id,
        "topic": topic,
        "phase": "ORIENT",
        "revision": 1,
        "current_task": None,
        "outcome_not_scored": None,
        "events": [
            {
                "rev": 1,
                "event_id": f"{sid}:init",
                "type": "phase",
                "from": None,
                "to": "ORIENT",
                "ts": now,
                "refs": {},
            }
        ],
        "created_at": now,
        "updated_at": now,
        "provenance": {"engine": ENGINE},
    }


def _validate_task(task: Any) -> Dict[str, Any]:
    if not isinstance(task, dict):
        raise TutorStateError("task must be an object")
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip() or len(task_id) > 200:
        raise TutorStateError("task_id must be nonempty text (max 200)")
    if task.get("answer_hidden") is not True:
        raise TutorStateError("T01: attempts require a hidden answer; refusing to open attempt with exposed answer")
    help_level = task.get("help_level", "none")
    if help_level not in HELP_LEVELS:
        raise TutorStateError(f"help_level must be one of {HELP_LEVELS}")
    authored_by = task.get("authored_by")
    if authored_by not in TASK_AUTHORS:
        raise TutorStateError(
            f"task provenance is mandatory: authored_by must be one of {TASK_AUTHORS}"
        )
    fingerprint = task.get("task_fingerprint")
    if fingerprint is not None and (not isinstance(fingerprint, str) or len(fingerprint) > 120):
        raise TutorStateError("task_fingerprint must be text (max 120 chars) when present")
    record: Dict[str, Any] = {
        "task_id": task_id,
        "answer_hidden": True,
        "help_level": help_level,
        "authored_by": authored_by,
    }
    if fingerprint is not None:
        record["task_fingerprint"] = fingerprint
    return record


def validate_state(doc: Any) -> Dict[str, Any]:
    """Strict schema validation; raises CorruptState on any mismatch."""
    if not isinstance(doc, dict):
        raise CorruptState("session document must be a JSON object")
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise CorruptState(
            f"unsupported session schema_version {doc.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    required = ("course_id", "topic")
    for key in required:
        if not isinstance(doc.get(key), str) or not doc[key]:
            raise CorruptState(f"session field {key!r} must be a nonempty string")
    if not isinstance(doc.get("session_id"), str) or not doc["session_id"]:
        raise CorruptState("session_id must be a nonempty string")
    phase = doc.get("phase")
    if phase not in PHASES:
        raise CorruptState(f"unknown phase {phase!r}")
    revision = doc.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise CorruptState("revision must be a positive integer")
    events = doc.get("events")
    if not isinstance(events, list) or not events:
        raise CorruptState("events must be a nonempty list")
    seen_ids = set()
    for event in events:
        if not isinstance(event, dict):
            raise CorruptState("each event must be an object")
        eid = event.get("event_id")
        if not isinstance(eid, str) or not eid or eid in seen_ids:
            raise CorruptState(f"event id missing or duplicated: {eid!r}")
        seen_ids.add(eid)
        if not isinstance(event.get("rev"), int):
            raise CorruptState("event rev must be an integer")
    task = doc.get("current_task")
    if task is not None:
        _validate_task(task)
    if phase == "ATTEMPT" and task is None:
        raise CorruptState("ATTEMPT phase requires a current_task")
    return doc


def replay_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rebuild phase/task from the event log only (crash/replay source of truth)."""
    derived_phase: Optional[str] = None
    derived_task: Optional[Dict[str, Any]] = None
    for event in sorted(events, key=lambda e: e.get("rev", 0)):
        if event.get("type") != "phase":
            raise CorruptState(f"replay: unknown event type {event.get('type')!r}")
        target = event.get("to")
        if target not in PHASES:
            raise CorruptState(f"replay: unknown phase {target!r}")
        derived_phase = target
        if target in ("ATTEMPT", "TRANSFER") and (event.get("refs") or {}).get("task"):
            derived_task = _validate_task(event["refs"]["task"])
        elif target == "COMPLETE":
            derived_task = None
    return {"phase": derived_phase, "current_task": derived_task}


def attempt_independence(
    task: Optional[Dict[str, Any]], not_scored: Optional[Dict[str, Any]] = None
) -> str:
    """Classify the instructional independence of a task attempt.

    Returns INDEPENDENT | ASSISTED | NOT_SCORED | NO_TASK. Never grants or
    denies competency status; the canonical ledger evaluator (rules/
    EVIDENCE.md) stays the single status authority. Answer-visible tasks are
    invalid inputs (T01).
    """
    if task is None:
        return "NO_TASK"
    if not_scored:
        return "NOT_SCORED"
    if task.get("answer_hidden") is not True:
        raise TutorStateError("T01: task answer must stay hidden")
    help_level = task.get("help_level", "none")
    if help_level not in HELP_LEVELS:
        raise TutorStateError(f"help_level must be one of {HELP_LEVELS}")
    if help_level != "none":
        return "ASSISTED"
    return "INDEPENDENT"


def transfer_contract(
    source_task: Optional[Dict[str, Any]], candidate_task: Dict[str, Any]
) -> None:
    """Enforce the fresh, materially-novel transfer contract (T04/T05).

    Conservative by design: ambiguity (missing fingerprints) is failure.
    Raises TutorStateError when the candidate is not a valid novel transfer.
    """
    if not isinstance(candidate_task, dict):
        raise TutorStateError("transfer candidate must be a task object")
    if source_task is None or not isinstance(source_task, dict):
        raise TutorStateError("transfer requires a preceding attempt to transfer from")
    if candidate_task.get("task_id") == source_task.get("task_id"):
        raise InvalidTransition("T04: transfer task must be fresh, not the attempted task")
    source_fp = source_task.get("task_fingerprint")
    candidate_fp = candidate_task.get("task_fingerprint")
    if not candidate_fp or not isinstance(candidate_fp, str):
        raise InvalidTransition("T05: transfer candidate lacks a task_fingerprint; declining")
    if source_fp and candidate_fp.strip().casefold() == source_fp.strip().casefold():
        raise InvalidTransition("T05: transfer fingerprint equals the attempted task; declining")


def _same_request(
    event: Dict[str, Any], to: str, task_id: Optional[str],
    help_level: Optional[str] = None, task_author: Optional[str] = None,
    external_ref: Optional[str] = None,
) -> bool:
    refs = event.get("refs") or {}
    same_task = refs.get("task_id") == task_id
    if refs.get("task") is not None:
        same_task = same_task and (
            task_id is not None
            and (refs["task"].get("help_level") == (help_level or "none"))
            and (refs["task"].get("authored_by") == task_author)
        )
    if refs.get("external_ref") is not None:
        same_task = same_task and refs.get("external_ref") == external_ref
    return event.get("to") == to and same_task


def apply_transition(
    doc: Dict[str, Any],
    to_phase: str,
    event_id: str,
    task_id: Optional[str] = None,
    help_level: str = "none",
    reason: Optional[str] = None,
    expect_rev: Optional[int] = None,
    now: Optional[str] = None,
    task_author: Optional[str] = None,
    task_fingerprint: Optional[str] = None,
    external_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Pure transition applier; returns a NEW session document.

    Raises TutorStateError subclasses on invalid, duplicate-conflicting or
    stale requests. Never mutates the input document.
    """
    validate_state(doc)
    if to_phase not in PHASES:
        raise InvalidTransition(f"unknown target phase {to_phase!r}")
    if not isinstance(event_id, str) or not event_id.strip() or len(event_id) > 240:
        raise TutorStateError("event_id must be nonempty text (max 240)")
    phase = doc["phase"]
    revision = doc["revision"]
    if expect_rev is not None and expect_rev != revision:
        raise StaleRevision(f"stale write: caller expected revision {expect_rev}, state at {revision}")

    for event in doc["events"]:
        if event.get("event_id") == event_id:
            if event.get("type") == "phase" and _same_request(
                event, to_phase, task_id, help_level, task_author, external_ref
            ):
                return doc  # idempotent replay: identical request is a no-op
            raise DuplicateEventId(f"event_id already recorded with a different request: {event_id}")

    if phase == "COMPLETE":
        raise InvalidTransition("session is COMPLETE; start a new session for another cycle")
    if to_phase not in ALLOWED_TRANSITIONS[phase]:
        raise InvalidTransition(f"transition {phase} -> {to_phase} is not allowed")

    new_doc = json.loads(json.dumps(doc))  # deep copy via json (stdlib, no shared mutables)
    new_doc["phase"] = to_phase
    new_revision = revision + 1
    refs: Dict[str, Any] = {}
    resolved_task = new_doc.get("current_task")
    if to_phase in TASK_REQUIRED_FOR:
        if not task_id:
            raise TutorStateError(f"{to_phase} requires an explicit task_id")
        task = _validate_task(
            {
                "task_id": task_id,
                "answer_hidden": True,
                "help_level": help_level,
                "authored_by": task_author,
                "task_fingerprint": task_fingerprint,
            },
        )
        if task_id == (resolved_task or {}).get("task_id"):
            raise InvalidTransition(
                "T04: resuming an already-attempted task is not allowed; open a fresh task"
            )
        stale_ids = set()
        not_scored = new_doc.get("outcome_not_scored") or {}
        if not_scored.get("task_id"):
            stale_ids.add(not_scored["task_id"])
        if task_id in stale_ids:
            raise InvalidTransition(
                "T04: resuming an already-attempted task is not allowed; open a fresh task"
            )
        if to_phase == "TRANSFER":
            if not task.get("task_fingerprint"):
                raise InvalidTransition(
                    "T05: transfer candidate lacks a task_fingerprint; declining ambiguous novelty"
                )
            source = resolved_task or {}
            fingerprint = task["task_fingerprint"]
            if source.get("task_fingerprint") and fingerprint and \
                    source["task_fingerprint"].strip().casefold() == fingerprint.strip().casefold():
                raise InvalidTransition(
                    "T05: transfer task fingerprints must differ from the assisted task"
                )
        refs["task"] = task
        refs["task_id"] = task_id
        new_doc["current_task"] = task
        new_doc["outcome_not_scored"] = None
    elif to_phase in EXITS_SCORED_SAFELY and resolved_task is not None:
        refs["task_id"] = resolved_task.get("task_id")
    elif to_phase == "EXPLAIN" and task_id:
        refs["task_id"] = task_id

    if to_phase == "DELAYED_RETRIEVAL":
        if not isinstance(external_ref, str) or not external_ref.strip() or len(external_ref) > 240:
            raise TutorStateError(
                "delayed retrieval requires an external reference (review/ledger id); "
                "the tutor never fabricates a delayed event"
            )
        refs["external_ref"] = external_ref.strip()[:240]

    confusion = False
    if phase == "ATTEMPT" and to_phase == "EXPLAIN":
        if reason and reason.strip().lower() in ("confusion", "masih gak ngerti", "masih_gak_ngerti"):
            confusion = True
        else:
            raise InvalidTransition("leaving ATTEMPT without evaluation requires reason=confusion")
    if to_phase == "EXPLAIN" and reason and reason.strip() and not confusion:
        refs["reason"] = reason.strip()[:200]
    if confusion:
        new_doc["outcome_not_scored"] = {
            "reason": "confusion_exit",
            "task_id": (new_doc.get("current_task") or {}).get("task_id"),
        }

    if to_phase == "COMPLETE":
        new_doc["current_task"] = None

    new_doc["revision"] = new_revision
    new_doc["events"].append(
        {
            "rev": new_revision,
            "event_id": event_id,
            "type": "phase",
            "from": phase,
            "to": to_phase,
            "ts": now or _now_iso(),
            "refs": refs,
        }
    )
    new_doc["updated_at"] = now or _now_iso()
    validate_state(new_doc)
    return new_doc


def atomic_write_session(path: Path, doc: Dict[str, Any]) -> None:
    """Write the session document atomically: same-dir temp file, fsync, replace."""
    validate_state(doc)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, str(path))
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


def load_session(path: Path) -> Dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_state(doc)
    derived = replay_events(doc["events"])
    if derived["phase"] != doc["phase"]:
        raise CorruptState(
            f"replay mismatch: stored phase {doc['phase']!r} != rebuilt {derived['phase']!r}"
        )
    return doc


def agreed_state(path: Path) -> Dict[str, Any]:
    """Load and confirm the durable phase agrees with the event log (resume)."""
    return load_session(Path(path))


NEXT_ACTION_TEXT = {
    "ORIENT": "Determine your initial goal and constraints, then run a short diagnosis (0-3 probes).",
    "EXPLAIN": "Read the concise explanation and worked example. Ask when something is unclear.",
    "GUIDED": "Complete the guided practice step. Help is visible at this stage, that is normal.",
    "ATTEMPT": "Answer the practice question on your own without help. Write your answer first.",
    "FEEDBACK": "Check your attempt feedback, then decide: repeat the material or continue.",
    "TEACH_BACK": "Explain the mechanism in your own words (you may use an analogy).",
    "TRANSFER": "Work on a new, different problem, without hints.",
    "DELAYED_RETRIEVAL": "Do a scheduled review problem to maintain the skill.",
    "COMPLETE": "Session cycle complete. Check your progress record and next step.",
}

# Explicit opt-in language choice. Keep the English default and return shape
# unchanged for existing host adapters; this is presentation only.
NEXT_ACTION_TEXT_ID = {
    "ORIENT": "Tentukan tujuan belajar dan batasanmu untuk sesi ini.",
    "EXPLAIN": "Baca penjelasan singkat ini dan tanyakan bagian yang belum jelas.",
    "GUIDED": "Kerjakan langkah latihan terbimbing berikut.",
    "ATTEMPT": "Jawab soal latihan ini sendiri tanpa bantuan.",
    "FEEDBACK": "Baca umpan balik untuk jawabanmu.",
    "TEACH_BACK": "Jelaskan kembali mekanismenya dengan kata-katamu sendiri.",
    "TRANSFER": "Selesaikan masalah baru dengan konteks berbeda tanpa petunjuk.",
    "DELAYED_RETRIEVAL": "Kerjakan satu soal ulasan yang sudah dijadwalkan.",
    "COMPLETE": "Periksa catatan kemajuanmu untuk menentukan langkah berikutnya.",
}


def next_action(doc: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
    """Presentation only: one learner-visible next action per phase.

    Language must be explicitly 'en' (backward-compatible default) or 'id'.
    No inference from learner data; this never scores or persists evidence.
    """
    if not isinstance(language, str) or language not in ("en", "id"):
        raise ValueError("unsupported next-action language; choose 'en' or 'id'")
    validate_state(doc)
    phase = doc["phase"]
    messages = NEXT_ACTION_TEXT_ID if language == "id" else NEXT_ACTION_TEXT
    return {
        "phase": phase,
        "learner_action": messages[phase],
        "allowed_next_phases": sorted(ALLOWED_TRANSITIONS[phase]),
        "assistance_next_turn": (
            doc["current_task"]["help_level"] if doc.get("current_task") else None
        ),
        "presentation": "one visible action, no internals dumped on the learner",
    }


# ------------------------------ CLI ------------------------------


def _print(doc: Dict[str, Any]) -> None:
    print(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True))


def cmd_init(a: argparse.Namespace) -> int:
    sid = a.session_id or str(uuid.uuid4())
    doc = initial_state(course_id=a.course_id, topic=a.topic, session_id=sid)
    atomic_write_session(Path(a.file), doc)
    _print(doc)
    return 0


def cmd_show(a: argparse.Namespace) -> int:
    _print(agreed_state(Path(a.file)))
    return 0


def cmd_resume(a: argparse.Namespace) -> int:
    doc = agreed_state(Path(a.file))
    derived = replay_events(doc["events"])
    _print(
        {
            "resumed": True,
            "phase": doc["phase"],
            "replay_phase": derived["phase"],
            "revision": doc["revision"],
            "events": len(doc["events"]),
        }
    )
    return 0


def cmd_replay(a: argparse.Namespace) -> int:
    doc = json.loads(Path(a.file).read_text(encoding="utf-8"))
    validate_state(doc)
    derived = replay_events(doc["events"])
    result = {
        "session_id": doc.get("session_id"),
        "replay_phase": derived["phase"],
        "stored_phase": doc.get("phase"),
        "agreement": derived["phase"] == doc.get("phase"),
        "events_replayed": len(doc.get("events", [])),
    }
    _print(result)
    if not result["agreement"]:
        return 2
    return 0


def cmd_transit(a: argparse.Namespace) -> int:
    doc = agreed_state(Path(a.file))
    if a.answer_shown and a.to_phase == "ATTEMPT":
        raise TutorStateError("T01: --answer-shown cannot be combined with entering ATTEMPT")
    new_doc = apply_transition(
        doc,
        to_phase=a.to_phase,
        event_id=a.event_id,
        task_id=a.task_id,
        help_level=a.help_level,
        reason=a.reason,
        expect_rev=a.expect_rev,
        task_author=a.task_author,
        task_fingerprint=a.task_fingerprint,
        external_ref=a.external_ref,
    )
    atomic_write_session(Path(a.file), new_doc)
    _print(new_doc)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="learnprint_tutor.py",
        description="Deterministic tutor session FSM: explicit phases, durable idempotent state.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    ini = sub.add_parser("init", help="create a new tutor session starting in ORIENT")
    ini.add_argument("--file", required=True, help="explicit session JSON path (no implicit Courses writes)")
    ini.add_argument("--course-id", required=True)
    ini.add_argument("--topic", required=True)
    ini.add_argument("--session-id", default=None)
    ini.set_defaults(func=cmd_init)

    show = sub.add_parser("show", help="load, validate and print the session")
    show.add_argument("--file", required=True)
    show.set_defaults(func=cmd_show)

    res = sub.add_parser("resume", help="confirm durable state agrees with event log after crash")
    res.add_argument("--file", required=True)
    res.set_defaults(func=cmd_resume)

    rep = sub.add_parser("replay", help="rebuild phase from events only; report agreement")
    rep.add_argument("--file", required=True)
    rep.set_defaults(func=cmd_replay)

    tr = sub.add_parser("transit", help="apply one validated phase transition")
    tr.add_argument("--file", required=True)
    tr.add_argument("--to", dest="to_phase", required=True, choices=PHASES)
    tr.add_argument("--event-id", required=True)
    tr.add_argument("--task-id", default=None)
    tr.add_argument("--help-level", default="none", choices=HELP_LEVELS)
    tr.add_argument("--reason", default=None, help="e.g. confusion when leaving ATTEMPT without scoring")
    tr.add_argument("--task-author", default=None, choices=TASK_AUTHORS,
                    help="required task provenance when opening an attempt or transfer")
    tr.add_argument("--task-fingerprint", default=None,
                    help="required for TRANSFER; fingerprints must differ from the assisted task")
    tr.add_argument("--external-ref", default=None,
                    help="required for DELAYED_RETRIEVAL; external review/ledger reference")
    tr.add_argument("--answer-shown", action="store_true", help="disallowed with --to ATTEMPT")
    tr.add_argument("--expect-rev", type=int, default=None, help="reject stale writes unless revision matches")
    tr.set_defaults(func=cmd_transit)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TutorStateError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"NOT_FOUND: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
