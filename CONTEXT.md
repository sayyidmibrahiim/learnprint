# Learnprint

A portable, evidence-gated adaptive learning workspace for coding agents and learners.

## Language

**Course**:
An isolated, durable learning workspace dedicated to a specific topic identified by an immutable identifier.
_Avoid_: Class, subject, module

**Competency**:
A discrete, demonstrable unit of skill or knowledge within a course.
_Avoid_: Objective, goal, topic item

**Demonstration Cycle**:
The ordered sequence of demonstration tiers (Application, Transfer, and Delayed Retrieval) required to establish competency progression.
_Avoid_: Exam workflow, quiz loop, grading cycle

**Evidence Ledger**:
An append-only log of timestamped evaluation events and observations that serves as the single source of truth for learner progress.
_Avoid_: Progress cache, transaction log, audit history

**Retention Floor**:
A configurable minimum time interval required between initial demonstration and delayed retrieval before long-term retention can be credited.
_Avoid_: Cooldown period, test delay, waiting timer

**Learner Profile**:
A structured record of observed behavioral preferences, pacing, and constraints, explicitly rejecting fixed neurological styles.
_Avoid_: Learning style, personality type, diagnostic label

**Course Registry**:
The index tracking registered courses, their immutable identities, paths, and metadata.
_Avoid_: Catalog, course table, database index
