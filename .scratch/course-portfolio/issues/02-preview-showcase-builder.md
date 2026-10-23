# 02 — Deterministic public course preview and showcase generation

Status: resolved
Blocked by: 01

## Task

Implement course-level publication eligibility/visibility, read-only preview and an explicitly approved curated public package. Output a useful public learning roadmap, demonstrable competencies with provenance labels, reproducible hands-on project source and instructions. Separate user-authored proof from agent-generated sample; never invent mastery or source results.

## Acceptance

- [ ] Dry-run/preview is genuinely read-only and lists exact output paths.
- [ ] Bad paths, secrets, profiles, event ledger, session receipts, notes or symlinks fail closed.
- [ ] Public artifact content derives only from verified/observed safe inputs.
- [ ] Publishing never changes private canonical evidence or course IDs.
- [ ] No automatic git/network action.
- [ ] Positive and negative regression tests pass on disposable roots.

## Comments
- 2026-10-23, release verification relay: Implemented deterministic preview digests and local-only export in `scripts/learnprint_portfolio.py`. Regression coverage: `tests/test_course_portfolio.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
