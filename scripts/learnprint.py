#!/usr/bin/env python3
"""Learnprint local validator/record keeper. Python stdlib only; no network or grading AI."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"unknown", "emerging", "demonstrated", "retention_due", "maintained", "needs_review"}
ASSESSMENT = {"unassessed", "provisional", "assessed"}
ORIGINS = {"observed_task", "self_report", "source_document"}
VERIFICATIONS = {"observed", "reported", "independently_checked", "unverified"}
HELP = {"none", "hint", "worked_example", "solution"}
TYPES = {"recognition", "causal_explanation", "independent_application", "novel_transfer", "delayed_retrieval", "debugging", "decision", "confirmation", "correction"}
DEMO_TYPES = {"independent_application", "novel_transfer", "delayed_retrieval"}
GRADER_SOURCES = {"agent", "learner", "third_party"}
TIER_BASIS = {"provisional", "learner_confirmed", "substantiated"}
SOURCE_STATUSES = {"verified", "UNVERIFIED", "learner-reported", "agent-generated", "unknown"}
_COURSE_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, obj, overwrite=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise ValueError(f"Refusing to overwrite {path}")
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_profile(p):
    errs = []
    for k in ("schema_version", "profile_id", "assessment_status", "public_template", "evidence_quality", "observed_claims", "evidence", "instruction_defaults"):
        if k not in p: errs.append("missing " + k)
    if errs: return errs
    if p["schema_version"] != "1.0": errs.append("unsupported schema_version")
    if p["assessment_status"] not in ASSESSMENT: errs.append("invalid assessment_status")
    if p["evidence_quality"] not in {"limited", "moderate", "strong"}: errs.append("invalid evidence_quality")
    if not isinstance(p["public_template"], bool): errs.append("public_template must be boolean")
    if not isinstance(p["instruction_defaults"], dict): errs.append("instruction_defaults must be object")
    if not isinstance(p["evidence"], list) or not isinstance(p["observed_claims"], list):
        return errs + ["evidence and observed_claims must be arrays"]
    ids = set()
    for e in p["evidence"]:
        if not isinstance(e, dict): errs.append("evidence entry not object"); continue
        for x in ("id", "description", "source"):
            if not isinstance(e.get(x), str) or not e[x].strip(): errs.append("bad evidence " + x)
        if e.get("origin") not in ORIGINS: errs.append("invalid evidence origin")
        if e.get("verification") not in VERIFICATIONS: errs.append("invalid verification")
        if e.get("origin") == "self_report" and e.get("verification") in {"observed", "independently_checked"}:
            errs.append("self_report cannot be upgraded to observed without a task")
        if e.get("id") in ids: errs.append("duplicate evidence id")
        ids.add(e.get("id"))
    cids = set()
    for c in p["observed_claims"]:
        if not isinstance(c, dict): errs.append("claim entry not object"); continue
        if c.get("id") in cids: errs.append("duplicate claim id")
        cids.add(c.get("id"))
        if c.get("category") not in {"observed", "reported_preference", "hypothesis"}: errs.append("invalid claim category")
        if not isinstance(c.get("claim"), str) or not c["claim"].strip(): errs.append("claim missing statement")
        if not c.get("evidence_ids") or not isinstance(c["evidence_ids"], list): errs.append("claim missing evidence ids")
        else:
            for ref in c["evidence_ids"]:
                if ref not in ids: errs.append(f"claim missing linked evidence: {ref}")
        if c.get("category") == "observed":
            for ref in c.get("evidence_ids", []):
                matched = next((e for e in p["evidence"] if e.get("id") == ref), {})
                if matched.get("origin") == "self_report": errs.append(f"observed claim {c.get('id')} backed by self-report")
    if p["assessment_status"] == "assessed" and not p["observed_claims"]:
        errs.append("assessed profile requires evidence-linked claims")
    if p["public_template"] and p["assessment_status"] == "assessed":
        errs.append("public founder template must not claim assessed learner-specific best method")
    return errs


def validate_topic(p):
    errs=[]
    for k in ("schema_version", "topic_id", "goal", "learning_scope", "syllabus"):
        if k not in p: errs.append("missing " + k)
    if errs: return errs
    if p["schema_version"] != "1.0": errs.append("unsupported schema_version")
    ids=set()
    for x in p["learning_scope"]:
        if x.get("status") not in STATUSES: errs.append("bad competency status")
        if not x.get("id") or x["id"] in ids: errs.append("bad/duplicate competency id")
        ids.add(x.get("id"))
    if "sources" in p:
        if not isinstance(p["sources"], list): errs.append("sources must be array")
        else:
            for s in p["sources"]:
                if not isinstance(s, dict): errs.append("source entry not object"); continue
                if s.get("status") not in SOURCE_STATUSES:
                    errs.append("source entry requires status in verified/UNVERIFIED/learner-reported/agent-generated/unknown")
    return errs


def events_read(path):
    if not path.exists(): return []
    out=[]
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: item=json.loads(line)
        except json.JSONDecodeError as e: raise ValueError(f"events.jsonl line {lineno}: {e}")
        out.append(item)
    return out


def _write_all(fd, data: bytes) -> None:
    """os.write() may perform a SHORT write. Loop until all bytes are out."""
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        if n <= 0:
            raise OSError("os.write returned no progress")
        view = view[n:]


def append_event_line(path, line: str, durable: bool = True) -> None:
    """Crash-safe single-line append to a JSONL ledger.

    Payload + trailing newline go out as ONE write so an interrupted append
    cannot produce a record without its terminator.
    """
    path = Path(path)
    payload = (line + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        _write_all(fd, payload)
        if durable:
            os.fsync(fd)
    finally:
        os.close(fd)


def ledger_diagnose(path, workspace_root=None):
    """READ-ONLY diagnostic. Never mutates. Returns a damage report.

    Triage data for humans and `course validate` ONLY — its output must
    never feed progress(), reports, scheduling, or any mutation.
    """
    path = Path(path)
    if not path.exists():
        initialized = (workspace_root is not None
                       and (Path(workspace_root) / ".learnprint").exists())
        return {"status": "absent", "path": str(path), "records": 0,
                "damage": [],
                "absent_kind": ("missing-expected" if initialized
                                else "workspace-not-initialized")}
    raw = path.read_bytes()
    damage = []
    records = 0
    offset = 0
    for line_no, raw_line in enumerate(raw.split(b"\n"), 1):
        stripped = raw_line.strip()
        if stripped:
            try:
                json.loads(stripped.decode("utf-8"))
                records += 1
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                damage.append({
                    "line_no": line_no,
                    "byte_offset": offset,
                    "reason": str(exc),
                    "raw_bytes_preserved": True,
                    "is_truncated_tail": not raw.endswith(b"\n") and line_no == raw.count(b"\n") + 1,
                })
        offset += len(raw_line) + 1
    return {
        "status": "damaged" if damage else "ok",
        "path": str(path),
        "records": records,
        "damage": damage,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def ledger_read_trusted(path, workspace_root=None):
    """STRICT read for authoritative consumers (progress, reports, scheduling).

    Three layers: presence (missing-expected raises LedgerMissing; 0-byte
    file is a legitimate empty ledger), syntax + validate_event() schema
    (valid JSON that is not a valid event raises LedgerDamage), uniqueness
    (duplicate event_id raises LedgerDamage). Callers MUST NOT catch these
    and continue with partial data.
    """
    path = Path(path)
    if not path.exists():
        initialized = (workspace_root is not None
                       and (Path(workspace_root) / ".learnprint").exists())
        if initialized:
            raise LedgerMissing(f"expected evidence ledger absent: {path}")
        raise WorkspaceNotInitialized(
            f"no workspace at {workspace_root}; run course init first")
    raw = path.read_bytes()
    if not raw.strip():
        return []
    events = []
    seen_ids = set()
    offset = 0
    for line_no, raw_line in enumerate(raw.split(b"\n"), 1):
        stripped = raw_line.strip()
        if stripped:
            try:
                record = json.loads(stripped.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise LedgerDamage(f"ledger {path} line {line_no} (byte {offset}): {exc}")
            schema_error = validate_event(record)
            if schema_error:
                raise LedgerDamage(f"ledger {path} line {line_no} (byte {offset}): "
                                   f"schema: {schema_error}")
            eid = record.get("event_id")
            if eid in seen_ids:
                raise LedgerDamage(f"ledger {path} line {line_no} (byte {offset}): "
                                   f"duplicate event_id: {eid!r}")
            seen_ids.add(eid)
            events.append(record)
        offset += len(raw_line) + 1
    return events


def ledger_repair_truncate_partial_tail(path):
    """EXPLICIT non-destructive repair for a truncated final record only.

    Allocates its own immutable uniquely-named backup
    (<name>.bak.<UTC-ts>.<sha8>); refuses if that name exists. Audit entry
    (pre/post SHA256) is appended via the durable locked primitive.
    """
    path = Path(path)
    report = ledger_diagnose(path)
    if report["status"] != "damaged":
        return report
    tail = [d for d in report["damage"] if d["is_truncated_tail"]]
    others = [d for d in report["damage"] if not d["is_truncated_tail"]]
    if others:
        raise LedgerDamage(
            f"ledger {path} line {others[0]['line_no']}: "
            f"{len(others)} damaged record(s) that are not a truncated tail; "
            "manual review required")
    if len(tail) != 1:
        raise LedgerDamage(f"ledger {path}: multiple damaged tail records; "
                           "manual review required")

    raw = path.read_bytes()
    cut = tail[0]["byte_offset"]
    sha8 = hashlib.sha256(raw).hexdigest()[:8]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.parent / f"{path.name}.bak.{stamp}.{sha8}"
    if backup_path.exists():
        raise LedgerDamage(f"ledger {path}: backup {backup_path.name} already "
                           "exists; refusing to overwrite a previous backup")
    with open(backup_path, "wb") as fh:
        fh.write(raw)
    with open(path, "r+b") as fh:
        fh.truncate(cut)
    log = {
        "repaired_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "original_sha256": report["sha256"],
        "backup_path": str(backup_path),
        "backup_sha256": hashlib.sha256(raw).hexdigest(),
        "repaired_sha256": hashlib.sha256(raw[:cut]).hexdigest(),
        "removed_byte_offset": cut,
        "removed_line_no": tail[0]["line_no"],
        "removed_reason": "truncated tail from interrupted append",
        "raw_removed_bytes": raw[cut:].hex(),
    }
    append_event_line(path.parent / "recovery-log.jsonl",
                      json.dumps(log, ensure_ascii=False), durable=True)
    return ledger_diagnose(path)


def validate_event(e):
    errs=[]
    for key in ("event_id", "date", "topic_id", "competency_id", "task_type", "observed_answer", "help_level", "rubric", "feedback", "grader", "evidence_origin"):
        if key not in e: errs.append("missing event."+key)
    if errs: return errs
    if e["task_type"] not in TYPES: errs.append("invalid event.task_type")
    if e["help_level"] not in HELP: errs.append("invalid event.help_level")
    if e["grader"] not in {"ai_reviewed", "human_reviewed", "not_graded"}: errs.append("invalid event.grader")
    if e["evidence_origin"] not in {"observed_response", "self_report"}: errs.append("invalid event origin")
    if not isinstance(e["observed_answer"], str) or not e["observed_answer"].strip(): errs.append("missing actual observed answer")
    if not isinstance(e["rubric"], dict): errs.append("rubric must be object")
    else:
        for k in ("concept", "mechanism", "application", "transfer"):
            if e["rubric"].get(k) not in (0,1,2,None): errs.append("invalid rubric."+k)
    try:
        d=dt.datetime.fromisoformat(e["date"])
        if d.tzinfo is None: errs.append("event timestamp must have timezone")
    except (ValueError, TypeError): errs.append("invalid timestamp")
    if e.get("is_synthetic_example", False) and e.get("grader") == "human_reviewed":
        # fixtures are allowed but excluded from real scoring
        pass
    # Optional provenance linkage fields: validated when present, never required
    # (legacy events predate them). verified_by is informational metadata only
    # and is NEVER used for tiering (see evidence_basis).
    if "course_id" in e and not isinstance(e["course_id"], str):
        errs.append("course_id must be string")
    elif isinstance(e.get("course_id"), str) and not _COURSE_ID_RE.match(e["course_id"]):
        errs.append("course_id must be UUIDv4")
    if "grader_source" in e and e["grader_source"] not in GRADER_SOURCES:
        errs.append("invalid event.grader_source")
    for link in ("confirms_event_id", "corrects_event_id", "corroborates_event_id"):
        if link in e and (not isinstance(e[link], str) or not e[link].strip()):
            errs.append(f"{link} must be a non-empty event id")
    if e.get("task_type") == "confirmation" and not e.get("confirms_event_id"):
        errs.append("confirmation requires confirms_event_id")
    if e.get("task_type") == "correction" and not e.get("corrects_event_id"):
        errs.append("correction requires corrects_event_id")
    return errs


def is_observed_unassisted(e):
    """Pure predicate: event is usable demonstration evidence (provisional basis).

    Grader labels gate nothing. confirmation/correction events are linkage
    metadata, not demonstration evidence.
    """
    return (e.get("help_level") == "none"
            and e.get("evidence_origin") == "observed_response"
            and e.get("rubric") is not None
            and e.get("task_type") in DEMO_TYPES)


def evidence_basis(cycle_events, ledger):
    """Derive claim strength from linked acknowledgement/corroboration.

    The validator computes this; recorders never set it. verified_by strings
    are ignored. See plan Step 1.1a.
    """
    if not cycle_events:
        return "provisional"
    ids = {e["event_id"] for e in cycle_events}
    course_id = cycle_events[0].get("course_id")
    comp_id = cycle_events[0].get("competency_id")
    confirmed = any(
        e.get("task_type") == "confirmation"
        and e.get("confirms_event_id") in ids
        and e.get("evidence_origin") == "observed_response"
        for e in ledger
    )
    # Corroboration compares against the TARGET's source, not the whole
    # cycle's: a linked second review from a different source than the
    # reviewed event counts even when both belong to the same cycle.
    # (Comparing against the whole cycle would make substantiation
    # unreachable, since a valid corroborator is itself cycle evidence.)
    by_id = {e.get("event_id"): e for e in ledger if isinstance(e, dict)}
    corroborated = any(
        e.get("task_type") in DEMO_TYPES
        and e.get("corroborates_event_id") in ids
        and e.get("course_id") == course_id and course_id is not None
        and e.get("competency_id") == comp_id
        and e.get("rubric") is not None
        and e.get("help_level") == "none"
        and e.get("evidence_origin") == "observed_response"
        and e.get("grader_source") is not None
        and e.get("grader_source") != (by_id.get(e.get("corroborates_event_id")) or {}).get("grader_source")
        for e in ledger
    )
    if corroborated:
        return "substantiated"
    if confirmed:
        return "learner_confirmed"
    return "provisional"


RETENTION_POLICY = {"min_elapsed_hours": 20, "intervals_days": [1, 3, 7, 21]}


class LedgerDamage(ValueError):
    """Raised when events.jsonl cannot be parsed completely."""


class LedgerMissing(ValueError):
    """Raised when an expected evidence ledger is absent."""


class WorkspaceNotInitialized(ValueError):
    """Raised when no workspace exists at the given root."""


class LedgerReferenceError(ValueError):
    """Raised when an event references an unresolvable course/topic/competency
    or a linkage target absent from the snapshot."""


def _parse_dt(s):
    """Parse ISO datetime, always timezone-aware.

    Handles 'Z' suffix for Python 3.9 compatibility (fromisoformat only
    supports 'Z' natively from Python 3.11+).
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)


