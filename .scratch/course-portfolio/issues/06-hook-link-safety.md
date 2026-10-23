# 06 — Refuse linked pre-commit hooks during privacy guard installation

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03B; parent ticket: 03-git-safety-and-migration.md
Severity: High (local file integrity; requires explicit hook-upgrade approval)
Owner: maintainer review pending
Environment: Windows, Python 3.14.0, Git for Windows, disposable test Git repository only

## Reproduction and expected behavior

Before the patch, create a regular file outside .git/hooks/ containing the exact
known legacy Learnprint pre-commit hook. Hard-link it to
.git/hooks/pre-commit inside a disposable repository. With the publication
guard scripts present, call install.install_hooks(repo, approve=True).

Expected: fail closed; no external file modified. Actual before fix: returned
0 and wrote the v2 hook through the hard link, changing the unrelated file.
A symlink to the same file has an analogous unsafe write path, including
dangling-link ambiguity. The real checkout's hooks were NOT inspected or changed.

## Fix implemented locally, uncommitted

- scripts/install.py: require a real .git/hooks directory; reject symlinked
  .git or hooks directory; reject symlink and multiply linked pre-commit hook
  before comparing/upgrading existing content.
- tests/test_publish_hook_install.py: disposable hardlink regression, plus
  symlink regression (skipped when host disallows symlink creation).
- No real hook installation, Git index staging, commit, push or private Courses
  modification was authorized or performed.

## Evidence

- RED: `python -m pytest tests/test_publish_hook_install.py -q`
  returned 1 failed, 5 passed, 1 skipped. The hardlink case returned 0
  instead of required 2 before the fix.
- GREEN focused: `python -m pytest tests/test_publish_hook_install.py tests/test_install.py tests/test_publish_guard.py -q`
  returned 32 passed, 1 skipped, 2 subtests passed.
- GREEN full: `python -m pytest tests/ -q`
  returned 318 passed, 2 skipped, 70 subtests passed (91.44 seconds).
- `python scripts/check_package.py` returned PACKAGING OK.
- `python scripts/learnprint_publish_guard.py --repo .` returned OK
  with zero public and private indexed files.

## Remaining risks / release gate

The preflight is not a complete guarantee against concurrent filesystem
replacement between validation and writing. Existing hook migration still
requires scoped owner approval, rollback/backup review and independent
Windows/Linux/macOS validation. Never mark the whole hook workstream DONE
based on this single local regression.

## Comments

- 2026-10-22 03:00 WIB: Initial defect and locally tested patch recorded for
  independent maintainer security review. No Git integration authorized.
- 2026-10-23, release verification relay: Resolved fail-closed. `scripts/install.py` writes a hook only when the path is proven absent and refuses every pre-existing or linked hook without mutating it. Regression coverage: `tests/test_publish_hook_install.py`. Manual reviewed migration is documented in `docs/PRODUCTION-WALKTHROUGH.md`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
