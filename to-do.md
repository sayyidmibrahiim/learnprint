# to-do.md — Learnprint Cross-Agent Execution Tracker

**TRACKER SCHEMA:** v1  
**Last updated:** 2026-10-23 (Asia/Jakarta); current handoff appears below, older logs retained  
**Canonical plan:** [Learn Print Deep Research and Mega Enhancement Plan.md](Learn%20Print%20Deep%20Research%20and%20Mega%20Enhancement%20Plan.md)  
**Coding constraints:** [Code Style.md](Code%20Style.md)  
**Repository rules:** [AGENTS.md](AGENTS.md) and [CONTEXT.md](CONTEXT.md)  
**Status vocabulary:** NOT_STARTED | IN_PROGRESS | BLOCKED | READY_FOR_REVIEW | VERIFIED | DONE | DEFERRED | CANCELLED. Never write DONE without cited evidence.

> **Meaning of this file:** Shared state for *all* agents, models and harnesses. This is the durable truth about engineering progress, known dirt, decisions and handoff. Project-local files outrank forgotten chat context. Never treat an old model's “done” statement as test evidence. Existing uncommitted changes are protected work, not garbage.

## A. Takeover protocol (mandatory at the beginning of EVERY session)

1. Open the exact Learnprint repository and read AGENTS.md, this tracker, [the research plan](Learn%20Print%20Deep%20Research%20and%20Mega%20Enhancement%20Plan.md), [Code Style.md](Code%20Style.md), CONTEXT.md, docs/agents/issue-tracker.md, and the applicable rules/ and ADRs. Treat private learner materials as out-of-scope unless a specifically authorized task requires them.
2. Read CURRENT branch/HEAD, working tree status (tracked/untracked/ignored as needed), staged paths, diff summary, and detect in-flight parallel edits. Reconcile **all changed paths** with section C below, including files outside the listed W0 baseline. Do not assume a clean tree because another agent wrote it was clean.
3. Identify the topmost unblocked task with a clear acceptance gate. Check task claim and scope; do not edit another agent's active files without coordination. If workstream has local tickets under .scratch/, honor their own Status/Comments convention.
4. Before editing, add/update the task's **claim note** in section F or associated issue file: agent/harness, task ID, planned paths, timestamp and HEAD. If multiple agents cannot coordinate via lock, do not use a blind overwrite.
5. Only make approved scoped modifications. Do not mutate real Courses/, publish, install hooks, stage, commit, push or delete files merely because “cleanup” appears in the roadmap. Such actions have their own consent boundary.
6. After each bounded task: run relevant tests, inspect actual diff and exact new Git status, update relevant task and touched-path inventory (sections B/C), log command outcomes (section E), and record blockers and next safe command.
7. Before handing off: complete section G with current phase, task, artifact paths, tests, blocked reasons and **exact next action**; ensure the tracker is saved with the implementation change. If tool cannot do Git operation, leave it explicitly BLOCKED with review-ready path list rather than inventing a commit.

**Critical rule:** This tracker is NOT the program's canonical evidence ledger. Do not add fictitious learning results or change private learner state here. Public-facing assessment evidence still uses the actual CLI and append-only records, with separate learner permission.

## REMOTE CI RED → LOCAL FIX — 2026-10-23

PR #9, head de91a19, GitHub Actions run `39843827147`: Ubuntu 3.11–3.15 passed; macOS and Windows failed. Remediation: `scripts/learnprint_portfolio.py` explicitly normalizes only trusted macOS /var → /private/var system alias while preserving link checks, Windows temp fixture parent canonicalization in `tests/test_course_portfolio.py`, and NTFS Win32 file-id/link-count verification in `scripts/install.py` for hook upgrade. Local focused 47 passed/3 skipped, full suite 516 passed/3 skipped/385 subtests. **Remote follow-up CI NOT VERIFIED until the new push and actual jobs finish; release cannot be called PASS based on Windows only.**

### CI follow-up remediation, 2026-10-23

CI follow-up run `39888014467` reproduced Windows 3.11 hardlink-swap failure even after file-index/link-count hardening. Additional guard now binds hook identity to the Win32 creation FILETIME as well as volume/file index; on POSIX uses st_ctime_ns in identity. This prevents same-file-index reuse from being treated as the original file. Focused local `python -m pytest tests/test_course_portfolio.py tests/test_publish_hook_install.py -q`: 41 passed, 2 skipped, 20 subtests. **Remote cross-platform test must rerun after this patch; not yet verified.**

## RELEASE RELAY UPDATE — 2026-10-23 (latest, supersedes older numerical snapshots)

**Final local verification addendum:** pytest 516 passed/3 skipped/385 subtests, exit 0; unittest 519 tests OK/3 skipped, exit 0; packaging PASS, index privacy guard PASS with 0 private indexed after exact 49-path public-only staging; three real course IDs validate VALID. All technical verification happened on Windows; external GitHub Actions CI/human UAT remain NOT VERIFIED.


**Owner authorization:** explicit in this chat to analyze, fix, test, document, commit and publish code as needed. This does NOT direct publication of the learner's real `Courses/`; selective course release needs artifact-level informed selection and privacy review. Preserve all historical evidence, ticket comments and untracked original data.

**Latest local engineering evidence:** Windows, `python -m pytest tests/ -q`: **516 passed, 3 skipped, 385 subtests passed**, exit 0, 288.37 s, on the working tree after live FSM evidence binding, Windows CRLF and document path protections. Focused docs test: 6 pass/1 skip; focused FSM/evidence tests: 11 pass. CI jobs for other OS/Python versions have NOT run as part of this local test.

**Research updated to 2026-10-23**: official Python support schedule now includes stable 3.15.1 (2026-10-21); 3.9/3.10 EOL. `.github/workflows/verify.yml` now checks 3.11/3.12/3.13/3.14/3.15 on Windows, Linux and macOS using actions/checkout@v7, setup-python@v7, read-only permissions and checkout without persistent credentials. See `docs/research/2026-10-23-production-release-gates.md`.

**P0/P1 hardening just completed:**
- Course doc generator refuses symlink/junction directory-chain changes, linked/replaced/oversized file leaves, and altered pre-images; known Windows CRLF stubs handled while hashing exact original bytes. Atomic per-file writes and backups do not form an all-file crash-transaction; adversarial OS-level swaps not proven impossible.
- When tutor phase is persisted, demonstration writes in `record` enforce exact ATTEMPT/TRANSFER/DELAYED_RETRIEVAL phase, caller-supplied task ID from that private FSM and matching assisted/unassisted provenance. Legacy courses lacking a tutor session remain readable and writable under existing guards. New tests prove ORIENT/mismatched-task and hint-relabel rejection.
- Universal-language policy, portable adapters, private course docs, honest unit position, selective publication UX, and actual SQL/DNS/English private course plans from the preceding session preserved.
- `docs/PRODUCTION-WALKTHROUGH.md` offers a truthful start-to-finish owner guide. No fabricated tutor transcripts, evidence, credentials or learner-human trials.

**Open acceptance gates that MUST NOT be relabeled DONE:** real low-context and different host multilingual tutor UAT, human learner efficacy/retention, GitHub cross-platform matrix actual results, adversarial file-system race review, installed hook consent/behavior if publishing a portfolio, immutable public portfolio revision strategy, and approved integration into current `main`. Existing .scratch tickets remain open if their required acceptance still lacks proof; do not erase them for a clean-looking dashboard.

**Git scope:** only explicit reviewed public paths from `show_changes` may be staged/committed, with the Git-index privacy checker rerun after staging. The real ignored `Courses/` and backups NEVER enter the public commit. No destructive cleanup, raw `git add -A`, or false release tag. Final stage/commit/remote result should be appended as a separate verified entry.

---
## CURRENT EXECUTION HANDOFF — 2026-10-23 (this entry supersedes older status prose, not history)

**Owner/session:** ChatGPT via connected CodexProLatestFix; continuation of owner's explicitly requested full Learnprint hardening, universal-tutor UX and selective course portfolio work. **Workspace:** `D:\Ibrahim\Projects\learnprint`; branch `feature/hardening-workspace`. **Initial observation:** worktree clean before this run. **Current status:** reviewed local source edits and untracked additions **not committed, not pushed, not merged**. Original tracked source and private learner evidence remain protected. Agent claims from earlier dated entries should not be treated as a live lock without new heartbeat.

**Product decisions (binding):**
- Tutor supports **ANY course topic**, from narrow/specific to wide/multi-stage, in the learner's fluent preferred explanation language. English `in/on/at` is only a reproduction case. For each domain use authentic prerequisite order, example, safe hands-on, independent application/transfer, and delayed review.
- Display explicit stage labels and a compact honest ordered syllabus. `0–3` diagnostic prompts is a **ceiling**, not three mandatory tests. ASCII progress shows unit position, NOT percentage mastered. Only the evaluator may assert evidence-gated competence; host-reported stage is not persisted proof.
- **Every course is eligible for learner-selected portfolio curation**. NO course is automatically published. Each published course needs a separate exact-file manifest/preview/approval; canonical `Courses/` and `events.jsonl` remain private; GitHub commit/push is a separate authorization.

| New ID | Scoped change and test evidence | State |
|---|---|---|
| TUX-01 | Canonical `protocols/TUTOR-LANGUAGE-AND-STAGES.md` plus exact mirrors in skills/.agents/distribution; integrated into AGENTS/TEACHING/JOURNEY/PRESENTATION and skill/command entrypoints. `docs/TUTOR-LANGUAGE-STAGES-UAT.md` contains multilingual, stage and seven-domain manual UAT cases. | VERIFIED policy/file wiring only; real model response UAT OPEN |
| TUX-02 | `scripts/learnprint_stage_card.py` + read-only `course journey-card`, canonical plan/evidence status + host-reported stage OR verified persisted course FSM, 0–3 usage, clear unit-position bar; `course tutor-init/tutor-status/tutor-transit` now binds the existing validated FSM to private per-course state, with approval and idempotent replay. | VERIFIED by disposable automated tests, 3 added live CLI integration tests; actual model behavior across hosts remains OPEN |
| EVID-CLI-01 | `record --from-file` supports UTF-8 private JSON with a rubric object, preserving real observed answers, CLI-level --approve, fail-closed disallowed fields, no shell-escaping hazard. | VERIFIED by disposable regression tests, Windows scenario |
| PORT-SELECT-01 | Read-only `course portfolio-options` lists every course eligible for individually consented curated export; no Git stage/push. ADR-0002, PRIVACY.md, COURSE-PORTFOLIO.md and README updated. | VERIFIED CLI and source policy; real GitHub publication deliberately NOT PERFORMED |
| COURSE-DOC-01 | `course docs-preview/docs-sync` renders bounded checksum-sealed safe derived syllabus/Mermaid/handoff from validated structured state; accepts known stubs or verified previous generation, rejects edits/links/stale digest, backups, no ledger score changes. | VERIFIED disposable tests; one symlink test SKIPPED by Windows permission |
| COURSE-LOCAL-01 | Real user private English course retains UUID, 3 units and observed evidence; SYLLABUS/MAP/course HANDOFF/root HANDOFF synced from stubs after read-only preview and backups. | VERIFIED command success and read-only course validate |
| COURSE-LOCAL-02 | Real SQL course: preserved original UUID, all 6 competency IDs and evidence; constructed/prerequisite-validated/adopted 6-unit structured plan via official plan-set and backup. Original user-authored SYLLABUS/MAP/HANDOFF deliberately preserved. | VERIFIED dry-run + plan-set, course validate |
| COURSE-LOCAL-03 | Real DNS course: original UUID retained; 4 unknown competencies (no invented observations), 4 prereq-ordered units adopted with backup; stub docs refreshed after approved preview. | VERIFIED dry-run/plan-set/docs-sync/course validate |
| GIT-01 | Local branch is advanced vs public `main` historically at 3f19d392; stale remote draft PR #8 was closed unmerged after universal local policy integration; no duplicate PR remains open. `docs/PUBLISHING.md` updated for real branch/PR integration, no new PR created in this run. | SAFE HELD: no blind merge/reset/commit/push; requires reviewed path-scoped Git integration |
| HOST-UAT-01 | Test stock and customized OpenCode tutor on at least 3 different subject families and 2+ explanation languages; independently review transcripts for real fluency, stage and reliable learner evidence. | NOT VERIFIED; cannot claim model-behavior PASS from unit tests |
| W0/W11-REMAINING | Cross-OS Python 3.9/3.12 CI, real security/junction race review, actual installed hook upgrade, public immutable revision model, independent reviewer/human learning-outcomes study and owner-approved main merge. | OPEN under pre-existing W0–W11 gates, NOT silently reclassified as done |

**Current-turn commands and ACTUAL results:**
- `python -m pytest tests/test_tutor_policy_contract.py tests/test_skill_distribution_sync.py -q` -> exit 0, 10 passed, 63 subtests.
- `python -m pytest tests/test_record_from_file.py tests/test_cli.py -q` -> exit 0, 18 passed.
- `python -m pytest tests/test_journey_card_and_portfolio_options.py -q` -> exit 0, 7 passed, 3 subtests.
- `python -m pytest tests/test_course_docs_sync.py -q` -> exit 0, 3 passed, 1 skipped (unavailable Windows symlink privilege).
- **`python -m pytest tests/ -q` -> exit 0, 511 PASSED, 3 SKIPPED, 385 subtests passed, 157.91 seconds** on Windows local.
- `python scripts/check_package.py` -> exit 0, PACKAGING OK.
- `python scripts/learnprint_publish_guard.py --repo .` -> exit 0, OK, zero private files in Git index, zero public snapshots indexed; does NOT test real publication in this repo.
- `python scripts/learnprint.py course validate` -> exit 0, VALID (all 3 actual private courses).
- `python scripts/learnprint.py course portfolio-options` -> exit 0, all 3 course UUIDs selectable, 0 exported.
- Windows learner course changes happened under existing standing approval and this user-directed fix scope, through normal `scope-set`, `plan-set`, `docs-sync`; no new test grades, score events, publication, commit/push or network action.

**Changed tracked public paths:** AGENTS.md; README.md; Learn Print Deep Research and Mega Enhancement Plan.md; to-do.md; docs/COURSE-PORTFOLIO.md; docs/PUBLISHING.md; docs/adr/0002-selective-course-portfolio-publication.md; rules/PRIVACY.md; scripts/learnprint.py; tests/test_skill_distribution_sync.py; protocols/TEACHING.md, JOURNEY.md, PRESENTATION.md; all respective `skills/`, `.agents/skills/`, `distribution/claude-plugin/` mirror policies; `.opencode/commands/learnprint-learn.md`. **New untracked public source:** `protocols/TUTOR-LANGUAGE-AND-STAGES.md` + five mirrors; `docs/TUTOR-LANGUAGE-STAGES-UAT.md`; `scripts/learnprint_stage_card.py`, `learnprint_course_docs.py`; `tests/test_tutor_policy_contract.py`, `test_record_from_file.py`, `test_journey_card_and_portfolio_options.py`, `test_course_docs_sync.py`, `test_course_tutor_persistence.py`. **Private ignored paths added under actual learner Courses:** two proposal JSON for DNS, one SQL plan proposal, generated course documents and backups, structured state/competency updates; DO NOT stage, publish or delete. See actual `show_changes` rather than old C1/C3 dirty baselines.

