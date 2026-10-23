# Rollback Procedure: feature/hardening-workspace

Scope: reverting the W6-W11 hardening work without touching any real
learner data. Read `docs/RELEASE-NOTES.md` for the inventory first.

## Rule zero

Real `Courses/` learner state is never reverted by these steps. The
baseline manifest of `Courses/` hashes lives outside the repository
(`%TEMP%\learnprint-baseline\courses-hash-20261022.json`). If anything
about `Courses/` looks changed, re-hash and compare before doing
anything else; report any mismatch to the owner, never "fix" state.

## Scenario A: nothing committed yet (current state)

All W6-W11 work is uncommitted in the work tree on
`feature/hardening-workspace` (HEAD d98cf93 at session start).

1. Inventory the touched paths (from `to-do.md` section C, plus git
   status): never `git checkout --` or `git clean` blindly.
2. To discard a single new file: delete it (they are all untracked):
   `scripts/learnprint_adapters.py`, `scripts/learnprint_sources.py`,
   `scripts/learnprint_eval.py`, `tests/test_tutor_adapters.py`,
   `tests/test_sources_provenance.py`, `tests/test_portfolio_labels.py`,
   `tests/test_eval_lab.py`, `schemas/tutor-turn.schema.json`,
   `docs/RELEASE-NOTES.md` (this file), `docs/ROLLBACK.md`,
   `protocols/JOURNEY.md`, `protocols/PRESENTATION.md`.
3. To restore a modified tracked file: `git diff -- <path>` first, then
   `git checkout -- <path>` per file only with owner approval. Known
   modified tracked files: `scripts/learnprint_tutor.py`,
   `scripts/learnprint_portfolio.py`, `docs/adr/0003-canonical-
   pedagogical-policy.md`, `tests/test_tutor_state.py`,
   `tests/test_skill_distribution_sync.py`, mirror copies of
   JOURNEY.md/PRESENTATION.md under `skills/` and `.agents/`.
4. After any rollback: `python -m pytest tests/ -q` must return to the
   pre-branch baseline (411 passed, 2 skipped) if W2-W5 work is kept, or
   the prior recorded number for whatever subset is being restored.

## Scenario B: after the release commit (post W0-05 approval)

1. `git revert` the release commit(s) individually; never `reset --hard`.
2. Ledger and course state files were not touched by design; verify with
   the hash manifest before and after.
3. Protocols mirrors are byte-copies; restoring the canonical files and
   running `tests/test_skill_distribution_sync.py` re-proves parity.

## Scenario C: bad portfolio export shipped

Exports are snapshots; the private canonical ledger is unaffected.
Delete the published snapshot only; fix the manifest labels in the
course directory; re-run `python scripts/learnprint_portfolio.py` export
with owner approval.

## Emergency contact

Owner approval for any destructive git op is mandatory (W0-05 packet).
If verification numbers above cannot be reproduced, stop and report;
do not improvise.
