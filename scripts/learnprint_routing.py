#!/usr/bin/env python3
"""Learnprint deterministic routing library. Stdlib only; no LLM, no I/O.

Imported by scripts/learnprint.py (never a standalone CLI). Covers Step
3.2a/3.3/3.3a: normalization, slugs, immutable identity, registry lookup,
parent-scoped classification gate. Filesystem orchestration lives in
learnprint.py, which reuses these primitives.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid

CANONICAL_CATEGORIES = {
    "languages": {"label": "Languages", "aliases": ["bahasa", "language", "linguistics"]},
    "science": {"label": "Science", "aliases": ["sains", "ipa", "natural-science"]},
    "mathematics": {"label": "Mathematics", "aliases": ["math", "matematika", "numeracy"]},
    "technology": {"label": "Technology",
                   "aliases": ["tech", "komputer", "computing", "it", "programming"]},
    "business": {"label": "Business",
                 "aliases": ["bisnis", "economics", "ekonomi", "management"]},
    "arts": {"label": "Arts",
             "aliases": ["seni", "art", "creative", "music", "design"]},
    "health": {"label": "Health",
               "aliases": ["kesehatan", "medicine", "kedokteran", "fitness"]},
    "life": {"label": "Life Skills",
             "aliases": ["kehidupan", "personal-development", "productivity"]},
}
MAX_CATEGORY_DEPTH = 3
_COURSE_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_PUNCT = re.compile(r"[^\w\s-]", re.UNICODE)
_SPACES = re.compile(r"[\s_-]+", re.UNICODE)


def normalize_key(text):
    """Canonical form for every lookup and collision comparison.

    NFC → casefold → punctuation removal → separator collapsing. Text
    normalization ONLY: never corrects spelling, never equates semantics.
    """
    s = unicodedata.normalize("NFC", text or "")
    s = s.casefold()
    s = _PUNCT.sub(" ", s)
    s = _SPACES.sub("-", s.strip())
    return s.strip("-")


def slugify(title):
    """Filesystem-safe slug. Non-Latin titles that fold to empty fall back
    to topic-<sha8>; the title itself is always preserved separately."""
    folded = "".join(c for c in unicodedata.normalize("NFKD", title or "")
                     if not unicodedata.combining(c))
    s = "".join(c if c.isascii() and c.isalnum() else "-" for c in folded.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "topic-" + hashlib.sha256(
            unicodedata.normalize("NFC", title or "").encode("utf-8")).hexdigest()[:8]
    return s


def is_course_id(value):
    """Public predicate: value is a well-formed immutable course UUID."""
    return isinstance(value, str) and bool(_COURSE_ID_RE.match(value))


def allocate_course_id(registry):
    """Allocate an immutable UUIDv4 course_id, never derived from mutable
    title/category/path/slug. Registry uniqueness check rejects collisions."""
    new_id = str(uuid.uuid4())
    if any(c.get("course_id") == new_id for c in registry.get("courses", [])):
        raise ValueError(f"course_id collision (retry allocation): {new_id}")
    return new_id


def resolve_course(query, registry):
    """Deterministic lookup: found / ambiguous / not_found. Never guesses."""
    for c in registry.get("courses", []):
        if c.get("course_id") == query:
            return {"status": "found", "course": c, "matched_by": "course_id"}
    qn = normalize_key(query)
    for c in registry.get("courses", []):
        if qn in c.get("normalized_aliases", []):
            return {"status": "found", "course": c, "matched_by": "alias"}
    matches = [c for c in registry.get("courses", [])
               if c.get("normalized_title") == qn]
    if len(matches) == 1:
        return {"status": "found", "course": matches[0], "matched_by": "title"}
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "candidates": [
                {"course_id": c["course_id"], "title": c["title"],
                 "category_path": c["category_path"], "rel_path": c["rel_path"]}
                for c in matches
            ],
            "reason": "normalized title matches multiple courses",
        }
    return {"status": "not_found", "normalized_query": qn,
            "sibling_hints": sorted({c.get("category_path", "")
                                     for c in registry.get("courses", [])})}


def _direct_children(parent_path, registry):
    """Normalized → canonical names of categories exactly one level below
    parent_path ("" = root level is handled by the caller via taxonomy).

    Any registry path passing THROUGH the parent contributes its next
    segment, so intermediate directories count even when no course sits
    directly at that level.
    """
    parent_segs = [s for s in parent_path.strip("/").split("/") if s]
    kids = {}
    for c in registry.get("courses", []):
        segs = [s for s in c.get("category_path", "").strip("/").split("/") if s]
        if len(segs) > len(parent_segs) and segs[:len(parent_segs)] == parent_segs:
            nxt = segs[len(parent_segs)]
            kids.setdefault(normalize_key(nxt), nxt)
    return kids


def validate_classification(category_path, registry, allow_new_top=False):
    """Parent-scoped deterministic pre-creation gate.

    Maintains the full canonical parent path; inspects ONLY direct children
    of each resolved parent. Returns (ok, result) with per-segment verdicts:
    "reuse" (exact normalized/alias match → canonical spelling, descend) or
    "new-needs-confirmation" (requires --confirm-new-segment per segment).
    Never fuzzy-matches, never auto-corrects spelling.
    """
    segs = [s for s in (category_path or "").strip("/").split("/") if s]
    if not segs:
        return (False, "empty category path")
    if len(segs) > MAX_CATEGORY_DEPTH:
        return (False, f"category depth {len(segs)} exceeds {MAX_CATEGORY_DEPTH}")

    root = segs[0]
    root_names = {normalize_key(k) for k in CANONICAL_CATEGORIES}
    root_names |= {normalize_key(a) for meta in CANONICAL_CATEGORIES.values()
                   for a in meta.get("aliases", [])}
    if normalize_key(root) not in root_names and not allow_new_top:
        return (False, f"unknown top-level category '{root}'; "
                       f"known: {sorted(CANONICAL_CATEGORIES)}. "
                       "Proposing a new root requires --approve-new-category "
                       "and user confirmation.")

    resolved, verdicts, new_segments = [], [], []
    for i, s in enumerate(segs):
        parent = "/".join(resolved)
        if i == 0:
            root_pool = {}
            for key, meta in CANONICAL_CATEGORIES.items():
                root_pool[normalize_key(key)] = key
                for a in meta.get("aliases", []):
                    root_pool.setdefault(normalize_key(a), key)
            n = normalize_key(s)
            if n in root_pool:
                resolved.append(root_pool[n])
                verdicts.append({"segment": s, "verdict": "reuse",
                                 "resolved_as": root_pool[n], "parent": "(root)"})
            else:
                verdicts.append({"segment": s, "verdict": "new-needs-confirmation",
                                 "parent": "(root)",
                                 "candidates": sorted(root_pool.values())})
                resolved.append(s)
                new_segments.append(s)
            continue
        pool = _direct_children(parent, registry)
        n = normalize_key(s)
        if n in pool:
            resolved.append(pool[n])
            verdicts.append({"segment": s, "verdict": "reuse",
                             "resolved_as": pool[n], "parent": parent})
        else:
            verdicts.append({"segment": s, "verdict": "new-needs-confirmation",
                             "parent": parent,
                             "candidates": sorted(pool.values())})
            resolved.append(s)
            new_segments.append(s)
    if new_segments:
        return (True, {"verdict": "new-needs-confirmation",
                       "resolved_path": "/".join(resolved),
                       "segments": verdicts,
                       "requires_flags": [f"--confirm-new-segment {s}"
                                          for s in new_segments]})
    return (True, {"verdict": "reuse", "resolved_path": "/".join(resolved),
                   "segments": verdicts})
