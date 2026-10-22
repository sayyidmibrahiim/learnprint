# Release Notes: Hardening Workspace (feature/hardening-workspace)

Status: release candidate, uncommitted work tree (see to-do.md handoff card).
Date: 2026-10-22. Python 3.9+ standard library only, no new dependencies.

## What is in this release

Roadmap phases W6-W11 of the mega enhancement plan, verified against
`tests/` (481 passed, 2 skipped; see Verification below).

- W6 tutor turn contract: `scripts/learnprint_adapters.py` renders a
  provider-neutral, deterministic turn contract (generic / markdown /
  low_context presets) and parses model output strictly. Parsing fails
  closed on: two JSON objects, unknown kinds, embedded score fields (T08),
  answer-key leaks in task prompts (T01), hints that leak the solution or
  lack assistance attribution (T03), help beyond the contracted level,
  clarify turns disclosing the answer (T02), delayed reminders without an
  external reference (T06), and fabricated source statuses (T07).
  Schema contract: `schemas/tutor-turn.schema.json` (kept in sync by test).
- W7 source provenance: `scripts/learnprint_sources.py` validates a local
  source registry (verified status requires url + retrieved_at), fails
  closed on fabricated citations, rejects claims citing retracted or
  superseded sources, downgrades external claims without verified sources
  to UNVERIFIED (never presented as facts), and flags instruction-injection
  attempts in learner content (content stays data).
- W8 portfolio evidence labels: achievements in the public portfolio must
  be honest: `human_reviewed` requires a named reviewer, `ai_reviewed`
  requires a deterministic evaluation reference, `self_reported` carries
  neither. EVIDENCE.md lines carry the labels; hosting claims no
  certification; publication stays private by default.
- W9 learner presentation: `next_action(doc)` in
  `scripts/learnprint_tutor.py` gives exactly one learner-visible action
  per phase, never claiming scores or mastery.
- W10 evaluation lab: `scripts/learnprint_eval.py` replays scripted
  learner journeys through the deterministic FSM and reports
  false_mastery_leaks (must be 0), confusion_pauses, and scored-field
  guarantees. Every output is labeled `simulated: true`,
  `human_participants: 0`; real outcomes come only from real sessions.
  Invalid scripts fail closed via the engine (blocked_at_behavior).
- W11 release engineering: this file, the rollback procedure, the full
  regression run, packaging gate, and the owner approval packet (W0-05).
- W1 completion: `protocols/JOURNEY.md` and `protocols/PRESENTATION.md`
  joined the canonical pedagogical set (ADR-0003) with byte-identical
  mirrors in `skills/learnprint/references/` and `.agents/skills/`.

## Verification evidence

- `python -m pytest tests/ -q`: 481 passed, 2 skipped (baseline before
  this branch was 411 passed, 2 skipped).
- `python scripts/check_package.py`: PACKAGING OK (SKILL.md frontmatter
  and size limits).
- Syntax gate `tests/test_python39_syntax.py` green (3.9-only constructs).
- CLI smoke: `learnprint_adapters.py|learnprint_sources.py|
  learnprint_eval.py --help` all exit 0.
- New test files: `tests/test_tutor_adapters.py` (25),
  `tests/test_sources_provenance.py` (18), `tests/test_portfolio_labels.py`
  (7), `tests/test_eval_lab.py` (8), plus W9 presenter tests (3) and the
  extended distribution-parity test (5).

## Not verified here (remaining gates)

- Cross-OS CI (Windows-only runs), real Python 3.9 runtime (dev runs
  3.14; syntax gate covers 3.9 constructs statically), installed-hook
  upgrade consent, and human UAT stay documented as open gates in
  `to-do.md` (W0 acceptance cards).
- W0-05 staging/commit waits for owner approval: exact path list,
  privacy evidence and rollback notes are in the to-do.md handoff card.
