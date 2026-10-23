# Feature: Publishable Learnprint course portfolios with per-course privacy

Status: engineering verified on head cecda70 (15/15 CI jobs green, PR #9); human UAT, real learner efficacy and independent security review remain OPEN
Date: 2026-10-19
Governing decision: docs/adr/0002-selective-course-portfolio-publication.md

## Product contract

A course is a learner-owned, GitHub-shareable record of what they studied, practiced and *demonstrated* using real hands-on projects. Users may keep selected courses private by adding the course path to .gitignore through a supported, clear workflow. Personal profiles, raw answers, unfiltered agent notes, receipts, local preferences, backups and canonical evidence ledger are never auto-published.

Do not conflate a learning portfolio or self-issued statement with an institution-accredited certificate. Claims include review provenance and explicit limitations. GitHub is a hosting surface, not an independent credential issuer.

## Current baseline

- Historical baseline: entire `Courses/` was initially gitignored.
- Historical baseline: installed pre-commit hook initially rejected all `Courses/` files.
- Current candidate makes only `Courses/public/<uuid>/` Git-trackable, with index guard and installable v2 hook; upgrading the actual local installed hook is still pending.
- Current course folders mix public-looking files with state.json, HANDOFF, method-sessions.jsonl and possible logs.
- Canonical progress evidence is in ignored `Courses/.learnprint/events.jsonl`.
- Existing real learner data at repo Courses/ must be kept intact.
- Branch contains earlier six-file hardening changes; do not overwrite or revert them.

## Release architecture

1. Private source of truth remains ignored and in place. `state.json`, `HANDOFF.md`, `method-sessions.jsonl`, `learning-log.jsonl`, backups and private generated files remain excluded at every nesting level.
2. Explicit course visibility, default safe-unpublished until the publication boundary and tests pass; once enabled the *curated public artifact subset* is easy to commit and portable across hosts.
3. Each public course has a useful README, sanitized syllabus/map, evidence/competency summary labeled as provisional or independently reviewed, and runnable projects or links to preserved actual outputs. Generated examples must never be presented as actual work.
4. Independent, deterministic publish preview listing all files, redaction warnings, Git ignore/tracking consequences and evidence/provenance checks. Refuse by default if any risky or unknown file is selected. Commit/push requires separate explicit action, outside the learning write grant.
5. Per-course private switch adds ignore rule and prevents future exports, while detecting already tracked files and explicitly warning about Git history/remotes/forks.
6. Implement backward-compatible migration for existing courses with NO mutation until approved. A rollback path must preserve immutable course IDs and evidence ledger.
7. Publish index only lists approved public course summaries, never private names or private progress.
8. Keep 3.9+ stdlib constraints; portable installer/hook behavior and tests run on Windows/Linux/macOS.

## Gates

- No change to .gitignore, privacy hook or any learner course before fail-closed publication tests are green.
- No automatic commit/push, remote API call or destructive repo clean.
- No changes to existing personal data (except narrowly authorized migration after preview).
- Security tests: staged raw ledger, profile, session receipt, private answers, secret fixtures, binary files, symlinks, path traversal, nested private paths, ignored/unignored/tracked variants, Unicode paths, relabel public-to-private, and partial-interruption recovery.
- Functional tests: publish and private modes, good public hands-on code, proof links, evidence basis labels, content revisions, new sessions, revalidate after changes, offline use.
- Human UAT: real learner demonstrates an actual practical task; independent reviewer assesses the output; learner inspects exact public preview before any remote publish.

## Work order

1. 01-public-private-contract: enumerate all paths and entrypoints, freeze exact schema and safe file policy.
2. 02-preview-showcase-builder: implement deterministic, read-only-by-default export + schema/provenance/visibility interface.
3. 03-git-safety-and-migration: update ignore/hook/installer as atomic release; preserve real Courses/ and backcompat.
4. 04-evidence-ux-and-uat: sample portable course portfolio, hands-on artifacts and honest provenance, cross-host tests + docs.
5. 05-release-gate: all tests/CI, actual learner UAT, security review and separate PR; no publication of real data without explicit owner approval.

## Execution checkpoint — 2026-10-19

Implemented locally on feature/hardening-workspace (UNCOMMITTED):
- scripts/learnprint_portfolio.py: fail-closed, text-only, selected hands-on artifacts, privacy scan, preview digest, atomic export.
- scripts/learnprint.py: course portfolio-preview and portfolio-export commands.
- tests/test_course_portfolio.py: disposable data, private/public, digest, provenance, negative path and credential cases.
- tests/test_skill_distribution_sync.py: package check and portable skill mirror consistency.
- docs/COURSE-PORTFOLIO.md: exact manifest format and safe usage.
- README.md: documentation pointer.

Verification:
- Portfolio + Git index + hook integration tests run in temporary Git repositories, with no real Courses/ mutation.
- Most recent whole local suite: **315 passed, 1 skipped, 68 subtests passed** (Windows Python 3.14, 2026-10-19).
- Packaging check runs through pytest regression; project installer legacy compatibility restored (18 installer tests passed in focused run).
- Previous full-suite runs showed nondeterministic timeout on Windows around syllabus/prerequisite tests; isolated and later full runs passed. Treat runtime reliability as NOT FULLY VERIFIED.
- Still pending: actual cross-platform CI, upgraded real checkout hook, human learner UAT, independent source/security review, separated commits/PR.

Known remaining work:
- Root .gitignore now permits only curated Courses/public/<uuid>/ snapshots to be trackable; private source Courses/<category>/ and .learnprint remain ignored. Per-course opt-out documented and tested; previously tracked snapshots need separate untracking.
- CLI requires user-maintained manifest; novice-friendly interactive manifest authoring is still a product improvement. Current README/EVIDENCE claims are self-declared, not independently attested.
- Credentials/PII scanner is heuristic and cannot guarantee confidentiality.
- Claims in EVIDENCE.md have self-declared provenance, not ledger-backed independent attestation.
- Only UTF-8 text hands-on files can export; no binary/image/media yet.
- Never delete/move actual Courses/, and never auto-push user content.
- Branch isolation required before committing: feature/hardening-workspace already contains unrelated uncommitted hardening changes. Separate independently reviewed scoped commits/PRs. Do not git add -A or auto-push.
- Current CodexPro bridge exposes read/write/edit/verification but no authorized Git stage/commit/push operation; leaving worktree dirty is a tooling limitation, not completion.
- Existing .git/hooks/pre-commit in this checkout was installed before v2. The source installer supports explicit verified legacy-hook upgrade, but the real hook upgrade was NOT performed. Do not try to publish until it is installed/tested.

## References

- Git ignore limitations: https://git-scm.com/docs/gitignore
- GitHub sensitive data removal: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- Open Badges 3.0 semantics and evidence: https://standards.1edtech.org/open-badges/specifications/standards/v3p0