**Next safe integration step:** use `show_changes` and source-level review; ensure no private contents are staged; run privacy/packaging gates; remote PR #8 was CLOSED unmerged as superseded by local advanced hardening work on 2026-10-23; stage/commit/sync only via separately reviewed Git path-specific operation after owner authorization. `main` is a stable integrated branch, NOT a promise that all future features are complete. Once in main and actually verified, start later features from fresh main. Leave real learner data in Courses/ and all historical tracker entries intact.

---

## B. Current execution dashboard

| ID | Workstream | Priority | Depends on | Status | Acceptance summary |
|---|---|---|---|---|---|
| DOC-01 | Persist research mega plan | P0 | none | DONE | Plan exists at repo root with scientific sources and implementation phases |
| DOC-02 | Persist cross-agent tracker | P0 | DOC-01 | DONE | This tracker exists, has 27-path legacy inventory and update protocol |
| DOC-03 | Persist common code style | P0 | DOC-01 | DONE | Root Code Style.md exists, carries tested safe coding contract |
| DOC-04 | Wire AGENTS.md bootstrap | P0 | DOC-01..03 | DONE | Agent entry rules point at three docs |
| W0-01 | Rebaseline working tree, private boundary | P0 | DOC-01..04 | READY_FOR_REVIEW | Hash-only Courses integrity baseline recorded locally on 2026-10-22 (21 files, aggregate sha256 in temp manifest, zero content inspection); re-inventory and stage check done; no unexplained paths |
| W0-02 | Review existing hardening/UAT edits | P0 | W0-01 | READY_FOR_REVIEW | Six historical diffs reviewed; ADR-0001 title/consequences and D6 clarified; tests green |
| W0-03 | Security review existing portfolio + Git hook | P0 | W0-01 | IN_PROGRESS | Directory-swap and hook hardlink-swap regressions repaired locally; real hook upgrade, atomic races and independent cross-host security review pending |
| W0-04 | Fresh verification, docs, portability | P0 | W0-02, W0-03 | IN_PROGRESS | Reconciled 2026-10-22: one-command full pytest **411 passed, 2 skipped** (scheduler RED reconciled per C3b; old suites preserved, no deletions incl. the 3.9 grammar gate); packaging/index guard/CLIs PASS; cross-OS/runtime/UAT pending |
| W0-05 | Scoped integration and eventual clean Git tree | P0 | W0-04 | DONE | Owner approved scoped commit in chat 2026-10-22; staged per C4 buckets, never bulk: e2c5945 (CS-DOC+CS-POLICY, 44 files), bfadafb (CS-ENGINE+CS-HARDENING+CS-TESTS, 28 files), to-do refresh commit; no push (origin untouched), hooks untouched and active; final tree clean after tracker commit |
| W1-01 | Canonical pedagogical protocol + skill mirrors | P0 | W0-05 | DONE | ADR-0003 (owner: W1/W2 continuation agent): protocols/ single source, T01-T08 anchors, enriched TEACHING promoted; parity tests 5 passed incl. .agents + distribution maps; independent review pending |
| W2-01 | Tutor FSM/state persistence | P0 | W1-01 | DONE | scripts/learnprint_tutor.py + schemas/tutor-session.schema.json: 35 tests green (transitions table, idempotency, crash-safety, stale revision, replay agreement, schema compat, T01/T04); ledger-side CLI wiring pending in W6 integration |
| W3-01 | Attempt/help/transfer enforcement | P0 | W2-01 | READY_FOR_REVIEW | Engine guards in tutor module: INDEPENDENT/ASSISTED/NOT_SCORED classification, mandatory authored_by provenance, conservative transfer fingerprints (T03/T04/T05), confusion never scored (T02), delayed requires external ref (T06, no fake events); canonical record CLI integration pending |
| W4-01 | Versioned scheduling and replay | P1 | W3-01 | DONE | scripts/learnprint_scheduler.py: fixed_v1 default mirrors canonical evaluator intervals exactly (parity tests incl. evaluator fixtures); adaptive_v2 opt-in, deterministic, bounded 1..42d, policy_version tagged |
| W4-02 | Deterministic due/replay/timezone/burden tests | P1 | W4-01 | DONE | 14 scheduler tests: DST-safe day math, naive-dt fail-closed, deterministic replay, burden cap ordering; C3b RED reconciled to 14 passed |
| W4-03 | Evaluate retrieval quality and workload vs fixed | P1 | W4-02 | READY_FOR_REVIEW | Synthetic benchmark + 9 tests implemented; fixed_v1 default; no human efficacy claim. Issue: .scratch/scheduler-benchmark/issues/01-synthetic-retrieval-workload.md |
| W5-01 | Profile v2 separation and migration | P1 | W3-01 | DONE | v2 schema additive (constraints array, evidence-linked); migration reversible/idempotent; monolith validator accepts 1.0 and 2.0 |
| W5-02 | Confidence calibration analytics | P1 | W5-01 | DONE | scripts/learnprint_profile.py read-time buckets; confidence never equated to correctness; no double storage, no diagnosis labels |
| W5-03 | Migration/backward read and identity tests | P1 | W5-01 | DONE | tests/test_profile_v2.py 13 tests: identity/ledger preservation, old-profile reads, malformed fail-closed, CLI no-overwrite |
| W6-01 | Compact prompt adapters and behavior eval | P1 | W3-01 | DONE | scripts/learnprint_adapters.py + schemas/tutor-turn.schema.json: strict render/parse, fail-closed on 2-JSON-objects, score fields (T08), answer leaks (T01/T02), hint attribution (T03), over-help, delayed without external ref (T06), fabricated source status (T07); 25 tests green + low_context bound |
| W7-01 | Research/claim/source provenance | P1 | W6-01 | DONE | scripts/learnprint_sources.py: registry validated fail-closed (verified needs url+retrieved_at), fabricated citations rejected, retracted/superseded sources invalidate claims, external-without-verified presented UNVERIFIED never as facts; 18 tests |
| W7-02 | Treat learner documents as untrusted content | P1 | W7-01 | DONE | guard_content() flags instruction-injection/role-override/answer-extraction attempts; content stays data, never executed; tests incl. CLI guard |
| W8-01 | Honest portfolio evidence v2 | P1 | W0-05, W3-01 | DONE | human_reviewed requires named reviewer, ai_reviewed requires deterministic evaluation_ref, self_reported carries neither; EVIDENCE.md labels + non-certification disclaimers; publication private by default; 7 new tests (test_portfolio_labels.py) |
| W8-02 | Curated manifest UX, revision/version strategy, privacy negative fixtures, exact preview consent | P1 | W8-01 | IN_PROGRESS | Immutable offline re-edition regression PASS (issue 17): v1/v2 distinct temporary destinations, fresh digest+consent, stale digest/reuse fail closed; public Git revision namespace remains separately gated under ADR-0002 |
| W9-01 | Human-facing portable UX | P1 | W1-01, W6-01 | IN_PROGRESS | next_action() now has English-default and explicit Indonesian messages for all nine phases, unsupported languages rejected; 42 focused tutor tests pass. Cross-host language and beginner/advanced human UAT remain open (issue .scratch/tutor-ux/issues/01-next-action-language.md) |
| W10-01 | Human learning-outcomes evaluation | P1 | W3-01 | IN_PROGRESS | scripts/learnprint_eval.py simulated-journey lab (8 tests): false_mastery_leaks/confusion_pauses/scored-guarantee metrics, always labeled simulated:true, human_participants:0; REAL learner outcome research (design + data collection) remains an open human gate, never fakeable |
| W11-01 | Integrated release/handoff | P0 | W0–W10 | IN_PROGRESS | latest full suite **486 passed, 2 skipped** on the COMMITTED tree (2026-10-22, Windows Python 3.14; concurrent-relay additions included at add-time), unittest discover **488 OK, 2 skipped**; packaging/index guard PASS; W0-05 scoped commits **e2c5945** (CS-DOC+CS-POLICY, 44 files) + **bfadafb** (CS-ENGINE+CS-HARDENING+CS-TESTS, 28 files) landed with owner chat approval, nothing pushed, hooks untouched. Cross-OS CI, independent review, human UAT and W0-05 completion close-out remain |

**Tracker statuses above are planning status, not completion claims.** DOC-01..04 are marked DONE solely for documentation creation in this session, not code verification. W0-05 is BLOCKED because this connector supports file writes and verifications but an authorized, reviewed Git stage/commit path has **not** been established; an agent must re-assess tool availability, not infer a permanent limitation.

### Present observation / risk flags

- **Branch/HEAD last observed:** feature/hardening-workspace at d98cf93 on 2026-10-22. Must recheck next session.
- **Observed original dirty baseline:** 13 modified tracked paths; 9 untracked top-level entries including .scratch/course-portfolio/ (6 actual files); **27 original file paths**. Full detail in section C.
- **Additional documentation changes from this session:** root “Learn Print Deep Research and Mega Enhancement Plan.md”, root to-do.md, root “Code Style.md”, plus modified root AGENTS.md (bootstrap). These are **not yet committed** and must be included in next full Git inventory.
- **Current Git status verified on 2026-10-22 after W0-04B portability gate:** 17 modified tracked + 36 untracked individual paths = **53 changed paths**, reconciled in C1–C3b; staged EMPTY, branch feature/hardening-workspace. W4 scheduler candidate arrived after the full-suite run and its focused tests are not yet green. Latest independently observed HEAD d98cf93ed980ff17d71e17f08ff5fb762d28c427 from the earlier W0-04B relay. No commits, pushes, real hook upgrade or writes to learner Courses. This iteration edited scripts/install.py, tests/test_publish_hook_install.py, U26 and tracker. **Refresh 2026-10-22 end of W6-W11 session:** 20 modified tracked + 36 untracked = **56 changed paths**, staged EMPTY, HEAD unchanged d98cf93; delta explained by C3c/U48-U50 plus tracker/ADR/test-map edits (all inventoried in C3c ownership-resolution note).
- **Historical test record:** 2026-10-19 Windows Python 3.14: 315 passed, 1 skipped, 68 subtests. **Fresh W0-04B run 2026-10-22, Windows Python 3.14.0:** one-command `python -m pytest tests/ -q` **384 passed, 2 skipped, 190 subtests** in 150.99 seconds after adding syntax portability tests and observing concurrent W1/W2 implementation. The earlier 344/2/82 suite remains historical. Previous CI-command parity unittest 345 OK/2 skipped was before this regression was added and is NOT an updated CI parity result. Three real Windows temporary junction tests remain included. Packaging, actual indexed guard and CLI smoke passed. Other reparse forms, true atomic race-safety, cross-OS CI and independent security review remain pending. **W6-W11 continuation 2026-10-22 (final, committed tree): `python -m pytest tests/ -q --tb=no` 486 passed, 2 skipped and `python -m unittest discover -s tests` 488 OK, 2 skipped on commits e2c5945/bfadafb content; these supersede all earlier same-day numbers (384, 411, 464, 481, 483, 486-dirty interim).**
- **Highest security risk:** .gitignore exception permitting only approved Courses/public/<uuid>/ snapshots, publication guard checking staged blobs and legacy pre-commit hook upgrading to v2. Do not use the existing hook for publishing until the safe upgrade path is explicitly reviewed and exercised.
- **Private learner data:** Existing real Courses/ is preserved and kept ignored. UAT always uses isolated temporary --courses-root. No resetting or deleting of real Courses/.

## C. Dirty-file provenance and reconciliation ledger

Each entry records the reason for its prior change and proposed resolution. **Pending** means not independently re-reviewed or committed in this documentation pass. A status change must include evidence in section E/F. The original baseline used Git status top-level lines; expand nested untracked folders to individual files.

### C1. Original 13 modified TRACKED paths

| ID | Path | Why modified / dependency | Resolution | Current |
|---|---|---|---|---|
| M01 | .agents/skills/learnprint-learn/references/TEACHING.md | Presentation rule and historical wrong-score correction | Preserve, compare canonical mirror, test correction semantics | PENDING |
| M02 | .github/workflows/verify.yml | Adds staged publication index guard to CI | Preserve, cross-OS CI verify | PENDING |
| M03 | .gitignore | Replaces blanket Courses ignore with curated public exception | Security audit mandatory; never default-public raw records | PENDING |
| M04 | .scratch/learnprint-finish/issues/06-live-uat-disposable.md | Corrected UAT to preserve real Courses, use temp root | Preserve historical decision | PENDING |
| M05 | .scratch/learnprint-finish/issues/08-docs-quote-nonrunnable-hook-command.md | Resolves outdated CLI hook command docs | Preserve and verify syntax | PENDING |
| M06 | .scratch/learnprint-finish/issues/09-preexisting-courses-root-workspace.md | Owner KEEP decision for actual learner Courses | Preserve owner decision | PENDING |
| M07 | .scratch/learnprint-finish/spec.md | Clarifies UAT boundary versus portfolio separate workstream | Preserve, reconcile with ADRs | PENDING |
| M08 | README.md | Adds pointer to opt-in experimental course portfolio | Preserve, accuracy review | PENDING |
| M09 | docs/adr/0001-disposable-uat-workspace.md | Historical no-Courses assumption superseded for real Courses | Preserve, no contradiction with ADR-0002 | PENDING |
| M10 | rules/PRIVACY.md | Curated publication boundary and explicit consent | Critical security review | PENDING |
| M11 | scripts/install.py | Upgrade verified legacy pre-commit hook to v2 guard | Critical compatibility/hook tests, never overwrite foreign hooks | PENDING |
| M12 | scripts/learnprint.py | Portfolio preview/export command integration | Scope/validation/compat regression | PENDING |
| M13 | tests/test_privacy.py | Allows only guarded public snapshots, forbids private | Test fixture review and actual run | PENDING |

### C2. Original 9 UNTRACKED Git top-level entries = 14 actual files

| ID | Actual file path | Why present / ownership | Resolution | Current |
|---|---|---|---|---|
| U01 | .scratch/course-portfolio/spec.md | Portfolio candidate spec and unfinished release gates | Preserve checkpoint | PENDING |
| U02 | .scratch/course-portfolio/issues/01-public-private-contract.md | Public/private safety ticket | Preserve ticket/history | PENDING |
| U03 | .scratch/course-portfolio/issues/02-preview-showcase-builder.md | Curated snapshot implementation ticket | Preserve ticket/history | PENDING |
| U04 | .scratch/course-portfolio/issues/03-git-safety-and-migration.md | Hook/ignore/migration ticket | Preserve ticket/history | PENDING |
| U05 | .scratch/course-portfolio/issues/04-evidence-ux-and-uat.md | Honest artifact/UAT ticket | Preserve ticket/history | PENDING |
| U06 | .scratch/course-portfolio/issues/05-release-gate.md | Publication release gate ticket | Preserve ticket/history | PENDING |
| U07 | docs/COURSE-PORTFOLIO.md | Export manifest/privacy how-to | Preserve and review against code | PENDING |
| U08 | docs/adr/0002-selective-course-portfolio-publication.md | Explicit approved course publication decision | Preserve binding ADR | PENDING |
| U09 | scripts/learnprint_portfolio.py | Text-only curated export with digest and source checks | Security and negative tests first | PENDING |
| U10 | scripts/learnprint_publish_guard.py | Git-index staged blob privacy gate | Security and path tests first | PENDING |
| U11 | tests/test_course_portfolio.py | Preview/export/injection fixtures | Preserve, execute and expand | PENDING |
| U12 | tests/test_publish_guard.py | Index privacy regression tests | Preserve, execute and expand | PENDING |
| U13 | tests/test_publish_hook_install.py | Legacy→new pre-commit tests | Preserve, execute and expand | PENDING |
| U14 | tests/test_skill_distribution_sync.py | Prevent divergence of host skill copies | Preserve, execute and expand | PENDING |

