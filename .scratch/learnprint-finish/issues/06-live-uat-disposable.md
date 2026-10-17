# 06 — Live UAT on disposable workspace

Status: ready-for-agent
Blocked by: 03, 05

## Purpose

Run the full User Acceptance Test (docs/USER-ACCEPTANCE-TEST.md, scenarios
0-9) against a DISPOSABLE workspace root. This is the only ticket that needs
the human in the loop as the learner — schedule it as an interactive session
with the owner present.

## Binding decisions

- **ADR-0001** (docs/adr/0001-disposable-uat-workspace.md): every scenario
  uses `--courses-root <tempdir>`; the repo root NEVER gets a `Courses/`
  directory; ALL learner data (including the profile) is deleted at the end.
- D6: the learner is the real owner — run the real profile assessment
  (learnprint-assess flow), do not use a scripted persona.
- D7: any defect found becomes a NEW ticket under
  `.scratch/learnprint-finish/issues/`; nothing is fixed inline here.
  Record each defect as `Defect: <NN>-<slug>` under Comments as it appears.

## Mechanics

1. Create temp root: `$env:TEMP\uat-learnprint-<date>` (or POSIX equivalent).
2. Scenario 0 (sanity) runs against the default paths as written (it is
   read-only). For every mutating command in scenarios 1-9, append
   `--courses-root <temproot>`.
3. Scenario 1 (first run): the approval prompt happens in chat, exactly as
   the doc specifies — the standing approval is recorded inside the temp
   workspace.
4. Scenarios 2 and 9 need cross-session resume: keep the SAME temp root and
   start a fresh chat session, per the doc.
5. Scenario 5 (misconception) and any teaching scenario: learner answers are
   DATA (repo invariant 3); record them via the recorder as the doc says.
6. Scenarios 8-9 already specify disposable dirs — still route them under
   the same temp root for uniform cleanup.
7. After scenario 9: run `course validate` one final time (expect VALID),
   then delete the entire temp root (including any `.bak`/recovery files).
8. Confirm `Test-Path Courses` at repo root → False.

## Acceptance

- [ ] Scenarios 0-9 each pass (or their failure is filed as a Defect ticket)
- [ ] All defect tickets referenced under Comments; PR-blocking vs
      non-blocking classification noted per defect
- [ ] Temp workspace deleted; `Courses/` absent at repo root
- [ ] Results summary under Comments (one line per scenario: PASS/DEFECT)

## Commit

None directly — only new defect tickets (if any), one commit per ticket file.
