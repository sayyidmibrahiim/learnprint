# Learner journey: plan -> diagnose -> teach -> practice -> test -> review

**Required tutor output:** also follow [language and stages](../skills/learnprint/references/TUTOR-LANGUAGE-AND-STAGES.md). Explicitly distinguish diagnostic **SCREENING AWAL** (at most 3 short prompts; may end early) from **BELAJAR**, **TES MANDIRI**, **TES TRANSFER**, and **REVIEW TERTUNDA**. Use idiomatic selected language, target-language exercises in clear full sentences and an ASCII unit-position roadmap without invented mastery percentages. Host/model adherence requires live human UAT, not just unit tests.


Learnprint must show the learner a roadmap BEFORE asking diagnostic questions.

1. Load effective method from 'learner method' and show source plus short fingerprint.
2. Run 'course plan --course-id UUID'. Show syllabus units in prerequisite order,
   plain-language objectives, hands-on activities, completion checks, and current
   evidence status (or 'belum dinilai'). If a legacy SYLLABUS.md is present,
   show it as a draft, do not overwrite it without explicit agreement.
3. Ask what learner knows and wants. Topic baseline 0-3 short questions, one at a
   time, is separate from optional personal learning-method assessment.
4. Teach a prerequisite, not a big complex test, when the learner is confused.
   Use stable analogy mappings with explicit limitations, then literal
   inputs/process/outputs and a worked example.
5. Hands-on (safe simulated data, local execution, conversation role play,
   physical or written exercises). Show concrete input, action, observable
   result, verification, and cleanup. Never claim a command ran if it did not.
6. Ask graded independent application and novel transfer only after instruction,
   with a prewritten rubric. Record actual responses and help level as evidence.
   'Masih bingung', 'unknown' and questions are NOT graded incorrect answers.
7. Use canonical evaluator; progress is provisional when AI-reviewed. A topic is
   demonstrated only after application + separate transfer, maintained only
   after successful delayed retrieval. Syllabus reading is not mastery.
8. End with covered module, real evidence, unanswered questions, next action,
   review due, and method fingerprint.

## New prerequisite while learning

First inspect the current syllabus, ask whether the question belongs in an
existing unit. If missing, propose a unit name, prerequisites, outcome,
linked competency, and hands-on success task. Show before/after ordering and
get learner approval. Use 'course plan-set --course-id UUID --from-file FILE
--approve' to apply safely. The CLI refuses cyclic or missing dependencies,
unknown competencies, duplicate IDs, deletion of existing unit IDs, missing
hands-on or changed existing competency linkage. It backs up previous state.

## Structured syllabus JSON example (illustrative only)

[
  {
    "unit_id": "database-prerequisites",
    "title": "SQL language, engine and client",
    "outcome": "Distinguish SQL, MySQL, SQLite and DBeaver",
    "competency_ids": ["database-taxonomy"],
    "requires": [],
    "hands_on": "Use local Python sqlite3 in-memory and run SELECT 1",
    "success_check": "Show actual query result and explain which software executes SQL",
    "practice_mode": "hands_on"
  }
]

Prerequisite order is computed deterministically by the engine. Candidate
files stay private; do not commit them. A structured plan lives in state.json;
old SYLLABUS.md is retained as a legacy readable document until approved adoption.

## Research basis and limitations

Practice testing and spaced/distributed practice:
https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html

CAST UDL 3.0 (prior knowledge, learner agency, multiple representations,
graduated support, meaningful real-world performance):
https://udlguidelines.cast.org/

EEF review emphasizes positive but context-dependent evidence and limitations:
https://educationendowmentfoundation.org.uk/education-evidence/evidence-reviews/cognitive-science-approaches-in-the-classroom/

These are educational-design principles, not proof of a uniquely optimal
learning style or identical performance across LLM providers.

## What have I covered versus what can I demonstrate?

After actually covering or practicing a module, the tutor can record a
non-graded note within the existing scoped workspace approval:

    python scripts/learnprint.py course lesson-log --course-id UUID --unit-id UNIT_ID --kind covered --note "Actually discussed SQL vs database engine" --approve

Kinds: covered, practice, question, clarification. The private per-course
learning-log.jsonl is separate from the canonical assessment evidence ledger.
Read 'course plan --course-id UUID' to see coverage, last discussion date and
recent questions; evidence_status remains not_assessed without real answers.
An agent-reported coverage note is not proof of knowledge or skill mastery.

## Audit the actual method instead of taking the tutor's word

Run `learner method` to get the complete active method/preferences and
v2 effective fingerprint. During authorized sessions the first-party CLI
can record a method receipt and link notes/graded answers to its UUID.
`course method-audit` checks linked artifacts and flags configuration
drift, but explicitly marks human-dependent compliance as NOT_VERIFIED.
Read [Method Audit](METHOD-AUDIT.md). Agent-written explanations and
self-reported notes cannot independently prove the tutor followed the
method or that a real hands-on action was performed.