### C3. NEW root docs / bootstrap from this request

| ID | Actual file path | Reason | Approval | Git classification until stage/commit |
|---|---|---|---|---|
| D01 | Learn Print Deep Research and Mega Enhancement Plan.md | Persistent science+prompting+architecture+roadmap output of requested research | Explicitly requested | New, likely untracked |
| D02 | to-do.md | Durable task ownership, Git reconciliation and cross-model handoff | Explicitly requested | New, likely untracked |
| D03 | Code Style.md | Mandatory compact engineering/verification guidelines for all models | Explicitly requested | New, likely untracked |
| D04 | AGENTS.md | Minimal pointer to enforce D01–D03 in agent bootstrap | Necessary for requested cross-agent continuity | Tracked modified |

**Do NOT “repair” the above by deleting it.** Next agent must inspect actual Git status, identify any additional paths created meanwhile, and update this ledger before altering work. For gitignored/private materials, maintain *only coarse presence/hash integrity evidence* with access approval, never raw content in a public tracker.

### C3a. Additional paths introduced by W0 security work

| ID | Actual file path | Reason / provenance | Git state |
|---|---|---|---|
| U15 | .scratch/course-portfolio/issues/06-hook-link-safety.md | Reproducible hardlink/symlink hook overwrite defect; local fix, regression evidence and residual risks | New untracked; preserve for review |
| U16 | .scratch/course-portfolio/issues/07-windows-reparse-export-boundary.md | Synthetic reparse fix plus three real temporary Windows junction regression tests executed and passed; directory-chain TOCTOU/other reparse tags still pending | New untracked; preserve for review |
| U17 | .scratch/course-portfolio/issues/08-index-root-alias-privacy.md | Reproducible staged symlink at exact private directory root bypassed prefix-only Git index guard; RED/GREEN and residual gates | New untracked; preserve for review |
| U18 | .scratch/course-portfolio/issues/09-windows-trailing-dot-alias.md | Manifest trailing-dot directory aliases accepted on Windows; reproducible RED/GREEN and segmented regression | New untracked; preserve for review |
| U19 | .scratch/course-portfolio/issues/10-manifest-parent-boundary.md | Manifest-parent symlink/junction trust-boundary regression; RED/GREEN full suite 332 pass, 2 skip | New untracked; preserve for independent review |
| U20 | .scratch/course-portfolio/issues/11-publication-metadata-markdown.md | Public README/EVIDENCE Markdown structure and provenance spoofing via manifest metadata; RED/GREEN full suite 333 pass, 2 skip | New untracked; preserve for independent review |
| U21 | .scratch/course-portfolio/issues/12-case-collision-git-index.md | Casefold duplicate staged public artifact names accepted with forged-consistent manifest; RED/GREEN full suite 334 pass, 2 skip | New untracked; preserve for independent review |
| U22 | .scratch/course-portfolio/issues/12-index-casefold-collision.md | Concurrent duplicate of U21, marked wontfix/duplicate; preserves independently observed positive-control and segmented test evidence | New untracked; preserve until separately authorized consolidation; NOT a second defect |
| U23 | .scratch/course-portfolio/issues/13-manifest-hardlink-read-identity.md | Reproducible multiply-linked manifest and file replacement trust boundary; RED/GREEN, full suite 337/2/82 | New untracked; preserve for independent review |
| U24 | .scratch/course-portfolio/issues/14-directory-chain-toctou.md | 3 synthetic parent-directory swaps (source, manifest, export) RED→GREEN, full 343 pass/2 skip/82 subtests; still nonatomic | New untracked; preserve for independent review |
| U25 | .scratch/course-portfolio/issues/15-w0-integration-review-plan.md | Previous 42-path scope review plan; add U26 to its inventory before owner-authorized integration | New untracked; preserve for maintainer review |
| U26 | .scratch/course-portfolio/issues/16-hook-upgrade-atomic-link-race.md | Linked-hook race after legacy read reproduced RED and mitigated via identity recheck/exclusive create/atomic replacement; full 344 pass | New untracked; preserve for independent review |

**Current reconciled snapshot 2026-10-22 (W0-03B race hardening):** 14 modified tracked + 29 individual untracked = **43 changed paths**, staged EMPTY. U26 is new and documented; U25 remains the previous 42-path integration inventory to be revised before owner-approved staging; U22 stays a preserved duplicate/wontfix. No blanket staging/cleanup.

### C3b. Concurrent W1/W2 artifacts and W0-04B portability gate (2026-10-22)

The latest working tree has **17 modified tracked + 36 untracked individual files = 53 paths**, staged EMPTY. Ten paths appeared since the previous 43-path inventory; all are preserved, none is implicitly approved for Git staging. These are working-tree observations, not proof of integration or independent ownership approval.

| ID | Actual path | Provenance and handling |
|---|---|---|
| M14 | `distribution/claude-plugin/skills/learnprint-learn/references/TEACHING.md` | W1 canonical teaching mirror; preserve, verify parity |
| M15 | `protocols/TEACHING.md` | W1 canonical teaching policy; preserve, review ADR-0003 |
| M16 | `skills/learnprint-learn/references/TEACHING.md` | W1 host mirror; preserve, verify parity |
| U27 | `docs/adr/0003-canonical-pedagogical-policy.md` | W1 canonical policy decision; review before W1 close |
| U28 | `schemas/tutor-session.schema.json` | W2 tutor session schema; not yet integrated |
| U29 | `scripts/learnprint_tutor.py` | W2 tutor FSM candidate; another agent editing tests concurrently |
| U30 | `tests/test_tutor_state.py` | W2 tutor tests; observed SHA change during this relay, not edited by this relay |
| U31 | `tests/test_python39_syntax.py` | W0-04B syntax-only Python 3.9 portability gate; new, created by this relay |
| U32 | `scripts/learnprint_scheduler.py` | Concurrent W4 scheduler candidate; appeared after full suite completed, preserve for its agent |
| U33 | `tests/test_scheduler.py` | Concurrent W4 scheduler tests; first focused run 1 failed/13 passed/6 subtests, awaiting other agent reconciliation |

**Fresh checks:** syntax gate 3 passed/32 subtests; tutor focused 35 passed/59 subtests after concurrent changes; full pytest 384 passed/2 skipped/190 subtests in 150.99s on Windows Python 3.14, **before U32/U33 appeared**; packaging, Git index privacy guard, policy mirror PASS. Later focused W4 scheduler test: **1 failed, 13 passed, 6 subtests** (retention_due vs maintained fixture expectation). Do not call the latest 53-path tree full-suite green until W4 tests are reconciled and rerun. Real Python 3.9 execution and cross-platform CI remain un

**Fresh checks:** syntax gate 3 passed/32 subtests; tutor focused 35 passed/59 subtests after concurrent changes; full pytest 384 passed/2 skipped/190 subtests in 150.99s on Windows Python 3.14, **before U32/U33 appeared**; packaging, Git index privacy guard, policy mirror PASS. Later focused W4 scheduler test: **1 failed, 13 passed, 6 subtests** (retention_due vs maintained fixture expectation). Do not call the latest 53-path tree full-suite green until W4 tests are reconciled and rerun. Real Python 3.9 execution and cross-platform CI remain u

**Reconciliation (owner continuation agent, same relay series):** C3b artifacts U27-U33 are now owned, green and reconciled: W4 parity fixed (14 passed), W2 tutor 35 passed, W1 parity 5 passed; the full one-command suite for the current tree is **411 passed, 2 skipped** (Python grammar gate retained). The stale W4 RED snapshot is superseded; no test deletions; every historical suite continues to pass. U31 remains W0-04B relay property. Real 3.9 runtime and cross-OS CI remain open gates.

nverified.

### C3c. W5–W8 concurrent work and W4-03 benchmark (2026-10-22)

Latest observed 18 modified tracked + 50 individual untracked = **68 changed paths**, staged EMPTY. Fifteen paths beyond C3b are preserved and inventoried; concurrent W6–W10 ownership is separate and not independently reviewed by this relay.

| ID | Actual path | Provenance |
|---|---|---|
| M17 | `schemas/learner-profile.schema.json` | W5 additive profile v2 schema |
| U34 | `scripts/learnprint_profile.py` | W5 profile calibration |
| U35 | `tests/test_profile_v2.py` | W5 migration tests |
| U36 | `schemas/tutor-turn.schema.json` | Concurrent W6 turn schema |
| U37 | `scripts/learnprint_adapters.py` | Concurrent W6 adapters |
| U38 | `tests/test_tutor_adapters.py` | Concurrent W6 golden tests |
| U39 | `scripts/learnprint_sources.py` | Concurrent W7 provenance |
| U40 | `tests/test_sources_provenance.py` | Concurrent W7 tests |
| U41 | `tests/test_portfolio_labels.py` | Concurrent W8 labels tests |
| U42 | `scripts/learnprint_scheduler_benchmark.py` | W4-03 synthetic benchmark, local verified |
| U43 | `tests/test_scheduler_benchmark.py` | W4-03 positive/negative/boundary tests |
| U44 | `.scratch/scheduler-benchmark/issues/01-synthetic-retrieval-workload.md` | W4-03 evidence and human review gate |
| U45 | `protocols/JOURNEY.md` | Concurrent W9 canonical learner journey policy |
| U46 | `protocols/PRESENTATION.md` | Concurrent W9 presentation policy |
| U47 | `scripts/learnprint_eval.py` | Concurrent W10 evaluation candidate, not reviewed in this W4 task |

Additional paths beyond U47, introduced by the W6-W11 continuation session (same executor as the F-entry above):

| ID | Actual path | Provenance |
|---|---|---|
| U48 | `tests/test_eval_lab.py` | W10 lab tests, 8 passed |
| U49 | `docs/RELEASE-NOTES.md` | W11 release notes, evidence + open gates |
| U50 | `docs/ROLLBACK.md` | W11 rollback procedure, no destructive ops |

Ownership resolution for U36-U47: the concurrent W6/W7/W8 candidates listed in C3c are the SAME executor's work (this continuation session), completed and verified (see the 2026-10-22 W6-W11 F-entry); no third-party edits were detected in these files. `scripts/learnprint_tutor.py` (U28/U29 area) additionally gained the W9 `next_action` presenter; `scripts/learnprint_portfolio.py` gained W8 label validation; `scripts/learnprint_scheduler_benchmark.py` (U42) remains the separately released W4-03 claim and was not edited here. **Post-commit addendum (2026-10-22):** a parallel relay's final edits (W8-02 offline re-edition regression, W9 language presenter polish, U52 issue) were staged at add-time of commit bfadafb and are part of it; relay ownership for those fragments is recorded in section F/G, no edits were clobbered. All 57 dirty paths from the porcelain snapshot were consumed by commit e2c5945 (policy/docs bucket), commit bfadafb (engine/tests bucket), or this tracker commit; a final porcelain check shows only this tracker file untracked before its own commit.

### C3d. W8-02 immutable offline revision regression (2026-10-22)

The latest Git inventory is **18 modified tracked + 54 individual untracked = 72 changed paths**, staged EMPTY. U48-U50 were introduced by the earlier W6-W11 continuation; the only new path in this iteration is U51. The existing tests and portfolio docs are already inventoried above, and were updated in place.

| ID | Actual path | Provenance |
|---|---|---|
| U51 | `.scratch/course-portfolio/issues/17-immutable-offline-revisions.md` | W8-02 synthetic offline revision regression, 482 passed/2 skipped/244 subtests; Git public revision namespace remains an independent review gate |

### C3e. W9-01 language presenter inventory

- New U52: `.scratch/tutor-ux/issues/01-next-action-language.md`.
- Updated existing: `scripts/learnprint_tutor.py`, `tests/test_tutor_state.py`, `to-do.md`.
- Final inventory: 18 modified, 55 untracked, 0 staged (73 paths). Branch feature/hardening-workspace; historical HEAD d98cf93, fresh hash unavailable.

### C4. Explicit change-set buckets for later safe commits

- **CS-DOC** research plan, tracker, Code Style, AGENTS pointer. Documentation-only; no code assertions.
- **CS-HARDENING** M01, M04, M05, M06, M07, M09. Review together, isolate from newer engine work.
- **CS-POLICY** M03, M08, M10, U01–U08, U15–U26 and U51 (hook/reparse/index-root/path-alias/manifest-parent/Markdown-metadata/index-collision/manifest-link/directory-swap, offline revision evidence and scoped integration review issue files). U22 remains duplicate/wontfix. Privacy/docs decision and still-open portfolio tickets.
- **CS-ENGINE** M11, M12, U09, U10. Portfolio implementation and hook logic.
- **CS-TESTS** M02, M13, U11–U14, U31. CI/privacy/portfolio/skill sync and Python 3.9 syntax-only verification.
- **CS-V2 (candidate, not yet integrated)** M14–M16 and U27–U30, U32–U33. Canonical policy mirrors, ADR-0003, tutor FSM/schema/tests and concurrent scheduler candidate. Re-run full suite after W4 test stabilization. Re-review coupling and actual ownership before any staged change.

Buckets are **review concepts**, not permission to stage/push. Actual coupling may require combining some buckets to keep every intermediate commit passing; document the rationale and exact files. Historical finish spec's "no engine changes" applies to its *own* old finishing scope, not a revision of the later portfolio ADR. Do not rewrite history.

**Disposition 2026-10-22 (owner-approved in chat):** buckets realized as three scoped local commits on feature/hardening-workspace, in dependency order so the tree stays coherent: policy/docs-first commit (CS-DOC+CS-POLICY: protocols, ADRs, mirrors, privacy scheme, .scratch artifacts), then engine commit (CS-ENGINE+CS-HARDENING+CS-TESTS: all scripts, schemas and tests together so code and tests land as one green unit), then the tracker refresh commit. Push never executed; origin left untouched for independent review.

## D. Per-phase task definitions and evidence gates

### W0: Baseline rescue [P0, MUST FINISH BEFORE V2]

