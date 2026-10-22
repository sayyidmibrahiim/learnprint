# 05 — Verify, review and ship course portfolios

Status: ready-for-agent
Blocked by: 04

## Task

Independent review of source, test matrix, Git safety, no-touch baseline of existing private Courses/ and real learner UAT. Reconcile ADR-0001/0002, privacy rules, CI, installer, packaging, tests and documentation. Only then submit a separate scoped PR; merge and remote publication require the user's separate authorization.

## Acceptance

- [ ] All automated tests and security gates green; cross-platform CI green.
- [ ] Real Courses/ hashes unchanged, no private data staged/tracked.
- [ ] No unapproved external publication.
- [ ] All known blockers resolved or documented explicitly.
- [ ] Reviewed diff and clean branch state with scoped commit(s).
- [ ] Evidence-backed release readiness statement, no zero-defect claim.

## Comments

- 2026-10-22 13:50 WIB — **W0-04B local Windows CI-command parity verified (not cross-OS CI)**. Executor GPT-6 scheduled relay, isolated fixture tests only; branch `feature/hardening-workspace`, HEAD `d98cf93ed980ff17d71e17f08ff5fb762d28c427` independently confirmed. Exact `.github/workflows/verify.yml` commands run on Windows Python 3.14.0: `python -m unittest discover -s tests` **exit 0, Ran 345 tests, OK (skipped=2), 166.237s**; `python scripts/learnprint.py validate --profile profiles/founder-default.json` **VALID**; `python scripts/learnprint.py validate --profile templates/learner-profile-starter.json --topic templates/topic-state.json` **VALID**; `python scripts/check_package.py` **PACKAGING OK**; `python scripts/learnprint_publish_guard.py --repo .` **OK, private_files_indexed=0, public_courses_checked=0**. Additional mirror test `python -m pytest tests/test_skill_distribution_sync.py -q`: **3 passed, 15 subtests**. Expected negative hook tests printed error messages to stderr while unittest overall passed; do not confuse with installation of real hook. Worktree before: 14 modified tracked + 27 untracked, staged 0. Another concurrent agent created issue 15 during this verification, so worktree is now 14 modified + 28 untracked; all existing changes preserved. **Linux/macOS, Python 3.9/3.12 matrix, actual hook upgrade, private original hash check, human UAT, independent security review, owner-approved Git integration still NOT VERIFIED.** No real learner data or remote operations.
- 2026-10-22 14:53 WIB — W0-04B additional Python 3.9 grammar gate added at `tests/test_python39_syntax.py`. Positive control, negative Python 3.10 `match` control, and every first-party script/test file: `python -m pytest tests/test_python39_syntax.py -q` **3 passed, 32 subtests**. New concurrent W2 tutor tests initially had two fixture failures; an independent agent edited that file, so this relay did not overwrite it. Later `python -m pytest tests/test_tutor_state.py -q` **35 passed, 59 subtests**. Full one-process `python -m pytest tests/ -q` **384 passed, 2 skipped, 190 subtests** in 150.99s, Windows Python 3.14. `python scripts/check_package.py` PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` OK with 0 indexed private files; mirror tests **5 passed, 32 subtests**. Working tree 17 modified + 34 untracked individual files, staged 0. **Python 3.9 grammar parsing is not actual Python 3.9 execution or cross-OS CI.** Other human, privacy, security and authorized integration gates remain open. No original Courses/ writes, real hooks or remote actions.
- Later in the same run, a separate agent introduced `scripts/learnprint_scheduler.py` and `tests/test_scheduler.py` (W4), **after** the 384-pass full run. New focused W4 tests are not yet green: latest `python -m pytest tests/test_scheduler.py -q` **1 failed, 13 passed, 6 subtests** (canonical due-date parity assertion). Do not treat the earlier 384-pass suite as verification of the latest tree. The syntax gate rerun against the new files passed **3 tests, 34 subtests**. Worktree 17 modified + 36 untracked, 0 staged. W4 owner must reconcile before the next full suite; no edits made to its source/tests.
