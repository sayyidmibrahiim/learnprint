# 17 — Immutable offline portfolio revision regression

Status: ready-for-human
Date: 2026-10-22
Task: W8-02

## Scope and claim

Executor: GPT-6 Learnprint relay. Branch feature/hardening-workspace, HEAD d98cf93ed980ff17d71e17f08ff5fb762d28c427. Git preflight: 18 modified tracked, 53 untracked, 0 staged.

Claimed paths: tests/test_course_portfolio.py, docs/COURSE-PORTFOLIO.md, this issue, and to-do.md. All fixture exports use disposable directories outside the real Courses tree.

## Acceptance

- Export v1 with explicit approval and digest into a fresh temporary directory.
- Change synthetic source; stale v1 digest must fail without creating v2.
- Fresh v2 digest and approval export to a different temporary directory.
- v1 bytes remain unchanged; reusing v1 destination fails closed.
- Private synthetic course state and ledger remain untouched.
- Document limitation: this tests immutable offline snapshots only, NOT public Git revision namespaces (ADR-0002 still requires reviewed design).

## Comments

- 2026-10-22: Claimed for bounded regression and documentation. No real Git staging, hook changes, or learner data access.
- 2026-10-22: Verified `test_offline_revisions_are_immutable_and_require_fresh_consent` in `tests/test_course_portfolio.py`: two distinct disposable offline revisions, stale digest rejected, new consent required, original revision unchanged, destination reuse refused, private fixture state and ledger byte-identical. Updated `docs/COURSE-PORTFOLIO.md` to explain supported offline workflow and explicitly disallow assuming public Git version subfolders are supported.
- Exact focused results: `python -m pytest tests/test_course_portfolio.py -q` exit 0, **32 passed, 1 skipped, 20 subtests** (3.25s); `python -m pytest tests/test_portfolio_labels.py -q` exit 0, **6 passed, 2 subtests** (0.14s).
- Exact full results: `python -m pytest tests/ -q --tb=no` exit 0, **482 passed, 2 skipped, 244 subtests** (96.67s); `python scripts/check_package.py` exit 0 PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` exit 0, 0 public courses/files and 0 private indexed.
- Scope changed: `tests/test_course_portfolio.py`, `docs/COURSE-PORTFOLIO.md`, this issue, `to-do.md`. No real Courses, hook, staging, commit, push, or remote publication.
- Remaining decision gate: public Git revision/version namespace schema and index guard must receive separate ADR/owner review before implementation. Next safe task: W8-02 design review with exact public path/manifest/index semantics; alternatively continue unrelated W9/W10 verification. Human UAT, cross-OS CI, independent security review and W0-05 scoped Git integration remain release gates.