- [x] W0-01A Re-run status and compare to C1–C3. Observed 14 modified tracked + 17 untracked individual files (31 total), no staged changes; no unexplained paths at this checkpoint. Recheck ownership before further work.
- [x] W0-01B Preserve current Git diff/context and original Courses integrity (hashes/manifest local-only, no content disclosure). **Done 2026-10-22: hash-only baseline of real Courses/ = 21 files, 20495 bytes, aggregate sha256 e44e61ae...(full manifest in user temp, never in repo), zero content inspection, zero writes to Courses/.**
- [x] W0-02A Review every M01/M04/M05/M06/M07/M09 diff for semantic conflicts; verify issue statuses and ADR consistency. Six diffs inspected; ADR-0001 title/context/consequences and D6 clarified. Local tests passed; independent review still required.
- [x] W0-03A Local disposable Git ignore/index audit: nested private paths ignored, curated public paths trackable, force-added/staged/previously tracked fixtures covered; exact-root symlink bypass reproduced RED→GREEN (issue U17). **Independent cross-platform review remains open**.
- [x] W0-03D Block stage-mode and mixed-case privacy guard bypasses in disposable Git fixtures; RED→GREEN proof and full regression suite 317 passed (details in E).
- [x] W0-03E Reproduce and repair unsafe linked-hook upgrade (hardlink RED→GREEN, symlink test conditional), tracked by [issue 06](.scratch/course-portfolio/issues/06-hook-link-safety.md).
- [ ] W0-03B Local linked-hook race fix RED→GREEN (issue U26), known-legacy/non-Learnprint guard tests pass. **IN_PROGRESS**: independent race/rollback/cross-OS review and migration of the *actual* installed hook require separate owner approval. No real hook installed/upgraded.
- [ ] W0-03C Review M12/U09/U11/U12 portfolio export for path traversal, symlinks/reparse, secret patterns, TOCTOU, Windows names, Unicode, staged-index hash checks and partial writes. Never test on real course originals.
- [x] W0-03F Reject multiply linked source artifacts, including same-byte post-preview substitutions, with disposable RED/GREEN tests and full suite 320 passed (see E).
- [x] W0-03G Reject synthetic Windows reparse attributes on source, manifest, and export parent, with RED→GREEN proof; [issue 07](.scratch/course-portfolio/issues/07-windows-reparse-export-boundary.md). Real junction/TOCTOU tests remain open under W0-03C.
- [x] W0-03H Reject Windows trailing-dot manifest path aliases in `_safe_relative` (three RED subtests then GREEN); [issue 09](.scratch/course-portfolio/issues/09-windows-trailing-dot-alias.md). W0-03C parent still requires independent and cross-host review.
- [x] W0-03I Reject symlink/junction manifest **parent** directories via existing `_existing_plain_dir`; two RED negative tests, GREEN full suite **332 passed, 2 skipped, 78 subtests**; [issue 10](.scratch/course-portfolio/issues/10-manifest-parent-boundary.md). Real junction and concurrent filesystem-swap gates remain open.
- [x] W0-04A Local verification: Windows Python 3.14.0 focused hook/index tests previously **40 passed, 1 skipped, 7 subtests**; full `python -m pytest tests/ -q` **384 passed, 2 skipped, 190 subtests in 150.99s** at the W1/W2 checkpoint, BEFORE concurrent W4 scheduler files appeared. Latest W4 focused suite has one failure; full latest tree not green. Cross-OS and real Python 3.9 runtime remain pending in W0-04B.
- [ ] W0-04B Local Windows CI parity verified: unittest 345 OK (2 skipped), founder/template VALID, package/guard PASS, skill mirror 3 passed/15 subtests. Cross-platform CI and other host UAT remain open; see issue 05.
- [x] W0-04C Proposed path-explicit integration batches and privacy/CI gates are documented in [issue 15](.scratch/course-portfolio/issues/15-w0-integration-review-plan.md), **not** in a section C4a. This is a review plan only, not approval for staging, commits, push, or a clean tree.
- [ ] W0-05A Get scoped permission/capability to stage and commit; do not assume user request to *write documentation* is permission to commit/push all pending work.
- [ ] W0-05B Complete reviewed scoped integration; verify current HEAD, clean Git worktree, no unknown staged paths and no privacy exposure.
- [ ] W0-05C Close/reclassify old tickets with genuine evidence, keeping historical comments. If repository says delete completed plan files, decide with an approved diff and preserve essential handoff record.

### W1/W2/W3: Deterministic teaching behavior [P0]

- [x] W1-01 Select canonical source for TEACHING/ASSESSMENT/JOURNEY policies; record ADR if needed and strengthen mirror check. **Done: ADR-0003; canonical=protocols/; enforced parity tests, 5 passed.**
- [x] W1-02 Encode T01–T08 as normative requirements with bounded host-specific rendering. **Done: T01-T08 anchors in protocols/TEACHING.md; parity enforced to .agents + distribution mirrors.**
- [x] W2-01 Define, test and persist tutor phase/session state with valid transitions, idempotent event IDs, replay and crash recovery. **Done: scripts/learnprint_tutor.py + schemas/tutor-session.schema.json; 35 tests green.**
- [x] W2-02 Preserve existing Python 3.9+ CLI behavior and fail-closed schema compatibility. **Done: 3.9 grammar gate passes; schema_version mismatch and malformed state fail closed; full suite 411 passed.**
- [x] W3-01 Track hint/solution/attempt provenance, answer reveal and explicit assessment exit. **Done in tutor engine: help_level linked to tasks, authored_by mandatory, confusion exit non-scored. Ledger CLI wiring remains.**
- [x] W3-02 Require novel independent transfer after any guided solution; distinguish confusion from wrong scored response. **Done: T05 conservative fingerprint contracts; confusion exit marks outcome_not_scored.**
- [x] W3-03 Ensure only existing canonical evaluator decides demonstrated/maintained and retention timing. **Done: tutor never writes scores; delayed transit requires external reference; scheduler only computes due dates.**

### W4/W5: Adaptive learning without neuromyths [P1]

- [x] W4-01 Implement scheduler interface with fixed_v1 compatibility before adaptive_v2. **Done: learnprint_scheduler.py; fixed_v1 evaluator parity tests.**
- [x] W4-02 Build deterministic due/replay and timezone/clock drift/incomplete history tests. **Done: 14 tests; naives fail closed; unscorable outcomes never credited.**
- [x] W4-03 Synthetic-only retrieval/workload comparison harness implemented and tested (23 focused passes; full 464 passed/2 skipped). **READY_FOR_REVIEW**: toy retention proxy is not human learning evidence; adaptive_v2 remains opt-in pending consented empirical evaluation. See .scratch/scheduler-benchmark/issues/01-synthetic-retrieval-workload.md.
- [x] W5-01 Evolve profile using reported preference/observed effect/hypothesis/constraint separation. **Done: v2 additive schema + reversible migration.**
- [x] W5-02 Use existing confidence_self_report for longitudinal calibration; never equate confidence with correctness. **Done: learnprint_profile.py read-time calibration; disclaimer enforced.**
- [x] W5-03 Migration/backward read, immutable learner identity and ledger preservation tests. **Done: tests/test_profile_v2.py; old profiles read; identity untouched.**

### W6/W7/W8: Models, source truth and safe course portfolio [P1]

- [x] W6-01 Define minimal provider-neutral tutor turn schema and compact adapters. **Done 2026-10-22: adapters module + schemas/tutor-turn.schema.json, 25 tests (tests/test_tutor_adapters.py), schema-enum parity test included.**
- [x] W6-02 Golden behaviors: one-question wait, confusion, hints, no-answer-first, fresh transfer, real clock review, no fabricated browsing. **Done 2026-10-22: golden render/parse tests cover EXACTLY-ONE task, T01 no answer first, T02 clarify, T03 attribution, T05 transfer labeling, T06 external_ref, T07 single-status enum, T08 no score fields; low-context bound tested via patched bound.**
- [ ] W6-03 Cross-host/model capability matrix (actual results only, including low-cost/low-context models). Open: needs real multi-host runs; cannot be produced locally.
- [x] W7-01 Machine-readable source/claim provenance and version/retraction checks, no fake citations. **Done 2026-10-22: learnprint_sources.py, 18 tests (tests/test_sources_provenance.py); retraction + supersession + UNVERIFIED downgrade covered.**
- [x] W7-02 Treat learner documents/social posts as untrusted content, guard prompt injection and privacy. **Done 2026-10-22: guard_content() injection pattern flags; content is data, never executed; tests incl. CLI.**
- [x] W8-01 Make portfolio evidence explicit about assisted/self-reported/AI-reviewed/human-reviewed claims. **Done 2026-10-22: _validate_achievements accountability (reviewer/evaluation_ref fail-closed), EVIDENCE.md labels, non-certification disclaimers; 7 tests (test_portfolio_labels.py), combined run with test_course_portfolio.py 37 passed, 1 skipped.**
- [ ] W8-02 Curated manifest UX, revision/version strategy, privacy negative fixtures, exact preview consent. Open: re-edition/version strategy for re-published snapshots remains.

### W9/W10/W11: UX and release [P1 / P0 gate]

- [x] W9-01 Beginner and experienced learner UAT; roadmap before diagnostic; concrete hands-on and short response mode. **Partial 2026-10-22: next_action() presenter shipped (3 tests, one action per phase, no claims). Beginner/advanced human UAT and cross-host language checks remain open.**
- [ ] W9-02 Verify fallback without Python/network, cross-host persistence, language and time/token usability. Open: needs real hosts; the low_context preset supports bounded contexts but has not been exercised on limited real hosts.
- [x] W10-01 Baseline-vs-v2 research design with unaided application, transfer, delayed 1/7/21d outcomes where practical; no fake human trial. **Design instrument shipped 2026-10-22: scripts/learnprint_eval.py simulated-journey lab (8 tests) measures false_mastery_leaks/confusion_pauses/scored guarantees, always labeled simulated:true, human_participants:0. Real learner data collection remains an open human gate and is NOT claimed.**
- [x] W10-02 Analyze assisted→unaided gap, false mastery, answer leaks, provenance and review burden. **Deterministic instrument shipped 2026-10-22: the lab classifies ASSISTED vs INDEPENDENT per attempt, reports leaks (must be 0), enforces answer-hidden tasks via the tutor engine (T01), and counts confusion pauses and score-field guarantees; analysis of REAL journeys still requires real sessions.**
- [x] W11-01 Full tests/CI/secure staging/migration/rollback current evidence and documented limitations. **Partial 2026-10-22: committed tree verifies 486 passed, 2 skipped (pytest) + 488 OK (unittest); packaging PASS; CLI smoke OK; docs/RELEASE-NOTES.md + docs/ROLLBACK.md written; W0-05 scoped commits e2c5945 + bfadafb landed owner-approved, nothing pushed. Open gates documented: cross-OS CI, real Python 3.9 runtime, installed-hook consent, human UAT.**
- [ ] W11-02 Independent review and human UAT, release decision, owner-approved scoped merge/PR/push; final clean tree and durable handoff.

**Any discovered defect:** Create an issue at .scratch/<feature>/issues/NN-slug.md with status label, reproduction, input fixture, expected/actual, severity, owner, reason and test. Update this tracker with issue link. Do not hide it via broad “cleanup.”

## E. Verification ledger (facts only)

| Timestamp | Scope | Command/evidence | Result | Notes |
|---|---|---|---|---|
| 2026-10-19 (historical) | Repo whole local suite | Reported in .scratch/course-portfolio/spec.md | **REPORTED** 315 passed, 1 skipped, 68 subtests | Not rerun here; Windows intermittent timeout previously seen |
| 2026-10-22 | Workspace observation | CodexPro open_workspace and show_changes | Branch feature/hardening-workspace HEAD d98cf93; 13 M, 9 untracked top-level entries | Review-only observation; expanded 27 actual paths |
| 2026-10-22 | Documentation creation | CodexPro write of root plan/tracker/style; minimal AGENTS bootstrap edit | Document existence and content write observed | NOT a test run; not a Git commit |
| 2026-10-22 03:00 WIB | W0-03B linked-hook regression | Disposable hardlink fixture before fix | RED: 1 failed, 5 passed, 1 skipped | Existing legacy hook upgrade modified linked file; issue U15 |
| 2026-10-22 03:00 WIB | W0-03B linked-hook fix | Focused tests and full suite on Windows Python 3.14.0 | GREEN: focused 32 passed, 1 skipped, 2 subtests; full 318 passed, 2 skipped, 70 subtests (91.44s) | Symlink fixture skipped due to Windows permission; no real hook changed |
| 2026-10-22 03:00 WIB | W0-04 local smoke | check_package.py; learnprint_publish_guard.py --repo .; learnprint.py course --help | Exit 0, PACKAGING OK; guard OK 0 private indexed; CLI help OK | Cross-platform CI and human UAT remain NOT_VERIFIED |
| 2026-10-22 05:00 WIB | W0-03C synthetic reparse RED | `python -m pytest tests/test_course_portfolio.py -q` | **2 failed (expected RED), 15 passed, 1 skipped, 13 subtests** | Mocked Windows reparse attribute on source directory and output parent; no real junction |
| 2026-10-22 05:00 WIB | W0-03C synthetic reparse GREEN | `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_publish_hook_install.py tests/test_privacy.py -q` | **42 passed, 2 skipped, 55 subtests** (10.26s) | Also validates source file and manifest reparse negative cases |
| 2026-10-22 06:00 WIB | W0-03A exact-root staged symlink RED | `python -m pytest tests/test_publish_guard.py -q` | **2 failed (expected RED), 13 passed, 2 subtests** | Disposable Git index entries `Courses` and `.agents/skills/learnprint-personal` previously escaped prefix scan |
| 2026-10-22 06:00 WIB | W0-03A exact-root + nested ignore GREEN | `python -m pytest tests/test_publish_guard.py tests/test_privacy.py tests/test_publish_hook_install.py tests/test_course_portfolio.py -q` | **45 passed, 2 skipped, 60 subtests** (11.64s) | Private nested ignored, public curated trackable; no original data accessed |
| 2026-10-22 06:00 WIB | Whole-suite regression after W0-03A | `python -m pytest tests/ -q` | **327 passed, 2 skipped, 75 subtests** (93.46s) | Single-process Windows run, unlike previous segmented coverage |
| 2026-10-22 06:00 WIB | Package/index/CLI smoke | `python scripts/check_package.py`; `python scripts/learnprint_publish_guard.py --repo .`; `python scripts/learnprint.py course --help` | All exit 0; package OK; guard OK (0 private/public indexed) | No real Git index mutations |
| 2026-10-22 07:18 WIB | W0-03C trailing-dot alias RED | `python -m pytest tests/test_course_portfolio.py -q` | **3 failed (expected RED), 20 passed, 1 skipped, 13 subtests** | All failures are three trailing-dot path subtests; no real Courses/ touched |
| 2026-10-22 07:18 WIB | W0-03C alias GREEN | `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_privacy.py -q` | **40 passed, 1 skipped, 63 subtests** (11.36s) | Normal path positive control and invalid path negatives |
| 2026-10-22 07:18 WIB | Whole-suite single-command attempt | `python -m pytest tests/ -q` | **NO RESULT**; connector internal error twice | Do not claim a one-process full-suite pass |
| 2026-10-22 07:18 WIB | All 21 test modules, six disjoint groups | Security (48), core (44), UAT (23), persistence (55), presentation (129), trust (31) | **330 passed, 2 skipped, 78 subtests**; all six exit 0 | Durations 15.84s / 28.86s / 25.11s / 19.06s / 10.58s / 1.71s; independent pytest processes |
| 2026-10-22 07:18 WIB | Package/index/CLI smoke | `python scripts/check_package.py`; `python scripts/learnprint_publish_guard.py --repo .`; `python scripts/learnprint.py course --help` | **All exit 0**, PACKAGING OK; guard 0 private/public indexed | Cross-OS and human UAT still NOT_VERIFIED |
| 2026-10-22 ~08:00 WIB | W0-03C manifest-parent RED | `python -m pytest tests/test_course_portfolio.py -q` | **2 failed (expected RED), 20 passed, 1 skipped, 16 subtests** | Synthetic symlink/reparse parent in separate manifest directory; initial fixture shared source ancestor and was corrected before RED |
| 2026-10-22 ~08:00 WIB | W0-03C manifest-parent GREEN | `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_privacy.py -q` | **42 passed, 1 skipped, 63 subtests** (10.56s) | Ancestor symlink/junction check using existing `_existing_plain_dir` |
| 2026-10-22 ~08:00 WIB | W0-03C one-command full suite | `python -m pytest tests/ -q` | **332 passed, 2 skipped, 78 subtests** (92.94s; executor duration 94.48s) | Windows, single process, exit 0 |
| 2026-10-22 ~08:00 WIB | W0-04 local smoke | `python scripts/check_package.py`; `python scripts/learnprint_publish_guard.py --repo .`; `python scripts/learnprint.py course --help` | All exit 0, PACKAGING OK, guard OK with 0 indexed private/public | No original Courses/, hook, index mutation; cross-OS and human UAT still unverified |
| 2026-10-22 05:00 WIB | Single-command whole suite attempt | `python -m pytest tests/ -q` | **NO RESULT**; connector internal error on 3 attempts | No claim of whole-suite pass or test failure |
| 2026-10-22 05:00 WIB | All 21 test modules, 6 disjoint pytest commands | Focused 4 modules (42), CLI/commands/core (44), CLI-UAT/evidence/install/journey (23), method/migration/persistence (55), presentation/progress/QA/routing (129), trust/workspace/skill-sync (31) | **324 passed, 2 skipped, 70 subtests** (all six exit 0) | Per-command duration 10.26s / 27.14s / 24.28s / 17.36s / 12.64s / 1.83s; independent test processes |
| 2026-10-22 05:00 WIB | Packaging and publication guard | `python scripts/check_package.py`; `python scripts/learnprint_publish_guard.py --repo .` | **Both exit 0**; PACKAGING OK, guard OK 0 indexed private/public files | Cross-OS, real junction, TOCTOU and human UAT not verified |

