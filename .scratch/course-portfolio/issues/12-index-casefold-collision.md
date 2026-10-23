# 12 — Reject case-colliding paths in indexed public course snapshots

Status: wontfix
Duplicate of: 12-case-collision-git-index.md (canonical issue)
Reason: This supplemental issue record was created concurrently with the canonical issue for the same defect. Preserve its independent positive-control and segmented test evidence, but do not count it as a second distinct bug or release gate.
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03A / W0-03 Git index privacy and portability
Parent ticket: 03-git-safety-and-migration.md
Severity: Medium (cross-filesystem publication integrity; not proven private data disclosure)
Owner: Maintainer independent security review pending

## Finding

The staged Git index validator checked that each public file matched its declared SHA-256 and that the publication preview digest matched the manifest. It did **not** reject distinct indexed paths whose Unicode casefold values collide, for example `hands-on/query.sql` and `hands-on/QUERY.sql`. Git can store both index entries; a case-insensitive filesystem cannot reliably represent both as separate checked-out files. The source exporter already rejects case-colliding artifact names, but an independently crafted Git index plus self-consistent publication manifest bypassed that export-time check.

## Reproduction and correction (synthetic temporary Git repositories)

- **RED before fix:** `python -m pytest tests/test_publish_guard.py -q` returned **1 failed, 16 passed, 7 subtests passed**; `test_case_colliding_staged_artifact_paths_rejected` failed because no `ValueError` was raised.
- **Fix:** `scripts/learnprint_publish_guard.py::_validate_package` now rejects repeated `path.casefold()` values across the declared public files before hash validation.
- **Negative:** two staged `100644` blobs with `query.sql` / `QUERY.sql`, both listed in a self-consistent `PUBLICATION.json`, are rejected with `case-colliding published artifact paths`.
- **Positive:** two distinct staged paths `query.sql` / `second.sql` with identical blob contents and self-consistent publication manifest are still accepted. This confirms that equal hashes alone are not rejected.
- **Focused after final tests:** `python -m pytest tests/test_publish_guard.py tests/test_course_portfolio.py -q` returned **41 passed, 1 skipped, 27 subtests passed**.
- **Whole repository after initial fix, before adding positive control:** `python -m pytest tests/ -q` returned **334 passed, 2 skipped, 82 subtests passed** in 168.82s.
- **Final after positive-control test:** one-process whole suite attempted but the connector execution timed out without a pytest verdict; all 21 test modules then ran in two non-overlapping groups, **145 passed, 1 skipped, 20 subtests** and **190 passed, 1 skipped, 62 subtests**, totaling **335 passed, 2 skipped, 82 subtests**. These are segmented outcomes, not a claim of one-process full-suite pass.
- **Packaging:** `python scripts/check_package.py` returned `PACKAGING OK`. **Actual repository index check:** `python scripts/learnprint_publish_guard.py --repo .` returned OK, zero indexed private and zero public snapshot files.

## Scope and residual risk

Changed only previously untracked candidate `scripts/learnprint_publish_guard.py`, `tests/test_publish_guard.py`, new issue 12 and `to-do.md`. Tests use temporary synthetic Git repositories. No real `Courses/`, installed Git hooks, real Git staging, commit, push, publication or network action was authorized or performed.

Independent Windows/macOS/Linux CI, actual junction/reparse and TOCTOU behavior, hook-path claim reconciliation, human privacy UAT, real Courses hash-only baseline and owner-scoped Git integration remain release gates. This fix prevents casefold-colliding declared paths; it does not prove arbitrary cross-platform Unicode filename safety or source authenticity.

## Comments

- 2026-10-22: RED reproduced, fail-closed casefold guard added, distinct-path positive control GREEN, all 21 test modules passed in segmented runs. Ready for independent review; release gate remains open.
- 2026-10-23, release verification relay: Historical duplicate. Superseded by `12-case-collision-git-index.md`, which implements and tests the same defect class. Status intentionally stays wontfix so the duplicate is not reopened. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