def load_retention_policy(courses_root=None):
    """Merge user-tunable policy from Courses/.learnprint/config.json over defaults.

    Changing the policy re-evaluates state without rewriting evidence.
    """
    policy = {"min_elapsed_hours": RETENTION_POLICY["min_elapsed_hours"],
              "intervals_days": list(RETENTION_POLICY["intervals_days"])}
    if courses_root is not None:
        cfg = Path(courses_root) / ".learnprint" / "config.json"
        if cfg.exists():
            try:
                user = json.loads(cfg.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return policy
            if isinstance(user.get("min_elapsed_hours"), (int, float)) and user["min_elapsed_hours"] > 0:
                policy["min_elapsed_hours"] = user["min_elapsed_hours"]
            if isinstance(user.get("intervals_days"), list) and user["intervals_days"]:
                policy["intervals_days"] = list(user["intervals_days"])
    return policy


def _validate_references(topic, topic_events, ledger_ids):
    """Fail closed on unresolvable references (plan Step 4.4/C1)."""
    scope_ids = {c["id"] for c in topic.get("learning_scope", [])}
    for e in topic_events:
        if e.get("competency_id") not in scope_ids:
            raise LedgerReferenceError(
                f"event {e.get('event_id')!r} references unknown competency "
                f"{e.get('competency_id')!r} for topic {topic.get('topic_id')!r}")
    for e in topic_events:
        for link in ("confirms_event_id", "corrects_event_id", "corroborates_event_id"):
            target = e.get(link)
            if target is not None and target not in ledger_ids:
                raise LedgerReferenceError(
                    f"event {e.get('event_id')!r}: dangling {link} {target!r}")


def _evaluate_competency(c, ev_sorted, ledger, now, policy):
    """Single canonical evaluator. Returns (status, detail).

    ev_sorted: this competency's schema-valid events, sorted by
    (_parse_dt(date), event_id). ledger: full validated snapshot (basis
    linkage). now: timezone-aware datetime. policy: retention policy dict.
    """
    corrections = {}
    for x in ledger:
        if (x.get("task_type") == "correction" and x.get("corrects_event_id")
                and isinstance(x.get("rubric"), dict)):
            corrections[x["corrects_event_id"]] = x["rubric"]

    def rub(x):
        return corrections.get(x["event_id"], x.get("rubric") or {})

    independent = [x for x in ev_sorted if is_observed_unassisted(x)]
    if not ev_sorted:
        return ("unknown", {"app_ok": False, "transfer_ok": False,
                            "delayed_pass": False, "basis": "provisional",
                            "cycle_start": None, "fresh_due_at": None,
                            "interval_days": None,
                            "latest": {"independent_application": None,
                                       "novel_transfer": None,
                                       "delayed_retrieval": None}})

    latest = {"independent_application": None,
              "novel_transfer": None, "delayed_retrieval": None}
    for x in reversed(independent):
        if latest[x["task_type"]] is None:
            latest[x["task_type"]] = x
        if all(latest.values()):
            break

    latest_app = latest["independent_application"]
    latest_transfer = latest["novel_transfer"]
    latest_delayed = latest["delayed_retrieval"]
    app_ok = (latest_app is not None and rub(latest_app).get("application") == 2)
    transfer_ok = (latest_transfer is not None
                   and rub(latest_transfer).get("transfer") == 2
                   and (latest_app is None
                        or _parse_dt(latest_transfer["date"]) >= _parse_dt(latest_app["date"])))
    demonstrated = app_ok and transfer_ok

    cycle_start = (max(_parse_dt(latest_app["date"]), _parse_dt(latest_transfer["date"]))
                   if demonstrated else None)
    delayed_pass = False
    if not demonstrated:
        status = "emerging"
    elif latest_delayed is None or _parse_dt(latest_delayed["date"]) < cycle_start:
        status = "demonstrated"
    elif (rub(latest_delayed).get("concept") == 2
          and rub(latest_delayed).get("application") == 2):
        elapsed = _parse_dt(latest_delayed["date"]) - cycle_start
        if elapsed < dt.timedelta(hours=policy["min_elapsed_hours"]):
            status = "demonstrated"
        else:
            status = "maintained"
            delayed_pass = True
    else:
        status = "needs_review"

    fresh_due, interval_days = None, None
    if demonstrated:
        passed_delayed = sum(
            1 for e in independent
            if e["task_type"] == "delayed_retrieval"
            and _parse_dt(e["date"]) >= cycle_start
            and rub(e).get("concept") == 2
            and rub(e).get("application") == 2
            and (_parse_dt(e["date"]) - cycle_start).total_seconds()
                >= policy["min_elapsed_hours"] * 3600)
        failed_latest = (
            latest_delayed is not None
            and _parse_dt(latest_delayed["date"]) >= cycle_start
            and (rub(latest_delayed).get("concept") != 2
                 or rub(latest_delayed).get("application") != 2))
        intervals = policy["intervals_days"]
        interval_days = 1 if failed_latest else intervals[min(passed_delayed, 3)]
        last_eligible = independent[-1]
        fresh_due = _parse_dt(last_eligible["date"]) + dt.timedelta(days=interval_days)

    if status in {"demonstrated", "maintained"} and fresh_due is not None and fresh_due <= now:
        status = "retention_due"

    basis = evidence_basis(independent, ledger) if demonstrated else "provisional"
    return (status, {"app_ok": app_ok, "transfer_ok": transfer_ok,
                     "delayed_pass": delayed_pass, "basis": basis,
                     "cycle_start": cycle_start.isoformat() if cycle_start else None,
                     "fresh_due_at": fresh_due.isoformat() if fresh_due else None,
                     "interval_days": interval_days,
                     "latest": {k: (v["event_id"] if v else None)
                                for k, v in latest.items()}})


def progress(topic, events, now=None, policy=None, registry=None):
    """Evidence-derived progress over one canonical evaluation per competency."""
    now = now or dt.datetime.now(dt.timezone.utc)
    policy = policy or RETENTION_POLICY
    ledger = events
    ledger_ids = {e.get("event_id") for e in ledger if isinstance(e, dict)}
    by_comp = {}
    for e in ledger:
        if e.get("topic_id") != topic.get("topic_id") or e.get("is_synthetic_example"):
            continue
        if validate_event(e):
            continue
        by_comp.setdefault(e["competency_id"], []).append(e)
    _validate_references(topic, [e for v in by_comp.values() for e in v], ledger_ids)
    if registry is not None:
        course_ids = {c.get("course_id") for c in registry.get("courses", [])}
        legacy_topics = {c.get("topic_id") for c in registry.get("courses", [])}
        for v in by_comp.values():
            for e in v:
                cid = e.get("course_id")
                if cid is not None and cid not in course_ids and e.get("topic_id") not in legacy_topics:
                    raise LedgerReferenceError(
                        f"event {e.get('event_id')!r} references unknown course {cid!r}")

    results = []
    for c in topic.get("learning_scope", []):
        ev = sorted(by_comp.get(c["id"], []),
                    key=lambda x: (_parse_dt(x["date"]), x["event_id"]))
        status, detail = _evaluate_competency(c, ev, ledger, now, policy)
        results.append({
            "id": c["id"], "name": c["name"], "status": status,
            "basis": detail["basis"],
            "observations": len(ev),
            "independent_pass_application": detail["app_ok"],
            "independent_pass_transfer": detail["transfer_ok"],
            "delayed_pass": detail["delayed_pass"],
            "due_at": detail["fresh_due_at"],
            "interval_days": detail["interval_days"],
        })

    denominator = len(results)
    eligible = sum(x["status"] in {"demonstrated", "maintained", "retention_due"}
                   for x in results)
    maintained = sum(x["status"] == "maintained" for x in results)
    basis_counts = {}
    for x in results:
        basis_counts[x["basis"]] = basis_counts.get(x["basis"], 0) + 1
    return {
        "topic_id": topic["topic_id"],
        "bounded_competencies": denominator,
        "observed_immediate_coverage_percent": round(eligible / denominator * 100, 1) if denominator else None,
        "observed_maintained_percent": round(maintained / denominator * 100, 1) if denominator else None,
        "coverage_basis": basis_counts,
        "important_note": "States reflect agent-graded observed responses unless basis says otherwise. Provisional states guide learning; they are not proof of externally verified mastery.",
        "competencies": results,
    }


def resolve_effective_profile(local_path):
    """Profile-first personalization (plan Step 2.1).

    Returns (profile_dict, source) where source is "local" or
    "founder_fallback:<reason>". An unassessed local profile NEVER overrides
    the founder fallback for teaching preferences; missing/invalid profiles
    fall back with the reason noted. Reading a file works on every host.
    """
    local_path = Path(local_path)
    if local_path.exists():
        try:
            p = load(local_path)
        except (ValueError, OSError):
            p = None
        if isinstance(p, dict) and not validate_profile(p):
            if p.get("assessment_status") in {"assessed", "provisional"}:
                return p, "local"
            return load(ROOT / "profiles/founder-default.json"), \
                "founder_fallback_until_assessed"
        reason = "invalid" if p is not None else "unreadable"
        return load(ROOT / "profiles/founder-default.json"), f"founder_fallback_{reason}"
    return load(ROOT / "profiles/founder-default.json"), "founder_fallback_missing"


def cmd_validate(a):
    p=load(a.profile)
    err=validate_profile(p)
    if a.topic: err.extend(validate_topic(load(a.topic)))
    if a.events:
        for i,e in enumerate(events_read(Path(a.events)),1): err.extend(f"event {i}: {x}" for x in validate_event(e))
    print("VALID" if not err else "INVALID\n"+"\n".join(err))
    return 0 if not err else 2


def cmd_init(a):
    path=Path(a.workspace).expanduser().resolve()
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Nonempty workspace; refuse to overwrite: {path}")
    path.mkdir(parents=True, exist_ok=True)
    for name, rel in (("learner/profile.json","learner-profile-starter.json"),("reviews.json","review-queue.json")):
        dest=path/name; dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/"templates"/rel,dest)
    dump(path/"manifest.json", {"schema_version":"1.0","active_topic":None,
        "profile_path":"learner/profile.json","events_path":"events.jsonl",
        "reviews_path":"reviews.json", "topics_dir":"topics",
        "profile_priority":"local assessed profile > public founder fallback; never publish private state"})
    (path/"topics").mkdir()
    (path/"events.jsonl").write_text("",encoding="utf-8")
    (path/"HANDOFF.md").write_text("# Learnprint handoff\n\nNo verified completed learning events. Next: assessment or select a topic.\n",encoding="utf-8")
    print(f"CREATED private workspace: {path}")
    return 0