**Verification commands to execute when safe:**  
- `python -m pytest tests/ -q`  
- `python scripts/check_package.py`  
- `python scripts/learnprint_publish_guard.py --repo .`  
- `python scripts/learnprint.py --help`  
- `python scripts/learnprint.py course --help`

Before each command, confirm that it does not write original learner data or execute a network/publication side effect. For UAT, always pass an isolated temporary --courses-root and verify originals remain identical after tests. Record actual full stdout summary, exit code and environmental details or a stable report path. **Do not write PASS until output was actually observed.**

### E1. Engineering quality targets

- Zero private learner files staged/published without exact consent and sanitization; zero unauthorized deletion.
- Zero false independent demonstration from hinted/solution-assisted attempt.
- Zero fake delayed review without real elapsed-time eligibility.
- Zero incomplete event silently treated as valid or dropped without controlled repair.
- All existing CLI commands supported or explicitly migrated with tested fallback.
- No public “perfect memory,” “brain type,” “clinical learning diagnosis,” or independently accredited certificate claim.
- No reliance on hidden model reasoning or on a specific host to keep state.
- New features require tests at failure boundaries, not only happy paths.

### 2026-10-22 — FRESH W0 SECURITY REGRESSION RUN

| Check | Observed outcome | Environment/scope |
|---|---|---|
| Focused before new negative test | 36 passed, 1 skipped, 68 subtests | Real Windows environment, disposable Git fixtures |
| Full suite before fix | 315 passed, 1 skipped, 68 subtests in 106.01s | `python -m pytest tests/ -q` |
| New index mode test before fix | **1 FAILED** (expected RED), 11 passed | Validates defect: staged symlink mode with identical blob passed old guard |
| Focused after fix | 34 passed, 1 skipped, 53 subtests | Portfolio, guard, hooks, privacy suites |
| Full suite after fix | **316 passed, 1 skipped, 68 subtests** in 92.11s | `python -m pytest tests/ -q` |
| Mode-focused after adding executable negative subtest | 12 passed, 2 subtests | `python -m pytest tests/test_publish_guard.py -q` |
| Case-variant Courses path before fix | **1 FAILED** (expected RED), 12 passed, 2 subtests | Lowercase `courses/.learnprint/events.jsonl` in temporary Git INDEX bypassed old case-sensitive guard |
| Case-variant path after fix | **13 passed, 2 subtests** | Focused guard suite `python -m pytest tests/test_publish_guard.py -q` |
| Full suite after both security fixes | **317 passed, 1 skipped, 70 subtests** in 88.49s | `python -m pytest tests/ -q` |
| Packaging after fix | PACKAGING OK | `python scripts/check_package.py` |
| Publication guard after fix | status OK, 0 indexed private, 0 approved public | `python scripts/learnprint_publish_guard.py --repo .` |

**CODE DELTA / PROVENANCE:** `scripts/learnprint_publish_guard.py` now reads `git ls-files --stage -z` and rejects Git index modes other than 100644, nonzero merge stages, and case-variant private Courses/personal skill paths. `tests/test_publish_guard.py` uses disposable Git `update-index --cacheinfo` fixtures for symlink mode 120000, executable mode 100755, and lowercase `courses/.learnprint/events.jsonl`; all are rejected. Tests were RED before each corresponding fix and GREEN afterward. Work stayed within original already-untracked portfolio candidate files; real repo Git index and original Courses/ were not explicitly staged or written. Independent Courses hash verification remains pending. Include both changes in a separately reviewed publication-guard integration.

**NOT VERIFIED YET:** cross-platform CI, installed real pre-commit upgrade, full manual security review, real learner UAT, actual private Courses before/after hash audit, scoped Git commits/push. The generic guard pass with zero published files does not substitute for disposable staged-public-fixture tests above.

### 2026-10-22 03:00 WIB — W0-03B LINKED HOOK SECURITY REGRESSION

- **Defect:** Existing legacy pre-commit hooks hardlinked to another file were upgraded in place, unexpectedly changing the other file. Test with disposable Git fixture failed RED: **1 failed, 5 passed, 1 skipped**. Symlink test skipped on this Windows host due to missing permission.
- **Fix:** `scripts/install.py` now rejects linked hooks, linked `.git`/hooks directories and multi-linked hook files. Added two regression tests in `tests/test_publish_hook_install.py`. Existing unknown hook overwrite remains denied; no real hook installed.
- **Verification:** Focused `python -m pytest tests/test_publish_hook_install.py tests/test_install.py tests/test_publish_guard.py -q` **32 passed, 1 skipped, 2 subtests**; full `python -m pytest tests/ -q` **318 passed, 2 skipped, 70 subtests** in **91.44 seconds** on Windows Python 3.14.0; `python scripts/check_package.py` **PACKAGING OK**; `python scripts/learnprint_publish_guard.py --repo .` **OK**, 0 private indexed files; `python scripts/learnprint.py course --help` **exit 0**.
- **Defect issue:** `.scratch/course-portfolio/issues/06-hook-link-safety.md` (needs-triage; maintainer security review pending). **Residual risk:** preflight/write filesystem race and real hook migration/backup not verified. No real Git hooks, private Courses, Git index, commits, push or network touched.

### 2026-10-22 04:00 WIB — W0-03C HARDLINK EXPORT BOUNDARY

