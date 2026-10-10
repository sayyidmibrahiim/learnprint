#!/usr/bin/env python3
"""Validate bundled skill conventions without external libraries."""
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
errors=[]
for folder in sorted((ROOT/"skills").iterdir()):
    if not folder.is_dir(): continue
    path=folder/"SKILL.md"
    if not path.exists(): errors.append(f"missing SKILL.md: {folder}");continue
    b=path.read_text(encoding="utf-8")
    if len(b)>8000: errors.append(f"SKILL.md exceeds 8000 characters: {path}")
    m=re.match(r"\A---\n(.*?)\n---\n",b,re.S)
    if not m: errors.append(f"missing frontmatter: {path}");continue
    name=re.search(r"(?m)^name: (.+)$",m.group(1))
    desc=re.search(r"(?m)^description: (.+)$",m.group(1))
    if not name or name.group(1)!=folder.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",folder.name):errors.append(f"invalid name: {path}")
    if not desc or not 1 <=len(desc.group(1))<=1024:errors.append(f"invalid description: {path}")
print("\n".join(errors) if errors else "PACKAGING OK: all SKILL.md frontmatter and size checks passed")
sys.exit(bool(errors))
