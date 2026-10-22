# 14 — Directory-chain replacement / TOCTOU in portfolio preview and export

Status: needs-triage
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C portfolio filesystem trust boundary
Severity: High (path boundary and export destination may change after preflight)
Owner: Independent security review pending

## Reproduced cases (all disposable temporary fixtures)

The previous source/manifest protection verified non-reparse path components and the opened file identity, but did not bind the *ancestor directory identities* across the read. On Windows, a parent could be renamed and recreated, then the exact same file inode and identical bytes moved into the replacement path. Leaf-only checks passed even though the originally reviewed directory chain was different.

- SOURCE: `test_source_parent_swap_with_same_file_inode_is_rejected` injects an in-fixture rename of `hands-on` at `os.open` time and moves the same query file inode into the recreated directory.
- MANIFEST: `test_manifest_parent_swap_with_same_file_inode_is_rejected` similarly swaps the manifest parent without changing the manifest inode/content.
- EXPORT: `test_export_parent_swapped_before_staging_is_rejected` swaps the destination parent inside the temporary `mkdtemp` call, after the old code had approved that parent.

**RED:** First two regressions returned 2 failed, 28 passed, 1 skipped, 20 subtests. After fixing source/manifest, the third (export-parent) regression returned 1 failed, 30 passed, 1 skipped, 20 subtests. The failures were intentional proof that the old code accepted changed directory identities.

## Mitigation

In `scripts/learnprint_portfolio.py`, add `_snapshot_directory_chain` and `_assert_directory_chain_unchanged`: validate each ancestor is a regular directory, not a Windows reparse point/symlink; record `st_dev/st_ino` before file open; compare the chain again after reading the manifest or artifact. Also pin/check the approved destination-parent chain after staging starts and immediately before `os.rename`. Do not use absolute resolution of a symlink as a substitute for checking the actual path. All logic is Python stdlib and does not read real learner files.

- GREEN focused `python -m pytest tests/test_course_portfolio.py -q`: **31 passed, 1 skipped, 20 subtests**.
- GREEN full `python -m pytest tests/ -q`: **343 passed, 2 skipped, 82 subtests** in 135.38s on **Windows Python 3.14.0**.
- `python scripts/check_package.py`: PACKAGING OK.
- `python scripts/learnprint_publish_guard.py --repo .`: OK, actual index has 0 private and 0 public course files.
- `python scripts/learnprint.py course --help`: exit 0.
- Existing tests for three *real* temporary Windows junction boundaries remain part of passing suite.

## Limitations / release gate

This is **detection of specific directory identity changes**, not atomic open-by-handle containment. A hostile process may cause a sufficiently tight ABA swap between checks, and on Windows Python `O_NOFOLLOW` may be unavailable. Destination parent can change in the extremely small interval between final snapshot verification and `os.rename`. Cross-platform secure handle-relative traversal and independent adversarial/concurrency review are still required before asserting a fully race-safe export. Do not change this issue to verified release-wide security without that evidence.

The original `Courses/` directory, its history/ledgers, installed hooks, actual Git index, commits/push and remotes were not intentionally read/written. Only synthetic fixture roots were mutated. This is a review-ready local fix, not a claim that Learnprint is release-ready.

## Comments

- 2026-10-22: RED/GREEN and complete suite evidence recorded, awaiting independent filesystem/security review.
