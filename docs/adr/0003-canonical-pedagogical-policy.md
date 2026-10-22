# ADR-0003: Canonical pedagogical policy and enforced mirror parity

**Date:** 2026-10-22
**Status:** Accepted
**Scope:** W1-01/W1-02 of the Learn Print Deep Research and Mega Enhancement Plan.

## Context

Learnprint is portable across agent hosts. The teaching, assessment, and
review policies historically existed in three locations:

- `protocols/TEACHING.md`, `protocols/ASSESSMENT.md`, `protocols/REVIEW.md`
- `skills/<skill>/references/*.md` (discoverable copy for native OpenCode skills)
- `.agents/skills/<skill>/references/*.md` (agent mirror)
- `distribution/claude-plugin/skills/<skill>/references/*.md` (Claude plugin)

The copies drifted independently (observed 2026-10-22): `skills/.../TEACHING.md`
had gained the learner-facing communication contract, the mandatory journey
contract, the Courses-CLI portability update, and the historical wrong-score
repair rule, while `protocols/TEACHING.md` kept only the older body. Any host
loading the stale copy silently taught conflicting rules. There was also no
machine-readable statement of the guard invariants (T01-T08) that tutor
adapters must honor, so behavioral tests had no stable anchor to assert.

## Decision

1. **Single authoritative source:** `protocols/TEACHING.md`,
   `protocols/ASSESSMENT.md`, `protocols/REVIEW.md` are the one canonical
   policy set. All other locations are byte-identical mirrors.
2. **Enforced parity:** `tests/test_skill_distribution_sync.py` asserts
   protocols-to-mirror byte identity for every mapped source and mirror,
   in addition to the existing `skills` to `.agents` and
   `skills` to `distribution` coverage. A mirror may never diverge silently;
   a legitimate divergence requires an ADR with a justified mapping entry.
3. **Normative guards T01-T08:** the canonical `protocols/TEACHING.md` anchors
   the eight invariants (attempt gate, confusion gate, help contamination,
   fresh task, transfer, delayed floor, source, evidence). Tests assert these
   anchors exist and stay worded so the roadmap's behavioral contracts remain
   visible. The deterministic tutor engine (W2/W3) enforces them in code; the
   anchors give prompt-level and audit-level tests a stable reference.
   The same canonical-and-mirror policy also covers `protocols/JOURNEY.md`
   and `protocols/PRESENTATION.md` (mirrored to `skills/learnprint/` and its
   `.agents` copy; the Claude plugin distribution intentionally ships only
   the learn/assess skill bundles).
4. **Intentional non-mirrors:** `SKILL.md` dispatchers and
   `references/founder-default.json` are host-specific or data artifacts and
   are excluded from this parity rule; they remain covered by the existing
   distribution sync test where applicable.

## Consequences

- Editing policy means editing `protocols/` first, then running the mirror
  script/sync test; a stale copy fails tests before release.
- The enriched TEACHING content (journey contract, presentation rule,
  correction-repair rule) becomes universal, so hosts that previously loaded
  `protocols/TEACHING.md` gain the newer rules rather than losing them.
- The deterministic tutor FSM and evaluator (W2/W3) remain the code-level
  authority; T01-T08 prose can inform behavior but cannot change status.
- Hosts loading either copy now see the same policy, removing the observed
  2026-10-22 divergence.

## References

- `Learn Print Deep Research and Mega Enhancement Plan.md` W1/W2
- ADR-0002 (selective course portfolio publication)
- `rules/EVIDENCE.md` (canonical evaluator)
