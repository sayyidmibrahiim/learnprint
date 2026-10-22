# W9-01 — Language selection for next action

Status: ready-for-human
Date: 2026-10-22
Owner: GPT-6 via CodexProLatestFix

## Scope

Existing presenter provides English instructions for every tutor phase, even when learner chooses Indonesian. Keep English as the backward-compatible default. Add Indonesian next-action strings, explicit language validation, and positive/negative tests.

Files: scripts/learnprint_tutor.py; tests/test_tutor_state.py; to-do.md; this issue.

## Acceptance

- Every phase has one concise Indonesian learner action.
- Existing English callers receive identical output.
- Unsupported or invalid language fails closed.
- No evidence, scoring, session persistence, or private Courses modifications.
- Run focused and full tests, packaging and index guard.

## Comments

- 2026-10-22: Claim established. Branch feature/hardening-workspace; last known HEAD d98cf93, fresh hash query unavailable; 18 modified tracked + 54 untracked, staged empty. No active W9 file claim observed. Prior focused tutor suite 38 passed, 68 subtests.
- 2026-10-22 17:26 WIB: Local implementation VERIFIED; scope released. New test first reproduced RED: `python -m pytest tests/test_tutor_state.py -q` 9 failed, 39 passed, 68 subtests (3 test failures and 6 negative subtest failures). `scripts/learnprint_tutor.py` now supports `next_action(doc, language='id')` with concise Indonesian messages for all 9 phases; English default/return shape unchanged; unsupported language raises ValueError without state mutation. `tests/test_tutor_state.py` adds four test methods covering all phases, default compatibility, negative type/value inputs and no state mutation. GREEN focused: 42 passed, 83 subtests in 0.76s. Full suite: `python -m pytest tests/ -q --tb=no` 486 passed, 2 skipped, 259 subtests in 146.47s. `python scripts/check_package.py` PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` OK with 0 private indexed; Python 3.9 grammar gate 3 passed, 45 subtests. No real Courses, actual hook/index, commits, push or publication. Open: real host/language UAT and independent review; full W9 remains IN_PROGRESS. Next safe task: review W8-02 public revision namespace or W9 host test fixtures, subject to fresh claims and approvals.