def cmd_generate(a):
    w=Path(a.workspace).expanduser().resolve()
    p=load(w/"learner/profile.json")
    err=validate_profile(p)
    if err: raise ValueError("Invalid local profile: "+"; ".join(err))
    if p["public_template"] or p["assessment_status"] != "assessed":
        raise ValueError("Personal skill generation requires a local assessed non-public profile")
    if (len(p["observed_claims"]) < 2 or
        sum(e.get("origin") == "observed_task" for e in p["evidence"]) < 2 or
        not any(c.get("category") == "observed" for c in p["observed_claims"])):
        raise ValueError("Need >=2 claims, >=2 observed-task entries and >=1 observation-backed claim")
    if not a.approve:
        raise ValueError("Explicit local file write approval required: --approve")
    dest=w/".agents/skills/learnprint-personal"
    if dest.exists(): raise ValueError(f"Will not overwrite existing personal skill: {dest}")
    (dest/"references").mkdir(parents=True)
    (dest/"SKILL.md").write_text("""---
name: learnprint-personal
description: Apply the assessed learner's private evidence-linked teaching preferences and topic-specific tests to any learning request. Use for personalized study, practice, review, and progress tracking.
license: MIT
---

# Learnprint Personal (local)

1. Read `references/profile.json` and `references/TEACHING.md` before teaching.
2. This profile overrides the public founder defaults **only for this learner and only locally**.
3. Distinguish observed performance, reported preferences, hypothesis, and unknown. Re-test competence on each new topic.
4. Teach with accurate close analogies (and limits), functional diagrams, concrete examples, technical mechanism, guided hands-on, independent transfer and spaced retrieval.
5. Record evidence and track bounded competencies; do not claim fixed learning styles or whole-subject permanent mastery.
6. Do not publish learner data or write outside the approved workspace.
""", encoding="utf-8")
    shutil.copyfile(w/"learner/profile.json",dest/"references/profile.json")
    shutil.copyfile(ROOT/"protocols/TEACHING.md",dest/"references/TEACHING.md")
    shutil.copyfile(ROOT/"protocols/REVIEW.md",dest/"references/REVIEW.md")
    print(f"GENERATED standalone personal skill: {dest}; not installed globally, not pushed")
    return 0


