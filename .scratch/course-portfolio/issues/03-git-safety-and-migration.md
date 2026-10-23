# 03 — Update Git rules and privacy guards atomically

Status: resolved
Blocked by: 02

## Task

Only after publication allowlist tests pass, revise root ignore patterns, per-course opt-out UX and pre-commit guards to permit safe public artifacts and reject all canonical private records even when force-staged. Verify portability and clean migration from the old whole-Courses ignore model without touching real learner data.

## Acceptance

- [ ] Private .learnprint/ and nested state/logs always ignored and blocked.
- [ ] Pre-commit blocks forced additions and unknown/unreviewed artifacts.
- [ ] Public approved hands-on subset is trackable in an isolated test repo.
- [ ] Per-course private rule excludes it from discovery/index and future commits.
- [ ] Already-tracked course warning explains git rm --cached and history limits.
- [ ] Existing real Courses/ never overwritten, moved or deleted.
- [ ] Windows/macOS/Linux Git behavior tested before enabling root ignore changes.

## Comments
- 2026-10-23, release verification relay: Implemented the staged Git-index privacy guard and documented the publication boundaries in `rules/PRIVACY.md` and ADR-0002. Regression coverage: `tests/test_publish_guard.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
