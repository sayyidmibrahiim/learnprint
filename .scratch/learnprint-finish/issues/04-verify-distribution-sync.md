# 04 — Verify distribution/claude-plugin sync

Status: resolved
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

## Comments

- 2026-10-17 builder: DRIFTED on first pass → resynced per ticket (W6
  mechanical copy source → distribution, zero hand edits).
- Compared pairs (7): assess/SKILL.md, assess/references/ASSESSMENT.md,
  learn/SKILL.md, learn/references/{founder-default.json (vs skills copy AND
  vs profiles/founder-default.json), REVIEW.md, TEACHING.md}.
- First-pass SHA256: 3 DRIFTED (assess/SKILL.md, learn/SKILL.md,
  TEACHING.md — distribution copies stale since initial commit c4a433b;
  sources carried workspace-era additions: unified-skill integration, course
  workspace/context-budget sections, journey/presentation contract,
  correction workflow, portability rewrite). 4 IN-SYNC.
- After copy: all 7 pairs byte-identical at BOTH worktree and committed-blob
  level (blob SHAs equal: assess/SKILL 95f719280a8a, learn/SKILL
  f406ac526170, TEACHING 64751d9b066e).
- `python scripts/check_package.py` → PACKAGING OK (re-run post-copy).
- Frozen trees untouched: `git diff --name-only` shows no paths under
  scripts|schemas|profiles|protocols|skills|rules.
- Commit: `f5ee5ad` — `chore: sync claude-plugin distribution copies`
  (3 files, +60/-1).
- Status: resolved.
- Note for the planner: nothing runs a sync check (ticket premise); future
  drift would go unnoticed again — consider a sync-check ticket (not filed
  here per D7-only-for-defects policy).
- 2026-10-23, release verification relay: Resolved: distribution and host mirrors are byte-checked by `tests/test_skill_distribution_sync.py`, and `python scripts/check_package.py` exits 0 with PACKAGING OK. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
