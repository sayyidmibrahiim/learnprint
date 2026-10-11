# Learnprint User Acceptance Test (one sitting, ~30 minutes)

You need: the repo open in an AI agent (OpenCode, Codex, Claude Code, Kiro,
Gemini CLI, or Antigravity), Python 3.9+, and a terminal. Nothing is
installed globally; all learning data stays in the private `Courses/`
directory (git-ignored, never committed).

> Rule: test in the REAL `Courses/` workspace for scenarios 1–7
> (that is the product). Scenarios 8–9 use disposable temp directories so
> your real workspace is never at risk.

## 0. Sanity (2 min)

PowerShell:

```powershell
python scripts/learnprint.py course --help
python scripts/learnprint.py validate --profile profiles/founder-default.json
```

POSIX (`bash`/`zsh`): same commands with `python3`.

Expected: help text, then `VALID`.

## 1. First run — "Belajar: in/on/at"

Say to the agent:

```text
Belajar: in/on/at
```

Expected:

1. Agent finds `AGENTS.md` at repo root and follows the course-workspace
   rules (resolve → gate → create with approval).
2. If no `Courses/` exists, the agent ASKS for permission to initialize it
   (standing approval + `--approve`); nothing is created silently.
3. On approval it creates `Courses/` with `.learnprint/` inside
   (registry, ledger, profile, approval record).
4. It creates (or reuses) the English Grammar course and STARTS TEACHING:
   objective, baseline check, explanation, practice — without asking you
   to navigate directories.
5. Verify on disk:

```powershell
python scripts/learnprint.py course list
python scripts/learnprint.py course validate
```

Expected: one course under `languages/english/grammar`, output `VALID`.

## 2. Reuse — same topic, new session

Start a NEW agent session (fresh chat), say:

```text
Belajar English prepositions in, on, and at
```

Expected: the existing course is recognized (alias/title match), NO second
course folder appears, previous progress is intact.

```powershell
python scripts/learnprint.py course list
```

Count stays at 1 for this topic.

## 3. Different language — no silent merge

```text
Belajar grammar bahasa Jepang
```

Expected: a DISTINCT branch `languages/japanese/grammar` is created
(after the confirmation gate for the new `japanese` segment). English
Grammar is NOT reused. `course list` shows both.

## 4. Technical vocabulary — no keyword hijack

```text
Belajar vocabulary DevOps: CI/CD, IaC, deployment
```

Expected: placed under `technology/devops/...` (after confirmation),
NOT under English. The router validates taxonomy; it does not keyword-match
"vocabulary" into English.

## 5. Resume — "Continue"

In a new session say:

```text
Continue
```

Or run:

```powershell
python scripts/learnprint.py course resume
```

Expected: the active course resumes with prior evidence accessible.
Statuses reflect ONLY recorded responses — no fabricated progress.
(If several courses are equally recent, the agent must ASK which to resume.)

## 6. Evidence and retention — one learning unit

Complete one taught unit (answer, get graded, do the transfer task).
Then inspect:

```powershell
python scripts/learnprint.py course plan-reviews --approve
python scripts/learnprint.py course dashboard --approve
Get-Content Courses\.learnprint\events.jsonl | Select-Object -Last 3
```

Expected:

- Each answer appended ONE line of JSON with `rubric`, `grader`,
  `evidence_origin: observed_response`.
- `INDEX.md` shows per-course status counts plus `Due now`
  (overdue/ready) SEPARATELY from `Scheduled reviews` (future).
  Future reviews are never labeled due.
- Every percentage carries its basis: `provisional` (AI-graded),
  `learner_confirmed`, or `substantiated` (two-source). Provisional is
  normal and honest — not a failure.

## 7. Fresh host session — state from disk

Open the repo in a SECOND host app (or a clean session) and say
`Continue`. Expected: same course, same evidence — loaded from disk,
not from chat memory.

## 8. Denial / revocation (disposable sandbox)

```powershell
$T = "$env:TEMP\lp-deny"; mkdir $T -Force | Out-Null
python scripts/learnprint.py course init --courses-root $T --approve
python scripts/learnprint.py course revoke-approval --courses-root $T
python scripts/learnprint.py course create --courses-root $T --category life/imported `
  --title "denied" --goal "g" --confirm-new-segment imported --approve
