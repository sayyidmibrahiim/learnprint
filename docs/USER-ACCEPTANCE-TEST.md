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
