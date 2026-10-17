# Implementation Plan: Learnprint Completion & Polish (v2 — post-grilling)

## Objective

Finish the repository per the grilling session of 2026-10-17 (decisions D1-D9,
recorded in docs/adr/0001-disposable-uat-workspace.md and
`.scratch/learnprint-finish/spec.md`): green suite, committed docs, privacy
hook, completed plans removed, live UAT on a disposable workspace, branch
pushed, PR opened. No engine changes.

## Scope

Execution unit = the 7 tickets under `.scratch/learnprint-finish/issues/`,
worked blockers-first. Summary:

| Ticket | What | Blocked by |
|--------|------|------------|
| 01 | Fix meta-test via subprocess guard | — |
| 02 | Commit pending docs (AGENTS.md, CONTEXT.md, docs/agents/*) | — |
| 03 | Install + verify privacy pre-commit hook | — |
| 04 | Verify distribution/claude-plugin sync | — |
| 05 | Green-suite gate + delete completed plan files | 01, 02, 04 |
| 06 | Live UAT, disposable workspace (interactive, owner = learner) | 03, 05 |
| 07 | Push branch + open PR | 06 |

Out of scope: engine changes, cross-host live verification (manual
checklist), real learner workspace in this repo (requires reopening ADR-0001).

## Context

- Grilling settled all open decisions (D1-D9 in the spec); frontier empty.
  UAT = fully disposable (`--courses-root` exists on all course subcommands,
  26 argparse sites — verified). Learner = real owner, data purged after.
  Defects → new tickets, never inline fixes.
- Baseline (verified 2026-10-17): 282/283 tests pass; sole failure is the
  meta-test import-context bug (root cause verified: Python >=3.12 loader
  returns `_FailedTest` instead of raising ImportError; `tests/` lacks
  `__init__.py`; suite itself healthy). Packaging OK. UAT sanity passes.
  Branch == local main tip `3f19d39`; origin dry-fetch showed 7 new refs.
- Jev (recorded): delegation `needs_subagent=0.33` → inline; verify
  `proceed=0.86`, `needs_human=0.42` — the flagged confirms were settled in
  grilling (user chose the recommended options plus UAT scope).
- GEMINI.md "mojibake" is display-only (valid UTF-8 em-dash). Do not touch.

## Dependencies

None on sibling plans. Ticket-internal blocking edges as in the table.
Interactive dependency: ticket 06 requires the owner present (real profile
assessment + learner answers).

## Files / Areas Likely Affected

| File | Change |
|------|--------|
| `tests/test_progress_regression.py` | Ticket 01: one method → subprocess guard |
| `AGENTS.md`, `CONTEXT.md`, `docs/agents/*.md` | Ticket 02: commit as-is |
| `.git/hooks/pre-commit` | Ticket 03: installed (untracked by design) |
| `distribution/claude-plugin/**` | Ticket 04: only if drifted |
| `plan/*.md` | Ticket 05: both plan files deleted |
| temp dir outside repo | Ticket 06: disposable UAT workspace, deleted after |
| (new) `.scratch/learnprint-finish/issues/*` | Ticket 06: defect tickets if UAT finds bugs |

## Implementation Steps

Each ticket = one builder session, fresh context, ticket file is
self-contained. Inside a session: implement → verify per the ticket's
Acceptance → `/code-review` the diff against the spec before committing
(ask-matt /implement discipline). Ticket 01's red-green is already set up
(the failing test IS the red). Tickets 02-04 are mechanical — direct
implement + review, no TDD ceremony. UAT (06) is the acceptance run itself.

Order: 01/02/03/04 in any order (parallel-safe, all touch disjoint paths;
03 and 04 are command-only) → 05 gate → 06 interactive with owner → 07 ship.

## Acceptance Criteria

Whole-plan acceptance = spec acceptance list, verbatim: 283 green (full +
standalone meta-test file), PACKAGING OK, founder profile VALID, five doc
paths tracked, hook rejects a `-f` staged `Courses/` probe, `plan/` empty,
UAT 0-9 passed on temp workspace with cleanup verified, defect tickets (if
any) filed and listed in the PR, PR link recorded.

## Verification / Tests

Evidence-first per ticket (commands live in each ticket file). Final gate
(ticket 05) re-runs: full suite, packaging check, profile validation. Ticket
06 pastes per-scenario PASS/DEFECT lines into its Comments. Ticket 07
re-verifies green after any origin/main merge.

## Git (branch: feature/hardening-workspace)

Commits in order: 01 `test: run legacy-suite guard via subprocess...` → 02
`docs: add agent workflow references and repo domain glossary` → 04 `chore:
sync claude-plugin distribution copies` (only if drifted) → 05 `chore: remove
completed hardening plans` → 06 defect tickets (only if UAT finds bugs). 07
pushes and opens the PR. Planning artifacts (this plan, ADR-0001, spec,
ticket 01-07 files) are committed by the planner before execution starts.

## Delegation Strategy

| Step | Owner | Parallel batch | Why |
|------|-------|----------------|-----|
| 01 | builder | A | 5-line test edit; isolated path |
| 02 | builder | A | Pure git staging; disjoint paths |
| 04 | builder | A | Read-only compare (+ mechanical copy if drifted) |
| 03 | builder | A | Command-only install + destructive probe test; touches .git only |
| 05 | builder | - | Gate: depends on 01, 02, 04 (and 03 done for hook presence) |
| 06 | builder + owner | - | Interactive UAT; needs human as learner; D7 discipline |
| 07 | builder | - | Ship: depends on 06 for PR evidence |
| Review | reviewer | - | Read-only diff review after 01+02+04, before 05 |

Batch A = tickets 01-04 in any order (disjoint paths, no shared state).
Ticket 03's probe creates and deletes `Courses/_hook_probe.txt` — safe in
parallel because 01/02/04 never touch `Courses/`.

## Integration Notes

- Single branch, inline merge (branch == main locally; origin divergence
  handled inside ticket 07).
- No sibling plans. If ticket 06 files defect tickets, they are follow-up
  workstreams: small ones fold into a hotfix session before the PR merges;
  large ones get their own plan file. PR-blocking classification lives in
  ticket 06's Comments.
- After ticket 07 completes and the PR merges, delete
  `.scratch/learnprint-finish/` per repo rule (plan/issue files removed once
  fully landed).
