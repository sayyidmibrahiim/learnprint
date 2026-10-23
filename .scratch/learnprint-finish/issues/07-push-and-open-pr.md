# 07 — Push branch and open PR

Status: resolved
Blocked by: 06

## Purpose

Ship `feature/hardening-workspace` to origin as a PR against `main` (D9).
Owner approved push + PR; the fetch step below is a mandatory mechanical
precondition, not a decision point — origin showed 7 new refs on dry-fetch
and may have diverged.

## Steps

1. `git fetch origin` — inspect divergence:
   - `git log --oneline HEAD..origin/feature/hardening-workspace` (did the
     remote branch move?)
   - `git log --oneline HEAD..origin/main` (did main move?)
2. If origin's `feature/hardening-workspace` exists and diverged: STOP —
   report; rebasing someone else's pushed branch needs the owner.
   If only `origin/main` moved: merge `origin/main` into the feature branch,
   run the full suite again (must stay 283 green), then continue.
3. `git push origin feature/hardening-workspace`
4. Open PR `feature/hardening-workspace` → `main` (gh CLI if authenticated,
   otherwise print the compare URL for the owner to click).
5. PR description must contain:
   - What changed since PR #7 (meta-test fix, docs, hook, plan cleanup)
   - Verification evidence (283 green, packaging OK, UAT scenario summary
     from ticket 06 Comments)
   - Any open defect tickets from 06, each classified blocking / non-blocking

## Acceptance

- [ ] Branch pushed; PR to `main` exists (link under Comments)
- [ ] Suite re-verified green after any merge of origin/main
- [ ] PR description includes evidence + open-defects list (or "no defects")

## Commit

None — push + PR only.

## Comments

- 2026-10-23, release verification relay: Resolved: branch pushed and PR #9 opened against `main`. Runs `39890427415` and `39890434260` are 15/15 green on head `cecda70`; merge is a separate owner decision tracked by `course-portfolio/issues/05-release-gate.md`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
