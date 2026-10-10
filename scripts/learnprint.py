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
    # O_BINARY (no-op on POSIX): without it Windows translates \n to \r\n,
    # corrupting byte offsets used by ledger diagnostics and repair.
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o600)
    try:
        _write_all(fd, payload)
        if durable:
            os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(directory) -> None:
    """Best-effort directory-entry durability. POSIX fsyncs the directory fd;
    Windows skips (directory fsync unsupported) — file-data fsync still holds.
    """
    if sys.platform == "win32":
        return
    try:
        dir_fd = os.open(str(directory), os.O_RDONLY | os.O_DIRECTORY)
    except (OSError, AttributeError):
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def atomic_write(path, content: str, durable: bool = True) -> None:
    """Atomically replace path via unique temp file + os.replace().

    durable=True adds file fsync and best-effort directory fsync. Replace
    gives atomic VISIBILITY, not multi-file transactions.
    """
    import tempfile
    path = Path(path)
    data = content.encode("utf-8")
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp",
                               prefix=path.stem + "_")
    try:
        _write_all(fd, data)
        if durable:
            os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(tmp, str(path))
        if durable:
            _fsync_dir(path.parent)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def workspace_lock(courses_root, timeout_seconds: int = 5):
    """Advisory exclusive lock on Courses/.learnprint/.lock.

    Context manager yielding None. Every mutating workspace command holds it
    for its whole read-modify-write sequence; pure readers never take it.
    The lock FILE is persistent infrastructure: it is created on demand and
    NEVER deleted as recovery (deleting it under a holder splits the lock).
    """
    import time
    if sys.platform == "win32":
        import msvcrt
    else:
        import fcntl
    from contextlib import contextmanager

    @contextmanager
    def _lock():
        lock_path = Path(courses_root) / ".learnprint" / ".lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = lock_path.open("w")
        deadline = time.monotonic() + timeout_seconds
        try:
            while True:
                try:
                    if sys.platform == "win32":
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (IOError, OSError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Could not acquire workspace lock within "
                            f"{timeout_seconds}s. Another Learnprint process "
                            "may be running. Wait for it to finish.")
                    time.sleep(0.1)
            yield
        finally:
            if sys.platform == "win32":
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            f.close()
    return _lock()


APPROVAL_SCOPE_TOKENS = {"workspace-create", "course-create", "event-append",
                         "state-update", "dashboard-write", "profile-write"}


def read_approval(courses_root):
    """Read the standing-approval record. Returns dict, or None if absent.

    The record documents claimed scope; it is NOT proof of human consent and
    its provenance cannot be attested. Schema/scope coherence IS checked.
    """
    p = Path(courses_root) / ".learnprint" / "approval.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("schema_version") != "1.0":
        return None
    scope = data.get("scope")
    if not isinstance(scope, list) or not all(isinstance(s, str) for s in scope):
        return None
    if any(s not in APPROVAL_SCOPE_TOKENS for s in scope):
        return None
    if not isinstance(data.get("revoked"), bool):
        return None
    return data


