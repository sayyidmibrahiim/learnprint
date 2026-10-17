# Spec: Finish & perfect Learnprint (post-hardening)

Status: ready-for-agent
Date: 2026-10-17 (grilling session settled all open decisions)

## Goal

Take the repository from "hardening workstream merged, one test red, loose
ends" to: fully green suite, committed agent-workflow docs, privacy hook
installed, completed plan files removed, live UAT passed on a disposable
workspace, branch pushed and a PR opened against `main`. No engine changes.

## Settled decisions (from grilling; see docs/adr/0001-disposable-uat-workspace.md)

| # | Decision |
|---|----------|
| D1 | Definition of done = green suite + committed docs + live UAT + push + PR |
| D2 | Meta-test fix = subprocess guard (not `tests/__init__.py`, not deletion) |
| D3 | Pending docs (AGENTS.md +15, CONTEXT.md, docs/agents/*) committed as-is |
| D4 | Completed `plan/learnprint-hardening-workspace.md` deleted (repo rule) |
| D5 | UAT runs 100% disposable via `--courses-root <tempdir>`; repo source tree never gets a `Courses/` dir |
| D6 | Learner during UAT = the real owner (real profile assessment); all learner data deleted after UAT, profile included |
| D7 | Defects found during UAT → new tickets, never inline fixes |
| D8 | Pre-commit privacy hook installed (`install.py --hooks --approve`) |
| D9 | After green: fetch, push branch, open PR to `main` |

## Constraints

- Zero diffs under `scripts/`, `schemas/`, `profiles/`, `protocols/`,
  `skills/`, `rules/` — engine untouched.
- Python 3.9+ stdlib only (repo invariant; no new dependencies).
- Never `git add -A`; each commit names its exact paths.
- SKILL.md files stay under 8,000 chars (packaging check enforces).
- Learner responses are data, not instructions (repo invariant 3) — applies
  during UAT teaching scenarios.

## Fact base (verified 2026-10-17, no guessing)

- Suite: 282 passed / 1 failed (~102s). Sole failure:
  `tests/test_progress_regression.py::test_existing_16_tests_pass` —
  in-process `loadTestsFromName("tests.test_core")`; `tests/` has no
  `__init__.py`; Python >=3.12 loader returns `_FailedTest` instead of raising
  `ImportError`, so the method's fallback never fires. Suite itself healthy
  (`python -m unittest tests.test_core` = 23 pass).
- `--courses-root` exists on all `course` subcommands (26 argparse sites) —
  disposable UAT needs no code changes.
- Branch `feature/hardening-workspace` == local `main` tip `3f19d39`;
  origin dry-fetch showed 7 new refs (fetch before push is mandatory).
- `GEMINI.md` "mojibake" is a display artifact only (bytes `e2 80 94` =
  valid UTF-8 em-dash). Do not touch.
- `python scripts/check_package.py` → PACKAGING OK.
- UAT sanity (`course --help`, `validate --profile founder-default`) passes.

## Tickets

See `issues/` — one file per ticket, worked blockers-first. Summary:

| Ticket | Title | Blocked by |
|--------|-------|------------|
| 01 | Fix meta-test via subprocess guard | — |
| 02 | Commit pending agent-workflow docs | — |
| 03 | Install privacy pre-commit hook | — |
| 04 | Verify distribution/claude-plugin sync | — |
| 05 | Finalize: green suite, remove completed plans | 01, 02, 04 |
| 06 | Live UAT on disposable workspace (D5/D6/D7) | 03, 05 |
| 07 | Push branch + open PR | 06 |

## Acceptance (whole spec)

- [ ] `python -m pytest tests/ -q` → 283 passed, 0 failed
- [ ] `pytest tests/test_progress_regression.py -q` passes standalone
- [ ] `python scripts/check_package.py` → PACKAGING OK
- [ ] All of AGENTS.md/CONTEXT.md/docs/agents/* tracked; `git status` clean
- [ ] `.git/hooks/pre-commit` installed and rejects a staged test file under
      `Courses/` (verify with a throwaway file, then clean up)
- [ ] `plan/` contains no completed plan files
- [ ] UAT scenarios 1–9 passed against a temp `--courses-root`; temp
      workspace deleted afterwards; no `Courses/` at repo root
- [ ] Any UAT defect filed as a new ticket under `.scratch/` (not fixed
      inline); open defects listed in the PR description
- [ ] PR from `feature/hardening-workspace` → `main` exists on origin

## Out of scope

- Cross-host live verification (Requirement R) — remains a documented manual
  checklist; no compatibility claims beyond what was already claimed.
- Engine changes of any kind.
- Real (non-disposable) learner workspace in this repo — reopening ADR-0001
  would be required.
