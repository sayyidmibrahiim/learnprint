# ADR-0001: Disposable UAT with private learner workspace preserved

Status: accepted for disposable UAT; partially superseded by ADR-0002 for real Courses/ portfolios

Date: 2026-10-17

## Context

Learnprint is a public repository whose primary artifact is the source tree.
Its product, however, stores private learner data in a `Courses/` workspace.
Acceptance testing (docs/USER-ACCEPTANCE-TEST.md) originally assumed testing
in the real `Courses/` workspace "because that IS the product". The repo owner
decided to isolate testing: the public Git history stays free of private
learner records, and every UAT scenario runs against a disposable root.
Existing real Courses/ remains local and private under ADR-0002.

Decisions recorded in this ADR came from a grilling session on 2026-10-17:

- Definition of done for the finishing effort = green suite + live UAT run +
  push + PR (not green suite alone).
- UAT workspace: disposable for ALL scenarios (1-9), via `--courses-root`
  pointing into a temp directory. Never create or mutate real `Courses/` for UAT; existing learner data may remain at repo root under ADR-0002.
- Learner identity during UAT: the real repo owner (real profile assessment),
  not a scripted persona.
- After UAT completes, ALL **disposable UAT** learner data is deleted,
  including its temporary profile. The pre-existing real Courses/ workspace
  is preserved and must be verified unchanged.
- Defects surfaced by UAT become new tickets; they are not fixed inline in
  the UAT session.
- A privacy pre-commit hook (`python scripts/install.py --target opencode --self --hooks --approve`) is installed in
  this checkout: `.gitignore` alone is not a security boundary.

## Decision

1. Every UAT invocation passes `--courses-root <tempdir>`; the temp workspace
   survives only as long as the scenario chain needs it (scenarios 2 and 9
   require cross-session resume, so the same temp root is reused across the
   sessions of one scenario chain, then deleted).
2. The finishing effort deletes the temp workspace at the end. Learner data
   does not survive the test.
3. This repo's `main` branch must never contain raw private learner data.
   The private original Courses/ folders remain gitignored; only approved
   derived Courses/public/<uuid>/ snapshots may become trackable under ADR-0002.
   The indexed-publication guard enforces the manifest boundary. Disposable
   UAT never touches the real learner workspace.

## Consequences

- Standing-approval persistence across weeks is NOT covered by this UAT run
  (a temp workspace does not live that long). Cross-session resume within one
  sitting IS covered.
- Anyone re-running UAT later should treat this ADR as binding: do not
  "upgrade" to a real workspace without reopening it.
- Only the profile assessment performed in the disposable UAT root is
  throwaway by design. Existing real learner profiles are never removed;
  a later real learner assessment is governed by the existing profile state.
- Contradicts nothing; the USER-ACCEPTANCE-TEST.md preamble assumes a real
  workspace — scenario mechanics in the finishing spec override that preamble
  for this repo only.
