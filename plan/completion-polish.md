# Implementation Plan: Learnprint Completion & Polish (post-hardening)

## Objective

Bring the repository to a fully green, fully committed, self-consistent state
after the Rev 5 hardening workstream (plan/learnprint-hardening-workspace.md,
now complete): fix the single failing meta-test, commit the pending
agent-workflow docs, verify distribution copies, and remove the completed
hardening plan file. No engine changes.

## Scope

1. Fix 1 failing test: `test_existing_16_tests_pass` (test-infra only).
2. Commit pre-existing uncommitted docs: `AGENTS.md` (+15 lines), `CONTEXT.md`,
   `docs/agents/` (issue-tracker.md, triage-labels.md, domain.md).
3. Verify `distribution/claude-plugin/` skill copies are in sync with
   `skills/` sources; resync only if drifted.
4. Finalize the hardening workstream: full suite green -> delete the completed
   `plan/learnprint-hardening-workspace.md` per repo rule "Plan completion".
5. Report the manual-only remainder (UAT live scenarios, per-host checklist,
   optional pre-commit hook) — these cannot be automated and are NOT claimed
   done by this plan.

Explicit non-goals: no changes to `scripts/learnprint.py`,
`scripts/learnprint_routing.py`, competency/evidence logic, schemas, or
fixtures. No new features.

## Context

### Repository baseline (verified 2026-10-17)

- Branch `feature/hardening-workspace` == `main` tip `3f19d39` (PRs #6, #7
  merged). `main..HEAD` and `HEAD..main` both empty; no merge step needed.
- Full suite: **282 passed, 1 failed** (~102 s). Packaging check: PACKAGING OK.
- UAT scenario-0 sanity passes: `course --help` prints subcommands,
  `validate --profile profiles/founder-default.json` prints `VALID`.
- Hardening plan stages 1-10 all landed: routing/persistence/migration/trust
  test files exist and pass; `rules/` files, `schemas/course-registry.schema.json`,
  `GEMINI.md`, `install.py --self/--personal-skill/--hooks` all present.

### The one failure — root cause (verified, not guessed)

`tests/test_progress_regression.py::test_existing_16_tests_pass` calls
`unittest.TestLoader().loadTestsFromName("tests.test_core")` in-process.

- `tests/` has no `__init__.py` (verified `Test-Path False`).
- On Python >= 3.12 the loader converts import errors into a `_FailedTest`
  suite entry instead of raising, so the method's `except ImportError`
  fallback (`loadTestsFromName("test_core")`) never triggers. Captured stderr:
  `ModuleNotFoundError: No module named 'tests'`.
- Verified the suite itself is healthy: `python -m unittest tests.test_core`
  from repo root runs 23 tests fine. The bug is the import context under
  pytest, not the tests.

### GEMINI.md "mojibake" — NON-DEFECT, verified before flagging

PowerShell renders the header dash as `?`, but raw bytes are `e2 80 94`
(U+2014 em-dash, valid UTF-8). No fix required. Do not "fix" this file.

### Pending uncommitted work (authored by a previous session, never committed)

