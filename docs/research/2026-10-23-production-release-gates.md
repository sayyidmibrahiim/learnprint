# Learnprint production and publish readiness research
Date: 2026-10-23 (Asia/Jakarta) | Branch: feature/hardening-workspace

## What was independently checked today
1. **Runtime security lifecycle.** Python.org reports Python 3.9 end-of-life on **2025-10-31** and Python 3.10 on **2026-10-01**. The active supported CPython line today runs 3.11–3.15. Python **3.15.0** was released 2026-10-09; **3.15.1** arrived 2026-10-21 with security fixes. Decision: no EOL Python in production runtime documentation or CI. Retain best-effort source grammar backwards compatibility only. CI matrix now runs 3.11, 3.12, 3.13, 3.14, 3.15 on Windows, Ubuntu, macOS. **Local tests on Windows 3.14 do not prove those 15 jobs passed remotely.**
   - https://www.python.org/downloads/release/python-3925/
   - https://devguide.python.org/versions/
   - https://www.python.org/downloads/release/python-3151/
2. **GitHub Actions maintenance.** Verified official `actions/checkout` and `actions/setup-python` v7 release tracks. Decision: v7 in CI; `contents: read` job permission; checkout `persist-credentials: false`; exact version matrix; no automatic release/push or tokens from untrusted learner work.
   - https://github.com/actions/checkout/releases
   - https://github.com/actions/setup-python/releases
   - https://github.com/actions/setup-python/blob/main/README.md
3. **Privacy and portfolio publishing.** Git documents that `.gitignore` affects only untracked files, not already-tracked ones. GitHub notes that prior clones/forks/PR refs may retain removed secrets. OWASP recommends allowlisted file types, bounded sizes, safe names, authorization, and defense in depth; scanners are not guarantees. Decision: learner chooses any *eligible* course but none is auto-published. Only reviewed text artifacts selected in an exact manifest plus hash-approved snapshot can be locally exported; Git staging/push requires a separate reviewed act and index guard.
   - https://git-scm.com/docs/gitignore
   - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
   - https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

## Reconciled implementation
- **Provider-neutral pedagogy:** canonical TEACHING/JOURNEY/PRESENTATION/TUTOR-LANGUAGE-AND-STAGES protocols and byte-identical host mirrors; applies to any topic, small or broad. Pure unit tests verify policy presence, not real model communication quality.
- **State integrity:** course-scoped tutor FSM (`tutor-init/status/transit`), exact read-only `journey-card`, clear unit position vs demonstrated evidence. When an FSM is present, newly recorded demonstration events must match persisted tutor phase, task ID and assistance provenance; older courses without an FSM are backward compatible.
- **Private documents:** `docs-preview/docs-sync` preview-sealed, rollback backups, legacy Windows CRLF-aware stub recognition, bounded no-follow file reads, directory identity validation, pre-image rechecks; only known stubs or checksum-sealed generated docs are replaced. File-level atomic writes are not an all-files transaction, and adversarial OS-level concurrent directory swaps cannot be proven completely prevented by a portable path API.
- **Portable CLI:** `record --from-file` for faithful Unicode learner responses and structured rubric JSON, with independent CLI `--approve`, never approval embedded in JSON. No fake learner events or grading.
- **Portfolio selection:** `portfolio-options` read-only lists every course; `portfolio-preview` derives a bounded digest and `portfolio-export` requires specific approval; does not stage, commit, push or publish.

## Actual GitHub CI finding and remediation (2026-10-23)

The first PR #9 remote 15-job GitHub Actions matrix revealed **Ubuntu 3.11–3.15 passed, Windows and macOS jobs failed** despite 516 Windows-local pytest passes. These failures are genuine and no pre-fix remote PASS is claimed.

- macOS's OS-maintained `/var -> /private/var` alias made legitimate disposable fixtures fail portfolio directory-chain symlink validation before privacy assertions. `scripts/learnprint_portfolio.py` now normalizes **only that exact trusted macOS OS alias** for directory-chain verification; it still rejects arbitrary symlinks and linked paths below it.
- Windows GitHub runner temporary root used a path alias inconsistent with `Path.absolute()` vs `Path.resolve()` in three junction fixture containment assertions. The regression fixture now canonicalizes **the existing parent only**, never resolves the malicious junction leaf.
- Windows legacy hook upgrade link-swap race test showed a false acceptance under some NTFS/stat implementations. `scripts/install.py` now checks original/current hook identity and link count through Win32 `GetFileInformationByHandle` (read-only), rather than relying only on potentially incomplete CRT stat inode/link metadata.
- Focused local regression tests: 47 passed, 3 skipped; fresh full Windows-local pytest **516 passed, 3 skipped, 385 subtests passed**. Cross-platform jobs must rerun on the new commit; no claiming success until observed.

### CI follow-up remediation, 2026-10-23

CI follow-up run `39888014467` reproduced Windows 3.11 hardlink-swap failure even after file-index/link-count hardening. Additional guard bound hook identity to the Win32 creation FILETIME as well as volume/file index; on POSIX st_ctime_ns. That patch was still followed by runner failures, which led to the fail-closed decision below. Final resolved state: installer refuses every pre-existing hook.

