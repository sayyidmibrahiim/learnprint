"""Fail-closed, stdlib-only learner portfolio preview and export.

A curated portfolio is distinct from canonical private learner records.
Exports create a NEW user-approved public snapshot, never modify the
canonical private source course, .gitignore, or Git index.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 262144
MAX_TOTAL_BYTES = 1048576
MAX_FILES = 32
ALLOWED_SUFFIXES = {".py", ".sql", ".js", ".ts", ".txt", ".md", ".mmd", ".json",
                    ".html", ".css", ".sh", ".yaml", ".yml"}
FORBIDDEN_NAMES = {"state.json", "handoff.md", "method-sessions.jsonl",
                   "learning-log.jsonl", "events.jsonl", "registry.json",
                   "approval.json", "profile.json", ".env"}
PATTERNS = {
    "credential": re.compile(r"(?i)\b(?:api[_-]?key|password|secret|access[_-]?token|authorization)\s*[:=]\s*['\"]?[^\s'\"}]{4,}"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[a-z0-9._-]{8,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "email_address": re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b"),
    "home_path": re.compile(r"(?i)(?:[a-z]:[\\/](?:users|documents)[\\/]|/(?:home|users)/[a-z0-9._-]+[/\\])"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
}

def _safe_text(value, field, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field} must be nonempty text (max {limit} characters)")
    if any(ord(c) < 32 and c not in "\r\n\t" for c in value):
        raise ValueError(f"{field} contains control characters")
    for name, pattern in PATTERNS.items():
        if pattern.search(value):
            raise ValueError(f"{field} contains possible private data ({name})")
    return value.strip()

def _safe_relative(value):
    if not isinstance(value, str) or len(value) > 220:
        raise ValueError("artifact path is not a safe relative path")
    if "\\" in value or "\0" in value or value.startswith("/"):
        raise ValueError("artifact path must be POSIX relative with no backslashes")
    parts = value.split("/")
    if len(parts) < 2 or parts[0] != "hands-on":
        raise ValueError("only explicit hands-on/ artifacts may be published")
    # Win32 may silently strip trailing dots from path components, mapping a
    # manifest entry to a different source file/directory than its spelling.
    if any(part.endswith(".") for part in parts):
        raise ValueError("artifact path contains a Windows trailing dot alias")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", part)
           or part.split(".")[0].upper() in
           {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))} for part in parts):
        raise ValueError("artifact path contains hidden, reserved or unsafe segments")
    if any(part.lower() in FORBIDDEN_NAMES or part.lower().endswith(
        (".jsonl", ".bak", ".private", ".key", ".pem")) for part in parts):
        raise ValueError("artifact path names a private or risky file")
    path = PurePosixPath(value)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("unsupported artifact extension (text only)")
    return parts

def _is_reparse_point(path):
    """Detect Windows junctions and other reparse points on Python 3.9+."""
    info = path.lstat()
    return bool(getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _existing_plain_dir(path):
    path = Path(path).absolute()
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError("symlink directory is not a trusted portfolio boundary")
        if item.exists() and _is_reparse_point(item):
            raise ValueError("reparse directory is not a trusted portfolio boundary")
    if not path.is_dir():
        raise ValueError(f"course directory missing: {path}")
    return path

def _snapshot_directory_chain(path):
    """Record approved directory identities, including ancestor boundaries.

    This catches directory swaps that preserve the leaf's inode. It does not
    provide atomic openat-style traversal against an adversarial concurrent
    filesystem writer.
    """
    chain = []
    current = Path(path).absolute()
    for item in (current, *current.parents):
        info = item.lstat()
        if (not stat.S_ISDIR(info.st_mode) or
                getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("directory chain has an untrusted link or reparse point")
        chain.append((item, info.st_dev, info.st_ino))
    return chain


def _assert_directory_chain_unchanged(chain):
    for item, device, inode in chain:
        try:
            info = item.lstat()
        except OSError as exc:
            raise ValueError("directory chain changed during portfolio read") from exc
        if (not stat.S_ISDIR(info.st_mode) or
                (info.st_dev, info.st_ino) != (device, inode) or
                getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise ValueError("directory chain changed during portfolio read")


def _load_manifest(manifest_path, course_id):
    p = Path(manifest_path).absolute()
    # A regular manifest leaf is insufficient: a symlink or Windows junction
    # in any ancestor could redirect the read to an unreviewed location.
    _existing_plain_dir(p.parent)
    parent_chain = _snapshot_directory_chain(p.parent)
    before = p.lstat()
    if (not stat.S_ISREG(before.st_mode) or
            getattr(before, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400) or
            before.st_size > 32768):
        raise ValueError("manifest must be a small, regular, non-link JSON file")
    if before.st_nlink != 1:
        raise ValueError("multiply linked manifest is not an isolated source")
    # Avoid following a replacement symlink where O_NOFOLLOW is available.
    # Check descriptor identity and size after opening even on Windows.
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as reader:
        opened = os.fstat(reader.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or
                opened.st_size > 32768 or
                (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError("manifest changed identity or became multiply linked")
        raw = reader.read(32769)
        finished = os.fstat(reader.fileno())
        if ((finished.st_size, finished.st_mtime_ns) !=
                (opened.st_size, opened.st_mtime_ns)):
            raise ValueError("manifest changed while being read")
    after = p.lstat()
    if ((after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino) or
            after.st_nlink != 1 or not stat.S_ISREG(after.st_mode) or
            getattr(after, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
        raise ValueError("manifest path changed or became multiply linked")
    _assert_directory_chain_unchanged(parent_chain)
    if len(raw) > 32768:
        raise ValueError("manifest exceeds size limit")
    m = json.loads(raw.decode("utf-8"))
    if not isinstance(m, dict) or m.get("schema_version") != "1":
        raise ValueError("unsupported portfolio manifest schema")
    if m.get("course_id") != course_id:
        raise ValueError("portfolio manifest course_id does not match registered course")
    if m.get("visibility") not in ("public", "private"):
        raise ValueError("visibility must be public or private")
    if m["visibility"] == "private":
        return m
    unknown = set(m) - {"schema_version", "course_id", "visibility", "title", "summary",
                        "artifacts", "achievements"}
    if unknown:
        raise ValueError("unknown portfolio manifest fields")
    _safe_text(m.get("title"), "title", 120)
    _safe_text(m.get("summary"), "summary", 1500)
    if not isinstance(m.get("artifacts"), list) or not m["artifacts"]:
        raise ValueError("public portfolio needs real hands-on artifacts")
    if len(m["artifacts"]) > MAX_FILES:
        raise ValueError("too many artifacts")
    if not isinstance(m.get("achievements", []), list) or len(m.get("achievements", [])) > 30:
        raise ValueError("achievements must be a bounded list")
    return m

def _load_artifacts(directory, m):
    result, total, seen = [], 0, set()
    for index, item in enumerate(m["artifacts"]):
        if not isinstance(item, dict) or set(item) != {"path", "origin"}:
            raise ValueError("each artifact requires only path and origin")
        if item["origin"] not in ("learner_authored", "ai_assisted", "third_party"):
            raise ValueError("invalid artifact origin")
        parts = _safe_relative(item["path"])
        key = item["path"].casefold()
        if key in seen:
            raise ValueError("duplicate or case-colliding artifact")
        seen.add(key)
        path = directory
        for part in parts:
            path = path / part
            if path.is_symlink():
                raise ValueError("symlink artifacts or parent directories are forbidden")
            if _is_reparse_point(path):
                raise ValueError("reparse artifacts or parent directories are forbidden")
        parent_chain = _snapshot_directory_chain(path.parent)
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("missing or nonregular artifact: " + item["path"])
        if before.st_nlink != 1:
            raise ValueError("multiply linked artifact is not an isolated source: " + item["path"])
        if before.st_size > MAX_FILE_BYTES:
            raise ValueError("artifact exceeds per-file size limit")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as reader:
            opened = os.fstat(reader.fileno())
            if (not stat.S_ISREG(opened.st_mode) or
                    (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
                raise ValueError("artifact changed type or identity while opening")
            if opened.st_nlink != 1:
                raise ValueError("multiply linked artifact while opening: " + item["path"])
            data = reader.read(MAX_FILE_BYTES + 1)
        after = path.lstat()
        if (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("artifact changed identity while reading")
        if after.st_nlink != 1:
            raise ValueError("multiply linked artifact while reading: " + item["path"])
        _assert_directory_chain_unchanged(parent_chain)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("artifact exceeds per-file size limit")
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("portfolio exceeds total size limit")
        text = data.decode("utf-8")
        if "\0" in text:
            raise ValueError("binary/NUL content not allowed")
        _safe_text(text, "artifact[" + str(index) + "]", MAX_FILE_BYTES)
        # Export a canonical LF snapshot. Git on Windows may clean CRLF to LF
        # while staging, otherwise the staged blob would differ from preview.
        clean = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        result.append({"path": item["path"], "origin": item["origin"],
                       "sha256": hashlib.sha256(clean).hexdigest(), "_content": clean})
    return result

def _validate_achievements(m, artifacts):
    known = {a["path"] for a in artifacts}
    validated = []
    for i, row in enumerate(m.get("achievements", [])):
        if (not isinstance(row, dict)
                or not {"claim", "evidence_path", "basis"} <= set(row)
                or set(row) - {"claim", "evidence_path", "basis", "reviewer",
                               "evaluation_ref"}):
            raise ValueError("achievement requires claim, evidence_path and basis")
        if row["basis"] not in ("self_reported", "ai_reviewed", "human_reviewed"):
            raise ValueError("unknown achievement basis")
        reviewer = row.get("reviewer", "")
        evaluation_ref = row.get("evaluation_ref", "")
        # Accountability honesty: a human review claim names its human, an AI
        # review claim names its deterministic evaluation record, and a 
        # self-report carries neither (labels gate nothing; they are labels).
        if row["basis"] == "human_reviewed":
            if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 80:
                raise ValueError("human_reviewed achievement must name the reviewer "
                                 "(max 80 chars); anonymous human review is forbidden")
        elif reviewer:
            raise ValueError("only human_reviewed achievements may carry a reviewer label")
        if row["basis"] == "ai_reviewed":
            if not isinstance(evaluation_ref, str) or not evaluation_ref.strip() or len(evaluation_ref) > 120:
                raise ValueError("ai_reviewed achievement must reference its evaluation "
                                 "record (max 120 chars)")
        elif evaluation_ref:
            raise ValueError("only ai_reviewed achievements may carry an evaluation reference")
        if row["evidence_path"] not in known:
            raise ValueError("achievement evidence must link to an included hands-on artifact")
        entry = {"claim": _safe_text(row["claim"], f"achievement[{i}]", 300),
                 "evidence_path": row["evidence_path"], "basis": row["basis"]}
        if reviewer:
            entry["reviewer"] = _safe_text(reviewer, f"achievement[{i}].reviewer", 80)
        if evaluation_ref:
            entry["evaluation_ref"] = _safe_text(evaluation_ref,
                                                 f"achievement[{i}].evaluation_ref", 120)
        validated.append(entry)
    return validated

def prepare(course_dir, course_id, manifest_path):
    directory = _existing_plain_dir(course_dir)
    m = _load_manifest(manifest_path, course_id)
    if m["visibility"] == "private":
        return {"status": "private", "course_id": course_id, "publishable": False,
                "files": [], "files_modified": 0}, {}
    artifacts = _load_artifacts(directory, m)
    achievements = _validate_achievements(m, artifacts)
    # Markdown metacharacters in plain summary fields must not create links/images.
    title = _safe_text(m["title"], "title", 120)
    summary = _safe_text(m["summary"], "summary", 1500)
    for value in (title, summary, *(a["claim"] for a in achievements)):
        if any(ord(char) < 32 or char in "<>[]!#*_|" or
               char in (chr(96), chr(92)) for char in value):
            raise ValueError("portfolio free-text contains markup requiring human review")
    readme = ("# " + title + "\n\n" + summary + "\n\n"
              "## Practical artifacts\n\n" +
              "".join("- " + a["path"] + " (origin: " + a["origin"] +
                      "; SHA-256: " + a["sha256"] + ")\n" for a in artifacts) +
              "\nThis is a learner portfolio, not an accredited certificate.\n")
    evidence = ("# Learning evidence (self-documented)\n\n"
                "The basis labels below are learner-supplied metadata, not independently "
                "authenticated reviewer identities.\n\n")
    evidence += "".join(
        "- " + a["claim"] + " | " + a["basis"] + " | " + a["evidence_path"]
        + (" | reviewer: " + a["reviewer"] if a.get("reviewer") else "")
        + (" | evaluation: " + a["evaluation_ref"] if a.get("evaluation_ref") else "")
        + "\n"
        for a in achievements)
    if not achievements:
        evidence += "No verified achievement claims are included.\n"
    output = {"README.md": readme.encode("utf-8"),
              "EVIDENCE.md": evidence.encode("utf-8")}
    output.update({a["path"]: a["_content"] for a in artifacts})
    hashes = {k: hashlib.sha256(v).hexdigest() for k, v in sorted(output.items())}
    seal = hashlib.sha256(json.dumps({"course_id": course_id, "hashes": hashes},
                                    sort_keys=True).encode("utf-8")).hexdigest()
    index = {"schema_version": "1", "course_id": course_id, "visibility": "public",
             "preview_digest": seal, "files": hashes}
    output["PUBLICATION.json"] = (json.dumps(index, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return {"status": "preview", "course_id": course_id, "publishable": True,
            "files": [{"path": k, "sha256": hashlib.sha256(v).hexdigest()}
                      for k, v in sorted(output.items())],
            "preview_digest": seal, "files_modified": 0,
            "warning": "Inspect every file before publishing; scanning is not proof of privacy."}, output

def export(course_dir, course_id, manifest_path, target, preview_digest, approve):
    if not approve:
        raise ValueError("explicit --approve required to export portfolio snapshot")
    preview, output = prepare(course_dir, course_id, manifest_path)
    if not preview.get("publishable"):
        raise ValueError("private course cannot be exported")
    if preview_digest != preview["preview_digest"]:
        raise ValueError("preview digest mismatch: preview again before export")
    destination = Path(target).absolute()
    directory = _existing_plain_dir(course_dir)
    if destination == directory or directory in destination.parents or destination in directory.parents:
        raise ValueError("export target must be separate from private Courses workspace")
    if destination.exists() or destination.is_symlink():
        raise ValueError("refusing to overwrite an existing export directory")
    parent = _existing_plain_dir(destination.parent)
    parent_chain = _snapshot_directory_chain(parent)
    # A stage directory is created only after full validation. Cleanup on failure.
    stage = Path(tempfile.mkdtemp(prefix=".learnprint-portfolio-", dir=str(parent)))
    try:
        _assert_directory_chain_unchanged(parent_chain)
        for rel, data in output.items():
            target_path = stage.joinpath(*PurePosixPath(rel).parts)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("xb") as f:
                f.write(data)
        _assert_directory_chain_unchanged(parent_chain)
        if destination.exists() or destination.is_symlink():
            raise ValueError("export destination appeared during staging")
        os.rename(str(stage), str(destination))
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {"status": "exported", "course_id": course_id,
            "destination": str(destination), "file_count": len(output),
            "preview_digest": preview["preview_digest"],
            "git_published": False}
