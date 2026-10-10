#!/usr/bin/env python3
"""Copy portable Learnprint skills into project-specific discovery directories safely."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "opencode": ".opencode/skills", "codex": ".agents/skills", "claude": ".claude/skills",
    "gemini": ".gemini/skills", "kiro": ".kiro/skills", "antigravity": ".agents/skills",
}
PERSONAL_SKILL = "learnprint-personal"
PACKAGED_SKILLS = ("learnprint-assess", "learnprint-learn")

HOOK_SCRIPT = """#!/bin/sh
# Learnprint privacy guard: reject staged learner data.
if git diff --cached --name-only | grep -qE '^(Courses/|\\.agents/skills/learnprint-personal/|\\.claude/skills/learnprint-personal/|\\.kiro/skills/learnprint-personal/|\\.gemini/skills/learnprint-personal/)'; then
    echo "ERROR: Attempting to commit private learner data. Remove with: git reset HEAD <file>"
    exit 1
fi
"""


def _fail(msg):
    print("ERROR:", msg, file=sys.stderr)
    return 2


def is_gitignored(path, repo_root=None):
    """True iff git check-ignore covers path. False (safe default) if git
    is unavailable or the path is outside any repo."""
    path = Path(path)
    if repo_root is None:
        for parent in ([path] if path.is_dir() else []) + list(path.parents):
            if (parent / ".git").exists():
                repo_root = parent
                break
        else:
            return False
    try:
        r = subprocess.run(["git", "check-ignore", "-q", str(path)],
                           cwd=str(repo_root),
                           capture_output=True, timeout=30)
        if r.returncode == 0:
            return True
        # Directory-intent destinations (skill dirs): a trailing-slash
        # pattern only matches when git treats the path as a directory.
        r = subprocess.run(["git", "check-ignore", "-q", str(path).rstrip("/\\") + "/"],
                           cwd=str(repo_root),
                           capture_output=True, timeout=30)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def install_skills(dest, target, dry_run=False, approve=False):
    """Copy packaged public skills to the host discovery dir under dest."""
    dest = Path(dest).expanduser().resolve()
    if not dest.is_dir():
        return _fail(f"Project directory does not exist: {dest}")
    if not (dest / ".git").exists():
        print("NOTICE: destination is not a git root; verify this is really your project")
    targets = [(ROOT / "skills" / n, dest / TARGETS[target] / n) for n in PACKAGED_SKILLS]
    for src, dst in targets:
        print(f"{src} -> {dst} {'(DRY RUN)' if dry_run else ''}")
        if dst.exists():
            return _fail(f"Refusing to overwrite existing skill {dst}")
        if not (src / "SKILL.md").exists():
            return _fail(f"Missing packaged skill {src}")
    if dry_run:
        return 0
    if not approve:
        return _fail("Pass --approve to explicitly permit writing to project")
    for src, dst in targets:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
    print("INSTALLED. Check skills in your target app; native loading not verified by this installer.")
    return 0


def ensure_gitignored(repo_root, rel_path):
    """Append rel_path to repo .gitignore unless already covered."""
    repo_root = Path(repo_root).expanduser().resolve()
    if is_gitignored(repo_root / rel_path, repo_root):
        return 0
    gi = repo_root / ".gitignore"
    with gi.open("a", encoding="utf-8") as fh:
        fh.write(f"\n# Learnprint self-install ({rel_path})\n{rel_path}\n")
    print(f"Added {rel_path} to {gi}")
    return 0


def install_personal_skill(source, dest_skill_dir, dry_run=False, approve=False):
    """Copy a GENERATED personal skill to a host discovery directory.

    Refuses unless the destination is gitignored (public-repo safety),
    refuses overwrites, requires --approve.
    """
    src = Path(source).expanduser().resolve() / ".agents" / "skills" / PERSONAL_SKILL
    dst = Path(dest_skill_dir).expanduser().resolve()
    print(f"{src} -> {dst} {'(DRY RUN)' if dry_run else ''}")
    if not (src / "SKILL.md").exists():
        return _fail(f"No generated personal skill at {src}; run learnprint.py generate first")
    if dst.exists():
        return _fail(f"Refusing to overwrite existing skill {dst}")
    if not is_gitignored(dst):
        return _fail(f"Destination {dst} is not gitignored; refusing to place private data there")
    if dry_run:
        return 0
    if not approve:
        return _fail("Pass --approve to explicitly permit writing the personal skill")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    print("INSTALLED personal skill (private, gitignored).")
    return 0


def install_hooks(dest, dry_run=False, approve=False):
    """Install the privacy pre-commit hook into dest/.git/hooks/."""
    dest = Path(dest).expanduser().resolve()
    hook = dest / ".git" / "hooks" / "pre-commit"
    if not (dest / ".git").exists():
        return _fail(f"Not a git checkout: {dest}")
    print(f"write {hook} {'(DRY RUN)' if dry_run else ''}")
    if hook.exists():
        return _fail(f"Refusing to overwrite existing hook {hook}")
    if dry_run:
        return 0
    if not approve:
        return _fail("Pass --approve to explicitly permit installing the hook")
    hook.write_text(HOOK_SCRIPT, encoding="utf-8")
    print("INSTALLED pre-commit privacy hook.")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", required=True, choices=sorted(TARGETS))
    p.add_argument("--dest", help="Exact project root (defaults to this repo with --self)")
    p.add_argument("--self", action="store_true",
                   help="Install into this repository itself; discovery dirs are added to .gitignore")
    p.add_argument("--personal-skill", action="store_true",
                   help="Also install the generated personal skill (requires --source)")
    p.add_argument("--source",
                   help="Courses/.learnprint dir holding the generated personal skill")
    p.add_argument("--hooks", action="store_true", help="Install the privacy pre-commit hook")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--approve", action="store_true", help="Explicitly approve file writes")
    a = p.parse_args(argv)
    if a.dest is None and not a.self:
        print("ERROR: --dest required (or use --self)", file=sys.stderr)
        return 2
    dest = Path(a.dest).expanduser().resolve() if a.dest else ROOT
    if a.hooks:
        return install_hooks(dest, a.dry_run, a.approve)
    if a.personal_skill:
        if not a.source:
            return _fail("--personal-skill requires --source <Courses/.learnprint>")
        # Preflight BEFORE any writes so a refused personal install leaves
        # no partial packaged-skill behind.
        rc = install_personal_skill(a.source, dest / TARGETS[a.target] / PERSONAL_SKILL,
                                    dry_run=True)
        if rc != 0:
            return rc
    rc = install_skills(dest, a.target, a.dry_run, a.approve)
    if rc != 0:
        return rc
    if a.self:
        for n in PACKAGED_SKILLS:
            rel = f"{TARGETS[a.target]}/{n}/"
            print(f"{ROOT / 'skills' / n} -> {dest / TARGETS[a.target] / n}")
            rc = ensure_gitignored(dest, rel)
            if rc != 0:
                return rc
    if a.personal_skill:
        return install_personal_skill(a.source, dest / TARGETS[a.target] / PERSONAL_SKILL,
                                      a.dry_run, a.approve)
    return 0


if __name__ == "__main__":
    sys.exit(main())
