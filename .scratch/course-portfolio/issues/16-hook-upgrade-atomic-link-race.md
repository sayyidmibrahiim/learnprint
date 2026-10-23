# 16 — Avoid writing through a swapped pre-commit hook during v1→v2 upgrade

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Workstream: W0-03B Git privacy hook installer
Parent: 03-git-safety-and-migration.md
Severity: High (out-of-scope file overwrite through an injected hardlink)
Owner: Independent security maintainer review pending

## Finding

Prior `scripts/install.py::install_hooks` inspected and read the legacy hook and then called `hook.write_text(desired)` on that pathname. A separate actor can replace the previously checked legacy hook with a hardlink to an unrelated file **after** `hook.read_text` but **before** `hook.write_text`. The updater follows the hardlink and silently overwrites the unrelated file. Earlier test coverage only considered links that were already present *before* hook preflight.

This is an adversarial filesystem race and does not imply any real learner data compromise.

## Disposable regression evidence

New test: `tests/test_publish_hook_install.py::TestPrivacyHookInstallation::test_legacy_upgrade_link_swap_after_read_refuses_without_target_write`.

1. Create a temporary Git repository, a known legacy hook, and an unrelated file with the same synthetic legacy text.
2. Mock the *hook read* so the fixture atomically removes that hook and adds a hardlink to the unrelated file immediately after the read.
3. Assert installer fails closed and the unrelated file content stays unchanged.

**RED before fix:** `python -m pytest tests/test_publish_hook_install.py -q` yielded **1 failed, 8 passed, 1 skipped**. Installer wrongly returned 0, upgraded through the hardlink and changed the unrelated file.

## Scoped fix

- Installer records original hook device/inode prior to reading it, then checks current identity, link count, file type and symlink state before upgrading.
- Legacy upgrades first prepare a complete temporary hook in the same directory and perform `os.replace` of the **path entry**, avoiding writes through current symlink/hardlink targets. Temporary file receives appropriate execute bits, retaining original permission bits where possible.
- New hook installation uses exclusive `open('x')` so an existing foreign hook appearing concurrently is not silently overwritten.
- A rejected upgrade leaves the tested unrelated file unchanged. All fixtures live under `tempfile.TemporaryDirectory`.

**GREEN focused:** `python -m pytest tests/test_publish_hook_install.py tests/test_install.py tests/test_publish_guard.py -q` yielded **40 passed, 1 skipped, 7 subtests** in 19.48s.

**GREEN full:** `python -m pytest tests/ -q` yielded **344 passed, 2 skipped, 82 subtests** in 109.88s (one-process Windows Python 3.14).

**Other checks:** `python scripts/check_package.py` PACKAGING OK; `python scripts/learnprint_publish_guard.py --repo .` OK (0 indexed private and 0 public files); course CLI help exit 0; skill mirror **3 passed, 15 subtests**.

## Explicit remaining limitations

Identity is checked immediately before `os.replace`, not atomically combined with it. A second actor might still replace the hook in that last instant. `os.replace` replaces the hook path entry without writing through a linked *target*, but it might replace a newly inserted foreign hook. Parent `.git/hooks` path substitution and cross-platform hook semantics likewise require independent review, and original hook upgrade/rollback needs **separate owner approval**. This is a narrowly verified improvement, **NOT** a fully race-free migration or authorization to install anything.

No access to original learner `Courses/`, no writes to the actual repository Git hooks/index, no stage, commit, push or remote publication. The Git commits exercised by hook tests occur **only** inside disposable repositories.

## Comments

- 2026-10-22: RED→GREEN and full Windows suite verified locally; review remains open.
- 2026-10-23, release verification relay: Closed by policy change rather than a race fix: automatic upgrade of an existing hook was removed, so the v1 to v2 swap path no longer exists. `scripts/install.py` refuses every pre-existing hook. Regression coverage: `tests/test_publish_hook_install.py`. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
