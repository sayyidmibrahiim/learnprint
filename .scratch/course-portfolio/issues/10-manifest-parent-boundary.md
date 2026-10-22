# 10 — Reject linked ancestors of portfolio manifest

Status: needs-triage
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C; parent ticket: 02-preview-showcase-builder.md
Severity: Medium (untrusted manifest path redirection; not evidence of actual data disclosure)
Owner: Maintainer independent review pending
Environment: Windows Python 3.14; disposable manifest fixtures and synthetic filesystem attributes

## Reproduction

`scripts/learnprint_portfolio.py::_load_manifest` previously validated only the manifest file leaf, not its parent directories. A regular manifest located under a symlink or Windows junction could be read through a redirected ancestor even though the manifest contract describes a non-link input boundary. The course source directory already had ancestor checks, which masked this gap when the test manifest shared the course's ancestor. The negative tests therefore relocate the manifest to a separate sibling directory.

- RED: `python -m pytest tests/test_course_portfolio.py -q` returned **2 failed, 20 passed, 1 skipped, 16 subtests**; the two expected failures accepted synthetic symlink and reparse-point parents.
- Fix: resolve the manifest path to an absolute path and run the existing `_existing_plain_dir(p.parent)` check before reading its leaf. This validates every ancestor for symlinks and Windows reparse attributes using the existing Python 3.9-compatible helper.
- GREEN focused: `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_privacy.py -q`: **42 passed, 1 skipped, 63 subtests**.
- GREEN full suite: `python -m pytest tests/ -q`: **332 passed, 2 skipped, 78 subtests**, 92.94 seconds, one process.
- Packaging: `python scripts/check_package.py` PACKAGING OK; staged publication guard: `python scripts/learnprint_publish_guard.py --repo .` OK with zero indexed private files.

## Scope and limitations

Only `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, this issue, and `to-do.md` changed in this bounded work. No real learner Courses/, installed Git hooks, staging, commits, pushes, or remotes were intentionally touched. Synthetic junction tests are not proof of real Windows junction behavior; concurrent filesystem swaps (TOCTOU), independent privacy review, and cross-platform CI remain release gates. A heuristic secret scan never guarantees absence of sensitive data.

## Comments

- 2026-10-22: Defect reproduced RED, corrected, and validated GREEN. Ready for independent maintainer review; W0-03C parent remains IN_PROGRESS.
