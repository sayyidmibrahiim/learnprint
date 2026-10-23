# 09 — Reject Windows trailing-dot aliases in curated artifact paths

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C; parent ticket: 02-preview-showcase-builder.md
Severity: Medium (cross-platform path ambiguity; possible unintended artifact selection)
Owner: Maintainer independent review pending
Environment: Windows Python 3.14; host-independent path-validation test with disposable data

## Reproduction

The portfolio manifest path validator accepted directory segments ending in one or more dots (e.g. `hands-on/alias./query.sql`). Win32 path normalization may resolve a trailing-dot segment to a different directory, so the manifest spelling may not uniquely identify the intended source file. This is a path-aliasing risk, not evidence that any actual learner data leaked.

- RED: `python -m pytest tests/test_course_portfolio.py -q` returned **3 failed, 20 passed, 1 skipped, 13 subtests**. The three expected failures were `alias.`, `alias..` and `alias...` subtests, each accepted by the old validator.
- Positive control: `hands-on/normal/query.sql` remains accepted.
- Fix: `scripts/learnprint_portfolio.py::_safe_relative` now rejects any path segment ending with `.`, before opening source artifacts.
- GREEN focused: `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_privacy.py -q` returned **40 passed, 1 skipped, 63 subtests**.
- Whole-suite invocation: connector returned **internal error** twice, with no pytest result. Instead all 21 test modules ran across six non-overlapping groups: **330 passed, 2 skipped, 78 subtests** (48+44+23+55+129+31), all six commands exit 0. Do not describe this as one-process full-suite pass.
- `python scripts/check_package.py`: PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .`: OK, zero indexed learner files; `python scripts/learnprint.py course --help`: exit 0.

## Residual gates

This closes only the trailing-dot manifest path ambiguity. It does not prove safety against real junctions, concurrent path swaps (TOCTOU), case-insensitive aliases or Windows device namespace variants outside the existing validator. Cross-platform CI and human inspection of exact public bytes remain mandatory. No real Courses/ data, installed hooks, Git index, commits, pushes or remotes were intentionally changed.

## Comments

- 2026-10-22 07:18 WIB: RED/GREEN reproduced in disposable tests; scoped fix and segmented regression evidence recorded. W0-03C remains IN_PROGRESS pending independent review and cross-host tests.
- 2026-10-23, release verification relay: Implemented rejection of Windows trailing-dot and trailing-space aliases in curated artifact paths across `scripts/learnprint_portfolio.py` and `scripts/learnprint_publish_guard.py`. Regression coverage: `tests/test_qa_hardening.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
