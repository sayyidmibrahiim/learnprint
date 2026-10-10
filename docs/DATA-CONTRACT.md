# Portable local data contract (version 1.0)

**Personal data is private by default.** Never copy local learning files to a public GitHub repository.

```text
my-learning/
  manifest.json                # versioned relative pointers
  learner/profile.json         # evidence-backed personal profile, initially unassessed
  topics/<topic-id>/state.json # explicit competency scope and current testable state
  topics/<topic-id>/map.mmd    # relation-labeled Mermaid concept graph
  topics/<topic-id>/SYLLABUS.md
  topics/<topic-id>/HANDOFF.md
  reviews.json                 # due dates derived from observed events
  events.jsonl                 # append-only observed answers + human/AI grading provenance
  HANDOFF.md                   # short cross-session checkpoint
  .agents/skills/learnprint-personal/SKILL.md # generated only after approved assessment
```

## Quick workflow

```sh
python scripts/learnprint.py init --workspace ./my-learning
python scripts/learnprint.py new-topic --workspace ./my-learning --topic in-on-at --goal "Speak naturally in meetings" --competency "place:Choose preposition for work location" --competency "time:Choose preposition for day and clock time" --competency "speech:Produce natural independent meeting update" --approve
python scripts/learnprint.py report --workspace ./my-learning
```

After a *real* learner response and independently reviewed scoring, `record` an event. Example syntax (replace all placeholders with actual observation; **never copy example answers into real learning logs**):

```sh
python scripts/learnprint.py record --workspace ./my-learning --event-id observation-001 --topic in-on-at --competency place --task-type independent_application --answer "ACTUAL_LEARNER_ANSWER" --expected "PREDECLARED_RUBRIC" --rubric '{"concept":2,"mechanism":null,"application":2,"transfer":null}' --feedback "REAL_GRADING_FEEDBACK" --grader human_reviewed --approve
python scripts/learnprint.py plan-reviews --workspace ./my-learning --dry-run
python scripts/learnprint.py plan-reviews --workspace ./my-learning --approve
```

Notes:
- Only independently observed **human-reviewed** events qualify for strict confirmed progress. AI-only grades are tracked but remain evidence-limited. A Python validator can't know whether someone fabricated a label or answer.
- `report` computes coverage against **declared, finite competencies** only; never entire subject mastery. Independent application **and** novel transfer must be observed for immediate demonstrated; delayed retrieval is required for maintained.
- Scheduling does not send notifications. The host can integrate a reminder tool if available and explicitly requested.
- `plan-reviews` operates solely on real logged successful tasks and computes due dates with a default 1/3/7/21-day progression; the teacher adjusts exercises and spacing when performance indicates it.
- The `profile.json` is not a clinical classification. Founder profile is temporary fallback when local profile remains `unassessed`.

## Courses/ workspace layout (new canonical tree, old my-learning/ still supported)

```text
Courses/
  .learnprint/
    registry.json          # course index: immutable UUID course_id, aliases, paths
    approval.json          # scoped standing-approval record (revocable)
    config.json            # tunable policy (retention floor, intervals)
    learner/profile.json   # personal profile (assessed/provisional/unassessed)
    events.jsonl           # append-only evidence for ALL courses (fail-closed)
    events.jsonl.bak.*     # immutable repair backups (never overwritten)
    recovery-log.jsonl     # auditable repair records with pre/post hashes
    reviews.json           # derived review queue (stale entries dropped on recompute)
    .lock                  # advisory lock (persistent, never deleted as recovery)
  INDEX.md                 # derived dashboard (badges: provisional/learner-confirmed/substantiated)
  <Category>/<Course>/     # README, SYLLABUS, MAP.mmd, HANDOFF.md, state.json
```

New evidence records carry UUIDv4 `event_id`, immutable `course_id`, and legacy `topic_id`. Competency states carry a `basis` label (provisional by default). Stored `due_at` values are a write-only cache: status always derives from fresh evidence.
