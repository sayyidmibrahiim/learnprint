# 03 — Update Git rules and privacy guards atomically

Status: ready-for-agent
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