def cmd_new_topic(a):
    w=Path(a.workspace).expanduser().resolve()
    if not (w/"manifest.json").exists(): raise ValueError("Initialize workspace first")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", a.topic): raise ValueError("topic ID must be lower-case kebab-case")
    if not a.approve: raise ValueError("Explicit local write approval required: --approve")
    scope=[]
    for raw in a.competency:
        if ":" not in raw: raise ValueError("--competency must be id:observable outcome")
        cid,label=raw.split(":",1)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",cid) or not label.strip():
            raise ValueError("Invalid competency slug/name")
        scope.append({"id":cid,"name":label.strip(),"status":"unknown","evidence_ids":[],"due_at":None})
    if len({x["id"] for x in scope}) != len(scope):raise ValueError("duplicate competency id")
    out=w/"topics"/a.topic
    if out.exists():raise ValueError(f"Refusing to overwrite topic: {out}")
    out.mkdir(parents=True)
    payload={"schema_version":"1.0","topic_id":a.topic,"goal":a.goal,
             "assumptions":[],"learning_scope":scope,"syllabus":[],
             "question_parking_lot":[],"sources":[],"last_session":None}
    dump(out/"state.json",payload)
    (out/"map.mmd").write_text("flowchart TD\n    GOAL[\"" + a.goal.replace('"', "'") + "\"]\n",encoding="utf-8")
    (out/"SYLLABUS.md").write_text("# "+a.topic+"\n\nSyllabus awaits learner-specific prerequisites and sourced research.\n",encoding="utf-8")
    (out/"HANDOFF.md").write_text("# Topic handoff\n\nGoal: "+a.goal+"\nNo learning evidence has been recorded yet.\n",encoding="utf-8")
    print(f"CREATED topic: {out} with {len(scope)} scoped competencies; none claimed mastered")
    return 0


