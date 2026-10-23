# 12 — Reject case-colliding Git-indexed portfolio artifact paths

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03A (privacy Git index hardening)
Parent ticket: 03-git-safety-and-migration.md
Severity: Medium (cross-platform snapshot integrity; possible path alias)
Owner: Maintainer independent review pending

## Defect and reproduction

The portfolio source exporter rejects casefold-colliding artifact paths, but the Git-index publication guard only validated membership, SHA-256 hashes and preview digest. A crafted index containing both `Courses/public/<uuid>/hands-on/query.sql` and `.../hands-on/QUERY.sql`, and a matching regenerated `PUBLICATION.json`, passed the previous guard. Case-insensitive checkouts may not represent both artifacts accurately.

Test `tests/test_publish_guard.py::TestIndexedCourseGuard::test_case_colliding_staged_artifact_paths_rejected` uses only a disposable Git repository and synthetic content. `git update-index --cacheinfo` stages the second case-variant path in that disposable repository; a self-consistent manifest and digest remove unrelated checksum failures.

- **RED before fix:** `python -m pytest tests/test_publish_guard.py -q` yielded **1 failed, 16 passed, 7 subtests passed**. The failure confirmed guard.check_index did *not* reject the collision.
- **Fix:** `scripts/learnprint_publish_guard.py::_validate_package` now enforces per-portfolio casefold uniqueness across staged published file names. This mirrors the source exporter rule.
- **GREEN focused:** `python -m pytest tests/test_publish_guard.py tests/test_course_portfolio.py -q` yielded **40 passed, 1 skipped, 27 subtests passed**.
- **GREEN full suite:** `python -m pytest tests/ -q` yielded **334 passed, 2 skipped, 82 subtests passed** in 193.54 seconds, single Windows run.
- **Packaging:** `python scripts/check_package.py` returned PACKAGING OK.
- **Current checkout indexed publication guard:** `python scripts/learnprint_publish_guard.py --repo .` returned OK with 0 public and 0 private indexed files.
- **CLI smoke:** `python scripts/learnprint.py course --help` exit 0.

## Scope and outstanding gates

Modified existing untracked candidate files `scripts/learnprint_publish_guard.py`, `tests/test_publish_guard.py`, plus `to-do.md` and this new issue. No real learner Courses/, actual Git index staging, hooks, commits, pushes, external services, or remote publication were intentionally touched. Only the test fixture repository was staged.

This does not establish authenticity or human consent for a published snapshot. Actual Windows/macOS/Linux Git behavior, CI, hook upgrade verification, review of junction/TOCTOU risks, original Courses integrity boundary and independent human UAT remain release gates.

## Comments

- 2026-10-22: RED proof and GREEN full suite recorded. Ready for independent security review; W0 remains IN_PROGRESS.
- 2026-10-22 supplemental validation: `test_distinct_staged_artifact_paths_with_same_blob_are_allowed` added as explicit positive control. Distinct `query.sql` / `second.sql` paths with identical blob content and valid staged manifest pass (5 indexed public files); the casefold-colliding variant still fails. Focused tests: **41 passed, 1 skipped, 27 subtests**. A one-process full suite attempt after the new positive test returned a connector timeout with no pytest verdict; all 21 modules then ran in two disjoint commands, **145 passed + 190 passed, 2 skipped, 82 subtests** total. Original 334-pass single-process result predates this additional positive test.
- Concurrently another executor wrote `.scratch/course-portfolio/issues/12-index-casefold-collision.md` for the same bug. It is marked `wontfix` as a duplicate, preserved for audit without treating it as a separate defect. Future work must coordinate task claims before creating issue numbers.
- 2026-10-23, release verification relay: Implemented rejection of case-colliding Git-indexed artifact paths in `scripts/learnprint_publish_guard.py`. Regression coverage: `tests/test_publish_guard.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