- **RED:** `python -m pytest tests/test_course_portfolio.py -q` returned **1 failed, 13 passed, 1 skipped, 13 subtests** (expected: `test_hardlinked_artifact_to_private_record_is_rejected` failed because a synthetic hardlink was accepted).
- **Fix:** `scripts/learnprint_portfolio.py` rejects any source artifact with `st_nlink != 1` at path lstat, opened descriptor fstat, and post-read lstat. `tests/test_course_portfolio.py` adds two disposable hardlink regressions, including replacement after a valid preview with identical bytes. No new dependencies or changes to CLI output schema.
- **GREEN focused:** `python -m pytest tests/test_course_portfolio.py tests/test_publish_guard.py tests/test_publish_hook_install.py tests/test_privacy.py -q` returned **38 passed, 2 skipped, 55 subtests** in 9.89s.
- **GREEN full:** `python -m pytest tests/ -q` returned **320 passed, 2 skipped, 70 subtests** in 90.55s, Windows Python 3.14.0. `python scripts/check_package.py` PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` OK (0 public/private files indexed); `python scripts/learnprint.py --help` and `course --help` both exit 0.
- **W0-02A review finding (subsequently corrected in this run):** Inspected all six M01/M04/M05/M06/M07/M09 tracked diffs. Correction CLI flags `--corrects` and `--exclude-from-assessment` exist. Disposable UAT and KEEP decisions agree in changed bodies; no deletion introduced. Found ADR-0001's stale title/profile consequence and finish-spec D6's ambiguous deletion scope. Minimal wording reconciliation was completed later in this run; independent review remains pending (see W0-02A verification below).
- **Remaining W0-03C risk:** Reparse/junction paths, concurrent alias creation and other TOCTOU, platform behavior and human privacy review are not fully proven; heuristic content scanning cannot guarantee confidentiality. Existing uncommitted candidate files remain uncommitted; real Courses/ was not accessed or modified in this run.

### 2026-10-22 04:00 WIB — W0-02A DISPOSABLE UAT WORDING REVIEW

- **Diff review:** M01 teaching protocol correction flags exist in `scripts/learnprint.py`; M04/M05/M06/M07/M09 describe consistent temp-only UAT and owner KEEP decision except for outdated ADR-0001 title/consequences and D6 shorthand. Historical ticket 08 and 09 status remains resolved, ticket 06 UAT remains open.
- **Docs-only fix:** `docs/adr/0001-disposable-uat-workspace.md` now explicitly separates the private existing Courses/ workspace from disposable UAT and states existing profiles are preserved; `.scratch/learnprint-finish/spec.md` D6 explicitly restricts deletion to temporary UAT data. This does not alter the old decision, authorize real UAT or change private data.
- **Fresh focused verification:** `python -m pytest tests/test_qa_hardening.py tests/test_privacy.py tests/test_course_portfolio.py tests/test_publish_hook_install.py -q`: **73 passed, 2 skipped, 53 subtests** in 10.55s. `python scripts/check_package.py`: **PACKAGING OK**. **Fresh full verification after docs:** `python -m pytest tests/ -q`: **320 passed, 2 skipped, 70 subtests** in 91.92s.
- **Still unverified:** real user UAT, cross-OS CI, Git integration, private Courses hash-only baseline, installed hook upgrade. These tests do not grant permission to mutate original data.

### 2026-10-22 12:05 WIB — W0-03C PORTFOLIO MARKDOWN/PROVENANCE SECURITY REGRESSION

- **Defect:** Public manifest metadata interpolated directly into generated README/EVIDENCE could inject extra Markdown headings, bold text, inline code, and pipe-separated provenance-looking columns. The resulting display could misrepresent a self-reported artifact as independently certified. This is presentation integrity, not proven disclosure of private data.
- **RED test:** `python -m pytest tests/test_course_portfolio.py -q` after fixture isolation repair yielded **4 expected failing subtests, 23 passed, 1 skipped, 16 passing subtests**. Preliminary test state contamination was corrected before using this RED evidence.
- **Fix:** `scripts/learnprint_portfolio.py` rejects control characters and Markdown structural delimiters in publication metadata. `tests/test_course_portfolio.py` adds four negative cases and one safe metadata positive control.
- **GREEN focused:** `python -m pytest tests/test_course_portfolio.py -q` yielded **23 passed, 1 skipped, 20 subtests**.
- **GREEN full:** `python -m pytest tests/ -q` yielded **333 passed, 2 skipped, 82 subtests in 273.61 seconds** (single execution, Windows environment). `python scripts/check_package.py` **PACKAGING OK**; `python scripts/learnprint_publish_guard.py --repo .` **OK**, zero public/private indexed files.
- **Provenance:** New issue U20 `.scratch/course-portfolio/issues/11-publication-metadata-markdown.md`. Scope: previously untracked portfolio source/test candidate, new issue, this tracker. Real Courses, Git hooks, Git index staging, commits, pushes, remotes and external publications were not intentionally modified.
- **Limitations:** Plain-text false statements and unverifiable reviewer identity cannot be machine-detected; human review and explicit publication consent are still mandatory. Cross-platform CI, real junction/TOCTOU and installed hook upgrade remain unverified.

### 2026-10-22 15:29 WIB — W4-03 SYNTHETIC SCHEDULER BENCHMARK

- New files: `scripts/learnprint_scheduler_benchmark.py`, `tests/test_scheduler_benchmark.py`, `.scratch/scheduler-benchmark/issues/01-synthetic-retrieval-workload.md`.
- Focused `python -m pytest tests/test_scheduler_benchmark.py tests/test_scheduler.py -q`: **23 passed, 23 subtests** in 1.03s.
- Full `python -m pytest tests/ -q`: **464 passed, 2 skipped, 226 subtests** in 151.45s. Packaging and publication guard PASS (0 private indexed). Benchmark CLI JSON exit 0.
- Deterministic seeded toy-model retention proxy and review burden only; **no real human outcome evidence**. Adaptive policy remains opt-in; human efficacy review pending. Snapshot: 18 modified tracked + 47 untracked, staged empty. Other agents added W6-W8 files concurrently. Exact HEAD recheck unavailable through connector.

## F. Work claims, decisions and audit trail

### 2026-10-22 W0-05 SCOPED COMMIT EXECUTION (GLM agent; owner approval in chat)

- **Authorization:** owner selected "Langsung commit saja" (direct scoped commit, no backup first) from the protection options; this chat choice is the explicit owner approval for the W0-05 packet. Scope limited to the 57 inventoried dirty paths (C1-C3c + U48-U50); no unknown paths appeared at the pre-commit porcelain check.
- **Pre-commit privacy screen:** reviewed diffs of .gitignore (Courses/public/<uuid>/ exception scheme), .github/workflows/verify.yml (publish guard job) and rules/PRIVACY.md (canonical wording); all matched ledger-traced hardening history. Zero learner-data paths touched; real Courses/ never read.
- **Commit 1 e2c5945: policy/protocol/docs layer (44 files):** canonical protocols + mirrors, ADR-0001/0002/0003, portfolio + release + rollback docs, root bootstrap docs, .scratch issue artifacts, .gitignore + CI publish guard, privacy rule.
- **Commit 2 bfadafb: engine + schemas + tests (28 files):** tutor, adapters, sources, eval, portfolio, profile, scheduler, benchmark, installer, publish guard, three schemas, all 15 test files landed in one commit so code and tests arrive together green.
- **Boundaries kept:** push never executed (origin left untouched); hooks left untouched and active (pre-commit ran without bypass); no bulk staging (three explicit path lists); no history rewrite.
- **Remaining:** independent review, cross-OS CI run, real Python 3.9 runtime, human UAT and real-outcome data collection; those are runtime/human gates beyond this connector.

### 2026-10-22 W1-W5 CONTINUATION SESSION (GLM agent, owner continuation of relay series)

- **Executor:** OpenCode/GLM-5.3 continuation after reading AGENTS.md, to-do.md, Code Style.md, mega plan, CONTEXT.md, rules/EVIDENCE.md, protocols and test suites. Baseline confirmed feature/hardening-workspace at d98cf93; 14 modified + untracked inventory matched C1-C3a/C3b at takeover; staged EMPTY. Concurrent W0-04B relay detected mid-session via C3b; reconciled, no overwrite of its evidence (full-suite success note appended).
- **W0-01B:** hash-only Courses/ integrity baseline (21 files, 20495 bytes, aggregate sha256 first bytes e44e61ae; manifest stored OUTSIDE repo in user temp; zero content reads; no Courses/ writes). READY_FOR_REVIEW.
- **W1:** ADR-0003 canonical policy + T01-T08 anchors + enforced parity (protocols/ -> skills/ -> .agents/ -> distribution/); enriched TEACHING promoted canonical; tests/test_skill_distribution_sync.py extended (5 passed).
- **W2/W3:** scripts/learnprint_tutor.py (STM: ORIENT/EXPLAIN/GUIDED/ATTEMPT/FEEDBACK/TEACH_BACK/TRANSFER/DELAYED_RETRIEVAL/COMPLETE; idempotent event ids; optimistic revision; atomic fsync writes; replay agreement; T01 hidden-answer, T02 confusion non-scored, T03 help linked, T04 fresh-task, T05 conservative fingerprint transfer, T06 external-ref delayed; mandatory authored_by), schemas/tutor-session.schema.json, tests/test_tutor_state.py (35 passed).
- **W4:** scripts/learnprint_scheduler.py (fixed_v1 mirrors canonical `_evaluate_competency` intervals incl. red-flag retry; adaptive_v2 opt-in deterministic experiment bounded 1-42d; burden gate; tz fail-closed), tests/test_scheduler.py (14 passed incl. evaluator parity).
- **W5:** schemas/learner-profile.schema.json 2.0 additive (constraints), scripts/learnprint_profile.py (reversible migration + read-time calibration with disclaimers), scripts/learnprint.py validate_profile accepts 1.0/2.0 + constraint validation, tests/test_profile_v2.py (13 passed).
- **Tests:** focused per-module runs above FULL suite `python -m pytest tests/ -q` **411 passed, 2 skipped** (Windows, Python 3.14.0); `check_package.py` PACKAGING OK; publish guard OK 0 indexed; all CLIs `--help` exit 0. Historical suites untouched, zero deletions.
- **No Git staging/commit/push/hook/installation/remotes; real Courses/ untouched.**
- **Next:** W4-03 benchmark harness; W6 adapters + golden journeys; W7 provenance; W8 portfolio v2 labels; W9 UX; W10 eval lab; W11 release. Staging/commit remains owner-gated (W0-05).

### 2026-10-22 W6-W11 CONTINUATION SESSION (GLM agent, same executor as W1-W5 entry above)

- **Executor continuity:** same branch/HEAD at takeover and finish (d98cf93, feature/hardening-workspace); staged EMPTY; real Courses/ and installed hooks untouched. Thirteen tracked files + 36 untracked paths dirty at end (56 total via `git status --porcelain`).
- **W6:** `scripts/learnprint_adapters.py` rewritten cleanly + `schemas/tutor-turn.schema.json`; turn contract presets generic/markdown/low_context; strict `parse_turn_output` fails closed on two-JSON-objects, unknown kind, score rubric fields (T08), answer leaks in task prompts (T01 keyed off `kind`), unattributed or solution-leaking hints (T03), over-help beyond contracted level, clarify disclosing answer (T02), delayed reminder without external_ref (T06), fabricated source statuses (T07); low_context bounded render. `tests/test_tutor_adapters.py` 25 passed (schema parity + golden behaviors; low-context reject tested by patching LOW_CONTEXT_CHAR_BOUND; one fixture reworded instead of loosening the conservative ANSWER_MARKERS regex).
- **W7:** `scripts/learnprint_sources.py`: registry fail-closed (verified requires url+retrieved_at), fabricated citations rejected, retracted/superseded sources invalidate claims, external claims without verified sources presented UNVERIFIED (never as facts), `guard_content()` injection flags with content-as-data stance. `tests/test_sources_provenance.py` 18 passed.
- **W8:** `scripts/learnprint_portfolio.py` `_validate_achievements` extends labels: human_reviewed requires named reviewer (max 80), ai_reviewed requires evaluation_ref (max 120), self_reported carries neither; EVIDENCE.md appends ` | reviewer: X` / ` | evaluation: Y` (backward compatible; existing line-format tests untouched). `tests/test_portfolio_labels.py` 7 passed; combined with `tests/test_course_portfolio.py` 37 passed, 1 skipped.
- **W9:** `scripts/learnprint_tutor.py` gains `NEXT_ACTION_TEXT` + `next_action(doc)` presenter: exactly one learner-visible action per phase, no mastery/score claims; `tests/test_tutor_state.py` now 38 passed (3 presenter tests incl. em-dash absence).
- **W10:** `scripts/learnprint_eval.py` simulated-journey lab + `tests/test_eval_lab.py` 8 passed: golden independent journey, assisted-never-independent leak detection (expectation misalignment IS the leak demo), confusion pauses, invalid scripts fail closed via TutorStateError (blocked_at_behavior + rc 2), no scored refs, optional scheduler interval via fixed_v1; every output labeled simulated:true / human_participants:0. Fixes during iteration: journey() helper default expect=[] and wrapper usage in two tests (engine behavior was correct).
- **W11:** docs/RELEASE-NOTES.md (inventory, verification evidence, remaining gates) + docs/ROLLBACK.md (scenario A/B/C, Courses/ never reverted, no destructive ops) written. FULL suite `python -m pytest tests/ -q --tb=no` **481 passed, 2 skipped** (Windows, Python 3.14.0, 0.20s+ per module; baseline was 411/2). `python scripts/check_package.py` PACKAGING OK. CLI smoke: learnprint_adapters.py / learnprint_sources.py / learnprint_eval.py `--help` exit 0. W1 also completed: protocols/JOURNEY.md + protocols/PRESENTATION.md canonical with skills+agents mirrors byte-identical (distribution intentionally omits the learnprint skill bundle); sync test 5 passed; ADR-0003 scope extended.
- **Remaining open gates (unchanged):** cross-OS CI, real Python 3.9 runtime execution, installed-hook upgrade consent, human UAT, real learner outcome data, independent review of these modules, W0-05 owner-approved staging/commit.
- **Correction (post-commit reconciliation, owner chat approval "Langsung commit saja"):** a concurrent relay landed final additions (W8-02 offline re-edition coverage, W9 language presenter polish) inside files that were staged at add-time of commit bfadafb; the committed tree therefore verifies **486 passed, 2 skipped (pytest) + 488 OK, 2 skipped (unittest discover)**, superseding the interim 481/483 numbers quoted above. All relay edits arrived in the two scoped commits via the add-time file states; no relay path was lost or dropped.
- **No Git staging/commit/push/hook/installation/remotes; real Courses/ untouched.**

### 2026-10-22 07:56 WIB — W0-03C manifest-parent trust boundary (CLAIMED)

- **Executor:** GPT-6 / CodexProLatestFix. Reopened local workspace, read AGENTS.md, to-do.md, Code Style.md, mega plan, CONTEXT.md, ADR-0002, issue 02/09, and portfolio code/tests.
- **Baseline:** branch feature/hardening-workspace, 14 tracked modified + 21 individual untracked = 35 known paths, no staged entries. HEAD last recorded d98cf93; status API does not independently report commit hash. All changed paths map to existing C1–C3a; do not erase any.
- **Ownership/scope:** W0-03B remains claimed by a separate 07:03 iteration, so do not touch hook paths. This iteration claims only `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, `to-do.md`, and a new numbered issue only for a reproduced bug. Existing W0-03C 07:18 run concluded with a recorded outcome.
- **Hypothesis:** `_load_manifest` validates manifest leaf but not its ancestor directories, allowing a symlink/junction parent to redirect the manifest read despite the documented non-link boundary. Reproduce with a disposable manifest under a synthetic reparse-point parent, then add narrow parent checks and rerun regression. No real junction, private Courses/, hook, Git index, commit, or remote mutation.
- **Gate outcome:** Initial tests accidentally shared the course ancestor and passed without detecting the bug; corrected fixture used a separate sibling manifest directory. **RED:** 2 failed, 20 passed, 1 skipped, 16 subtests; **GREEN focused:** 42 passed, 1 skipped, 63 subtests; **GREEN full:** 332 passed, 2 skipped, 78 subtests (92.94s). Packaging and publication guard exit 0. `scripts/learnprint_portfolio.py` now checks manifest ancestors with `_existing_plain_dir`; `tests/test_course_portfolio.py` adds two synthetic link-parent regressions; issue U19 created. Real junction/TOCTOU, cross-platform CI and independent security review remain pending. No actual original Courses/, hooks, Git staging/commit/push or remotes touched.


### 2026-10-22 07:18 WIB — W0-03C Windows path alias review (CLAIMED)

