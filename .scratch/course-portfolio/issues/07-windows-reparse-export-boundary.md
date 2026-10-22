# 07 — Reject Windows reparse/junction aliases at portfolio boundaries

Status: needs-triage
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C; parent ticket: 02-preview-showcase-builder.md
Severity: High (potential private source alias or unintended export destination)
Owner: Maintainer independent review pending
Environment: Windows Python 3.14; historical synthetic attributes + fresh real disposable Windows junction regression tests

## Reproduction

The portfolio preview/export previously rejected `Path.is_symlink()` but did not
reject a regular-mode directory or file carrying Windows
`FILE_ATTRIBUTE_REPARSE_POINT` (0x400). Directory junctions can redirect
traversal without reporting as symlinks. Synthetic `Path.lstat()` fixtures
mark an existing disposable `hands-on/` source directory or export destination
parent with that flag, while retaining ordinary directory `st_mode`.

Expected: preview and export refuse the aliased boundary before copying files.
Observed before patch: both negative tests failed (no ValueError); export wrote
a snapshot beneath the simulated alias. No real learner data was accessed.

## Local fix and regression evidence

- `scripts/learnprint_portfolio.py`: add stdlib-only reparse attribute check,
  applied to source path components, manifest and output parent/ancestors.
  Existing symlink checks and source hardlink checks remain in place.
- `tests/test_course_portfolio.py`: synthetic reparse attribute fixtures
  for source directory, source artifact, manifest and export parent.
- RED: `python -m pytest tests/test_course_portfolio.py -q` returned
  2 failed, 15 passed, 1 skipped, 13 subtests.
- GREEN focused: `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_publish_hook_install.py tests/test_privacy.py -q`
  returned 42 passed, 2 skipped, 55 subtests.
- Packaging: `python scripts/check_package.py` returned PACKAGING OK.
- Index guard: `python scripts/learnprint_publish_guard.py --repo .` returned
  status OK, zero indexed private/public course files.
- Single-command whole-suite invocation failed at connector level (no pytest
  result); all 21 test files were then run in six disjoint groups, totaling
  324 passed, 2 skipped, 70 subtests. This is not a single-process suite result.

## Residual risk and acceptance gates

Real Windows directory junctions were additionally tested on 2026-10-22 at
three boundaries (source artifact, manifest parent, export destination parent)
using only disposable temporary directories. All three tests executed and
rejected the junction on this Windows host. Other reparse tags/mount points,
independent Windows/Linux/macOS CI and concurrent path replacement (TOCTOU)
review remain unverified and mandatory. This fix does not prove atomic directory
identity across a preview/export race. The user's original Courses/ directory,
installed hooks, Git index, commits, and remotes were not modified.

## Comments

- 2026-10-22 05:00 WIB: Regression and scoped fix recorded for independent
  security review; W0-03C remains IN_PROGRESS.
- 2026-10-22 13:14 WIB: Added three real Windows junction tests in
  `tests/test_course_portfolio.py`, creating temporary `mklink /J` directory
  junctions and cleaning each alias with `os.rmdir` before deleting fixtures.
  Source artifact, manifest-parent and export-parent aliases were all rejected;
  focused `python -m pytest tests/test_course_portfolio.py -q` **28 passed, 1
  skipped, 20 subtests**. One-process full suite `python -m pytest tests/ -q`
  **340 passed, 2 skipped, 82 subtests in 126.48s**. Packaging, publication
  index guard and course CLI help exited 0. No production source changes, real
  Courses/ access, hook installation, actual index staging, commits or push.
  W0-03C remains IN_PROGRESS for directory-chain race review, other reparse
  forms, independent CI and human acceptance.
