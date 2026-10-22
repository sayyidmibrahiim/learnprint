#!/usr/bin/env python3
"""Copy portable Learnprint skills into project-specific discovery directories safely."""
import argparse
import os
import shutil
import stat
import tempfile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "opencode": ".opencode/skills", "codex": ".agents/skills", "claude": ".claude/skills",
    "gemini": ".gemini/skills", "kiro": ".kiro/skills", "antigravity": ".agents/skills",
}
PERSONAL_SKILL = "learnprint-personal"
PACKAGED_SKILLS = ("learnprint", "learnprint-assess", "learnprint-learn")

LEGACY_HOOK_SCRIPT = """#!/bin/sh
# Learnprint privacy guard: reject staged learner data.
if git diff --cached --name-only | grep -qE '^(Courses/|\\.agents/skills/learnprint-personal/|\\.claude/skills/learnprint-personal/|\\.kiro/skills/learnprint-personal/|\\.gemini/skills/learnprint-personal/)'; then
    echo "ERROR: Attempting to commit private learner data. Remove with: git reset HEAD <file>"
    exit 1
fi
"""

HOOK_SCRIPT = """#!/bin/sh
# Learnprint indexed portfolio privacy guard (v2).
# Fail closed without the Python verifier; never bypass sensitive files.
if command -v python >/dev/null 2>&1; then
    python scripts/learnprint_publish_guard.py --repo . || exit 1
elif command -v python3 >/dev/null 2>&1; then
    python3 scripts/learnprint_publish_guard.py --repo . || exit 1
else
    echo "ERROR: Python 3 is required for Learnprint privacy checks" >&2
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
    git_dir = dest / ".git"
    if not git_dir.is_dir() or git_dir.is_symlink():
        return _fail(f"Not a regular Git checkout directory: {dest}")
    if not hook.parent.is_dir() or hook.parent.is_symlink():
        return _fail(f"Refusing unsafe Git hooks directory: {hook.parent}")
    # An alternate core.hooksPath makes .git/hooks/pre-commit inactive. Do not
    # claim to install a working privacy gate at a location Git will not run.
    # Query effective config (including global/system), not only local config.
    try:
        configured = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"], cwd=str(dest),
            capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        return _fail(f"Cannot verify active Git hooks path: {exc}")
    if configured.returncode == 0:
        return _fail("Refusing hook install: Git core.hooksPath overrides .git/hooks")
    if configured.returncode != 1:
        return _fail("Cannot verify active Git hooks path (git config failed)")
    # Never follow a linked hook, including dangling symlinks. Upgrading a
    # legacy hook in place would otherwise also overwrite a hardlink target.
    if hook.is_symlink() or (hook.exists() and hook.stat().st_nlink != 1):
        return _fail(f"Refusing linked pre-commit hook: {hook}")
    print(f"write {hook} {'(DRY RUN)' if dry_run else ''}")
    guard = dest / "scripts" / "learnprint_publish_guard.py"
    # Other projects without the verifier receive the legacy deny-all hook.
    # The full index-aware policy is only installed where its verifier exists.
    portfolio = dest / "scripts" / "learnprint_portfolio.py"
    desired = HOOK_SCRIPT if guard.is_file() and portfolio.is_file() else LEGACY_HOOK_SCRIPT
    original_identity = None
    if hook.exists():
        original_info = hook.lstat()
        original_identity = (original_info.st_dev, original_info.st_ino)
        prior = hook.read_text(encoding="utf-8").replace("\r\n", "\n")
        if prior == desired:
            return _fail(f"Refusing to overwrite existing hook {hook}")
        if prior != LEGACY_HOOK_SCRIPT or desired != HOOK_SCRIPT:
            return _fail(f"Refusing to overwrite non-upgradable hook {hook}")
        print(f"upgrade verified legacy hook {hook} {'(DRY RUN)' if dry_run else ''}")
    if dry_run:
        return 0
    if not approve:
        return _fail("Pass --approve to explicitly permit installing/upgrading the hook")
    # Never open a pre-existing hook for writing after a separate path check.
    # With an old hook, first prepare the replacement away from the target;
    # os.replace swaps path entries without writing through symlink/hardlink targets.
    exec_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    try:
        if original_identity is None:
            # Exclusive create refuses a concurrently installed foreign hook.
            with hook.open("x", encoding="utf-8", newline="\n") as output:
                output.write(desired)
            hook.chmod(hook.stat().st_mode | exec_bits)
        else:
            fd, temp_name = tempfile.mkstemp(
                prefix=".learnprint-hook-", dir=str(hook.parent))
            candidate = Path(temp_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
                    output.write(desired)
                current = hook.lstat()
                if (hook.is_symlink() or current.st_nlink != 1 or
                        not stat.S_ISREG(current.st_mode) or
                        (current.st_dev, current.st_ino) != original_identity):
                    return _fail("Pre-commit hook changed during upgrade; refusing")
                candidate.chmod(stat.S_IMODE(current.st_mode) | exec_bits)
                os.replace(str(candidate), str(hook))
            finally:
                if candidate.exists():
                    candidate.unlink()
    except OSError as exc:
        return _fail(f"Cannot safely install pre-commit hook: {exc}")
    print("INSTALLED/upgraded pre-commit Learnprint privacy hook.")
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
            print(f"{ROOT / 'skills' / n} -> {dest / TARGETS[a.target] / n} {'(DRY RUN)' if a.dry_run else ''}")
            if a.dry_run:
                continue
            rc = ensure_gitignored(dest, rel)
            if rc != 0:
                return rc
    if a.personal_skill:
        return install_personal_skill(a.source, dest / TARGETS[a.target] / PERSONAL_SKILL,
                                      a.dry_run, a.approve)
    return 0


if __name__ == "__main__":
    sys.exit(main())