- `AGENTS.md`: +15-line "Agent skills" section pointing at docs/agents/*.
- `CONTEXT.md`: untracked domain glossary (course, competency, demonstration
  cycle, evidence ledger, retention floor, learner profile, course registry).
- `docs/agents/`: untracked issue-tracker.md, triage-labels.md, domain.md.

These match each other (AGENTS.md references the two docs files) and belong
in one docs commit.

### Jev decisions (recorded)

- Delegation: `owner=tester` (p=0.9, conf 0.87), `needs_subagent=0.33` (NO ->
  inline), `can_parallel=0.58` (UNCERTAIN -> sequential, safer branch),
  `context_isolation` uncertain. Verdict: builder-inline, sequential.
- Verify (approach below): `proceed=0.86`, `needs_human=0.42`,
  `spec_fit` constraint-fit p=0.67 (conf 0.34), `decision_risk` max dimension
  = reversibility 0.84 (mechanically HIGH tier; high reversibility means the
  change is trivially undoable). Fails the strict bar only on `needs_human`:
  flagged below as a batched confirmation, defaulting to the recommended
  option at execution time.

## Dependencies

None. No sibling plans exist. No shared schema/API/lockfile/migration coupling.

## Files / Areas Likely Affected

| File | Change |
|------|--------|
| `tests/test_progress_regression.py` | Rewrite one test method (subprocess guard) |
| `AGENTS.md`, `CONTEXT.md`, `docs/agents/*.md` | Commit only; zero edits |
| `plan/learnprint-hardening-workspace.md` | Delete (completed) |
| `plan/completion-polish.md` | This file; delete at the very end |
| `distribution/claude-plugin/**` | Touch ONLY if drift check fails |

## Implementation Steps

### Step 1 — Fix the meta-test (builder inline, ~5 lines)

Replace the in-process loader in `test_existing_16_tests_pass` with a
subprocess run of the real suite:

```python
def test_existing_16_tests_pass(self):
    import subprocess, sys
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_core"],
                       cwd=root, capture_output=True, text=True)
    self.assertEqual(r.returncode, 0, msg=r.stderr[-2000:])
```

(`Path` is already importable in the file; add to the import line if not.)

Why this and not the rejected alternatives:

- `tests/__init__.py` — also fixes the import, but flips pytest's import mode
  for ALL 282 tests (root-insert vs package). Same outcome, much larger blast
  radius. Rejected.
- Delete the meta-test — laziest, but silently drops the Rev 5 traceability
  guard (J row: "existing tests pass") that protects standalone
  `pytest tests/test_progress_regression.py` runs, where test_core would
  otherwise not run at all. Rejected; a 5-line subprocess keeps the guard
  honest with zero collection risk.

Verify immediately: `pytest tests/test_progress_regression.py -q` alone
(guard must pass standalone) before running the full suite.

### Step 2 — Full-suite verification (builder inline)

```
python -m pytest tests/ -q          # expect 283 passed, 0 failed
python scripts/check_package.py     # expect PACKAGING OK
```

If anything else fails, stop and report — do NOT patch engine code under
this plan; that is a new defect needing its own decision.

### Step 3 — Distribution drift check (builder inline, read-only unless drifted)

Byte-compare `distribution/claude-plugin/skills/*/SKILL.md` and
`references/*` against `skills/*/` sources and
`profiles/founder-default.json`. In sync -> no-op, record hashes. Drifted ->
resync by copying from `skills/` (mechanical copy, no content edits) with one
`chore: sync claude-plugin distribution copies` commit.

### Step 4 — Commit pending docs (builder inline, one commit)

Single commit, exactly these paths (never `git add -A`):

- `AGENTS.md`, `CONTEXT.md`, `docs/agents/issue-tracker.md`,
  `docs/agents/triage-labels.md`, `docs/agents/domain.md`

Message: `docs: add agent workflow references and repo domain glossary`

### Step 5 — Finalize hardening workstream (builder inline)

After Step 2 is green and Step 4 committed:

1. `git add plan/learnprint-hardening-workspace.md` (staged for deletion)
   + commit `chore: remove completed hardening plan`.
2. This plan file is deleted last, in the final commit, once every step and
   verification above is verified green (repo rule: never leave completed
   plan files).
3. Verify `git status` clean (Courses/ is gitignored and expected absent from
   status).

### Step 6 — Report manual-only remainder (builder, no code)

Print in the final summary; these are NOT automatable and NOT claimed done:

1. Full UAT: `docs/USER-ACCEPTANCE-TEST.md` scenarios 1-9 (~30 min, live agent
   session, touches the real `Courses/` workspace for 1-7).
2. Per-host verification checklist (Requirement R, Rev 5 plan section): claims
   of OpenCode/Codex/Claude Code/Gemini CLI/Kiro/Antigravity compatibility
   require a manual run per host. Unit-test green does NOT prove this.
3. Optional privacy hardening, user's choice:
   `python scripts/install.py --hooks --approve` (pre-commit guard rejecting
   staged files under `Courses/` and personal-skill paths).

## Acceptance Criteria

- [ ] `python -m pytest tests/ -q` -> 283 passed, 0 failed.
- [ ] `pytest tests/test_progress_regression.py -q` passes standalone.
- [ ] `python scripts/check_package.py` -> PACKAGING OK.
- [ ] `git status` clean; AGENTS.md/CONTEXT.md/docs/agents tracked.
- [ ] `plan/` empty of completed plans (both plan files removed).
- [ ] Zero diffs under `scripts/`, `schemas/`, `profiles/`, `protocols/`,
      `skills/`, `rules/` (engine untouched).

## Verification / Tests

All verification is command-run, evidence-first:

| Check | Command | Expected |
|-------|---------|----------|
| Meta-test standalone | `python -m pytest tests/test_progress_regression.py -q` | pass |
| Full suite | `python -m pytest tests/ -q` | 283 passed |
| Packaging | `python scripts/check_package.py` | PACKAGING OK |
| UAT sanity (re-run) | `learnprint.py course --help` + `validate --profile ...` | help + VALID |
| Distribution | hash compare (Step 3) | in sync or resynced |
| Clean tree | `git status --short` | empty |

## Git (branch: feature/hardening-workspace)

Current branch equals `main` tip; work continues here (no new branch needed —
the diff is 1 test method + doc commits; branching cost exceeds isolation
value).

Commit sequence:

1. `test: run legacy-suite guard via subprocess in progress regression meta-test`
2. `docs: add agent workflow references and repo domain glossary`
3. `chore: sync claude-plugin distribution copies` (only if drifted)
4. `chore: remove completed hardening plan` (includes this plan file)

## Delegation Strategy

| Step | Owner | Parallel batch | Why |
|------|-------|----------------|-----|
| 1 | builder | - | 5-line test edit; Jev `needs_subagent=0.33` -> inline; tester spawn overhead > work |
| 2 | builder | - | Sequential after 1; pure command runs |
| 3 | builder | - | Read-only hash compare; mechanical copy only if drifted (bulk op stays in one shell step, never split) |
| 4 | builder | - | Single staged commit; needs current git state |
| 5 | builder | - | Depends on 2 + 4 |
| 6 | builder | - | Reporting only |

No parallel batches: Jev `can_parallel=0.58` = UNCERTAIN -> sequential (safer
branch); every step shares the same working tree and git state, so parallel
dispatch would only create commit-ordering conflicts. Coordination-cost read
as HIGH (0.7) but the steps are coupled through one branch — splitting into
sibling plans would add integration overhead larger than the entire change.

## Integration Notes

- No sibling plans; no merge ordering. Single-branch work, merges inline
  (branch already equals main).
- Likely file overlaps with any future plan: none expected — this plan
  touches only test-infra, docs, and plan-file lifecycle.
- Follow-up work that MUST NOT be folded in here: any new engine defect
  surfaced by Step 2, UAT failures, or per-host verification findings — each
  deserves its own small plan.

## Open confirmations (batched, defaults chosen)

1. **Needs human confirm (Jev `needs_human=0.42`):** meta-test fix approach —
   default = subprocess guard (recommended above). Alternative = delete the
   meta-test. Proceeding with default unless the user objects at review.
2. Confirm committing the pre-existing uncommitted docs (they predate this
   session; Step 4 commits them as-is, no edits).
3. Confirm deleting the completed hardening plan file (repo rule mandates it;
   listed for visibility since it removes a 2431-line tracked file).
