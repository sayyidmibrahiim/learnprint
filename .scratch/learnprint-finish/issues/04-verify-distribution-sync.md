# 04 — Verify distribution/claude-plugin sync

Status: ready-for-agent
Blocked by: none

## Problem

`distribution/claude-plugin/` carries copies of `skills/learnprint-assess/`
and `skills/learnprint-learn/` (SKILL.md + references). Copies drift silently;
nothing runs a sync check. Before the finishing PR, verify the copies match
the sources.

## Change

Byte-compare each file under `distribution/claude-plugin/skills/` against its
source under `skills/` (and `references/founder-default.json` against
`profiles/founder-default.json`). PowerShell example:

```powershell
# from repo root; add each known pair
fc /b skills\learnprint-learn\SKILL.md distribution\claude-plugin\skills\learnprint-learn\SKILL.md
fc /b skills\learnprint-assess\SKILL.md distribution\claude-plugin\skills\learnprint-assess\SKILL.md
# ...same for every references/ file
```

- In sync → no code change; record "in sync" + the compared file list in this
  ticket's Comments section, then mark resolved.
- Drifted → resync by COPYING source → distribution (mechanical copy, zero
  content edits) in one commit. Never edit the distribution copies by hand.

After copying, re-run `python scripts/check_package.py` (must stay PACKAGING
OK).

## Acceptance

- [ ] Every distribution skill file byte-identical to its source (or resynced
      and committed)
- [ ] `python scripts/check_package.py` → PACKAGING OK
- [ ] Result recorded under `## Comments` in this file

## Commit (only if drifted)

`chore: sync claude-plugin distribution copies`
