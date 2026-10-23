# 04 — Demonstrable proof, hands-on portfolio and human UAT

Status: ready-for-human
Blocked by: 03

## Task

Build concise, learner-friendly examples of real evidence, project outputs and reproducible verification; add portable first-run publishing/privacy guidance and accessibility-friendly display. Run disposable-host UAT and human-judged learner exercise to check pedagogical integrity. Distinguish any future 1EdTech Open Badge credential from self-generated portfolio evidence.

## Acceptance

- [ ] Runnable sample course projects with real tested commands and outcomes.
- [ ] Accurate rubrics, verification steps and reviewer/source provenance.
- [ ] User can choose publishable vs private course without confusing prompts.
- [ ] No private transcript/answer/secret leaks in public preview.
- [ ] Human UAT outcomes recorded honestly (NOT_VERIFIED when absent).
- [ ] README and docs reflect publication workflow and limitations.

## Comments
- 2026-10-23, release verification relay: Engineering parts implemented: honest achievement labels (`human_reviewed`, `ai_reviewed`, `self_reported`) and hands-on artifact selection in `scripts/learnprint_portfolio.py`, covered by `tests/test_portfolio_labels.py`. Human UAT remains OPEN: no real learner portfolio session with an independent reviewer happened, so this ticket stays ready-for-human. Do not relabel it resolved from automated tests alone. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