def reviews_from_events(topics, events, stored_reviews=None):
    """Derive upcoming spaced checks from the canonical evaluator.

    No cycle logic lives here: due date, interval, and cycle_start are read
    from _evaluate_competency detail, never recomputed. Stored queue entries
    whose cycle_start predates the fresh one are dropped (stale-queue
    elimination). Extra informational fields (topic_id, reason,
    based_on_event, delivery) are kept for backward compatibility.
    """
    ledger = events
    now = dt.datetime.now(dt.timezone.utc)
    out = []
    for topic in topics:
        by_comp = {}
        for e in ledger:
            if e.get("topic_id") != topic["topic_id"] or e.get("is_synthetic_example"):
                continue
            if validate_event(e):
                continue
            by_comp.setdefault(e["competency_id"], []).append(e)
        ledger_ids = {e.get("event_id") for e in ledger if isinstance(e, dict)}
        _validate_references(topic, [e for v in by_comp.values() for e in v], ledger_ids)
        for c in topic.get("learning_scope", []):
            ev = sorted(by_comp.get(c["id"], []),
                        key=lambda x: (_parse_dt(x["date"]), x["event_id"]))
            status, detail = _evaluate_competency(c, ev, ledger, now, RETENTION_POLICY)
            if detail["cycle_start"] is None or detail["fresh_due_at"] is None:
                continue
            latest_dl_id = detail["latest"]["delayed_retrieval"]
            last_eligible = ev[-1]["event_id"] if ev else None
            out.append({"topic_id": topic["topic_id"], "competency_id": c["id"],
                        "due_at": detail["fresh_due_at"],
                        "reason": "retrieval after observed independently assessed performance",
                        "interval_days": detail["interval_days"],
                        "cycle_start": detail["cycle_start"],
                        "basis": detail["basis"],
                        "based_on_event": latest_dl_id or last_eligible,
                        "delivery": "manual; no automatic notification"})

    # Stale-queue elimination by construction: output contains ONLY freshly
    # computed entries. Stored entries are never merged in, so a stored entry
    # whose cycle_start predates the current cycle simply has no counterpart
    # in the output. Stored due_at values are never read back into status.
    return {"schema_version": "1.0", "reviews": out}


