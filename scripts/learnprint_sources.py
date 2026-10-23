"""Learnprint source & claim provenance (W7 of the mega plan).

Contract:
- A local source registry declares every citable source with an explicit
  status: verified, UNVERIFIED, learner-reported, agent-generated, unknown.
  `verified` requires retrieval evidence (url + retrieved_at) or it fails
  closed as unclaimable.
- Claims (observations, inferences, learner reports, external claims) are
  checked AGAINST the registry: unknown source ids are fabricated citations
  and fail closed; retracted or superseded sources invalidate claims that
  cite them; external claims without verified sources are presented as
  UNVERIFIED, never quietly as facts.
- Lesson/answer content is DATA. `guard_content` flags text injection
  attempts aimed at the tutor agent; it never executes or obeys them.
- No research is performed here; the module never invents citations.

Python 3.9+ standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List, Optional

from learnprint_adapters import SOURCE_STATUSES


class ProvenanceError(ValueError):
    """Fail-closed provenance rejection."""


CLAIM_KINDS = ("observation", "inference", "reported", "external")
PRESENTATIONS = ("verified", "UNVERIFIED", "inference", "reported", "observation")


def validate_source(source: Any) -> Dict[str, Any]:
    if not isinstance(source, dict):
        raise ProvenanceError("source must be an object")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 120:
        raise ProvenanceError("source_id must be nonempty text (max 120)")
    status = source.get("status")
    if status not in SOURCE_STATUSES:
        raise ProvenanceError(f"source {source_id!r} status must be one of {SOURCE_STATUSES}")
    record = {
        "source_id": source_id,
        "status": status,
        "title": source.get("title") or "",
        "url": source.get("url") or "",
        "retrieved_at": source.get("retrieved_at") or "",
        "version": source.get("version") or "",
        "superseded_by": source.get("superseded_by") or "",
        "retracted": bool(source.get("retracted", False)),
    }
    if status == "verified":
        if not record["url"].strip() or not record["retrieved_at"].strip():
            raise ProvenanceError(
                f"source {source_id!r} claims verified status without retrieval evidence "
                "(url + retrieved_at); failing closed"
            )
    for key in ("title", "url", "retrieved_at", "version", "superseded_by"):
        if len(record[key]) > 400:
            raise ProvenanceError(f"source {source_id!r} field {key!r} exceeds 400 chars")
    return record


def validate_registry(registry: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(registry, list):
        raise ProvenanceError("registry must be a list of source objects")
    by_id: Dict[str, Dict[str, Any]] = {}
    for entry in registry:
        record = validate_source(entry)
        if record["source_id"] in by_id:
            raise ProvenanceError(f"duplicate source_id {record['source_id']!r}")
        by_id[record["source_id"]] = record
    for record in by_id.values():
        supersede = record["superseded_by"]
        if supersede and supersede not in by_id:
            raise ProvenanceError(
                f"source {record['source_id']!r} superseded_by unknown source {supersede!r}"
            )
    return by_id


def _presentation(claim: Dict[str, Any], cited: List[Dict[str, Any]]) -> str:
    kind = claim["kind"]
    if kind == "inference":
        return "inference"
    if kind == "reported":
        return "reported"
    if kind == "observation":
        return "observation"
    # external claims are only as strong as their weakest live source
    if not cited:
        return "UNVERIFIED"
    if all(source["status"] == "verified" for source in cited):
        return "verified"
    return "UNVERIFIED"


def check_claims(claims: Any, registry: Any) -> List[Dict[str, Any]]:
    """Fail-closed claim/registry cross-check. Returns per-claim results;
    raises ProvenanceError on fabricated citations, retracted or superseded
    sources, or malformed entries."""
    by_id = registry if isinstance(registry, dict) else validate_registry(registry)
    if not isinstance(claims, list):
        raise ProvenanceError("claims must be a list")
    results: List[Dict[str, Any]] = []
    for claim in claims:
        if not isinstance(claim, dict):
            raise ProvenanceError("each claim must be an object")
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id.strip() or len(claim_id) > 120:
            raise ProvenanceError("claim_id must be nonempty text (max 120)")
        text = claim.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ProvenanceError(f"claim {claim_id!r} needs text (max 2000 chars)")
        kind = claim.get("kind")
        if kind not in CLAIM_KINDS:
            raise ProvenanceError(f"claim {claim_id!r} kind must be one of {CLAIM_KINDS}")
        source_ids = claim.get("source_ids", [])
        if not isinstance(source_ids, list) or not all(isinstance(x, str) for x in source_ids):
            raise ProvenanceError(f"claim {claim_id!r} source_ids must be a list of strings")
        cited: List[Dict[str, Any]] = []
        for source_id in source_ids:
            source = by_id.get(source_id)
            if source is None:
                raise ProvenanceError(
                    f"fabricated citation in claim {claim_id!r}: source_id {source_id!r} "
                    "is not in the registry"
                )
            if source["retracted"]:
                raise ProvenanceError(
                    f"claim {claim_id!r} cites retracted source {source_id!r}; invalid"
                )
            supersede = source["superseded_by"]
            if supersede:
                raise ProvenanceError(
                    f"claim {claim_id!r} cites source {source_id!r} superseded by "
                    f"{supersede!r}; re-verify before reuse"
                )
            cited.append(source)
        results.append(
            {
                "claim_id": claim_id,
                "kind": kind,
                "presentation": _presentation(claim, cited),
                "source_ids": source_ids,
            }
        )
    return results


INJECTION_PATTERNS = {
    "instruction_override": re.compile(
        r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|earlier)\s+(instructions|rules|policies)"
    ),
    "role_override": re.compile(r"(?i)you\s+are\s+now\s+(a|an|the)"),
    "rule_tamper": re.compile(r"(?i)(set|change)\s+help_level\s+to\s+(?!none\b)\w+"),
    "answer_extraction": re.compile(r"(?i)reveal|print|show\s+(the\s+)?(answer|solution|kunci)"),
    "command_execution": re.compile(r"(?i)\b(run|execute)\s+(the\s+)?(command|shell|script)\b\s*[:\-]"),
}


def guard_content(text: str) -> List[Dict[str, str]]:
    """Flag instruction-injection attempts in learner/lesson content.

    Content is always treated as data; flags are advisory evidence for the
    presenting layer, never obedience.
    """
    if not isinstance(text, str):
        raise ProvenanceError("content to guard must be text")
    flags: List[Dict[str, str]] = []
    for name, pattern in INJECTION_PATTERNS.items():
        match = pattern.search(text)
        if match:
            snippet = text[max(0, match.start() - 20): match.end() + 40]
            flags.append({"flag": name, "snippet": snippet.strip()[:80]})
    return flags


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="learnprint_sources.py",
        description="Source registry and claim provenance checks (fail-closed, no fabrication).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    reg = sub.add_parser("validate-registry", help="validate a source registry JSON")
    reg.add_argument("--registry", required=True)
    reg.set_defaults(func=lambda a: _cli_registry(a))
    chk = sub.add_parser("check-claims", help="cross-check claims against a registry")
    chk.add_argument("--claims", required=True)
    chk.add_argument("--registry", required=True)
    chk.set_defaults(func=lambda a: _cli_claims(a))
    grd = sub.add_parser("guard", help="flag injection attempts in a text file")
    grd.add_argument("--text", required=True)
    grd.set_defaults(func=lambda a: _cli_guard(a))
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ProvenanceError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"NOT_READABLE: {exc}", file=sys.stderr)
        return 2


def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except ValueError as exc:
        raise ProvenanceError(f"{path} is not valid JSON: {exc}") from exc


def _cli_registry(a: Any) -> int:  # type: ignore[no-untyped-def]
    by_id = validate_registry(_read_json(a.registry))
    print(json.dumps({"sources": len(by_id), "valid": True}, ensure_ascii=False))
    return 0


def _cli_claims(a: Any) -> int:
    results = check_claims(_read_json(a.claims), validate_registry(_read_json(a.registry)))
    print(json.dumps(results, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


def _cli_guard(a: Any) -> int:
    with open(a.text, encoding="utf-8") as handle:
        text = handle.read()
    flags = guard_content(text)
    print(json.dumps({"flags": flags, "count": len(flags)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
