# 05 — Finalize: green suite, remove completed plans

Status: resolved
Blocked by: 01, 02, 04

## Purpose

The gate between "work done" and "ship it": prove everything green, then
remove the completed plan files (repo rule: never leave finished plan files).

## Steps

1. Full verification, evidence-first (all three must pass before proceeding):

   ```
   python -m pytest tests/ -q           # expect 283 passed, 0 failed
   python scripts/check_package.py      # expect PACKAGING OK
   python scripts/learnprint.py validate --profile profiles/founder-default.json  # expect VALID
   ```

2. If ANY command fails: STOP. Do not patch engine code here — file a new
   ticket under `.scratch/learnprint-finish/issues/` (D7 discipline applies
   to verification failures too) and mark this ticket blocked.

3. Remove completed plans (staged deletions, exact paths):

   ```
   git rm plan/learnprint-hardening-workspace.md
   git rm plan/completion-polish.md
   ```

   `.scratch/learnprint-finish/` (spec + issues) STAYS tracked — it is the
   working tracker for the remaining tickets 06 and 07.

4. Commit, then verify `git status --short` is clean.

## Acceptance

- [ ] All three verification commands pass; outputs pasted under Comments
- [ ] `plan/` directory gone (or empty and untracked)
- [ ] `.scratch/learnprint-finish/` still tracked
- [ ] `git status --short` clean

## Commit

`chore: remove completed hardening plans`

## Comments

- 2026-10-17 builder: gate re-run on HEAD=68ac45e (fresh runs, all three):
  - `python -m pytest tests/ -q` → **283 passed** (exit 0)
  - `python scripts/check_package.py` → **PACKAGING OK: all SKILL.md frontmatter and size checks passed** (exit 0)
  - `python scripts/learnprint.py validate --profile profiles/founder-default.json` → **VALID** (exit 0)
- Removed both completed plans (exact paths): `git rm
  plan/learnprint-hardening-workspace.md plan/completion-polish.md`;
  commit `6ca7072` — `chore: remove completed hardening plans`.
- `plan/` gone from disk and tracked tree.
- `.scratch/learnprint-finish/` still tracked (10 files: spec + issues 01-09).
- This evidence file was committed right after via
  `docs: record ticket 05 evidence`; `git status --short` clean.
- Batch review: performed INLINE by the builder (reviewer subagent unavailable
  — its configured model is missing in this environment). No blocking
  findings; frozen-tree invariant verified across fac156c..HEAD; reduced
  review independence noted for the PR.
- Open items carried to ticket 06 (owner present): ticket 08 (non-runnable
  hook command quoted in docs; non-blocking) and ticket 09 (pre-existing
  `Courses/` workspace decision; must be resolved before 06's final check).
- Status: resolved.
- 2026-10-23, release verification relay: Resolved: the full suite is green, completed plan files were removed, and this ticket now records the outcome. Tracker history is retained by design. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
