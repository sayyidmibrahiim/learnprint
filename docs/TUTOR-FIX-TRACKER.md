# Learnprint Tutor UX Remediation Tracker

**Started:** 2026-10-23. **Scope:** natural multilingual communication, explicit learning stages, accurate progress, faithful evidence.  
**Canonical implementation:** AGENTS.md, skills/learnprint/references/JOURNEY.md, PRESENTATION.md and TUTOR-LANGUAGE-AND-STAGES.md.  
**Acceptance:** docs/TUTOR-LANGUAGE-STAGES-UAT.md. **No claim that all broader Learnprint/W0 tasks are finished.**

This tracker describes the public branch work, not the learner's private local Courses/ status. Private files, real learner evidence and test receipts must never be copied into this public repository.

| ID | Task | State | Evidence / remaining work |
|---|---|---|---|
| TUX-01 | Author multilingual, idiomatic response contract | DONE IN BRANCH, NOT HOST-VERIFIED | TUTOR-LANGUAGE-AND-STAGES.md; explicit rule against unexpected third-language, gibberish and broken mixed-language exercises |
| TUX-02 | Require stage labels and screening ceiling | DONE IN BRANCH, NOT HOST-VERIFIED | New contract: 0–3 short prompts, ceiling not quota, count prompts/items separately, mode changes and transitions labeled |
| TUX-03 | Honest ASCII roadmap and progress | DONE IN BRANCH, NOT HOST-VERIFIED | Unit-position example; never convert 1/3 into 33% learned; canonical mastery only |
| TUX-04 | Apply policy across entrypoints | DONE IN BRANCH, NOT HOST-VERIFIED | AGENTS, portable skill mirrors, learn skill, PRESENTATION, JOURNEY references |
| TUX-05 | Add human-reviewed live host UAT | UAT SPEC WRITTEN; EXECUTION OPEN | docs/TUTOR-LANGUAGE-STAGES-UAT.md; stock/custom OpenCode + other hosts must be tested with real responses |
| TUX-06 | Ensure stage card is always generated at required transitions | OPEN | Agent instruction is not deterministic. Investigate persisted vs inferred phase, structured CLI snapshot or host bridge and regressions |
| TUX-07 | Fix private course HANDOFF/SYLLABUS/MAP projection consistency | OPEN, LOCAL EVIDENCE NEEDED | Reported private sample has stub syllabus/map and stale HANDOFF; use read-only audit, preserve current course ID/evidence, repair only with authorization |
| TUX-08 | Fix evidence recording command quoting across Windows shells | OPEN | Agent had repeated JSON argv parsing failures and resorted to private-script internal cmd_record; design documented public \`record\` input-file or stdin JSON option with CLI tests before modifying user records |
| TUX-09 | Catch learner-language regressions in real AI output | OPEN | Run human-reviewed transcripts across Indonesian, English and mixed instruction; static word bans are insufficient |
| TUX-10 | Research and product-readiness audit against current local W0/TODO | BLOCKED | CodexProLatestFix local connection unavailable during this review; public GitHub main was last seen at 3f19d392 from Oct 11, so it does not establish current local completeness |
| TUX-11 | Confirm personal assessment offer shown only once and default choice persists | OPEN, HOST-UAT | Existing journey/CLI rule; user shared \`assessment_offer=deferred\`, which alone cannot prove the offer was verbally presented originally |
| TUX-12 | Separate diagnostic/practice/test/transfer/review status in persistent rendering | OPEN | Need actual per-turn host evidence; \`course plan\` and ledger are canonical, no agent-invented counts or learned percent |

## Reconciliation rule

Before closing a task:
1. Read actual source at the branch/working tree in question and the learner-facing transcript.
2. Name the exact evidence and differentiate prompt policy PASS, deterministic test PASS, live host UAT PASS, and private learner state VERIFIED.
3. Link project workstreams without overwriting a separately owned TODO ledger.
4. For real learner data, never create/edit/exclude/grade events on the basis of this public issue report.
5. Keep this tracker and main implementation plan aligned once the local workspace is accessible.

**Current conclusion:** the new prompt contract is drafted and linked in the proposed branch; its observed behavior remains NOT VERIFIED. The old language failures are real examples in the user-provided transcript, not evidence that the new policy has corrected the host.