def write_approval(courses_root, scope=None, granted_by="chat-approval"):
    """Record a scope agreement. Called only via `course init --approve` after
    the agent asserts chat approval was obtained, or via tests."""
    scope = list(scope or ["workspace-create", "course-create", "event-append",
                           "state-update", "dashboard-write", "profile-write"])
    if any(s not in APPROVAL_SCOPE_TOKENS for s in scope):
        raise ValueError(f"unknown scope token in {scope}")
    rec = {"schema_version": "1.0",
           "granted_at": dt.datetime.now(dt.timezone.utc).isoformat(),
           "granted_by": granted_by,
           "scope": scope,
           "revoked": False, "revoked_at": None}
    d = Path(courses_root) / ".learnprint"
    d.mkdir(parents=True, exist_ok=True)
    atomic_write(d / "approval.json", json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    return rec


def revoke_approval(courses_root):
    """Flip revoked=True. All mutating commands refuse until a new grant."""
    current = read_approval(courses_root)
    if current is None:
        raise ValueError("no standing approval to revoke")
    current["revoked"] = True
    current["revoked_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    d = Path(courses_root) / ".learnprint"
    atomic_write(d / "approval.json", json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    return current


def approval_allows(approval, operation):
    """True iff a live (present, unrevoked) grant covers the operation."""
    if not isinstance(approval, dict):
        return False
    if approval.get("revoked"):
        return False
    return operation in (approval.get("scope") or [])


# Code-level lock policy declaration (plan Step 4.2). Rule: every mutator
# locks, every pure reader does not. Deliberately outside any grantable
# scope: publish, global install, delete, outside-Courses writes,
# destructive git, network access.
LOCK_TABLE = {
    "course init": {"mutates": True, "locks": True},
    "course create": {"mutates": True, "locks": True},
    "course rename": {"mutates": True, "locks": True},
    "course move": {"mutates": True, "locks": True},
    "record": {"mutates": True, "locks": True},
    "plan-reviews": {"mutates": True, "locks": True},
    "course validate --repair": {"mutates": True, "locks": True},
    "migrate": {"mutates": True, "locks": True},
    "course dashboard": {"mutates": True, "locks": True},
    "course resolve": {"mutates": False, "locks": False},
    "course list": {"mutates": False, "locks": False},
    "report": {"mutates": False, "locks": False},
}


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


try:
    import learnprint_routing as routing
except ImportError:  # loaded via spec without scripts/ on sys.path (tests)
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "learnprint_routing", Path(__file__).resolve().parent / "learnprint_routing.py")
    routing = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(routing)


def validate_path(proposed_path, courses_root):
    """Deterministic path safety (plan Step 5.1). Returns (valid, error)."""
    courses = Path(courses_root).resolve()
    if os.path.isabs(proposed_path):
        return False, "Absolute paths not allowed"
    normalized = proposed_path.replace("\\", "/")
    for part in normalized.split("/"):
        if part in ("..", ".") or part.startswith("~"):
            return False, "Path traversal not allowed"
    invalid = set("<>:\"|?*") | {chr(c) for c in range(0, 32)}
    for part in Path(proposed_path).parts:
        if any(ch in invalid for ch in part):
            return False, f"Invalid character in path component: {part}"
        if part != part.strip(". "):
            return False, f"Trailing dots/spaces in component: {part}"
    full = (courses / proposed_path).resolve()
    try:
        full.relative_to(courses)
    except ValueError:
        return False, "Path escapes courses root (possibly via symlink/junction)"
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
    for part in full.relative_to(courses).parts:
        if part.split(".")[0].upper() in reserved:
            return False, f"Windows reserved name: {part}"
    rel_parts = full.relative_to(courses).parts
    for i in range(1, len(rel_parts) + 1):
        part_path = courses.joinpath(*rel_parts[:i])
        parent = part_path.parent
        target = part_path.name.lower()
        if parent.exists():
            existing = {p.name.lower(): p.name for p in parent.iterdir() if p.is_dir()}
            if target in existing and existing[target] != part_path.name:
                return False, f"Case collision: '{part_path.name}' vs existing '{existing[target]}'"
    if len(rel_parts) > 6:
        return False, f"Path too deep ({len(rel_parts)} > 6 levels)"
    for part in rel_parts:
        if len(part) > 100:
            return False, f"Component too long: {len(part)} chars"
    return True, ""


def registry_path(courses_root):
    return Path(courses_root) / ".learnprint" / "registry.json"


def registry_read(courses_root):
    p = registry_path(courses_root)
    if not p.exists():
        return {"schema_version": "1.0", "courses": [], "active_course_id": None}
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("courses"), list):
        raise ValueError(f"registry corrupt: {p}")
    return data


def registry_write(courses_root, registry):
    """Backup-then-write under the caller's lock (plan Step 4.6)."""
    d = Path(courses_root) / ".learnprint"
    d.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(registry, ensure_ascii=False, indent=2) + "\n"
    atomic_write(d / "registry.json.bak", payload)
    atomic_write(d / "registry.json", payload)


def _cname(course_id):
    return (course_id or "")[:8]


def course_resolve(courses_root, query):
    """Registry lookup: found / ambiguous / not_found (never guesses)."""
    return routing.resolve_course(query, registry_read(courses_root))


def course_create(courses_root, category_path, title, goal, aliases=(),
                  confirm_new_segments=(), classification_source="agent"):
    """Create a course: gate → collision checks → directories → registry.

    Revalidates the gate on a FRESH registry read inside the workspace lock,
    so a competing session creating the same category first converges to
    safe reuse (never a silent duplicate). New events for this course use
    topic_id = course_id (stable key); registry topic_id stays null unless
    set by migration.
    """
    root = Path(courses_root)
    with workspace_lock(root):
        registry = registry_read(root)
        ok, gate = routing.validate_classification(category_path, registry)
        if not ok:
            raise ValueError(gate)
        if gate.get("verdict") == "new-needs-confirmation":
            required = {v["segment"] for v in gate["segments"]
                        if v["verdict"] == "new-needs-confirmation"}
            missing = required - set(confirm_new_segments or ())
            if missing:
                raise ValueError(
                    "new category segments need explicit confirmation: "
                    f"{sorted(missing)}")
        resolved_path = gate["resolved_path"]
        valid, err = validate_path(resolved_path, root)
        if not valid:
            raise ValueError(f"invalid category path: {err}")
        # Structural invariant: a category path must never land exactly on
        # an existing COURSE directory (no silent course<->category flips).
        for c in registry.get("courses", []):
            existing_dir = Path(c.get("rel_path", ""))
            if existing_dir.as_posix() == resolved_path:
                raise ValueError(
                    f"category path collides with existing course directory: {resolved_path}")
        slug = routing.slugify(title)
        rel = (Path(resolved_path) / slug).as_posix()
        for c in registry.get("courses", []):
            if (c.get("category_path") == resolved_path
                    and c.get("slug", "").lower() == slug.lower()):
                raise ValueError(
                    f"course slug collision in category: {rel}")
        norm_title = routing.normalize_key(title)
        for c in registry.get("courses", []):
            if (c.get("category_path") == resolved_path
                    and c.get("normalized_title") == norm_title):
                raise ValueError(
                    f"course already exists in category ({c.get('course_id')}); refusing duplicate")
        norm_aliases = [routing.normalize_key(a) for a in (aliases or [])]
        for a, na in zip(aliases or [], norm_aliases):
            for c in registry.get("courses", []):
                if na in c.get("normalized_aliases", []):
                    raise ValueError(
                        f"alias {a!r} already owned by course {c.get('course_id')} "
                        f"({_cname(c.get('course_id'))}); ask the user which course was meant")
        course_dir = root / rel
        adopted = False
        if course_dir.exists():
            if (course_dir / "state.json").exists():
                adopted = True  # crash-recovery: orphan dir, register it
            else:
                raise ValueError(f"Refusing to overwrite: {course_dir}")
        else:
            course_dir.mkdir(parents=True)
            (course_dir / "README.md").write_text(f"# {title}\n\nGoal: {goal}\n", encoding="utf-8")
            (course_dir / "SYLLABUS.md").write_text(f"# {title} — syllabus\n", encoding="utf-8")
            (course_dir / "MAP.mmd").write_text("flowchart TD\n", encoding="utf-8")
            (course_dir / "HANDOFF.md").write_text(f"# Handoff — {title}\n", encoding="utf-8")
            (course_dir / "state.json").write_text(json.dumps(
                {"schema_version": "1.0", "course_id": None, "goal": goal,
                 "learning_scope": [], "sources": []}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
        course_id = routing.allocate_course_id(registry)
        entry = {
            "course_id": course_id,
            "title": title,
            "normalized_title": norm_title,
            "slug": slug,
            "category_path": resolved_path,
            "rel_path": rel,
            "aliases": list(aliases or []),
            "normalized_aliases": norm_aliases,
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "last_activity": None,
            "classification_source": classification_source,
            "goal": goal,
            "topic_id": None,
        }
        registry.setdefault("courses", []).append(entry)
        registry_write(root, registry)
        state_path = course_dir / "state.json"
        try:
            st = json.loads(state_path.read_text(encoding="utf-8"))
            st["course_id"] = course_id
            state_path.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
        except (ValueError, OSError):
            pass
        entry["adopted_existing_dir"] = adopted
        return entry


def course_rename(courses_root, course_id, title, update_path=False):
    """Rename: title only. course_id, topic_id, events untouched by construction."""
    root = Path(courses_root)
    with workspace_lock(root):
        registry = registry_read(root)
        entry = next((c for c in registry.get("courses", []) if c.get("course_id") == course_id), None)
        if entry is None:
            raise ValueError(f"unknown course_id: {course_id}")
        entry["title"] = title
        entry["normalized_title"] = routing.normalize_key(title)
        if update_path:
            slug = routing.slugify(title)
            rel = (Path(entry["category_path"]) / slug).as_posix()
            for c in registry.get("courses", []):
                if c is not entry and c.get("rel_path") == rel:
                    raise ValueError(f"rename target collides: {rel}")
            os.replace(str(root / entry["rel_path"]), str(root / rel))
            entry["slug"] = slug
            entry["rel_path"] = rel
        registry_write(root, registry)
        return entry


def course_move(courses_root, course_id, category_path, confirm_new_segments=()):
    """Relocate: category_path + rel_path change. Identity and evidence stay valid."""
    root = Path(courses_root)
    with workspace_lock(root):
        registry = registry_read(root)
        entry = next((c for c in registry.get("courses", []) if c.get("course_id") == course_id), None)
        if entry is None:
            raise ValueError(f"unknown course_id: {course_id}")
        ok, gate = routing.validate_classification(category_path, registry)
        if not ok:
            raise ValueError(gate)
        if gate.get("verdict") == "new-needs-confirmation":
            required = {v["segment"] for v in gate["segments"]
                        if v["verdict"] == "new-needs-confirmation"}
            missing = required - set(confirm_new_segments or ())
            if missing:
                raise ValueError(
                    f"new category segments need explicit confirmation: {sorted(missing)}")
        resolved_path = gate["resolved_path"]
        rel = (Path(resolved_path) / entry["slug"]).as_posix()
        for c in registry.get("courses", []):
            if c is not entry and c.get("rel_path") == rel:
                raise ValueError(f"move target collides: {rel}")
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(root / entry["rel_path"]), str(dest))
        entry["category_path"] = resolved_path
        entry["rel_path"] = rel
        registry_write(root, registry)
        return entry


def _courses_root(args):
    """Resolve --courses-root (default: Courses/ under the git root)."""
    if getattr(args, "courses_root", None):
        return Path(args.courses_root).expanduser()
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent / "Courses"
    return cwd / "Courses"


def _require(args, root, scope_token):
    """Per-call --approve flag PLUS live standing approval (plan Step 3.0a)."""
    if not getattr(args, "approve", False):
        raise ValueError("Explicit approval required: --approve")
    ap = read_approval(root)
    if not approval_allows(ap, scope_token):
        raise ValueError(
            "Standing approval missing, revoked, or out of scope for "
            f"{scope_token}; ask the user in chat, then run course init --approve")


def _course_topics(root, registry):
    """Build progress-compatible topic dicts from course state.json files."""
    topics = []
    for c in registry.get("courses", []):
        sp = root / c.get("rel_path", "") / "state.json"
        try:
            st = json.loads(sp.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        topics.append({
            "schema_version": "1.0",
            "topic_id": c.get("topic_id") or c.get("course_id"),
            "course_id": c.get("course_id"),
            "goal": c.get("goal", ""),
            "learning_scope": st.get("learning_scope", []),
            "syllabus": [], "question_parking_lot": [],
            "sources": st.get("sources", []), "last_session": None,
        })
    return topics


def cmd_course_init(a):
    root = _courses_root(a)
    if not getattr(a, "approve", False):
        raise ValueError("Explicit approval required: --approve")
    lp = root / ".learnprint"
    if (lp / "registry.json").exists():
        raise ValueError(f"Workspace already initialized: {root}")
    lp.mkdir(parents=True, exist_ok=True)
    (lp / "learner").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "templates/course-registry.json", lp / "registry.json")
    shutil.copyfile(ROOT / "templates/learner-profile-starter.json", lp / "learner/profile.json")
    shutil.copyfile(ROOT / "templates/review-queue.json", lp / "reviews.json")
    (lp / "config.json").write_text(json.dumps(
        {"min_elapsed_hours": RETENTION_POLICY["min_elapsed_hours"],
         "intervals_days": list(RETENTION_POLICY["intervals_days"])},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (lp / "events.jsonl").write_text("", encoding="utf-8")
    (root / "HANDOFF.md").write_text(
        "# Learnprint handoff\n\nWorkspace initialized. No courses yet.\n", encoding="utf-8")
    rec = write_approval(root)
    print(f"CREATED Courses workspace: {root}")
    print(f"Standing approval recorded (scope: {', '.join(rec['scope'])})")
    return 0


def cmd_course_resolve(a):
    root = _courses_root(a)
    print(json.dumps(course_resolve(root, a.query), ensure_ascii=False, indent=2))
    return 0


def cmd_course_create(a):
    root = _courses_root(a)
    _require(a, root, "course-create")
    entry = course_create(root, a.category, a.title, a.goal, aliases=a.alias or [],
                          confirm_new_segments=a.confirm_new_segment or [],
                          classification_source="agent")
    with workspace_lock(root):
        registry = registry_read(root)
        registry["active_course_id"] = entry["course_id"]
        registry_write(root, registry)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_course_rename(a):
    root = _courses_root(a)
    _require(a, root, "course-create")
    entry = course_rename(root, a.course_id, a.title, update_path=a.update_path)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_course_move(a):
    root = _courses_root(a)
    _require(a, root, "course-create")
    entry = course_move(root, a.course_id, a.category,
                        confirm_new_segments=a.confirm_new_segment or [])
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_course_list(a):
    root = _courses_root(a)
    registry = registry_read(root)
    out = [{"course_id": c["course_id"], "title": c.get("title"),
            "category_path": c.get("category_path"), "rel_path": c.get("rel_path")}
           for c in registry.get("courses", [])]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_course_dashboard(a):
    root = _courses_root(a)
    _require(a, root, "dashboard-write")
    with workspace_lock(root):
        registry = registry_read(root)
        ledger = ledger_read_trusted(root / ".learnprint" / "events.jsonl", workspace_root=root)
        policy = load_retention_policy(root)
        now = dt.datetime.now(dt.timezone.utc)
        stored = {}
        rp = root / ".learnprint" / "reviews.json"
        if rp.exists():
            try:
                stored = json.loads(rp.read_text(encoding="utf-8"))
            except ValueError:
                stored = {}
        due_by_comp = {}
        for r in stored.get("reviews", []):
            due_by_comp.setdefault(r.get("competency_id"), r.get("due_at"))
        lines = ["# Learnprint Courses", ""]
        for c in registry.get("courses", []):
            topics = _course_topics(root, {"courses": [c]})
            if not topics or not topics[0]["learning_scope"]:
                badge, counts = "[no-evidence]", {}
            else:
                res = progress(topics[0], ledger, now=now, policy=policy, registry=registry)
                counts = {}
                for comp in res["competencies"]:
                    counts[comp["status"]] = counts.get(comp["status"], 0) + 1
                bases = {comp["basis"] for comp in res["competencies"]}
                badge = ("[substantiated]" if "substantiated" in bases
                         else "[learner-confirmed]" if "learner_confirmed" in bases
                         else "[provisional]")
            lines.append(f"## {badge} {c.get('title')} (`{c.get('rel_path')}`)")
            if counts:
                lines.append("- " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
            lines.append("")
        due_all = reviews_from_events(_course_topics(root, registry), ledger,
                                     stored_reviews=stored if stored else None)["reviews"]
        if due_all:
            lines.append("## Due reviews")
            for r in due_all:
                lines.append(f"- {r['competency_id']}: due {r['due_at']} [{r['basis']}]")
            lines.append("")
        atomic_write(root / "INDEX.md", "\n".join(lines) + "\n")
    print(f"DASHBOARD regenerated: {root / 'INDEX.md'}")
    return 0


def cmd_course_resume(a):
    root = _courses_root(a)
    registry = registry_read(root)
    courses = registry.get("courses", [])
    if not courses:
        print(json.dumps({"status": "none", "note": "no courses yet; start a new one"}))
        return 0
    active = registry.get("active_course_id")
    hit = next((c for c in courses if c.get("course_id") == active), None)
    if hit is not None:
        print(json.dumps({"status": "found", "course": hit}, ensure_ascii=False, indent=2))
        return 0
    dated = sorted([c for c in courses if c.get("last_activity")],
                   key=lambda c: c["last_activity"], reverse=True)
    if dated and (len(dated) == 1 or dated[0]["last_activity"] != dated[1]["last_activity"]):
        print(json.dumps({"status": "found", "course": dated[0]}, ensure_ascii=False, indent=2))
        return 0
    cands = [{"course_id": c["course_id"], "title": c.get("title"),
              "category_path": c.get("category_path")} for c in courses]
    print(json.dumps({"status": "ambiguous", "candidates": cands,
                      "note": "ask the user which course to resume"}, ensure_ascii=False, indent=2))
    return 0


def cmd_course_validate(a):
    root = _courses_root(a)
    registry = registry_read(root)
    problems = []
    for c in registry.get("courses", []):
        if not (root / c.get("rel_path", "") / "state.json").exists():
            problems.append(f"missing directory for course {c.get('course_id')}: {c.get('rel_path')}")
    known_dirs = {c.get("rel_path") for c in registry.get("courses", [])}
    for sp in root.rglob("state.json"):
        if ".learnprint" in sp.parts:
            continue
        rel = sp.parent.relative_to(root).as_posix()
        if rel not in known_dirs:
            problems.append(f"orphan directory (unregistered): {rel}")
    diag = ledger_diagnose(root / ".learnprint" / "events.jsonl", workspace_root=root)
    if diag["status"] == "damaged":
        problems.append(f"ledger damaged: {len(diag['damage'])} record(s)")
    if diag.get("absent_kind") == "missing-expected":
        problems.append("ledger missing: events.jsonl absent in initialized workspace")
    for tmp in (root / ".learnprint").glob("*.tmp"):
        problems.append(f"stale temp file: {tmp.name}")
    if problems and not (a.repair and a.approve):
        print("INVALID\n" + "\n".join(problems))
        return 2
    if a.repair:
        _require(a, root, "state-update")
        with workspace_lock(root):
            registry = registry_read(root)
            known = {c.get("rel_path") for c in registry.get("courses", [])}
            for sp in root.rglob("state.json"):
                if ".learnprint" in sp.parts:
                    continue
                rel = sp.parent.relative_to(root).as_posix()
                if rel not in known:
                    entry = {"course_id": routing.allocate_course_id(registry),
                             "title": sp.parent.name, "normalized_title": routing.normalize_key(sp.parent.name),
                             "slug": sp.parent.name, "category_path": sp.parent.parent.relative_to(root).as_posix(),
                             "rel_path": rel, "aliases": [], "normalized_aliases": [],
                             "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                             "last_activity": None, "classification_source": "imported",
                             "goal": "", "topic_id": None}
                    registry.setdefault("courses", []).append(entry)
                    problems.append(f"adopted orphan directory: {rel}")
                    known.add(rel)
            for tmp in (root / ".learnprint").glob("*.tmp"):
                tmp.unlink()
                problems.append(f"removed stale temp file: {tmp.name}")
            registry_write(root, registry)
    print("VALID" if not problems else "REPAIRED\n" + "\n".join(problems))
    return 0


def cmd_course_repair_evidence(a):
    root = _courses_root(a)
    _require(a, root, "event-append")
    with workspace_lock(root):
        report = ledger_repair_truncate_partial_tail(root / ".learnprint" / "events.jsonl")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_course_revoke_approval(a):
    root = _courses_root(a)
    revoke_approval(root)
    print("Standing approval revoked. Mutating commands will refuse until a new grant.")
    return 0


def cmd_course_plan_reviews(a):
    root = _courses_root(a)
    _require(a, root, "state-update")
    with workspace_lock(root):
        registry = registry_read(root)
        ledger = ledger_read_trusted(root / ".learnprint" / "events.jsonl", workspace_root=root)
        topics = _course_topics(root, registry)
        for t in topics:
            errs = validate_topic(t)
            if errs:
                raise ValueError(f"invalid course state: {errs}")
        rp = root / ".learnprint" / "reviews.json"
        stored = {}
        if rp.exists():
            try:
                stored = json.loads(rp.read_text(encoding="utf-8"))
            except ValueError:
                stored = {}
        result = reviews_from_events(topics, ledger, stored_reviews=stored or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if a.dry_run:
            return 0
        atomic_write(rp, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0


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
    courses_mode = not (w/"manifest.json").exists() and (w/".learnprint"/"registry.json").exists()
    if courses_mode:
        return _cmd_record_courses(a, w)
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


def _cmd_record_courses(a, w):
    """Record into a Courses/ workspace ledger (fail closed, under lock)."""
    root = w
    if not getattr(a, "approve", False):
        raise ValueError("Explicit write approval required: --approve")
    ap = read_approval(root)
    if not approval_allows(ap, "event-append"):
        raise ValueError("Standing approval missing, revoked, or out of scope for event-append")
    lp = root / ".learnprint"
    with workspace_lock(root):
        registry = registry_read(root)
        course_id = getattr(a, "course_id", None)
        if course_id:
            entry = next((c for c in registry.get("courses", [])
                          if c.get("course_id") == course_id), None)
            if entry is None:
                raise ValueError(f"unknown course_id: {course_id}")
            topic_id = a.topic or course_id
        else:
            topic_id = a.topic
        rubric = json.loads(a.rubric)
        e = {"event_id": a.event_id,
             "date": dt.datetime.now(dt.timezone.utc).isoformat(),
             "topic_id": topic_id,
             "competency_id": a.competency, "task_type": a.task_type,
             "expected_reasoning": a.expected, "observed_answer": a.answer,
             "rubric": rubric, "help_level": a.help, "feedback": a.feedback,
             "grader": a.grader, "evidence_origin": "observed_response",
             "confidence_self_report": a.confidence, "is_synthetic_example": False}
        if course_id:
            e["course_id"] = course_id
        for link, val in (("confirms_event_id", getattr(a, "confirms", None)),
                          ("corrects_event_id", getattr(a, "corrects", None)),
                          ("corroborates_event_id", getattr(a, "corroborates", None))):
            if val:
                e[link] = val
        if getattr(a, "grader_source", None):
            e["grader_source"] = a.grader_source
        errs = validate_event(e)
        if errs:
            raise ValueError("Invalid event: " + "; ".join(errs))
        existing = ledger_read_trusted(lp / "events.jsonl", workspace_root=root)
        if e["event_id"] in {x.get("event_id") for x in existing}:
            raise ValueError("Duplicate event_id")
        append_event_line(lp / "events.jsonl", json.dumps(e, ensure_ascii=False))
        if course_id:
            for c in registry.get("courses", []):
                if c.get("course_id") == course_id:
                    c["last_activity"] = e["date"]
            registry["active_course_id"] = course_id
            registry_write(root, registry)
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
    rec.add_argument("--course-id",default=None)
    rec.add_argument("--grader-source",choices=sorted(GRADER_SOURCES),default=None)
    rec.add_argument("--confirms",default=None);rec.add_argument("--corrects",default=None)
    rec.add_argument("--corroborates",default=None)

    course=sub.add_parser("course")
    cs=course.add_subparsers(dest="course_cmd",required=True)
    ci=cs.add_parser("init");ci.add_argument("--approve",action="store_true")
    ci.add_argument("--courses-root");ci.set_defaults(func=cmd_course_init)
    cr=cs.add_parser("resolve");cr.add_argument("--query",required=True)
    cr.add_argument("--courses-root");cr.set_defaults(func=cmd_course_resolve)
    cc=cs.add_parser("create");cc.add_argument("--category",required=True)
    cc.add_argument("--title",required=True);cc.add_argument("--goal",required=True)
    cc.add_argument("--alias",action="append",default=[])
    cc.add_argument("--confirm-new-segment",action="append",default=[])
    cc.add_argument("--approve",action="store_true");cc.add_argument("--courses-root")
    cc.set_defaults(func=cmd_course_create)
    rn=cs.add_parser("rename");rn.add_argument("--course-id",required=True)
    rn.add_argument("--title",required=True);rn.add_argument("--update-path",action="store_true")
    rn.add_argument("--approve",action="store_true");rn.add_argument("--courses-root")
    rn.set_defaults(func=cmd_course_rename)
    mv=cs.add_parser("move");mv.add_argument("--course-id",required=True)
    mv.add_argument("--category",required=True)
    mv.add_argument("--confirm-new-segment",action="append",default=[])
    mv.add_argument("--approve",action="store_true");mv.add_argument("--courses-root")
    mv.set_defaults(func=cmd_course_move)
    cl=cs.add_parser("list");cl.add_argument("--courses-root");cl.set_defaults(func=cmd_course_list)
    db=cs.add_parser("dashboard");db.add_argument("--approve",action="store_true")
    db.add_argument("--courses-root");db.set_defaults(func=cmd_course_dashboard)
    rs=cs.add_parser("resume");rs.add_argument("--courses-root");rs.set_defaults(func=cmd_course_resume)
    cv=cs.add_parser("validate");cv.add_argument("--repair",action="store_true")
    cv.add_argument("--approve",action="store_true");cv.add_argument("--courses-root")
    cv.set_defaults(func=cmd_course_validate)
    re_=cs.add_parser("repair-evidence");re_.add_argument("--approve",action="store_true")
    re_.add_argument("--courses-root");re_.set_defaults(func=cmd_course_repair_evidence)
    ra=cs.add_parser("revoke-approval");ra.add_argument("--courses-root")
    ra.set_defaults(func=cmd_course_revoke_approval)
    pr=cs.add_parser("plan-reviews");pr.add_argument("--approve",action="store_true")
    pr.add_argument("--dry-run",action="store_true");pr.add_argument("--courses-root")
    pr.set_defaults(func=cmd_course_plan_reviews)
    a=p.parse_args()
    try: return a.func(a)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("ERROR:",e,file=sys.stderr);return 2

if __name__ == "__main__": sys.exit(main())
