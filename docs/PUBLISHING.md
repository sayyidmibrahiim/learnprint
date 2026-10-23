# Learnprint publishing and branch integration

Updated 2026-10-23. The GitHub repository **already exists**:
https://github.com/sayyidmibrahiim/learnprint

## What the branches mean

- `main` is the reviewed, integrated release base. It does **not** mean every future feature is finished.
- `feature/hardening-workspace` was merged into `main` through PR #9 (merge commit `1b9b785`) and its remote branch was deleted after merge. `main` is now the source of truth.
- `fix/tutor-language-stage-contract-20261023` / PR #8 was the redundant parallel draft. It was **closed without merge** after the universal language/stage policy was integrated through PR #9. Do not reopen or merge the duplicate.

## Controlled integration to main (executed 2026-10-23 for PR #9)

Outcome: explicit path-level staging, privacy guard OK with zero indexed paths, pre-merge CI 15/15 on `83026b5`, merge commit `1b9b785`, and post-merge run `39908358179` 15/15 green. Steps below remain the reusable runbook.

1. Finish the applicable tasks on `feature/hardening-workspace`, rerun tests, package and staged-index publication guard. Check exact change inventory; protect all private `Courses/` state.
2. Resolve all on-disk edits/claims and use a local Git tool with explicit path-level staging, diff review and privacy scan. Commit coherent units only with owner authorization; never `git add -A`, `git reset --hard`, or `git clean`.
3. Fetch `origin/main`, inspect ancestry/divergence. Push the reviewed feature branch only with owner approval, then open a SINGLE integration pull request against `main`. PR #8 was closed without merge as superseded; integrate once through the primary workstream rather than merging duplicate work.
4. Require PR CI, Windows tests, cross-platform Python versions, privacy guard, and real host/model UAT for any feature making behavioral claims. Distinguish engineering PASS from human learning effectiveness NOT VERIFIED.
5. Merge via GitHub only after the diff/CI/reviews pass. Then update/recreate the next feature branch from the current `main`. Tag `v1.0.0` only when the specifically agreed release acceptance criteria are met. That tag was NOT created on 2026-10-23 because human UAT, learner efficacy and independent security review are still open.

## Private Courses and optional public course portfolios

ALL courses are *eligible for the learner to consider* as GitHub proof-of-work, regardless of subject or scope. NONE are automatically public.

Use read-only `python scripts/learnprint.py course portfolio-options`. For each chosen course, create a private manifest allowlisting only owned shareable artifacts, inspect the exact `portfolio-preview`, then explicitly approve `portfolio-export`. Each export creates a separate bounded public snapshot and still performs **no Git commit or push**. Use the staged Git index privacy guard before any separately approved Git publication. Courses not selected remain private. A course with no authentic shareable artifact is eligible to prepare but not ready to claim proof-of-work.

The canonical originals `Courses/.learnprint/` and `Courses/<category>/<course>/` are never pushed. Consult [ADR-0002](adr/0002-selective-course-portfolio-publication.md), [COURSE-PORTFOLIO.md](COURSE-PORTFOLIO.md), [PRIVACY.md](../rules/PRIVACY.md), and the [GitHub sensitive data/history guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). Even deleting a remote file later cannot erase copies already cloned or forked.

## This document does not authorize Git changes

It records the safe sequence only. A successful build is not permission to push learner work. If tooling only permits safe read/write/test actions, mark staging/merge unexecuted rather than manufacturing a clean release claim.
