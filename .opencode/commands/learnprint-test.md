---
description: Run the portable Learnprint learning workflow
---

Use the project-local Learnprint skill (load "learnprint", or read skills/learnprint/SKILL.md if native discovery is unavailable).
Action: test
User arguments: $ARGUMENTS

Follow the matching action in the skill, including read-only status checks,
scoped consent, evidence-based progress, and the user's language. Never
depend on global AgentMemory/JEV/Graphify or assume a file write succeeded.
