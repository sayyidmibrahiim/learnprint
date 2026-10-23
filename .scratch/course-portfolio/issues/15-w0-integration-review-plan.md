# 15 — W0-04C exact-path integration and release gate plan

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-04C/W0-05
Scope: Review-only plan; **no staging, commit, hook installation, push, or publication authorized**.

## Baseline and ownership

This path inventory reflects the snapshot after W0-03C directory-chain mitigation and new issue 14, **before this issue 15 exists**: 14 modified tracked and 27 individual untracked = 41. Adding this new issue yields 42 dirty paths when no other agent modifies the workspace. Another active agent claimed `to-do.md` for W0-04B Windows CI-command verification at 13:50 WIB, so this plan is recorded in a separate file to avoid overwriting their tracker edits; after that claim closes, synchronize these exact paths into `to-do.md`.

Historical HEAD: `d98cf93ed980ff17d71e17f08ff5fb762d28c427`, feature/hardening-workspace; recheck immediately before staging.

## Proposed review batches and exact paths

**Batch A: mandatory agent bootstrap (4)**
- `AGENTS.md`
- `Code Style.md`
- `Learn Print Deep Research and Mega Enhancement Plan.md`
- `to-do.md`

**Batch B: older hardening/UAT (6)**
- `.agents/skills/learnprint-learn/references/TEACHING.md`
- `.scratch/learnprint-finish/issues/06-live-uat-disposable.md`
- `.scratch/learnprint-finish/issues/08-docs-quote-nonrunnable-hook-command.md`
- `.scratch/learnprint-finish/issues/09-preexisting-courses-root-workspace.md`
- `.scratch/learnprint-finish/spec.md`
- `docs/adr/0001-disposable-uat-workspace.md`

**Batch C: portfolio feature, index guard and CI, atomic when interdependent (32 including issue 15)**

Tracked changes (7):
- `.github/workflows/verify.yml`
- `.gitignore`
- `README.md`
- `rules/PRIVACY.md`
- `scripts/install.py`
- `scripts/learnprint.py`
- `tests/test_privacy.py`

New documentation/spec (3):
- `.scratch/course-portfolio/spec.md`
- `docs/COURSE-PORTFOLIO.md`
- `docs/adr/0002-selective-course-portfolio-publication.md`

Issue records (17, preserve the known duplicate 12-index-casefold-collision as wontfix; do not count it as a second bug):
- `.scratch/course-portfolio/issues/01-public-private-contract.md`
- `.scratch/course-portfolio/issues/02-preview-showcase-builder.md`
- `.scratch/course-portfolio/issues/03-git-safety-and-migration.md`
- `.scratch/course-portfolio/issues/04-evidence-ux-and-uat.md`
- `.scratch/course-portfolio/issues/05-release-gate.md`
- `.scratch/course-portfolio/issues/06-hook-link-safety.md`
- `.scratch/course-portfolio/issues/07-windows-reparse-export-boundary.md`
- `.scratch/course-portfolio/issues/08-index-root-alias-privacy.md`
- `.scratch/course-portfolio/issues/09-windows-trailing-dot-alias.md`
- `.scratch/course-portfolio/issues/10-manifest-parent-boundary.md`
- `.scratch/course-portfolio/issues/11-publication-metadata-markdown.md`
- `.scratch/course-portfolio/issues/12-case-collision-git-index.md`
- `.scratch/course-portfolio/issues/12-index-casefold-collision.md`
- `.scratch/course-portfolio/issues/13-manifest-hardlink-read-identity.md`
- `.scratch/course-portfolio/issues/14-directory-chain-toctou.md`
- `.scratch/course-portfolio/issues/15-w0-integration-review-plan.md`
- `.scratch/course-portfolio/issues/16-hook-upgrade-atomic-link-race.md`

New implementation/tests (6):
- `scripts/learnprint_portfolio.py`
- `scripts/learnprint_publish_guard.py`
- `tests/test_course_portfolio.py`
- `tests/test_publish_guard.py`
- `tests/test_publish_hook_install.py`
- `tests/test_skill_distribution_sync.py`

Inventory accounting (2026-10-22): A 4 + B 6 + C (7+3+17+6=33) = **43 paths** total, subject to renewed Git status review.

## Dependency and acceptance gates

- Ensure a **single feature-atomic change set** for `.gitignore` exception, source export, Git index guard, hook upgrade installer, privacy policy, workflow and associated tests. Do not land permissive ignore changes alone.
- Before any Git staging: independent review of every diff; owner explicitly consents to exact paths and intended repository action. Review index entries and modes/content, never blanket `git add -A`, `reset --hard`, `clean -fd` or `git add -f` on real Courses.
- Original learner `Courses/`, method receipts, profile, events and generated private learner skills must **never** appear in Git index or package. Actual real Courses/ integrity comparison is separate consented W0-01B work.
- Disposable Git fixture tests include good public and malicious private staged records; actual checkout index guard currently only proves no private files staged (zero public files checked).
- Latest local test after installer hardlink race fix: **344 passed, 2 skipped, 82 subtests** in 109.88s, Windows Python 3.14.0; packaging/index/CLI and mirror tests exit zero. See issue 16. Existing CI workflow *declares* Windows/Ubuntu/macOS × Python 3.9/3.12 but real matrix outcomes must be observed after integration.
- Human privacy review, learner UAT, independently reviewed TOCTOU atomicity (ABA swaps), installed hook upgrade/rollback, cross-OS CI, exact final Git status and release signoff still BLOCK. The code is **not** release ready.

## Comments

- 2026-10-22: Created while concurrent relay had claimed `to-do.md`. Owner's intent is to finish W0, not approval to alter installed hooks, staged index, commits or remotes.
- **TRACKER RECONCILIATION REQUIRED:** `to-do.md` currently ticks W0-04C as plan-documented and references section C4a, but C4a was NOT inserted because a separate W0-04B agent held the tracker claim and an optimistic-concurrency SHA check rejected the write. This issue 15 is the actual complete path-explicit integration plan. Once W0-04B releases `to-do.md`, either link W0-04C directly to this issue or insert C4a, update counts to reflect 42 paths (unless Git changes), and keep task status evidence-accurate. Do not overwrite the competing agent's verification output. Reconcile issue 15 in the tracker when claim closes.
- 2026-10-23, release verification relay: Completed: the reviewed exact-path integration landed as commits `cc826ea`, `1d39b2d` and `cecda70` on `feature/hardening-workspace`, then as PR #9 with 15/15 green jobs. No bulk staging, reset or clean was used. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