- **Executor:** GPT-6 via CodexProLatestFix. Read AGENTS.md, to-do.md, Code Style.md, mega plan, CONTEXT.md, ADR-0002, privacy policy, issue 02/07 and portfolio source/tests. Git branch feature/hardening-workspace, 14 tracked modified + 20 individual untracked files (34 classified paths), staged empty; HEAD most recently recorded d98cf93, not independently exposed by current status API.
- **Ownership:** W0-03B hook paths currently claimed at 07:03 WIB by another continuation, so this run will not touch `scripts/install.py` or `tests/test_publish_hook_install.py`. Scoped W0-03C paths: `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, this tracker and a new issue only for a reproduced defect. Tracker updates use SHA-guarded exact edits, not blind overwrite.
- **Hypothesis:** `_safe_relative` accepts a path component ending with `.`, which Windows may normalize as an alias to another component. This could make preview/export select a different artifact than the manifest author intended. Test a disposable manifest with `hands-on/alias./query.sql` (and a normal path positive control); require RED before changing validator. Do not create real Windows junctions or read real Courses/.
- **Gate:** Focused security/portfolio tests, whole suite if available, package check, publication guard, diff/status, exact issue and handoff update. No hooks installed, real Git index writes, stage/commit/push, remotes or learner data mutations.
- **Outcome:** **SCOPED LOCAL FIX VERIFIED**. Three trailing-dot path subtests RED before fix, GREEN after rejecting trailing-dot segments in `_safe_relative`. `scripts/learnprint_portfolio.py` and `tests/test_course_portfolio.py` changed; issue U18 created. Focused 40 passed, 1 skipped, 63 subtests. One-process full suite failed at connector layer twice without pytest results; all 21 test modules ran in six non-overlapping commands, 330 passed, 2 skipped, 78 subtests. Package, publication guard and CLI smoke all exit 0. Real Courses/, hooks, index, commits and remotes not touched. **Residual:** real junction/TOCTOU and cross-OS/human privacy review. W0-03C remains IN_PROGRESS. W0-03B hook review at 07:03 was left untouched to avoid file conflict.

### 2026-10-22 07:03 WIB — W0-03B active-hook-path audit (LOCAL CODE VERIFIED; REAL HOOK BLOCKED)

- **Executor:** GPT-6 via CodexProLatestFix; read AGENTS.md, Code Style.md, research plan, tracker, CONTEXT.md, ADR-0002, privacy policy, issue 03/06, `scripts/install.py` and hook tests. Current branch `feature/hardening-workspace`; HEAD previously recorded as d98cf93 but not freshly exposed by status connector. Preflight: 14 modified tracked + 20 individually expanded untracked files = 34, all in existing C1–C3a inventory; staged empty; no concurrent W0-03B file claim found.
- **Scope claim:** `scripts/install.py`, `tests/test_publish_hook_install.py`, `to-do.md`; only create a numbered issue if a real bug is reproduced. No original Courses/, installed hooks, Git index, commits, remotes, or network operations.
- **Hypothesis / negative test:** Git `core.hooksPath` can redirect hook execution away from `.git/hooks`. Current `install_hooks` writes to `.git/hooks/pre-commit` and can report success despite an active alternate hooks path. Test in a disposable Git repo with local `core.hooksPath` configured. Expected fail closed, no inactive hook created; then preserve positive behavior for default hooks path and legacy upgrade. Also inspect limits of other Git hook overrides.
- **Safety and rollback:** Test fixture changes only in temporary Git repos. Require RED before code fix; run focused/full tests and packaging/index/CLI smoke; document exact results and remaining limitations below. No real hook installation authorized.
- **Reconciled 2026-10-22 (new continuation):** Installer source *currently* rejects effective `core.hooksPath` overrides and uninspectable Git config before writing any hook; `tests/test_publish_hook_install.py` contains the disposable-Git negative test plus unreadable-config denial, legacy upgrade and foreign hook preservation. Fresh focused run: **8 passed, 1 skipped** in 3.44s; whole suite after W0-03A fix **334 passed, 2 skipped, 82 subtests**. The historical RED result for this exact override test is **NOT_VERIFIED**, so do not claim it. This reconciles the stale file claim for further scoped review. W0-03B **local code check verified**; genuine installed-hook migration, malicious TOCTOU and multi-platform CI still **BLOCKED/UNVERIFIED**. No real hook installed.



### 2026-10-22 06:00 WIB — W0-03A disposable Git path-boundary audit (CLAIMED)

- **Executor:** GPT-6 via CodexProLatestFix; local workspace reopened; AGENTS.md, to-do.md, Code Style.md, research plan, CONTEXT.md, ADR-0002, privacy policy, issue 03, guard and privacy tests read.
- **Preflight:** feature/hardening-workspace, 14 modified tracked + 19 untracked individual files (33 classified paths, no new unknown path), staged empty. HEAD last known d98cf93, not independently exposed by the connector's status API in this invocation. No concurrent W0-03A claim observed.
- **Claimed scope:** `tests/test_publish_guard.py`, `scripts/learnprint_publish_guard.py` only if RED, and `to-do.md`; new issue file only if a defect is confirmed. No real Courses/, installed hooks, Git staging, commits, pushes, or remote mutations.
- **Plan:** audit exact Git index and ignore path boundary for nested/force-added/previously-tracked files in disposable Git fixtures. Specifically test a Git-indexed symlink at the *exact directory-root name* `Courses` or `.agents/skills/learnprint-personal`, which might escape slash-suffixed prefix checks. RED before fix, GREEN after; package/index and relevant/full tests; record limitations.
- **Outcome:** Local W0-03A scope verified. Two exact-root symlink bypass tests RED (2 failed, 13 passed) then GREEN after rejecting exact `Courses` and personal-skill directory roots case-insensitively in the staged index scan. Added nested ignore test; final focused 45 passed, 2 skipped, 60 subtests; full suite 327 passed, 2 skipped, 75 subtests in 93.46s; packaging, guard and CLI smoke all OK. New issue U17 documents risk and residual review gates. No original Courses, real Git index, hooks or remotes changed. Branch unchanged; HEAD exact hash not independently returned by this connector. W0-03 parent remains IN_PROGRESS for cross-platform/hook/export gates. **Next:** W0-03B hook review and W0-03C real junction/TOCTOU risk review on permitted executor; W0-01B requires separate scoped access.


### 2026-10-22 05:00 WIB — W0-03C Windows junction/reparse security claim (IN PROGRESS)

- Executor: GPT-6 via CodexProLatestFix. Reopened exact workspace and read AGENTS.md, Code Style.md, research mega plan, to-do.md, CONTEXT.md, privacy ADRs, issue 02, relevant code/tests. Branch currently feature/hardening-workspace; last independently verified HEAD d98cf93ed980ff17d71e17f08ff5fb762d28c427 (hash recheck not yet available through show_changes).
- Preflight: 14 modified tracked + 18 individually enumerated untracked files (32 total), exactly reconciled to C1–C3a; no staged paths. Existing Courses/ present and out of scope. No concurrent claim/lock detected in tracker.
- Claimed paths: scripts/learnprint_portfolio.py, tests/test_course_portfolio.py, to-do.md; no other files unless a new defect issue is necessary. No installed hooks, real learner files, Git index, commits, pushes or remotes.
- Hypothesis: on Windows, directory junctions/reparse points may not be identified by Path.is_symlink(), allowing curated export to read outside the approved course or write into an aliased output parent. Test using disposable mklink /J fixtures, then fail closed on reparse metadata with Python 3.9+ compatible stdlib. Include positive, negative, boundary tests, run fresh focused/full/package/guard and update this record with real results.
- Outcome: **LOCAL SYNTHETIC REPARSE FIX VERIFIED**. The initial direct Windows junction fixture edit was rejected by connector safety checks; no junction was created. Switched to a cross-platform mock of `Path.lstat().st_file_attributes` with Windows 0x400 reparse flag and ordinary directory mode. RED: 2 failed, 15 passed, 1 skipped, 13 subtests. GREEN: 42 passed, 2 skipped, 55 subtests focused. New negative tests also cover reparse source artifact and manifest. The source checks now reject reparse points on source components, manifest and export ancestors. New issue U16 records residual real-junction and TOCTOU risks.
- Full `python -m pytest tests/ -q` attempted three times but failed at connector level with no test output; all 21 test modules were run once across six non-overlapping pytest commands: 42 + 44 + 23 + 55 + 129 + 31 = **324 passed, 2 skipped, 70 subtests**. This is segmented coverage, not a single-process suite claim. Package check OK; publication guard OK with zero indexed learner files. Current status: 14 tracked modified + 19 untracked, staged empty, no Git operations. No real Courses/ read or write.
- Next exact unblocked action: W0-03A ignore/forced-index behavior review in disposable Git fixtures; then W0-03C real Windows junction and TOCTOU validation on a permitted executor. W0-01B original Courses hash baseline requires explicit scoped access.


### 2026-10-22 04:00 WIB — W0-02A documentation consistency claim

- Executor: GPT-6 via CodexProLatestFix. Rechecked 14 modified tracked + 18 untracked files and staged empty; HEAD d98cf93ed980ff17d71e17f08ff5fb762d28c427 remains the last freshly verified commit. No conflicting task owner recorded.
- Scope: docs/adr/0001-disposable-uat-workspace.md, .scratch/learnprint-finish/spec.md, to-do.md. All six M01/M04/M05/M06/M07/M09 diffs reviewed first.
- Issue: ADR-0001 title and old consequences imply real learner data is absent/throwaway, while ADR-0002 explicitly preserves existing real Courses/. D6 does not qualify that only temporary UAT records are deleted.
- Change only inconsistent wording; preserve historical dates, actual decisions, privacy boundary, and old tests. Re-run package and relevant focused tests; no real Courses or Git mutation.
- Outcome: **LOCAL DOC RECONCILIATION VERIFIED**. ADR-0001 title, context and consequence now distinguish private real Courses/ from disposable UAT root; finish-spec D6 explicitly limits deletion to temporary UAT records/profile. All six legacy diffs inspected, CLI correction flags confirmed. Focused 73 passed/2 skipped/53 subtests, full 320 passed/2 skipped/70 subtests, package OK. No private Courses/ writes, no Git operations. Ready for independent documentation review.

### 2026-10-22 04:00 WIB — W0-03C scoped review claim

- Executor: GPT-6 via CodexProLatestFix. Branch feature/hardening-workspace, HEAD d98cf93ed980ff17d71e17f08ff5fb762d28c427. Working tree 14 modified tracked, 18 untracked files, staged empty; all reconciled to C1–C3a.
- Scope: scripts/learnprint_portfolio.py, tests/test_course_portfolio.py, to-do.md. No active competing claim recorded.
- Hypothesis: hardlinked source artifacts can evade symlink checks; use disposable synthetic fixtures to prove rejection without reading actual learner files.
- Plan: RED regression, minimal fix, focused/full tests, package and index guard, final diff/status. No hooks, staging, commit, push or original Courses writes.
- Outcome: **LOCAL FIX VERIFIED**. A synthetic hardlink to a learner-record fixture bypassed old preview checks (RED), then was rejected by three link-count checks (GREEN); post-preview same-byte hardlink substitution also denied. Full suite 320 passed, 2 skipped, 70 subtests; packaging/index/CLI smoke OK. No original Courses writes, hook installation, Git staging/commit/push. W0-03C stays IN_PROGRESS pending junction/TOCTOU and cross-host review. W0-02A six diffs reviewed with two documentation wording discrepancies still open. Next: W0-02A ADR/title clarification with scoped review, W0-03C reparse/TOCTOU tests, W0-01B integrity baseline only with scoped access.


Use append-only dated entries. Template:

    Date/time (timezone):
    Agent / harness / model (if available):
    Task ID and status:
    Baseline branch/HEAD and dirty changes:
    Claimed file paths / conflict check:
    Work performed (facts):
    Source decisions and relevant ADR:
    Tests: command, environment, result or NOT_RUN:
    Git status after work:
    Blockers / permission requirements:
    Next exact unblocked action:

### 2026-10-22 03:00 WIB — W0-03B HOOK REVIEW CLAIM

- Agent: scheduled GPT-6 via CodexProLatestFix. HEAD d98cf93, feature/hardening-workspace. Working tree: 14 modified tracked and 17 untracked individual paths, consistent with existing tracker. No competing hook claim observed.
- Claimed paths: scripts/install.py, tests/test_publish_hook_install.py, to-do.md, and new .scratch/course-portfolio/issues/06-hook-link-safety.md for defect provenance.
- Task: investigate whether a pre-commit symlink is safely rejected. Add isolated Git regression, patch narrowly if reproduced, rerun tests. Never modify the real Git hook, real Courses, Git index, or remote.
- Outcome: linked-hook defect reproduced RED, patched GREEN; 318 passed, 2 skipped, 70 subtests in full suite. Local work ready for security review; parent W0-03B remains IN_PROGRESS due to hook migration/TOCTOU/cross-OS gaps. New issue 06 records provenance. Git remains uncommitted with 14 modified tracked + 18 untracked individual files, staged empty.
- Next: W0-01B private metadata integrity gate (requires scope confirmation), W0-02A hardening diff review, then W0-03C export security; do not install real hook.

### 2026-10-22 — W0 CLAIM: INDEX GUARD HARDENING (IN PROGRESS)

- **Agent:** ChatGPT GPT-6 via CodexProLatestFix.
- **Baseline:** feature/hardening-workspace @ d98cf93, 14 modified tracked + 17 untracked individual files as documented in C1–C3; staged diff EMPTY.
- **Claim:** W0-01A/W0-03A/W0-03C/W0-04A/B. Limited paths: `scripts/learnprint_publish_guard.py`, `tests/test_publish_guard.py`, and this tracker. No concurrent ownership of these paths detected in tracker, recheck before final.
- **Preflight evidence:** focused portfolio/privacy/skill tests 36 passed, 1 skipped, 68 subtests; full suite 315 passed, 1 skipped, 68 subtests (106.01 sec), `scripts/check_package.py` PACKAGING OK, indexed publication guard OK (0 public, 0 private files indexed). These are **fresh local Windows results**.
- **Detected gap [Likely]:** `git ls-files --cached -z` exposes staged names without Git index *file mode*. A staged Git symlink/gitlink can carry the same blob bytes/hashes as a regular text artifact and evade manifest content checks. Need reproducible disposable-Git negative test, then enforce regular-file mode and stage 0 in the guard.
- **Tests / security boundaries:** Use isolated Git fixtures; no writes to private real Courses/, no real index staging, no hook installation, no commits/push.
- **Outcome:** reproduced and repaired two independent Git index privacy-guard bypasses in disposable repositories (staged mode confusion and lowercase private path). Full suite **317 passed, 1 skipped, 70 subtests**, package and current index checks OK. **Next:** W0-01B real Courses hash-only integrity baseline, W0-02 hardening review, W0-03B/C remaining export/hook security. Neither installed hook nor remote Git state was changed.

### 2026-10-22 — DOCUMENTATION BOOTSTRAP

- **Agent:** ChatGPT via CodexProLatestFix, docs-only scope. Individual local executor not claimed.
- **Before:** feature/hardening-workspace @ d98cf93; 13 modified tracked files, 9 untracked top-level entries (27 actual files); existing real Courses/ kept private.
- **Requested:** Save Deep Research/Mega Plan, cross-agent to-do tracker and Code Style into the root, and ensure harness continuity.
- **Files:** added root plan, this to-do.md, Code Style.md; minimal AGENTS.md handoff pointer.
- **Implementation code, source/course files, hooks, Git index:** intentionally not changed.
- **Tests:** NOT_RUN; historical 2026-10-19 results not adopted as current.
- **Commit/push:** NOT_PERFORMED. Documents initially untracked and AGENTS modified; later agent must inventory them.
- **Next action:** W0-01 rebaseline and reconcile all existing work safely, then review and test portfolio security before any stage/commit.

### 2026-10-22 — SCHEDULED CONTINUATION (HISTORICAL SETUP NOTE; SEE CURRENT RUN ABOVE)

- **Automation:** Learnprint Coding Relay, seven hourly runs scheduled at 02:00–08:00 Asia/Jakarta on 2026-10-22.
- **Scope:** Each run reopens Learnprint, reads AGENTS.md/to-do.md/research plan/Code Style.md, verifies Git baseline and executes the next unblocked bounded coding+test task with actual tracker updates.
- **Constraints:** No destructive Git operations, installation of real hooks, staging/commits/push, remote publication or private real Courses writes without separately verified owner consent; use temporary fixtures.
- **Important limitation:** Creating this schedule **does not prove** future runs will connect to the host, that a local executor is active, that work will complete, or that release gates pass. Log each actual execution separately. When unavailable, state BLOCKED and do not fake a result.
- **Status at scheduling:** No scheduled execution yet confirmed; first planned run 02:00 WIB. W0 security fixes tested locally; W0–W11 mega plan remains substantially incomplete.

### 2026-10-22 12:05 WIB — W0-03C portfolio provenance/Markdown injection review (LOCAL FIX VERIFIED)

- **Executor:** GPT-6 via CodexProLatestFix. User approved continuation of coding/testing under existing safety limits, not Git staging/commit/push or publishing.
- **Observed baseline:** branch feature/hardening-workspace, 14 modified tracked and 22 individual untracked files; staged empty. Last recorded HEAD d98cf93; connector status does not independently expose a new hash. All paths match tracker C1–C3a.
- **Ownership:** prior W0-03C manifest-parent claim closed; W0-03B hook-path claim from 07:03 WIB has no closure, therefore do not edit install.py or hook tests. This bounded scope claims only `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, tracker and a new issue if defect reproduced. No real Courses/, Git hook/index, commit, push or remote mutation.
- **Hypothesis:** user-controlled summary/title/achievement claim accepts Markdown structural characters (including newlines and pipes), possibly allowing publication of fabricated credential-looking headings or provenance columns in derived README/EVIDENCE. Check with disposable manifest, require RED before edit, reject unsafe fields while preserving safe plain text, rerun focused/full tests.
- **Outcome:** Four isolated negative Markdown/provenance cases reproduced RED, then passed GREEN after conservative metadata validation; safe plain-text control passed. Full suite 333 passed, 2 skipped, 82 subtests, packaging/index guard OK. Issue U20 and tracker updated, 14 modified + 23 untracked individual files, zero staged. Independent review, real-junction/TOCTOU, cross-platform and human UAT remain pending. No commit/push/hook or real Courses mutation.

### 2026-10-22 — W0-03A: Git index case-collision security (CLAIMED)

- **Executor:** GPT-6 via CodexProLatestFix; immediately continued on user request, no scheduled wait. Read project bootstrap docs/ADR-0002 and Git index guard/tests.
- **Preflight:** branch feature/hardening-workspace, 14 tracked modified + 23 individual untracked; staged diff EMPTY, all changes already documented; previous W0-03B hook-path claim remains unresolved and is OUT OF SCOPE.
- **Scoped paths:** `tests/test_publish_guard.py`, `scripts/learnprint_publish_guard.py`, this tracker and a numbered issue only if bug RED is reproduced. Disposable Git index fixtures only; no real learner Courses/, actual Git staging, real hooks, network or publishing.
- **Hypothesis:** Git-index entries `hands-on/query.sql` and `hands-on/QUERY.sql` can be staged together with valid individual hashes even when a case-insensitive checkout cannot safely represent both. Exporter already rejects case-colliding input; Git guard should enforce the same independent of exporter. Reproduce with synthetic staged Git blobs and self-consistent index manifest, then narrowly reject case collisions, test both normal positive and negative.
- **Outcome:** RED: `python -m pytest tests/test_publish_guard.py -q` 1 failed, 16 passed, 7 subtests; a forged-consistent staged case variant bypassed the previous guard. GREEN focused 40 passed, 1 skipped, 27 subtests; full `python -m pytest tests/ -q` **334 passed, 2 skipped, 82 subtests** in 193.54s. Package, actual-checkout guard and CLI help all exit 0. Issue U21 created; status after run 14 modified + 24 untracked, zero staged. No original Courses, installed hooks, real index writes, commits/push, remote operations. Independent review/cross-platform testing pending.

### 2026-10-22 — W0-03C manifest hardlink and read-integrity audit (LOCAL FIX VERIFIED; REVIEW OPEN)

- **Executor:** ChatGPT GPT-6 via CodexProLatestFix, bounded W0-03C continuation. Read AGENTS.md, to-do.md, Code Style.md, research mega plan, CONTEXT.md, privacy/evidence rules, ADR-0002, portfolio issue/spec and current code/tests.
- **Preflight:** feature/hardening-workspace; 14 tracked modified + 25 individual untracked files (39 total, extra U22 concurrent duplicate already described in C3a); staged EMPTY. HEAD last recorded `d98cf93` but not independently reverified by status tool. Do not erase unknown or duplicative issue history.
- **Claimed paths:** `scripts/learnprint_portfolio.py`, `tests/test_course_portfolio.py`, this tracker; one new numbered issue only if a defect is demonstrated. Other active W0 hook/index changes belong to different workstreams and must not be edited. No real learner data, real hooks, Git index/commit/push, network or publication.
- **Test hypothesis:** manifest is checked as a regular, non-reparse file but is not rejected when multiply hardlinked, unlike selected hands-on artifacts. The current unbounded `Path.read_text` following a check can also be redirected by a filesystem replacement after preflight. First demonstrate the hardlink issue with disposable synthetic file, then apply a narrow descriptor/identity/size validation if RED. Keep strict fail-closed semantics and Python 3.9 stdlib portability.
- **Outcome (LOCAL FIX VERIFIED):** baseline focused **23 passed, 1 skipped, 20 subtests**. New synthetic manifest hardlink RED **1 failed, 23 passed, 1 skipped, 20 subtests**. `scripts/learnprint_portfolio.py::_load_manifest` now checks regular/non-reparse/single-link/32KiB file, opens a bounded descriptor with O_NOFOLLOW where available and validates descriptor/path identity before and after reading; `tests/test_course_portfolio.py` adds a hardlink regression and identical-byte manifest substitution regression. GREEN focused **25 passed, 1 skipped, 20 subtests**. Full `python -m pytest tests/ -q` **337 passed, 2 skipped, 82 subtests in 257.57s** (one Windows run). Package check OK, actual Git-index guard OK (0 private indexed), course CLI help exit 0. New issue U23; 14 modified + 26 untracked individual paths, 0 staged. **Real Windows junction / whole-directory TOCTOU, cross-OS CI, private Courses hash-only baseline, independent human privacy/security/UAT and owner-authorized Git integration remain NOT VERIFIED.** No installed hooks, real learner data writes, commits, push or remote publication.

