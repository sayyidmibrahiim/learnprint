# 01 — Inventory & freeze public/private file contract

Status: resolved
Blocked by: none

## Task

Audit all CLI read/write paths in scripts/ and exact per-course files (including HANDOFF, state, logs, sessions, attachments and hands-on outputs). Define schema-compatible per-course visibility and public artifact manifest, ownership and evidence provenance mapping, and release-level privacy boundaries. Confirm whether exporting by copy or through an allowlisted public view minimizes drift and data leakage. Use ADR-0002.

## Acceptance

- [ ] Complete matrix of existing artifact paths by sensitivity and purpose.
- [ ] Stable schema and public artifact allowlist with private exclusions.
- [ ] Safe default, opt-out and old-course migration described.
- [ ] Naming/presentation does not imply accredited certificates.
- [ ] Tests explicitly cover forbidden fields, mixed content, Git history caveat.
- [ ] No real course files changed; no ignore/hook relaxation.

## Comments
- 2026-10-23, release verification relay: Implemented the per-course visibility and public artifact contract with an allowlisted manifest, documented in ADR-0002 and enforced by `scripts/learnprint_portfolio.py`. Regression coverage: `tests/test_course_portfolio.py`, `tests/test_publish_guard.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
