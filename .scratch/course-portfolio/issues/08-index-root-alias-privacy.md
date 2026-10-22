# 08 — Git index privacy guard misses exact private directory-root entries

Status: needs-triage
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03A; parent ticket: 03-git-safety-and-migration.md
Severity: High (privacy policy bypass for staged symlink/file metadata)
Owner: Maintainer independent review pending
Environment: Windows, disposable Git index fixtures; no real Courses/ reads

## Reproduction

The publication guard used slash-terminated path-prefix matching for `Courses/`
and personal skill roots such as `.agents/skills/learnprint-personal/`.
Git may stage a file or symlink at the *exact directory name* with no slash.
Before this fix, those entries were omitted from the sensitive index scan.
A symlink's staged blob can reveal a private path or other unexpected content;
this does not establish that original private learner files were published.

- Fixture A: isolated Git repo with staged `120000` symlink blob at `Courses`.
- Fixture B: isolated Git repo with staged `120000` symlink blob at
  `.agents/skills/learnprint-personal`, alongside an otherwise valid
  curated portfolio.
- Expected: `guard.check_index()` raises `ValueError`.
- Before fix: both negative tests failed (guard accepted these entries).
  `python -m pytest tests/test_publish_guard.py -q`: 2 failed,
  13 passed, 2 subtests.

## Scoped fix

- `scripts/learnprint_publish_guard.py` rejects case-insensitive exact
  `Courses` and personal skill directory-root Git index entries, before
  prefix-based staged-mode and public-package validation.
- `tests/test_publish_guard.py` adds two isolated index fixtures, including
  an independent repository for the `Courses` directory/file conflict.
- Focused GREEN: `python -m pytest tests/test_publish_guard.py -q`
  returned 15 passed, 2 subtests.
- Extended nested ignore fixture validates three private paths ignored and two
  curated public paths trackable without modifying the actual Git index.
- Final focused GREEN: `python -m pytest tests/test_publish_guard.py
  tests/test_privacy.py tests/test_publish_hook_install.py
  tests/test_course_portfolio.py -q`: 45 passed, 2 skipped, 60 subtests.
- Final whole-suite GREEN: `python -m pytest tests/ -q`:
  **327 passed, 2 skipped, 75 subtests** in 93.46s.
- `python scripts/check_package.py`: PACKAGING OK.
  `python scripts/learnprint_publish_guard.py --repo .`: OK,
  zero public/private indexed learner files.
  `python scripts/learnprint.py course --help`: exit 0.

## Residual gates

This closes only the exact-root bypass. The index guard is defense in depth;
it is not a guarantee against secrets in other paths or historical Git
commits. Real Git index, hooks, Courses/, remotes and commits were not changed.
Cross-platform CI, code review and owner-approved integration remain pending.

## Comments

- 2026-10-22 06:00 WIB: RED/GREEN reproduced locally; issue awaiting
  independent security review and complete W0-03A acceptance checks.
