---
description: Audit learning-method configuration and session artifacts conservatively
---

Read project-local skill learnprint and references/JOURNEY.md.
Action: audit. User arguments: $ARGUMENTS
Find the learner-selected/active course ID using course overview.
Run python scripts/learnprint.py course method-audit --course-id UUID.
For the currently active learning session prefer its session ID:
  --session-id UUID
If the learner explicitly supplies a local OpenCode/host transcript path,
add --transcript-file PATH. It is read-only, only a SHA is returned; raw
transcript is NOT authenticated or automatically scored for compliance.
Show every PASS, FAIL, NOT_VERIFIED check with its real evidence and limits.
No fabricated checks, no self-certified success, no mutation of Courses/.
If there is no session receipt, say so; the first-party CLI can create one
with course session-start --course-id UUID --approve during the NEXT
authorized lesson, then attach --session-id to lesson-log and record actions.
