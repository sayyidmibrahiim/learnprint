# Learnprint workspace lifecycle (single-root operation)

The workspace lives at `Courses/` relative to the repo root. All commands run
from the repo root; never `cd` into subdirectories.

## Lifecycle
1. First run: agent explains the bounded scope (create courses, record
   evidence, update progress — inside `Courses/` only), user approves in chat,
   agent runs `python scripts/learnprint.py course init --approve`.
2. Learning: `course resolve` → `course create` (if needed) → teach →
   record evidence → update state.
3. Resume: `course resume` returns the active or most-recent course.
4. Dashboard: `course dashboard` regenerates `Courses/INDEX.md` (derived).

## Standing approval scope
Covered without re-prompting: workspace/course creation, event appends,
registry/reviews/state/HANDOFF/INDEX updates, profile copy. Never covered:
publishing, global skill installs, evidence deletion, writes outside
`Courses/`, destructive git, network access. Host permissions win over the
workspace grant. Revoke with `course revoke-approval`; deleting
`Courses/.learnprint/approval.json` equals revocation.

## Layout
`Courses/.learnprint/` holds registry.json, approval.json, config.json,
learner/profile.json, events.jsonl, reviews.json, recovery-log.jsonl, .lock.
`Courses/<Category>/<Course>/` holds README.md, SYLLABUS.md, MAP.mmd,
HANDOFF.md, state.json. `Courses/INDEX.md` is derived, never source of truth.

## Tiers without filesystem (Tier 0)
If the host denies writes: teach in chat, output a portable LEARNING_STATE
block, never claim a file write happened.

## Personal method, command navigation and evidence

Read-only status: learner status, course overview. Neither initializes a
fresh workspace. After chat consent, initialize exactly once, then offer
method assessment or the temporary founder default. Saving "deferred"
means do not ask automatically on every session. Assessed profiles
remain assessed across hosts sharing private files.

- learner use-default --approve: persist temporary default, NOT assessed.
- learner assessment-start --approve: start personal assessment.
- learner assessment-start --reassess --approve: explicitly recalibrate.
- learner assessment-complete --approve: validate private
  learner/profile-candidate.json and advance fingerprint/revision.
- course overview: inspect all courses and real progress from the ledger.
- course scope-set --course-id ID --from-file FILE --approve: safely
  replace a validated competency scope, never remove referenced IDs.

The fingerprint hashes the protocol and instructional settings, not the
learner identity or proof of optimal learning. Never silently repair
personal data, reset stored evidence, or use old agent memories as truth.