### CI cross-platform follow-up: fixture alias and pinned hook (2026-10-23)

Follow-up CI run `39888572396` demonstrated two distinct regressions: macOS synthetic reparse/link/path-swap fixtures compared the OS `/var` alias against normalized `/private/var` and missed the intended fixture path; Windows linked legacy hook upgrade still passed a rename/hardlink swap under runner conditions. The macOS test fixture now compares the same narrowly trusted system alias on both sides (without normalizing arbitrary links). The hook installer now pins an open descriptor for the original legacy hook during content read, validates identity/link count while the original inode is still pinned, and refuses if a concurrent Windows unlink is denied. The race test treats *either* denied unlink or detected hardlink swap as safe rejection; no external target may be overwritten. Focused Windows test `python -m pytest tests/test_publish_hook_install.py tests/test_course_portfolio.py -q` exit 0, 41 passed, 2 skipped, 20 subtests. This is a candidate fix: remote macOS/Windows CI still must actually pass.

### Security decision: remove automatic hook upgrade (2026-10-23)

The cross-platform CI matrix repeatedly demonstrated that automatic replacement of *existing* legacy `.git/hooks/pre-commit` can pass a link-swap test on Windows and macOS. Neither rechecking `stat` nor probing Win32 FILETIME/identity nor pinning a read descriptor proved stable across runners. **Accepted fail-closed resolution:** the installer now uses exclusive `open("x")` **only when no hook exists**, and refuses every pre-existing hook, including a valid legacy Learnprint hook. It does not mutate that hook or any external hardlink target. An owner can inspect and archive the old hook manually, then install a new one into a proven-empty path; this is a separately reviewed operation and not an implicit agent upgrade. The unreachable legacy-replacement code was removed, and regression `test_existing_legacy_hook_is_preserved_even_with_approval` added. Focused suite: 41 passed, 2 skipped (20 subtests). Real CI rerun still required; do NOT mark release DONE until all 15 GitHub jobs pass.

### macOS mock recursion regression (2026-10-23)

PR #9 CI run 39889996180: Windows Python 3.15 already passed after disabling unsafe existing-hook upgrade; macOS Python 3.13 exposed test-only infinite recursion because synthetic Path.lstat mock called `_trusted_system_alias`, which internally calls `Path.is_symlink`/lstat. New fixture `_fixture_path_key` uses strictly lexical `/var` to `/private/var` mapping under macOS; it never calls lstat/is_symlink, preventing recursive mocks while matching OS alias paths. Windows focused `python -m pytest tests/test_course_portfolio.py tests/test_publish_hook_install.py -q`: 41 passed, 2 skipped, 20 subtests. Cross-platform CI must run again on this commit.

## Verification result on head `cecda70` (2026-10-23)

- GitHub Actions run `39890427415` (push) and `39890434260` (pull_request): **15/15 jobs success**, ubuntu-latest, windows-latest, macos-latest x CPython 3.11, 3.12, 3.13, 3.14, 3.15.
- Local Windows: `python -m unittest discover -s tests` exit 0, 519 tests, OK (3 skipped). `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed.
- `python scripts/check_package.py` exit 0; `python scripts/learnprint_publish_guard.py --repo .` exit 0 with zero indexed paths; founder and starter profiles VALID; CLI help exit 0.
- The three human gates below remain open by design. Synthetic tests, AI review and local hashes cannot close them.

## Release gate truth table
| Gate | Evidence standard | Current scope |
| --- | --- | --- |
| Windows unit/integration suite | `python -m unittest discover -s tests`, successful exit | PASS on `cecda70`: 519 tests, OK (3 skipped) |
| Python 3.11–3.15 × 3 OS CI | Actual GitHub Actions run statuses | PASS on `cecda70`: 15/15 jobs in runs `39890427415` and `39890434260` |
| Packaging and index privacy | `python scripts/check_package.py`, `python scripts/learnprint_publish_guard.py --repo .` | PASS on `cecda70`: PACKAGING OK, zero indexed paths |
| Publication negative tests | Disposable staging, malicious paths, symlinks/reparse, forced private index entries | Automated fixtures pass locally and in CI; external adversarial security review OPEN |
| Human tutor behavior | Real transcripts: fluency, stage labels, independent response fidelity, prompt injection | NOT VERIFIED by synthetic tests; needs a real host and real tutor session |
| Human learning effectiveness | Repeated genuine learner performance, unaided transfer/delayed recall | NOT VERIFIED; no participants invented |
| Git integration | Exact reviewed public paths committed, branch pushed, PR CI green, approved merge | Committed and pushed; PR #9 MERGEABLE and CLEAN; merge into `main` pending |
| Real public portfolio | Per-course exact learner consent and review | NOT requested for any existing private course |

**Decision:** `production ready` and `publish ready` cannot honestly be marked PASS until all release-critical gates are observed. Closing a tracking ticket records its resolution; it never substitutes for a runtime/learner acceptance test. There is no technical reason to publish private Courses automatically.