def cmd_plan_reviews(a):
    w=Path(a.workspace).expanduser().resolve()
    manifest=load(w/"manifest.json")
    events=events_read(w/manifest["events_path"])
    topics=[load(p) for p in sorted((w/manifest["topics_dir"]).glob("*/state.json"))]
    if any(validate_event(e) for e in events): raise ValueError("Invalid event records")
    if any(validate_topic(t) for t in topics): raise ValueError("Invalid topic records")
    result=reviews_from_events(topics,events)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.dry_run: return 0
    if not a.approve: raise ValueError("Explicit approval required to save review queue: --approve")
    dump(w/manifest["reviews_path"],result,overwrite=True)
    return 0

def cmd_report(a):
    w=Path(a.workspace).expanduser().resolve()
    manifest=load(w/"manifest.json")
    profile, source = resolve_effective_profile(w/manifest["profile_path"])
    event_path=w/manifest["events_path"]
    events=events_read(event_path)
    for i,e in enumerate(events,1):
        errs=validate_event(e)
        if errs: raise ValueError(f"Invalid event {i}: "+"; ".join(errs))
    states=[]
    queue=load(w/manifest["reviews_path"]) if (w/manifest["reviews_path"]).exists() else {"reviews":[]}
    for path in sorted((w/manifest["topics_dir"]).glob("*/state.json")):
        topic=load(path)
        for comp in topic.get("learning_scope",[]):
            next_review=next((r for r in queue.get("reviews", []) if r["topic_id"]==topic["topic_id"] and r["competency_id"]==comp["id"]),None)
            if next_review: comp["due_at"]=next_review["due_at"]
        errs=validate_topic(topic)
        if errs: raise ValueError(f"Invalid topic {path}: "+"; ".join(errs))
        states.append(progress(topic,events))
    res={"profile_status":profile["assessment_status"],"effective_profile":source, "event_count":len(events),"topics":states}
    print(json.dumps(res,ensure_ascii=False,indent=2))
    return 0


