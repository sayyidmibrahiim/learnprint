"""Learner profile v2 helpers (W5 of the mega plan).

Contract:
- `migrate_v1_to_v2` is purely additive and reversible: identity
  (profile_id), evidence, claims and defaults are preserved byte-for-byte
  semantically; only schema_version becomes "2.0" and an empty
  `constraints` array appears when absent. Never deletes or rewrites
  learner history.
- `calibration` joins existing `confidence_self_report` values with rubric
  outcomes per event. It NEVER treats confidence as correctness, never
  stores a second copy (computed at read time), and never invents a
  clinical label.
- Reading fails closed on malformed profiles/events.

Python 3.9+ standard library only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

CALIBRATION_BUCKETS = ("low", "mid", "high")  # 0-0.33 / 0.34-0.66 / 0.67-1


class ProfileError(ValueError):
    """Fail-closed profile/read rejection."""


def _read_json(path: Path) -> Any:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ProfileError(f"{path} is not valid JSON: {exc}") from exc


def read_profile(path: Path) -> Dict[str, Any]:
    """Validate a v1.0 or v2.0 profile document (structurally, locally)."""
    profile = _read_json(path)
    if not isinstance(profile, dict):
        raise ProfileError("profile must be a JSON object")
    version = profile.get("schema_version")
    if version not in ("1.0", "2.0"):
        raise ProfileError(f"unsupported profile schema_version {version!r}")
    for field in ("profile_id", "assessment_status", "evidence_quality"):
        if not isinstance(profile.get(field), str) or not profile[field]:
            raise ProfileError(f"profile field {field!r} must be a nonempty string")
    if profile.get("profile_id") == "local-unassessed" and profile.get("public_template") is not True:
        pass  # starter template: no extra requirement
    return profile


def migrate_v1_to_v2(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Additive, reversible v1.0 -> v2.0 map. Pure; no ledger/identity edits."""
    if not isinstance(profile, dict):
        raise ProfileError("profile must be a JSON object")
    if profile.get("schema_version") != "1.0":
        raise ProfileError("migration requires a profile with schema_version 1.0")
    migrated = json.loads(json.dumps(profile))
    migrated["schema_version"] = "2.0"
    migrated.setdefault("constraints", [])
    return migrated


def _bucket(confidence: float) -> Optional[str]:
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        return None
    if not (0.0 <= float(confidence) <= 1.0):
        return None
    if confidence <= 0.33:
        return "low"
    if confidence <= 0.66:
        return "mid"
    return "high"


def calibration(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Confidence-vs-outcome analytics computed at read time.

    Buckets reported confidence (0..1) against scorable rubric outcomes of
    the SAME event. Correctness rule mirrors the canonical evaluator for
    delayed/application criteria: concept==2 and application==2 pass.
    Confidence is never asserted to be correct: accuracy and mean
    confidence are reported separately.
    """
    if not isinstance(events, list):
        raise ProfileError("events must be a list")
    buckets: Dict[str, Dict[str, Any]] = {
        b: {"n": 0, "correct": 0, "confidence_sum": 0.0} for b in CALIBRATION_BUCKETS
    }
    used = 0
    for event in events:
        if not isinstance(event, dict):
            raise ProfileError("each event must be an object")
        confidence = event.get("confidence_self_report")
        rubric = event.get("rubric")
        if confidence is None or not isinstance(rubric, dict):
            continue
        bucket = _bucket(confidence)
        if bucket is None:
            raise ProfileError(
                f"event {event.get('event_id')!r} confidence_self_report must be a number in [0, 1]"
            )
        outcome = rubric.get("concept"), rubric.get("application")
        if outcome[0] is None and outcome[1] is None:
            continue  # unscorable event: not evidence of correctness
        correct = 1.0 if (outcome[0] == 2 and outcome[1] == 2) else 0.0
        buckets[bucket]["n"] += 1
        buckets[bucket]["correct"] += correct
        buckets[bucket]["confidence_sum"] += float(confidence)
        used += 1
    summary: Dict[str, Any] = {"events_analyzed": used, "buckets": {}}
    for bucket, data in buckets.items():
        if data["n"] == 0:
            summary["buckets"][bucket] = {"n": 0, "accuracy": None, "mean_confidence": None}
            continue
        accuracy = data["correct"] / data["n"]
        mean_confidence = data["confidence_sum"] / data["n"]
        summary["buckets"][bucket] = {
            "n": data["n"],
            "accuracy": round(accuracy, 4),
            "mean_confidence": round(mean_confidence, 4),
        }
    scored = [
        (buckets[b]["confidence_sum"] / buckets[b]["n"],
         buckets[b]["correct"] / buckets[b]["n"])
        for b in CALIBRATION_BUCKETS if buckets[b]["n"] > 0
    ]
    if scored:
        # headline gap kept as a plain difference; no clinical interpretation
        summary["mean_overconfidence_gap"] = round(
            sum(c - a for c, a in scored) / len(scored), 4
        )
    else:
        summary["mean_overconfidence_gap"] = None
    summary["disclaimer"] = (
        "confidence is reported self-assessment, not correctness; no learning style"
        " or diagnosis may be derived from calibration numbers"
    )
    return summary


# --------------------------------- CLI ---------------------------------

def cmd_show(a) -> int:  # type: ignore[no-untyped-def]
    profile = read_profile(Path(a.profile))
    print(json.dumps(profile, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


def cmd_migrate(a) -> int:  # type: ignore[no-untyped-def]
    profile = read_profile(Path(a.profile))
    migrated = migrate_v1_to_v2(profile)
    out = Path(a.out)
    if out.exists() and not a.allow_overwrite:
        print(f"REJECTED: {out} exists; pass --allow-overwrite to replace it", file=sys.stderr)
        return 2
    out.write_text(json.dumps(migrated, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"migrated": True, "out": str(out), "profile_id": migrated["profile_id"]}))
    return 0


def cmd_calibrate(a) -> int:  # type: ignore[no-untyped-def]
    data = _read_json(Path(a.events))
    if isinstance(data, dict) and isinstance(data.get("events"), list):
        events = data["events"]
    elif isinstance(data, list):
        events = data
    else:
        raise ProfileError("--events must be a JSON list or an object with an events list")
    print(json.dumps(calibration(events), ensure_ascii=False, indent=1, sort_keys=True))
    return 0


def build_parser():
    import argparse

    p = argparse.ArgumentParser(
        prog="learnprint_profile.py",
        description="Profile v2 helpers: additive migration and confidence calibration (read-only).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    show = sub.add_parser("show", help="validate and print a learner profile")
    show.add_argument("--profile", required=True)
    show.set_defaults(func=cmd_show)
    mig = sub.add_parser("migrate", help="write v2 profile to a NEW file (source untouched)")
    mig.add_argument("--profile", required=True)
    mig.add_argument("--out", required=True)
    mig.add_argument("--allow-overwrite", action="store_true")
    mig.set_defaults(func=cmd_migrate)
    cal = sub.add_parser("calibrate", help="confidence-vs-outcome analytics over an events JSON")
    cal.add_argument("--events", required=True)
    cal.set_defaults(func=cmd_calibrate)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ProfileError, OSError) as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
