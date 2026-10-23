"""Validate the *Git index* before publishing any Courses/ portfolio files.

This is a defense-in-depth local guard, not proof that committed data is safe.
No network, Git writes or external dependencies are used.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

import learnprint_portfolio as portfolio

PREFIX = "Courses/public/"
PERSONAL_SKILLS = (
    ".agents/skills/learnprint-personal/",
    ".claude/skills/learnprint-personal/",
    ".kiro/skills/learnprint-personal/",
    ".gemini/skills/learnprint-personal/",
)

def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=str(root), capture_output=True,
                            timeout=45)
    if result.returncode:
        raise ValueError("git index inspection failed: " +
                         result.stderr.decode("utf-8", errors="replace")[:200])
    return result.stdout

def _indexed(root):
    # Name-only index enumeration cannot distinguish a regular text file from
    # a staged symlink (mode 120000) or submodule (mode 160000). Both can carry
    # Git blobs with valid hashes but violate the reviewed portfolio contract.
    try:
        entries = _git(root, "ls-files", "--stage", "-z").split(b"\x00")
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("unable to inspect Git index") from exc
    found = {}
    for raw in entries:
        if not raw:
            continue
        try:
            metadata, raw_name = raw.split(b"\t", 1)
            mode, _object_id, stage = metadata.split()
        except ValueError as exc:
            raise ValueError("malformed staged Git index entry") from exc
        original = raw_name.decode("utf-8", errors="strict")
        path = original.replace("\\", "/")
        folded = path.casefold()
        # Git can stage a symlink/file at the exact directory name, with no
        # trailing slash. A prefix-only check misses both private roots.
        if folded == "courses":
            raise ValueError("private learner Courses root must never be indexed")
        if any(folded == prefix[:-1].casefold() for prefix in PERSONAL_SKILLS):
            raise ValueError("personal learning skill root must never be indexed")
        # Windows treats case variants as the same filesystem directory, but
        # Git may store alternate casing in its index. Fail closed for those
        # names instead of accidentally omitting private data from the scan.
        sensitive = (path.casefold().startswith("courses/") or
                     any(path.casefold().startswith(prefix.casefold())
                         for prefix in PERSONAL_SKILLS))
        if sensitive:
            if not (path.startswith("Courses/") or path.startswith(PERSONAL_SKILLS)):
                raise ValueError("case-variant private learner path in Git index: " + path)
            if mode != b"100644" or stage != b"0":
                raise ValueError("published learner paths require regular Git blob mode 100644 and stage 0: " + path)
            if path in found:
                raise ValueError("duplicate Git index entry: " + path)
            found[path] = original
    return found

def _blob(root, path):
    try:
        return _git(root, "show", ":" + path)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("unable to read indexed file") from exc

def _validate_package(course_id, relative_blobs):
    if "PUBLICATION.json" not in relative_blobs:
        raise ValueError("public portfolio missing indexed PUBLICATION.json")
    manifest_raw = relative_blobs["PUBLICATION.json"]
    if len(manifest_raw) > 32768:
        raise ValueError("publication index too large")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("invalid publication index JSON") from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "course_id", "visibility", "preview_digest", "files"
    }:
        raise ValueError("invalid publication index keys")
    if (manifest["schema_version"] != "1" or manifest["visibility"] != "public"
            or manifest["course_id"] != course_id):
        raise ValueError("invalid course ID or visibility in publication index")
    files = manifest["files"]
    if not isinstance(files, dict) or len(files) > portfolio.MAX_FILES + 2:
        raise ValueError("invalid publication file listing")
    if not {"README.md", "EVIDENCE.md"}.issubset(files):
        raise ValueError("publication summary and evidence files are required")
    if len(files) < 3:
        raise ValueError("hands-on work required in public portfolio")
    if set(relative_blobs) != set(files) | {"PUBLICATION.json"}:
        raise ValueError("indexed file set does not match approved publication manifest")
    total = 0
    expected = {}
    folded_paths = set()
    for path, checksum in files.items():
        if not isinstance(path, str):
            raise ValueError("invalid published path type")
        folded = path.casefold()
        if folded in folded_paths:
            raise ValueError("case-colliding published artifact paths are forbidden: " + path)
        folded_paths.add(folded)
        if path not in ("README.md", "EVIDENCE.md"):
            portfolio._safe_relative(path)
        if not isinstance(checksum, str) or not re.fullmatch(r"[a-f0-9]{64}", checksum):
            raise ValueError("invalid declared file checksum")
        data = relative_blobs[path]
        if len(data) > portfolio.MAX_FILE_BYTES:
            raise ValueError("published file too large")
        total += len(data)
        if total > portfolio.MAX_TOTAL_BYTES:
            raise ValueError("published portfolio exceeds size budget")
        try:
            text = data.decode("utf-8", "strict")
        except UnicodeError as exc:
            raise ValueError("non-UTF8 publication file") from exc
        if "\x00" in text:
            raise ValueError("binary publication file")
        portfolio._safe_text(text, path, portfolio.MAX_FILE_BYTES)
        actual = hashlib.sha256(data).hexdigest()
        if actual != checksum:
            raise ValueError("published file differs from approved snapshot: " + path)
        expected[path] = actual
    seal = hashlib.sha256(json.dumps({"course_id": course_id, "hashes": expected},
                                    sort_keys=True).encode("utf-8")).hexdigest()
    if seal != manifest["preview_digest"]:
        raise ValueError("publication preview digest does not match file list")
    return len(files) + 1

def check_index(repo):
    root = Path(repo).resolve(strict=True)
    tracked = _indexed(root)
    batches = {}
    for path, original in tracked.items():
        if path.startswith(PERSONAL_SKILLS):
            raise ValueError("personal learning skill must never be tracked: " + path)
        if not path.startswith(PREFIX):
            raise ValueError("private learner records must never be tracked: " + path)
        components = path[len(PREFIX):].split("/")
        if len(components) < 2:
            raise ValueError("invalid Courses/public path")
        key = components[0]
        try:
            parsed = uuid.UUID(key)
        except (TypeError, ValueError) as exc:
            raise ValueError("published directory must use an immutable course UUID") from exc
        if str(parsed) != key:
            raise ValueError("course publication directory must be canonical lowercase UUID")
        inner = "/".join(components[1:])
        if not inner or any(part in ("", ".", "..") or part.startswith(".")
                            for part in components[1:]):
            raise ValueError("invalid public artifact path")
        batches.setdefault(key, {})[inner] = _blob(root, original)
    count = 0
    for cid, indexed_blobs in batches.items():
        count += _validate_package(cid, indexed_blobs)
    return {"status": "OK", "public_courses_checked": len(batches),
            "public_files_checked": count, "private_files_indexed": 0}

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    a = parser.parse_args()
    try:
        print(json.dumps(check_index(a.repo), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, UnicodeError, TypeError) as exc:
        print("PUBLICATION GUARD DENIED:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
