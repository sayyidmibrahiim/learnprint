# Learnprint release-candidate notes: merged into `main`

### Merged to main (2026-10-23)

- PR #9 merged into `main` as merge commit `1b9b7855fd9a45101ce7753ed44850657f1b8383`; post-merge push run `39908358179` reports 15/15 jobs success.
- Supply chain: `actions/checkout` and `actions/setup-python` are pinned to immutable v7 commit SHAs, weekly `github-actions` dependency updates are enabled, and `SECURITY.md` documents private reporting, supported runtimes and the fail-closed hook policy.
- No release tag was created. Human UAT, learner efficacy and independent security review are still open, so a `v1.0.0` tag would overclaim.

### Release-candidate verification, all 15 CI jobs green (2026-10-23)

- Head commit `cecda70cd0a4e14bfbb08fb3da0ebe891e3924a1` on `feature/hardening-workspace`; PR #9 targets `main`.
- GitHub Actions run `39890427415` (push) and run `39890434260` (pull_request): **15 of 15 jobs success**, covering ubuntu-latest, windows-latest and macos-latest for CPython 3.11, 3.12, 3.13, 3.14 and 3.15.
- Local Windows evidence on the same head: `python -m unittest discover -s tests` exit 0, **519 tests, OK (3 skipped)**; `python -m pytest tests/ -q` exit 0, **516 passed, 3 skipped, 385 subtests passed**.
- Static and privacy gates: `python scripts/check_package.py` exit 0 PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` exit 0 with zero indexed paths; `profiles/founder-default.json` and `templates/learner-profile-starter.json` both VALID; `learnprint.py --help` exit 0.
- Still open and honestly not PASS: real multilingual tutor UAT on a live host, independent human learning efficacy, independent adversarial filesystem security review. See `docs/research/2026-10-23-production-release-gates.md`.

### PR #9 cross-platform failure remediation (2026-10-23)

First remote CI run 39843827147: Ubuntu matrix passed, Windows/macOS failures observed. Root causes: macOS legitimate /var alias wrongly rejected, Windows junction fixture lexical-vs-resolved path mismatch, Windows hook link-swap identity false negative. Changed portfolio chain canonicalization for only the exact OS alias, fixed junction test parent-only canonicalization, and hardened Windows hook identity via kernel32. Local rerun `python -m pytest tests/ -q`: 516 passed, 3 skipped, 385 subtests, exit0; focused 47 passed, 3 skipped. This update requires fresh remote CI before release; do not treat initial CI as green.

### CI follow-up remediation, 2026-10-23

CI follow-up run `39888014467` reproduced Windows 3.11 hardlink-swap failure even after file-index/link-count hardening. Additional guard now binds hook identity to the Win32 creation FILETIME as well as volume/file index; on POSIX uses st_ctime_ns in identity. This prevents same-file-index reuse from being treated as the original file. Focused local `python -m pytest tests/test_course_portfolio.py tests/test_publish_hook_install.py -q`: 41 passed, 2 skipped, 20 subtests. **Remote cross-platform test must rerun after this patch; not yet verified.**

### CI cross-platform follow-up: fixture alias and pinned hook (2026-10-23)

Follow-up CI run `39888572396` demonstrated two distinct regressions: macOS synthetic reparse/link/path-swap fixtures compared the OS `/var` alias against normalized `/private/var` and missed the intended fixture path; Windows linked legacy hook upgrade still passed a rename/hardlink swap under runner conditions. The macOS test fixture now compares the same narrowly trusted system alias on both sides (without normalizing arbitrary links). The hook installer now pins an open descriptor for the original legacy hook during content read, validates identity/link count while the original inode is still pinned, and refuses if a concurrent Windows unlink is denied. The race test treats *either* denied unlink or detected hardlink swap as safe rejection; no external target may be overwritten. Focused Windows test `python -m pytest tests/test_publish_hook_install.py tests/test_course_portfolio.py -q` exit 0, 41 passed, 2 skipped, 20 subtests. This is a candidate fix: remote macOS/Windows CI still must actually pass.

### Security decision: remove automatic hook upgrade (2026-10-23)

The cross-platform CI matrix repeatedly demonstrated that automatic replacement of *existing* legacy `.git/hooks/pre-commit` can pass a link-swap test on Windows and macOS. Neither rechecking `stat` nor probing Win32 FILETIME/identity nor pinning a read descriptor proved stable across runners. **Accepted fail-closed resolution:** the installer now uses exclusive `open("x")` **only when no hook exists**, and refuses every pre-existing hook, including a valid legacy Learnprint hook. It does not mutate that hook or any external hardlink target. An owner can inspect and archive the old hook manually, then install a new one into a proven-empty path; this is a separately reviewed operation and not an implicit agent upgrade. The unreachable legacy-replacement code was removed, and regression `test_existing_legacy_hook_is_preserved_even_with_approval` added. Focused suite: 41 passed, 2 skipped (20 subtests). Real CI rerun still required; do NOT mark release DONE until all 15 GitHub jobs pass.

### macOS mock recursion regression (2026-10-23)

PR #9 CI run 39889996180: Windows Python 3.15 already passed after disabling unsafe existing-hook upgrade; macOS Python 3.13 exposed test-only infinite recursion because synthetic Path.lstat mock called `_trusted_system_alias`, which internally calls `Path.is_symlink`/lstat. New fixture `_fixture_path_key` uses strictly lexical `/var` to `/private/var` mapping under macOS; it never calls lstat/is_symlink, preventing recursive mocks while matching OS alias paths. Windows focused `python -m pytest tests/test_course_portfolio.py tests/test_publish_hook_install.py -q`: 41 passed, 2 skipped, 20 subtests. Cross-platform CI must run again on this commit.

### Historical pre-merge local verification (superseded by green CI and merge evidence above)

- `python -m pytest tests/ -q`: exit 0, **516 passed, 3 skipped, 385 subtests**, Windows, ~288.37 seconds.
- `python -m unittest discover -s tests`: exit 0, **519 tests, OK (3 skipped)**, ~236.3 seconds; this is the exact test runner invoked by GitHub Actions.
- `python scripts/check_package.py`: exit 0, PACKAGING OK.
- `python scripts/learnprint_publish_guard.py --repo .`: exit 0, OK, **zero private indexed paths** after exact-scope staging of **49 reviewed public files**, no `Courses/` paths in staged inventory.
- `python scripts/learnprint.py course validate`: exit 0, VALID for the three private courses. No private learner record staged, no auto-export.
- Remaining: real GitHub Actions jobs not observed, live OpenCode/language human UAT not observed, independent adversarial filesystem security review not done, real learner efficacy not proven. Do not call these PASS.
- Research: Python 3.15.1 released October 21, 2026 and support matrix 3.11–3.15; updated official Action majors to v7. See `docs/research/2026-10-23-production-release-gates.md`.
- Git: 49 public tracked/new paths were staged explicitly and reviewed; that local entry predates the published commits and is superseded by the green CI evidence above (`cecda70`).


## Latest execution evidence (2026-10-23, new remediation)

- Official current Python release check: Python 3.15.1 dated 2026-10-21, Python 3.9 EOL since 2025 and 3.10 EOL since 2026-10-01. CI source uses actions/checkout@v7 and setup-python@v7 with CPython 3.11–3.15 across ubuntu/windows/macos. **Superseded:** all 15 jobs passed on `cecda70` in runs `39890427415` and `39890434260`.
- Enforced evidence/FSM binding: if the course has a private tutor-session file, `record` with independent application, transfer or delayed review must match actual persisted phase, `task_id` and help-level. Backward compatibility for courses without FSM retained. Added two focused regression tests, including refusing false unassisted assessment of a hinted task.
- Hardened derived docs update against linked files and changed content, bounded pre-image reads and directory chain identity; CRLF known-stub backward compatibility and real-byte preview digest preserved. Added CRLF, hardlink and changed-file tests; one Windows symlink test remains skipped due privilege.
- **Latest Windows local full verification:** `python -m pytest tests/ -q` exit 0, **516 passed, 3 skipped, 385 subtests**, 288.37 s. This is the latest complete run superseding previous 511/3.
- Fresh instructions: `docs/PRODUCTION-WALKTHROUGH.md` and `docs/research/2026-10-23-production-release-gates.md`. Independent learner UAT and remote cross-OS CI remain explicitly NOT VERIFIED.
- Git stage, commit, push, merge and release tag are only DONE when their actual results are observed. Private learner course data remains excluded.

## Current local verification addendum (2026-10-23)

**Git status:** the hardening work is committed on `feature/hardening-workspace` and published to GitHub as PR #9, which is not merged yet. All Oct-22 numbers below are historical baselines. Current verified local Windows results on `cecda70`: `python -m pytest tests/ -q` **516 passed, 3 skipped, 385 subtests passed** (exit 0) and `python -m unittest discover -s tests` **519 tests, OK (3 skipped)**. Remote CI on the same head: 15 of 15 jobs success.

New capabilities now committed on this branch:
- Canonical subject-agnostic multilingual tutor writing/stage policy (`protocols/TUTOR-LANGUAGE-AND-STAGES.md`), byte-checked OpenCode/Claude mirrors and manual UAT across SQL/math/history/music/Japanese/DNS/large curricula; no surprise code-mixed scored sentences.
- Per-course `journey-card` returns honest screening/lesson/application/transfer/delayed labels and unit-position ASCII. Added consent-gated `course tutor-init/tutor-status/tutor-transit` backed by the existing deterministic tutor FSM and automatically consumed by `journey-card` when present; phase transitions do not manufacture learning evidence. Optional persisted FSM is checked against the same course; agent-reported stage is explicitly labeled not-verified.
- Portable `record --from-file PRIVATE.json` handles rubric JSON as an object, avoiding PowerShell argv stripping, and retains normal approval and ledger guards.
- `portfolio-options` shows **every course selectable** for individually curated public proof-of-work. NOTHING is automatically exported, indexed, committed or pushed. Actual publication remains a separately reviewed private-data consent decision.
- `docs-preview`/`docs-sync` create checksum-sealed derived syllabus, Mermaid and handoff artifacts from actual canonical plan, protect manual edits, and require exact preview digest and approval. Existing SQL manual syllabus/map/handoff were preserved.
- Three private learner courses validated, SQL/DNS structured plans adopted without changing their UUIDs, English/DNS stubs safely refreshed; no fabricated achievement or permanent mastery claims.

Local smoke exit 0: `python scripts/check_package.py` (PACKAGING OK), `python scripts/learnprint_publish_guard.py --repo .` (0 private indexed), `python scripts/learnprint.py course validate` (VALID); all 3 actual courses listed as selective portfolio options, no exports.

**Limitations not hidden:** 3 test skips (including a Windows symlink permission scenario); real low-cost-model/other-host learning-language UAT, independent human learning efficacy and independent adversarial filesystem security review are not proven. That paragraph predates the published branch; commit, push and cross-platform CI have since completed on `cecda70` (runs `39890427415`, `39890434260`), merge into `main` has not.

---



Historical state before integration: release candidate on `feature/hardening-workspace` at `cecda70`, with 15 green CI jobs. **Superseded:** PR #9 merged to `main`, and final `main` commit `e8340e8` passed 15/15 jobs.
Date: 2026-10-22, verification refreshed 2026-10-23. Python 3.11-3.15 standard library only, no new dependencies.

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

- Cross-OS CI is now green on `cecda70` (15/15 jobs, runs `39890427415` and `39890434260`). Real multilingual tutor UAT on a live host, independent human learning efficacy, and independent adversarial filesystem review remain open gates documented in `to-do.md`.
- W0-05 staging/commit completed; exact path lists, privacy evidence and rollback notes stay in the `to-do.md` handoff records. Merge into `main` is still a separate decision.
