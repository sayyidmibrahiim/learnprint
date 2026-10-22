# 13 — Manifest hardlink and open-time identity validation

Status: needs-triage
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C portfolio exporter, manifest trust boundary
Related: 07-windows-reparse-export-boundary.md; 10-manifest-parent-boundary.md
Severity: High (private-source aliasing / consented snapshot integrity)
Owner: Independent maintainer security review pending

## Finding and reproduction

A public portfolio manifest could itself be **multiply hardlinked** to a file inside a learner's private `Courses/.learnprint/` metadata area. Earlier protection required a regular, non-symlink, non-reparse manifest and checked its directory ancestors, but did not check the manifest's `st_nlink`. The manifest was subsequently read using a separate `Path.read_text` operation after path preflight. Artifacts already rejected multiply linked files; the manifest had a different trust boundary.

All tests below use synthetic data in disposable temporary Courses fixtures. They do not read or write the learner's actual Courses directory.

## Evidence and fix

- Baseline before regression: `python -m pytest tests/test_course_portfolio.py -q` **23 passed, 1 skipped, 20 subtests**.
- **RED:** after adding `test_hardlinked_manifest_to_private_metadata_is_rejected`, focused suite returned **1 failed, 23 passed, 1 skipped, 20 subtests**. Reproducer creates `os.link` from the harmless synthetic manifest into a synthetic `.learnprint/portfolio-metadata.json` and confirms the old preview accepted it. Source bytes remain unchanged.
- **Fix:** `scripts/learnprint_portfolio.py::_load_manifest` now validates `lstat` regular file, non-reparse attribute, `st_nlink == 1` and 32 KiB size, opens with `os.O_NOFOLLOW` wherever available, verifies opened descriptor's `st_dev/st_ino` matches preflight, checks size and link count after opening, limits actual bytes read to 32769, verifies descriptor is unchanged during read, and rechecks path identity/link/regular/reparse status after read. JSON parsing occurs only on those bounded bytes.
- Additional negative: `test_manifest_replacement_during_open_is_rejected` replaces the manifest with a *different file having identical contents* in the temporary fixture at `os.open` time; identity mismatch must reject.
- **GREEN focused:** `python -m pytest tests/test_course_portfolio.py -q` **25 passed, 1 skipped, 20 subtests**.
- **GREEN full:** `python -m pytest tests/ -q` **337 passed, 2 skipped, 82 subtests in 257.57s**, one Windows execution.
- `python scripts/check_package.py`: **PACKAGING OK**.
- `python scripts/learnprint_publish_guard.py --repo .`: **OK**, 0 actual indexed public/private files.
- `python scripts/learnprint.py course --help`: exit 0.

## Remaining acceptance and safety limits

The new file-descriptor checks reduce hardlink and file-replacement risks but **do not prove atomic identity for an entire directory chain**. In particular, Windows Python may lack `O_NOFOLLOW`, so a parent-directory replacement between boundary preflight and file opening remains possible in adversarial filesystem conditions. Real Windows junction testing, additional TOCTOU analysis and independent Windows/Linux/macOS CI remain required; do not declare filesystem race safety complete.

This session changed only the existing untracked portfolio module/tests, this issue and `to-do.md`. It did not stage/commit/push, install hooks, publish a portfolio, or intentionally access/change actual private Courses data. These checks are deterministic engineering safeguards, **not** proof of human learning/independent skill or authenticated reviewer identity.

## Comments

- 2026-10-22: RED confirmed, two regressions GREEN, full suite and package/index/CLI passes observed. Ready for independent review, parent W0-03C remains IN_PROGRESS.
