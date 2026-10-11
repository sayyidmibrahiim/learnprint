# Effective learning method and tutor audit

## What is actually configured?

From the repository root, run these READ-ONLY commands:

    python scripts/learnprint.py learner status
    python scripts/learnprint.py learner method

Or use /learnprint-method in OpenCode.

The method output includes:
- source: founder_default or personal_assessment
- assessment_status and method_revision
- instruction_defaults (mechanism, pacing, assessment and retrieval defaults)
- preferences (language, analogies, diagrams, feedback)
- fingerprint: LEGACY SHA-256 (instruction_defaults only), preserved for
  existing learner profiles and integrations
- effective_fingerprint: v2 SHA-256 (instruction_defaults + preferences)
- protocol and verification disclaimer

Neither fingerprint identifies a person or attests that the AI followed
the method. A personal method requires actual assessment evidence. If the
user has chosen founder_default and remains unassessed, say exactly that.

## Session-linked receipts and evidence

After the learner's standing scoped consent, before teaching a unit:

    python scripts/learnprint.py course session-start --course-id UUID --approve

This creates a new UUID method session receipt under the private course's
method-sessions.jsonl. It records source, revision and both hashes (no
full private profile). It records which CONFIGURATION was resolved; not
whether the host applied it.

When the agent actually covers material, asks/answers a question, or
conducts practice (not before), it may record a private lesson note:

    python scripts/learnprint.py course lesson-log --course-id UUID --unit-id UNIT --kind practice --note "Observed learner activity" --session-id SESSION_UUID --approve

When the learner actually submits a scored answer, the existing record
CLI accepts optional --session-id SESSION_UUID alongside --course-id UUID.
It validates that the session is registered for that course and preserves
the normal evidence-grade gates. No response should be fabricated solely
to satisfy the audit.

The prior unlinked course activities and events remain readable for
normal progress. Auditing an old session without session receipts should
show NOT_VERIFIED, never retroactively synthesize a session ID.

## Read-only audit

    python scripts/learnprint.py course method-audit --course-id UUID

Or: /learnprint-audit. For a specific session:

    python scripts/learnprint.py course method-audit --course-id UUID --session-id SESSION_UUID

To attach a learner-supplied exported host transcript, include
--transcript-file PATH. The command reads it only for size/hash; the raw
text is NOT written to a separate database or published. A transcript
is not authenticated by Learnprint and does not automatically satisfy
compliance. The user can provide it to an independent reviewer.

Statuses:
- PASS: precise objective artifact exists or hashes match (e.g. correct
  method receipt, actual linked ledger event). It does NOT certify teaching.
- FAIL: concrete detected contradiction such as method hash/revision drift.
- NOT_VERIFIED: behavioral quality, showing roadmap to learner, honest
  handling of confusion, accurate analogy, fairness of the assessment,
  actual hands-on execution, or absence of sufficient evidence.

Overall result intentionally remains NOT_VERIFIED unless a concrete FAIL
is detected. There is no complete machine-verifiable PASS of teaching
adherence from tutor-authored notes or a user-supplied editable transcript.
The human can compare the actual exchanged messages with the method and
JOURNEY.md. Do not describe the audit as objective verification of
every method rule.

## Fresh default host acceptance

1. Use an isolated temporary Courses root. /learnprint-method on an
   unassessed user must display founder preferences and v2 fingerprint.
2. On a legitimately assessed private profile, personalized preferences
   replace founder preferences and produce their own v2 fingerprint.
3. Begin approved session; validate receipt; collect truthful lesson
   activity and real answer. Audit returns PASS for the relevant artifacts
   while pedagogical adherence remains NOT_VERIFIED.
4. If method preferences change after the receipt, the audit detects
   configuration mismatch; no automatic profile rollback.
5. No receipt, no linked evidence, or missing transcript must not be
   treated as a failure of learning—only unverified audit facts.
6. Repeat using default OpenCode with no global agents, memory, MCP, or
   graph tools. Natural-language hosts can run the same Python CLI through
   their ordinary file/shell tools.

See skills/learnprint/references/JOURNEY.md for the teaching protocol.
