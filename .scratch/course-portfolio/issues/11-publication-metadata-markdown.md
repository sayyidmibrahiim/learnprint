# 11 — Reject Markdown provenance injection in public portfolio metadata

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03C / W0-03 portfolio export security
Parent ticket: 02-preview-showcase-builder.md
Severity: Medium (public portfolio presentation/integrity; not evidence of private data exposure)
Owner: Maintainer independent security/product review pending

## Finding

The curated portfolio exporter renders manifest-controlled `title`, `summary`, and `achievements[].claim` directly into generated public README.md and EVIDENCE.md. Prior markup validation rejected angle brackets, square brackets and exclamation points but allowed Markdown heading markers, newlines, emphasis, inline-code markers, backslashes and `|` column-like separators. A summary could therefore add a fabricated "Accredited Certificate" heading or an achievement claim could inject a misleading `human_reviewed`-looking column, despite the intended self-declared provenance boundary.

The exploit does not grant authenticated credentials or change underlying evidence; it can cause misleading presentation of self-reported content.

## Reproduction (disposable synthetic course only)

- Test: `tests/test_course_portfolio.py::TestPortfolio::test_publication_metadata_cannot_inject_markdown_provenance`.
- Cases: multi-line Markdown heading in summary; `**verified**` emphasis; inline-code marker in title; `|` provenance field spoofing in a claim. Positive control keeps safe plain-text metadata publishable.
- Before fix RED: `python -m pytest tests/test_course_portfolio.py -q` returned **4 failed subtests, 23 passed, 1 skipped, 16 subtests passed**, demonstrating the unsafe fields were accepted. Earlier preliminary run had a fixture-state contamination defect, corrected before recording this RED run.
- Narrow fix: `scripts/learnprint_portfolio.py::prepare` now rejects control characters and reserved Markdown structural delimiters in externally provided public metadata, while preserving existing plain-text metadata and the current output schema.
- After fix GREEN focused: **23 passed, 1 skipped, 20 subtests passed**.
- After fix GREEN whole repository: `python -m pytest tests/ -q` **333 passed, 2 skipped, 82 subtests passed in 273.61 seconds** (one process, Windows).
- Packaging: `python scripts/check_package.py` returned PACKAGING OK.
- Indexed privacy guard: `python scripts/learnprint_publish_guard.py --repo .` returned OK, zero approved public and zero indexed private learner files in actual checkout.

## Scope / limitations

Changes confined to existing untracked candidate `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, new issue 11 and `to-do.md`. No real Courses/ source or evidence ledger, installed Git hook, Git index stage/commit, remote operations or publication were intentionally modified.

This is a conservative policy and may reject harmless Markdown in author-provided title/summary, by design for the candidate v1 plain-text format. It is **not** an authenticity check: even plain text can state false achievements, and source/claim review plus learner consent remain mandatory. Cross-platform CI, real-junction and TOCTOU reviews, independent UAT and staging/commit approvals remain release blockers.

## Comments

- 2026-10-22: RED reproduced after fixture isolation repair; narrow metadata validator fix; focused and full suite GREEN. Ready for independent review, not final release approval.
- 2026-10-23, release verification relay: Implemented rejection of Markdown provenance injection in public portfolio metadata in `scripts/learnprint_portfolio.py`. Regression coverage: `tests/test_portfolio_labels.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
