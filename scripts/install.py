#!/usr/bin/env python3
"""Copy portable Learnprint skills into project-specific discovery directories safely."""
import argparse
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGETS={
  "opencode":".opencode/skills", "codex":".agents/skills", "claude":".claude/skills",
  "gemini":".gemini/skills", "kiro":".kiro/skills", "antigravity":".agents/skills",
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target",required=True,choices=sorted(TARGETS))
    p.add_argument("--dest",required=True,help="Exact project root. This command never guesses your project path")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--approve",action="store_true",help="Explicitly approve copying new skill files")
    a=p.parse_args()
    dest=Path(a.dest).expanduser().resolve()
    if not dest.is_dir():
        print("ERROR: Project directory does not exist:",dest,file=sys.stderr);return 2
    if not (dest/".git").exists():
        print("NOTICE: destination is not a git root; verify this is really your project")
    targets=[(ROOT/"skills"/n,dest/TARGETS[a.target]/n) for n in ("learnprint-assess","learnprint-learn")]
    for src,dst in targets:
        print(f"{src} -> {dst} {'(DRY RUN)' if a.dry_run else ''}")
        if dst.exists():
            print("ERROR: Refusing to overwrite existing skill",dst,file=sys.stderr);return 2
        if not (src/"SKILL.md").exists():
            print("ERROR: Missing packaged skill",src,file=sys.stderr);return 2
    if a.dry_run: return 0
    if not a.approve:
        print("ERROR: Pass --approve to explicitly permit writing to project",file=sys.stderr);return 2
    for src,dst in targets:
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(src,dst)
    print("INSTALLED. Check skills in your target app; native loading not verified by this installer.")
    return 0

if __name__ == "__main__": sys.exit(main())
