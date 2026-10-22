# 09 — Pre-existing Courses/ learner workspace at repo root (owner decision)

Status: resolved
Blocked by: none — owner chose KEEP for existing Courses/; see ADR-0002
Found during: ticket 03 probe (2026-10-17)

## Finding

The repo root contains an untracked, `.gitignore`d `Courses/` workspace with
REAL learner data, mtimes 2026-10-11 (pre-dates ADR-0001 and this plan):

- `Courses/.learnprint/` — `approval.json` (granted_by `chat-approval`,
  2026-10-11T04:10Z, scope incl. `profile-write`), `config.json`,
  `events.jsonl` (~3.7KB), `registry.json` (+`.bak`), `reviews.json`,
  `learner/profile.json` (~733B), `.lock`
- `Courses/technology/database-sql-interview-sprint/` — `state.json` (~3.2KB),
  `SYLLABUS.md` (~4.1KB), `HANDOFF.md`, `MAP.mmd`, `method-sessions.jsonl`
- `Courses/technology/cara-dns-bekerja-saat-buka-website/` — `state.json`,
  `SYLLABUS.md`, `HANDOFF.md`, `README.md`, `MAP.mmd`, `method-sessions.jsonl`
- `Courses/HANDOFF.md`

Provenance: created during the hardening workstream (its commit sequence lists
`feat: Courses/ workspace initialization + first-run UX`). It was NOT created
by ticket 03: the probe's `mkdir Courses` failed with "already exists". The
probe file `_hook_probe.txt` has been removed; everything else is untouched.

## Tension with current binding docs

- ADR-0001: "No `Courses/` is ever created at repo root"; title says the
  source repo never holds learner data.
- Ticket 06 mechanics step 8: "Confirm `Test-Path Courses` at repo root → False".
- D6's deletion policy is scoped to the UAT temp workspace — it does not
  explicitly cover this pre-existing Oct-11 workspace.
- Deleting it is irreversible (learner profile + two courses' progress).

## Options (owner decision; NO action taken by the builder)

1. DELETE — matches ADR-0001's end state; destroys the profile and both
   courses' records. Irreversible.
2. KEEP — accept a local, gitignored workspace at repo root; reinterpret
   ticket 06's final check as "no UAT leftovers at repo root".
3. RELOCATE — move it outside the repo (e.g. `%USERPROFILE%\learnprint\`),
   using the existing `--courses-root` support on all mutating commands;
   repo root clean, data preserved. Needs a canonical-location decision.

Builder note (non-binding): option 3 preserves data and satisfies ADR intent;
option 1 is acceptable only with explicit owner approval.

## Acceptance

- [x] Owner picked an option
- [x] Ticket 06's final check + D5/ADR wording reconciled with the choice
- [x] No delete/relocate executed (KEEP); existing data untouched

## Commit

Folded into the tracker evidence commit
`docs: record finishing-plan ticket evidence (01-04) and file tickets 08-09`.

## Comments

- 2026-10-17 builder: filed from ticket 03; data left completely intact.
- PR-blocking classification (for ticket 07's description): NON-blocking for
  the PR itself, but MUST be resolved before/at ticket 06's final check.
- 2026-10-19: Owner clarified that Courses/ is intended as a selectively
  publishable portfolio of learning evidence and hands-on projects. Decision:
  KEEP the existing real Courses/ at the repo root. Never delete/relocate it
  for disposable UAT. See ADR-0002. Public publishing is a separate gated
  feature and not authorization to stage the existing private contents.