def cmd_record(a):
    w=Path(a.workspace).expanduser().resolve()
    p=w/"events.jsonl"
    if not (w/"manifest.json").exists(): raise ValueError("Initialize workspace first")
    if not a.approve: raise ValueError("Explicit write approval required: --approve")
    rubric=json.loads(a.rubric)
    e={"event_id":a.event_id,"date":dt.datetime.now(dt.timezone.utc).isoformat(),
       "topic_id":a.topic,"competency_id":a.competency,"task_type":a.task_type,
       "expected_reasoning":a.expected,"observed_answer":a.answer,"rubric":rubric,
       "help_level":a.help,"feedback":a.feedback,"grader":a.grader,
       "evidence_origin":"observed_response", "confidence_self_report":a.confidence,
       "is_synthetic_example":False}
    errs=validate_event(e)
    if errs: raise ValueError("Invalid event: "+"; ".join(errs))
    # C1/C7: full trusted pre-flight (schema + uniqueness), never diagnose-only.
    existing = ledger_read_trusted(p, workspace_root=w)
    if e["event_id"] in {x.get("event_id") for x in existing}:
        raise ValueError("Duplicate event_id")
    append_event_line(p, json.dumps(e, ensure_ascii=False))
    print(f"RECORDED: {a.event_id}; grading supplied by {a.grader}, NOT independently verified by script")
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate");v.add_argument("--profile",required=True);v.add_argument("--topic");v.add_argument("--events");v.set_defaults(func=cmd_validate)
    ini=sub.add_parser("init");ini.add_argument("--workspace",required=True);ini.set_defaults(func=cmd_init)
    nt=sub.add_parser("new-topic");nt.add_argument("--workspace",required=True);nt.add_argument("--topic",required=True)
    nt.add_argument("--goal",required=True);nt.add_argument("--competency",action="append",required=True)
    nt.add_argument("--approve",action="store_true");nt.set_defaults(func=cmd_new_topic)
    g=sub.add_parser("generate");g.add_argument("--workspace",required=True);g.add_argument("--approve",action="store_true");g.set_defaults(func=cmd_generate)
    r=sub.add_parser("report");r.add_argument("--workspace",required=True);r.set_defaults(func=cmd_report)
    rr=sub.add_parser("plan-reviews");rr.add_argument("--workspace",required=True)
    rr.add_argument("--dry-run",action="store_true");rr.add_argument("--approve",action="store_true")
    rr.set_defaults(func=cmd_plan_reviews)
    rec=sub.add_parser("record")
    for key in ("workspace","event-id","topic","competency","task-type","answer","rubric","expected","feedback"):
        rec.add_argument("--"+key,required=True)
    rec.add_argument("--grader",choices=["ai_reviewed","human_reviewed","not_graded"],default="not_graded")
    rec.add_argument("--help-level",dest="help",choices=sorted(HELP),default="none")
    rec.add_argument("--confidence",type=int);rec.add_argument("--approve",action="store_true");rec.set_defaults(func=cmd_record)
    a=p.parse_args()
    try: return a.func(a)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("ERROR:",e,file=sys.stderr);return 2

if __name__ == "__main__": sys.exit(main())
