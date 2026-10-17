# ADR-0001: UAT runs disposable; source repo never holds learner data

Status: accepted

Date: 2026-10-17

## Context

Learnprint is a public repository whose primary artifact is the source tree.
Its product, however, stores private learner data in a `Courses/` workspace.
Acceptance testing (docs/USER-ACCEPTANCE-TEST.md) originally assumed testing
in the real `Courses/` workspace "because that IS the product". The repo owner
decided the opposite for this checkout: the source tree stays clean, and every
UAT scenario runs against a disposable workspace root.

Decisions recorded in this ADR came from a grilling session on 2026-10-17:

- Definition of done for the finishing effort = green suite + live UAT run +
  push + PR (not green suite alone).
- UAT workspace: disposable for ALL scenarios (1-9), via `--courses-root`
  pointing into a temp directory. No `Courses/` is ever created at repo root.
- Learner identity during UAT: the real repo owner (real profile assessment),
  not a scripted persona.
- After UAT completes, ALL learner data is deleted, including the profile
  (redoing the assessment later costs ~5-10 minutes). No salvage, no migration
  into a real workspace.
- Defects surfaced by UAT become new tickets; they are not fixed inline in
  the UAT session.
- A privacy pre-commit hook (`install.py --hooks --approve`) is installed in
  this checkout: `.gitignore` alone is not a security boundary.

## Decision

1. Every UAT invocation passes `--courses-root <tempdir>`; the temp workspace
   survives only as long as the scenario chain needs it (scenarios 2 and 9
   require cross-session resume, so the same temp root is reused across the
   sessions of one scenario chain, then deleted).
2. The finishing effort deletes the temp workspace at the end. Learner data
   does not survive the test.
3. This repo's `main` branch must never contain learner data. The pre-commit
   hook plus `.gitignore` enforce this for the `Courses/` and personal-skill
   paths; the disposable-UAT convention extends the guarantee to testing.

## Consequences

- Standing-approval persistence across weeks is NOT covered by this UAT run
  (a temp workspace does not live that long). Cross-session resume within one
  sitting IS covered.
- Anyone re-running UAT later should treat this ADR as binding: do not
  "upgrade" to a real workspace without reopening it.
- The real profile assessment performed during UAT is throwaway by design;
  the owner accepts redoing it when they start actual learning.
- Contradicts nothing; the USER-ACCEPTANCE-TEST.md preamble assumes a real
  workspace — scenario mechanics in the finishing spec override that preamble
  for this repo only.