```

POSIX:

```bash
T=$(mktemp -d)
python3 scripts/learnprint.py course init --courses-root $T --approve
python3 scripts/learnprint.py course revoke-approval --courses-root $T
python3 scripts/learnprint.py course create --courses-root $T --category life/imported \
  --title denied --goal g --confirm-new-segment imported --approve
```

Expected: the create FAILS (exit 2, standing-approval error) and NO course
directory is created. Then delete `$T` / `$T`.

## 9. Move / rename keeps identity (disposable sandbox)

```powershell
$T = "$env:TEMP\lp-move"; mkdir $T -Force | Out-Null
python scripts/learnprint.py course init --courses-root $T --approve
$C = python scripts/learnprint.py course create --courses-root $T --category life/imported `
  --title "moveme" --goal "g" --confirm-new-segment imported --approve | ConvertFrom-Json
$ID = $C.course_id
python scripts/learnprint.py course rename --courses-root $T --course-id $ID --title "moved" --approve
python scripts/learnprint.py course move --courses-root $T --course-id $ID `
  --category life/renamed --confirm-new-segment renamed --approve
python scripts/learnprint.py course validate --courses-root $T
```

Expected: `VALID`; the `course_id` is unchanged after rename+move;
evidence (if any) still resolves to the same course.

## 10. No filesystem / unsupported host — honest fallback

If the host cannot run tools or write files, the agent must say so and
continue in prompt-only mode. It must NEVER claim files were written.
Verify any such claim with `course list` / `course validate`.

## Troubleshooting (safe, read-only first)

```powershell
python scripts/learnprint.py course validate            # INVALID? read the listed problems
python scripts/learnprint.py course validate --repair --approve   # adopt orphans, clear stale temps
python scripts/learnprint.py course repair-evidence --approve     # truncated ledger tail only
git status --short                                    # Courses/ must never appear
```

- `INVALID ... MANUAL INTERVENTION REQUIRED`: do NOT delete evidence.
  Back up `Courses/`, then ask for help with the exact message.
- Never hand-edit `events.jsonl`, `registry.json`, or `state.json`.
- Never `git add -f Courses/`.
- Mid-file ledger damage is REFUSED by repair by design — that is the
  tool protecting your history, not a bug.

## What this guide does NOT prove

- Other AI hosts behave identically (only YOUR host + version is tested).
- The LLM classified every topic perfectly (check `course list` paths).
- The pedagogy is optimal (that is a human judgment per unit).
- Zero defects remain (report issues with exact commands + output).


## 11. New Learnprint command suite (manual, project-local)

On a **fresh default OpenCode install** in the Learnprint repository root,
with no global custom skills or memory providers:

1. Run /learnprint. It should read method status, show assessment vs
   founder-default choice when needed, and NOT create Courses/ before
   explicit chat approval.
2. Approve initialization only after the scope is stated. Choose the default
   method; close and reopen the agent; /learnprint must NOT ask again.
3. On a disposable learner workspace, start /learnprint-assessment.
   Answer two different types of real questions; after a new session, the
   agent must use learner assessment-history and must not re-ask the same
   completed questions. It may not claim the method is assessed until a
   valid evidence-linked private candidate is applied.
4. Invoke /learnprint-continue-learn; expect real listed course IDs,
   paths and evidence-based status, never invented percentages.
5. Invoke /learnprint-test, /learnprint-progress, /learnprint-review,
   /learnprint-dashboard and /learnprint-help. Check honest behavior for
   missing workspace, no evidence, unavailable CLI and denied writes.
6. Verify that /learnprint-reassessment leaves the active assessed profile
   unchanged until a fully validated candidate is completed.
7. Compare behavior with and without custom global OpenCode plugins.
   Local Courses/ data is canonical in BOTH cases.
8. If a legacy course state has competency IDs without names, expect
   state_invalid rather than fake progress. Repair privately via
   course scope-set with the same IDs and accurate names; never delete
   existing evidence or re-init a populated workspace.

This section defines user acceptance; automated tests only prove CLI and
packaging behavior, NOT live semantic model or pedagogical quality.

## 12. Live tutoring regression: roadmap, confusion, hands-on, test

Perform this in a disposable local course; do NOT erase existing learner
evidence to reproduce the old bugs.

1. Start /learnprint-learn or /learnprint-continue-learn. Before a quiz,
   the agent must run learner method and course plan, SHOW method source,
   fingerprint and a real ordered syllabus (or visibly proposed draft).
2. Check at least one real-world practical task per syllabus unit, its
   input, output, verification and measurable success criterion.
3. Say "Gak ngerti gw maksudlu probe" at the diagnostic. Expect a
   simple explanation and one small question at a time, NOT an automatic
   scored failure or a complex JOIN exercise.
4. Ask for a concept missing from the syllabus. The agent should show
   whether it belongs to an existing unit or propose a new prerequisite
   with before/after position and ask approval before plan-set.
5. Say "masih gak ngerti" after a weak analogy. The agent must pause
   tests, identify the actual misunderstanding and use a consistent
   literal explanation / concrete demonstration, not randomly swap
   metaphor domains or record the statement as a 0-score test.
6. Ask /learnprint-practice to perform an actual local safe SQL example
   (e.g., SQLite in-memory SELECT, only if available); verify observed
   output. Denied tool access must be reported, not fabricated.
7. Request /learnprint-test only after teaching. Verify independent
   application and novel transfer are different fresh tasks, with
   criterion-level rubric and real learner answer recorded.
8. Request /learnprint-progress; it must be provisional where
   AI-graded. A completed unit must NOT be called permanent mastery
   without actual delayed retrieval evidence.
9. Start a new host session; method fingerprint, syllabus, events and
   next unit should be read from local Courses/ rather than agent memory.
10. Repeat on a standard OpenCode install without global memory/graph
    tools. Manual host behavior cannot be inferred from CI tests.

See docs/LEARNING-JOURNEY.md for CLI/JSON contract and research context.

## 13. Method visibility and audit, including noncompliance

On a temporary course and default OpenCode (no global plugins):
1. /learnprint-method should show effective source, language, analogy and
   other real preferences, revision and v2 fingerprint.
2. After explicitly approving the learning session, obtain
   `course session-start --course-id ID --approve` and verify the
   returned session UUID is echoed in subsequent lesson-log/record calls.
3. /learnprint-audit should PASS method receipt integrity and any existing
   linked canonical artifacts; behavioral adherence should remain
   NOT_VERIFIED, never auto-PASS from agent narration.
4. On a disposable workspace ONLY, change an active preference after
   starting a session, then run method-audit. It should detect method
   drift and report FAIL with nonzero exit (do NOT tamper with real profile).
5. Missing receipt on a historical course -> NOT_VERIFIED, not FAIL.
6. Supply a fake transcript saying "I followed everything"; the audit
   hashes it but MUST NOT certify the teaching behavior as compliant.
7. Verify both default and customized OpenCode configurations agree on
   source-of-truth profile/evidence. Human review of actual chat/tool
   output remains essential to test pedagogy.


## 14. Human-friendly teaching presentation UAT

In a new session of stock OpenCode and again in a plain-text/limited host,
using the existing private course READ-ONLY until a separately approved
write is necessary:

1. Run /learnprint-method: verify plain-language summary first, full actual
   preferences and v1/v2 hashes available, no claim of tutor compliance.
2. Run /learnprint-syllabus: complete roadmap in order with prerequisites,
   hands-on and checks; unknown progress must not be invented.
3. Say "masih gak ngerti SQL, MySQL, DBeaver": expect ONE concise faithful
   comparison table or ASCII diagram, explanation in learner language and
   one small follow-up. No scored failure or written evidence.
4. Request /learnprint-progress: real counted observations separate from
   independent performance and retained mastery; no invented due dates.
5. Test a non-technical topic: useful role-play/writing visual, not a
   SQL-style diagram or forced code example.
6. Try host-native selection and numbered text fallback. Selection of a
   course alone must not create a receipt. Ask explicit write approval.
7. Check Unicode-limited Windows output; fall back to ASCII when needed.
   Plain-text content must not require ANSI colours, emojis, or plugins.
8. Check that an error/help message explains recovery without exposing a
   long unparsed CLI traceback as the main learner response.

This contract is prompt-level UX: static tests cannot prove a live model
will consistently follow it. Inspect actual host transcripts.