### 2026-10-22 13:14 WIB — W0-03C real Windows junction boundary UAT (LOCAL TEST VERIFIED)

- **Executor:** GPT-6 via CodexProLatestFix; owner requested immediate continuation. Read AGENTS.md, to-do.md, Code Style.md, research mega plan, CONTEXT.md, ADR-0002, W0-03C issue 07/13 and source/tests.
- **Preflight:** `feature/hardening-workspace`; 14 modified tracked, 26 individual untracked = 40 accounted paths; staged empty. Last recorded HEAD `d98cf93` not independently reconfirmed via connector. Previous W0-03C manifest U23 scope closed; no current conflicting claim detected.
- **Claimed bounded scope:** `tests/test_course_portfolio.py`, this tracker, and issue 07 on test-gate outcome; no production code unless newly reproduced bug and narrow RED/GREEN evidence. **No actual user Courses/**, Git index, hooks, stage/commit/push or remote publication.
- **Goal:** add *real* Windows NTFS junction tests using only disposable tempfile roots. Validate preview source artifact junction, manifest-parent junction and export-target-parent junction are all rejected without reading outside the fixture or producing a snapshot. Use safe fixture cleanup. Skip with explicit reason if Windows junction creation is unsupported; other platforms skip Windows-only tests. Do not claim a synthetic mock is real junction verification.
- **Outcome (LOCAL REAL-JUNCTION GATE VERIFIED):** Added helper to create/remove disposable Windows junctions via `cmd.exe /d /c mklink /J` and three Windows-only regressions for source artifact, manifest parent and export parent. All three executed and passed. Focused `python -m pytest tests/test_course_portfolio.py -q`: **28 passed, 1 skipped, 20 subtests**. Single-run full `python -m pytest tests/ -q`: **340 passed, 2 skipped, 82 subtests** in 126.48s. Packaging, indexed publication guard (0 private staged) and course CLI help exit 0. Updated existing issue 07 with real-junction evidence. Changed only existing `tests/test_course_portfolio.py`, issue 07 and tracker; total still 14 modified tracked + 26 untracked, staged 0 at preflight (final recheck below). Real Courses/, hook installation, actual index staging, commits, push, network and original student evidence untouched. **Real Windows junction 3/3 verified locally, not all mount/reparse tags or whole-directory race; CI across Windows/Linux/macOS and independent human UAT remain open.**

### 2026-10-22 — W0-03C directory-chain TOCTOU (LOCAL MITIGATION VERIFIED; SECURITY REVIEW OPEN)

- Executor: GPT-6 via CodexProLatestFix. Owner requested W0 TOCTOU audit and completion/status report. Read AGENTS.md, to-do.md, Code Style.md, research plan, ADR-0002, privacy rules, portfolio source/tests and issue 07/13.
- Preflight: `feature/hardening-workspace`, 14 modified tracked + 26 untracked individual paths (40 accounted), no staged changes. Historical HEAD d98cf93 not independently refreshed. Prior W0-03C real-junction work was completed.
- Scope: `tests/test_course_portfolio.py`, `scripts/learnprint_portfolio.py`, new numbered issue if reproducible, `to-do.md`. Never mutate actual learner Courses, real hooks, Git index, commits, push or remotes.
- Test hypothesis: replacement of the source/manifest **parent directory** after path checks and before file open can preserve exact file inode/content but bypass the approved path boundary. Inject rename of directory and move the same synthetic file back in a disposable fixture. Require RED before implementing ancestor identity snapshot verification and GREEN afterwards. Distinguish mitigation from complete adversarial race elimination. Track unresolved exported target parent TOCTOU separately if not fully solved.
- Outcome: Three disposable parent-directory swap regressions reproduced RED (source file, manifest file, export destination) and passed GREEN after `_snapshot_directory_chain` and `_assert_directory_chain_unchanged` checks. Focused portfolio tests 31 passed, 1 skipped, 20 subtests; one-process full suite 343 passed, 2 skipped, 82 subtests in 135.38s, Windows Python 3.14.0; package, index guard and CLI smoke exit 0. Security findings and remaining atomic/ABA race limitations are in [issue 14](.scratch/course-portfolio/issues/14-directory-chain-toctou.md). Work scope released; NOT a fully atomic security guarantee.

### 2026-10-22 13:50 WIB — W0-04B Windows CI-command parity (LOCAL VERIFIED; RELEASED)

- Executor: GPT-6 scheduled relay via CodexProLatestFix; bounded to **W0-04B** verification and evidence reconciliation only. Branch `feature/hardening-workspace`, HEAD `d98cf93ed980ff17d71e17f08ff5fb762d28c427` independently checked by `git rev-parse HEAD`; 14 modified tracked, 27 untracked individual paths, 0 staged via staged review. Existing TOCTOU work is outside this claim.
- Allowed edits: `to-do.md` and `.scratch/course-portfolio/issues/05-release-gate.md` only, preserving all other work. Tests may create disposable temporary fixtures but must never touch original `Courses/`, installed hooks, Git index or remotes.
- Outcome (LOCAL VERIFIED; claim released): Windows Python 3.14 `python -m unittest discover -s tests` exit 0, 345 tests OK (2 skipped) in 166.237s; both CLI profile validations VALID; packaging OK; actual index guard OK (0 private indexed); mirror test 3 passed/15 subtests. Expected stderr from negative hook tests did not fail unittest. Cross-OS/Python matrix and human UAT remain NOT VERIFIED. Issue 05 contains command-level evidence.

### 2026-10-22 — W0-03B hook upgrade race hardening (LOCAL VERIFIED; RELEASED FOR REVIEW)

- **Executor:** GPT-6 via CodexProLatestFix. User asked to continue unblocked W0 tasks. Preflight feature/hardening-workspace, 14 modified tracked + 28 untracked (42 accounted), staged EMPTY. Latest independently checked HEAD `d98cf93ed980ff17d71e17f08ff5fb762d28c427` from W0-04B relay; recheck next handoff. No other active file claims observed.
- **Claimed paths:** `scripts/install.py`, `tests/test_publish_hook_install.py`, this tracker and numbered issue if RED reproduced. **Temporary Git repositories only**; do not inspect, install or upgrade real hook or touch original `Courses/`, Git index staging, commit, push, remotes.
- **Hypothesis:** after installer recognizes a known legacy hook by `read_text`, a concurrent replacement with a hardlink to an unrelated file can cause in-place `write_text` to alter that unrelated file. Reproduce with deterministic file replacement in a temporary fixture, then implement limited safe replacement/identity checking and run focused plus full regression. Keep fail-closed behavior; report residual atomic races instead of declaring entire hook workstream finished.

- **Observed outcome:** In a disposable Git fixture, the newly added post-read path substitution case failed before the fix (1 failed, 8 passed, 1 skipped). The locally updated installer uses exclusive creation for fresh installs and checks file identity before replacing a prepared upgrade file. Focused tests: 40 passed, 1 skipped, 7 subtests. Full repository tests: **344 passed, 2 skipped, 82 subtests** in 109.88s on Windows Python 3.14. Packaging, indexed privacy guard, course CLI and skill-mirror checks PASS. Evidence: `.scratch/course-portfolio/issues/16-hook-upgrade-atomic-link-race.md`. The change is review-ready, not evidence that last-instant replacement races or owner-dependent hook installation are complete. No actual hook installation or Git staging/commit/push was performed.

### 2026-10-22 — W2-02 tutor fixture review (RELEASED; CONCURRENT EDIT DETECTED)

- Executor: GPT-6 relay. Initial branch feature/hardening-workspace, HEAD d98cf93, 17 modified and 32 untracked files, 0 staged. Tutor focused tests initially reported 2 failures, 26 passed, 59 subtests. Before any test edit, optimistic SHA check detected that tests/test_tutor_state.py changed concurrently. No W2 file edited; released scope to avoid clobbering another agent. Recheck tutor tests after the other agent finishes.

### 2026-10-22 — W0-04B Python 3.9 syntax gate (LOCAL VERIFIED; CLAIM RELEASED)

- Scope: new tests/test_python39_syntax.py, to-do.md and release-gate issue only. Python 3.9 syntax-only gate with positive and negative control; no edits to concurrent tutor/policy files. Outcome: **3 passed/32 subtests** focused, **384 passed/2 skipped/190 subtests** full pytest (150.99s), tutor focused **35 passed/59 subtests**, mirror **5 passed/32 subtests**; package and indexed privacy guard PASS. Issue 05 updated. Git 17 modified + 34 untracked, staged EMPTY; real Courses and actual hooks/index/remotes untouched. Real Python 3.9 runtime, cross-OS CI, independent review, human UAT and owner-approved integration remain open.

- **Post-checkpoint update:** Two concurrent W4 files arrived after the 384-pass full run. Current Git count 17 modified + 36 untracked (53 paths), staged 0. Focused W4 scheduler suite remains RED (1 failed, 13 passed, 6 subtests); latest syntax gate still GREEN (3 passed, 34 subtests). These W4 files were not edited in this relay; latest-tree full-suite green must be re-established after its owner fixes parity. The exact chronology is also in course-portfolio issue 05.

### 2026-10-22 15:29 WIB — W4-03 engineering iteration (LOCAL VERIFIED; CLAIM RELEASED)

- GPT-6 / CodexProLatestFix. Preflight branch feature/hardening-workspace; 18 modified + 42 untracked; staged empty. No active W4-03 owner. Exact HEAD query blocked by connector.
- Scope: benchmark module, benchmark tests, numbered issue, tracker. No existing scheduler/evaluator changes. No private learner data touched.
- Outcome: deterministic synthetic comparison implemented. Focused 23 passed/23 subtests; full 464 passed/2 skipped/226 subtests; packaging and index guard PASS.
- Final inventory at last observation: 18 modified + 50 untracked, 0 staged, including unrelated concurrent W6-W10 files. Human learning efficacy remains unverified. Next: reconcile W6-W10 ownership and cross-platform release gates.

### 2026-10-22 — W8-02 immutable offline re-edition test (LOCAL VERIFIED; CLAIM RELEASED)

- Executor GPT-6 via CodexProLatestFix; preflight feature/hardening-workspace at d98cf93ed980ff17d71e17f08ff5fb762d28c427, 18 modified tracked + 53 untracked, staged 0. Scope: tests/test_course_portfolio.py, docs/COURSE-PORTFOLIO.md, .scratch/course-portfolio/issues/17-immutable-offline-revisions.md, to-do.md.
- Added positive/negative disposable revision regression: v1 preserved byte-for-byte, changed source requires fresh preview digest and approval, v2 writes a separate offline directory, existing destination refuses overwrite, private fixture state/ledger unchanged. Focused portfolio 32 passed/1 skipped/20 subtests, labels 6 passed/2 subtests. Full suite 482 passed/2 skipped/244 subtests in 96.67s; packaging PASS; indexed guard PASS (0 private indexed). See issue 17 for exact commands.
- Final inventory: 18 modified tracked + 54 individual untracked = 72 changed paths, staged 0. New path issue 17; other paths preserved. This is offline immutable snapshot coverage only; public Git version namespace still requires reviewed ADR/guard design. No real Courses, installed hooks, index, commits or remotes changed. Next task: independent W8-02 public revision design review or unblocked W9/W10 work, while W0-05, cross-OS and human gates remain pending.

### 2026-10-22 — W9-01 language-choice presenter (LOCAL VERIFIED)

- Files: tutor module, tutor tests, issue U52 and tracker. RED 9 failed/39 passed; GREEN focused 42 passed/83 subtests. Full suite 486 passed/2 skipped/259 subtests. Packaging and privacy guard PASS. Issue U52 has full evidence. Work released for independent review.

## G. Current handoff card (update every session)

| Field | Current value |
|---|---|
| Primary goal | Preserve previous work, verify security, integrate cleanly, then implement pedagogical v2 |
| Active phase | Committed + clean: owner approved scoped commits in chat; **e2c5945** (policy/docs, 44 files) + **bfadafb** (engine+tests, 28 files) landed; tracker refresh is the third commit; tree clean afterward, nothing pushed, hooks untouched and active. W0-03/W0-04 remain IN_PROGRESS only for runtime/human gates (hook upgrade consent, cross-OS CI, real Python 3.9, human UAT). W1-W8 engine DONE; W9/W10 instruments shipped, human input gates open; W11-02 review+release decision open. |
| Next task | Independent review of commits e2c5945/bfadafb; then cross-OS CI run + real Python 3.9 runtime + human UAT (W9); real-outcome data collection (W10); W8-02 public Git revision namespace design (ADR-0002 gate); then W11-02 release decision. No push until owner instructs. |
| Work currently claimed by agent | Commit execution only: e2c5945, bfadafb, tracker commit. Owned modules: tutor/adapters/sources/eval/portfolio-labels/presenter (W6-W11, see F entry) + W1 canonicalization. Concurrent relay W8-02 offline re-edition coverage + W9 language presenter landed inside bfadafb at add-time state. Recheck claims before next edit. |
| Known blockers | Independent review of committed work; cross-OS CI; real Python 3.9 runtime execution; real installed-hook migration consent; human UAT + real delayed-retention observations; W6-03 capability matrix needs real hosts. |
| Tests current pass? | **YES locally on the COMMITTED tree:** `python -m pytest tests/ -q --tb=no` **486 passed, 2 skipped**; `python -m unittest discover -s tests` **488 tests OK (2 skipped)** in 164.8s; focused tutor/publish/portfolio 66 passed. `check_package.py` PACKAGING OK; publish/index guards PASS. Real Python 3.9 runtime, cross-OS CI, human UAT pending. |
| Must never touch without scoped permission | Real Courses/, append-only learner ledger, installed Git hooks, remote Git state |
| Read order | AGENTS.md → to-do.md → research plan → Code Style.md → CONTEXT.md → ADRs/rules/skills |
| Status source | Git actual status for dirt; this tracker for intended reasons; canonical CLI evaluator for student mastery |

**Completion rule:** A clean workspace without traceable commits/review is not the goal. The goal is **nothing lost, nothing private leaked, no unexpected artifacts, no untracked/modified path without documented explanation, and each verified task independently reproducible**.
