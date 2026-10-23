"""Conservative generated course docs from canonical structured plans (Python 3.9+).

Only replace known new-course stubs or byte-verified prior generated output.
Never mutate state.json, the evidence ledger or learner-authored documents.
"""
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from learnprint_portfolio import (
    _assert_directory_chain_unchanged,
    _snapshot_directory_chain,
)

MARKER = "<!-- LEARNPRINT DERIVED; BODY-SHA256: {} -->"
MAX_DOC_SIZE = 256 * 1024


def _read_plain_document(target):
    """Bounded, no-follow best-effort read; refuse linked/replaced files."""
    before = target.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
            getattr(before, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400) or
            before.st_size > MAX_DOC_SIZE):
        raise ValueError("course document is not an isolated regular file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or
                (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError("course document changed while opening")
        content = stream.read(MAX_DOC_SIZE + 1)
        finished = os.fstat(stream.fileno())
        if (len(content) > MAX_DOC_SIZE or
                (opened.st_size, opened.st_mtime_ns) !=
                (finished.st_size, finished.st_mtime_ns)):
            raise ValueError("course document changed while reading")
    after = target.lstat()
    if ((after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
            or after.st_nlink != 1 or not stat.S_ISREG(after.st_mode)
            or getattr(after, "st_file_attributes", 0) &
            getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
        raise ValueError("course document path changed while reading")
    return content


def _escape_md(value):
    raw = str(value if value is not None else "").strip()
    return " ".join(raw.replace("|", "\\|").replace("\r", " ").split())


def _mermaid(value):
    raw = _escape_md(value)
    safe = re.sub(r"[^\w .,:;()/?+-]", " ", raw, flags=re.UNICODE)
    return " ".join(safe.split())[:120] or "Untitled"


def _seal(body):
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return MARKER.format(digest) + "\n" + body


def _generated_intact(existing):
    head, sep, body = existing.partition("\n")
    prefix = "<!-- LEARNPRINT DERIVED; BODY-SHA256: "
    if not sep or not head.startswith(prefix) or not head.endswith(" -->"):
        return False
    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return head == MARKER.format(actual)


def _render(plan, registry):
    units = plan["units"]
    title = _escape_md(plan.get("title", "Course"))
    goal = _escape_md(plan.get("goal", ""))
    lines = [f"# {title}: syllabus", "",
             f"Course ID: `{plan['course_id']}`", "",
             f"Goal: {goal}", "",
             "Source: structured state.json plan, not an assessment certificate.", ""]
    for i, unit in enumerate(units, 1):
        needs = ", ".join(unit.get("requires", [])) or "none"
        lines += [
            f"## Unit {i}: {_escape_md(unit['title'])}", "",
            f"- Unit ID: `{unit['unit_id']}`",
            f"- Outcome: {_escape_md(unit['outcome'])}",
            f"- Prerequisites: {_escape_md(needs)}",
            f"- Practice: {_escape_md(unit['hands_on'])}",
            f"- Success check: {_escape_md(unit['success_check'])}",
            f"- Evidence: {unit.get('evidence_status', 'not_assessed')} "
            "(see canonical ledger; agent notes are not proof)", "",
        ]
    syllabus = _seal("\n".join(lines).rstrip() + "\n")
    ids = {u["unit_id"]: f"u{i}" for i, u in enumerate(units, 1)}
    diagram = ["flowchart TD"]
    for unit in units:
        diagram.append(f'    {ids[unit["unit_id"]]}["{_mermaid(unit["title"])}"]')
    for unit in units:
        for req in unit.get("requires", []):
            diagram.append(f'    {ids[req]} --> {ids[unit["unit_id"]]}')
    mapped = _seal("\n".join(diagram) + "\n")
    handoff = [
        f"# Handoff: {title}", "",
        "Derived summary, not independent evidence of learning.", "",
        f"Course ID: `{plan['course_id']}`",
        f"Goal: {goal}",
        f"Structured units: {len(units)}", "",
    ]
    for i, unit in enumerate(units, 1):
        handoff.append(
            f"- {i}. {_escape_md(unit['title'])}: "
            f"{unit.get('evidence_status', 'not_assessed')}"
        )
    handoff += ["", "Next: read canonical `course plan` and ledger review queue;",
                "ask learner what to work on before grading.", ""]
    course_handoff = _seal("\n".join(handoff))
    registry_lines = [
        "# Learnprint workspace handoff", "",
        f"Registered courses: {len(registry.get('courses', []))}", "",
    ]
    for c in registry.get("courses", []):
        registry_lines.append(
            f"- {_escape_md(c.get('title', 'Untitled'))} "
            f"(`{c['course_id']}`)"
        )
    registry_lines += ["", "Courses and evidence stay private. No automatic GitHub push.", ""]
    root_handoff = _seal("\n".join(registry_lines))
    return {
        "SYLLABUS.md": syllabus,
        "MAP.mmd": mapped,
        "HANDOFF.md": course_handoff,
        "../root-HANDOFF": root_handoff,
    }


def _known_scaffold(name, title):
    if name == "SYLLABUS.md":
        return f"# {title} — syllabus\n"
    if name == "MAP.mmd":
        return "flowchart TD\n"
    if name == "HANDOFF.md":
        return f"# Handoff — {title}\n"
    return "# Learnprint handoff\n\nWorkspace initialized. No courses yet.\n"


def verify_unchanged_targets(preview, targets):
    """Recheck each exact pre-image without changing any course artifacts.

    Used immediately before a consented docs-sync. The workspace lock
    coordinates Learnprint writers; external adversarial swap races remain
    outside the guarantee of portable Python path-based file operations.
    """
    rows = preview.get("files")
    if not isinstance(rows, list) or len(rows) != len(targets):
        raise ValueError("invalid docs preview target inventory")
    originals = {}
    for (target, _content), row in zip(targets.items(), rows):
        parent_chain = _snapshot_directory_chain(target.parent)
        if target.is_symlink():
            raise ValueError("course document became a linked file")
        if target.exists():
            raw = _read_plain_document(target)
            actual = hashlib.sha256(raw).hexdigest()
        else:
            raw, actual = None, None
        if actual != row.get("original_sha256"):
            raise ValueError("course document changed after preview; retry before writing")
        _assert_directory_chain_unchanged(parent_chain)
        originals[target] = raw
    return originals


def preview_documents(root, course_dir, plan, registry):
    """Return (read-only preview with SHA, validated write plan).

    All existing paths must be plain unlinked files, matching scaffolds or
    checksum-sealed generated content. Unknown user edits block every write.
    """
    if not plan.get("units"):
        raise ValueError("cannot materialize syllabus with no structured plan")
    from_path = Path(course_dir)
    root = Path(root)
    # Reject directory symlinks/junctions and capture ancestor identity.
    # Filesystem transactions remain best-effort, not protection from an
    # adversarial writer with permission to swap directories continuously.
    chains = [_snapshot_directory_chain(root),
              _snapshot_directory_chain(from_path)]
    derived = _render(plan, registry)
    targets = {}
    rows = []
    hash_input = hashlib.sha256()
    for name, content in derived.items():
        target = root / "HANDOFF.md" if name == "../root-HANDOFF" else from_path / name
        parent_chain = _snapshot_directory_chain(target.parent)
        if target.is_symlink():
            raise ValueError(f"refusing to replace linked course document: {target.name}")
        if target.exists():
            old = _read_plain_document(target).decode("utf-8")
            # Windows Path.write_text(newline=None) created CRLF stubs in
            # some existing courses. Match only the known scaffold with
            # normalized line endings; hash the EXACT old bytes for consent.
            scaffold_text = old.replace("\r\n", "\n")
            if old == content:
                status = "unchanged"
            elif (scaffold_text == _known_scaffold(name, plan["title"])
                  or _generated_intact(old)):
                status = "refresh_generated_or_scaffold"
            else:
                raise ValueError(f"unmanaged/manual course document preserved: {target.name}")
        else:
            old = None
            status = "create"
        _assert_directory_chain_unchanged(parent_chain)
        hash_input.update(name.encode("utf-8") + b"\0")
        hash_input.update(hashlib.sha256((old or "").encode("utf-8")).digest())
        hash_input.update(hashlib.sha256(content.encode("utf-8")).digest())
        targets[target] = content
        rows.append({"file": name, "status": status,
                     "original_sha256": (
                         hashlib.sha256(old.encode("utf-8")).hexdigest()
                         if old is not None else None),
                     "proposed_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()})
    for chain in chains:
        _assert_directory_chain_unchanged(chain)
    return ({"status": "validated_read_only_preview", "course_id": plan["course_id"],
             "preview_digest": hash_input.hexdigest(), "files": rows,
             "private": True, "changes_publication": False}, targets)
