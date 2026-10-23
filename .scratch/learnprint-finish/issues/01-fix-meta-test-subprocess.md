# 01 — Fix meta-test via subprocess guard

Status: resolved
Blocked by: none

## Problem

`tests/test_progress_regression.py::test_existing_16_tests_pass` fails under
pytest. Root cause (verified): it calls
`unittest.TestLoader().loadTestsFromName("tests.test_core")` in-process.
`tests/` has no `__init__.py`, and on Python >= 3.12 the loader returns a
`_FailedTest` entry instead of raising `ImportError`, so the method's
`except ImportError` fallback never triggers. Stderr:
`ModuleNotFoundError: No module named 'tests'`. The suite itself is healthy
(`python -m unittest tests.test_core` runs 23 tests green from repo root).

## Change

In `tests/test_progress_regression.py`, replace the body of
`test_existing_16_tests_pass` with a subprocess run of the real suite:

```python
def test_existing_16_tests_pass(self):
    import subprocess, sys
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_core"],
                       cwd=root, capture_output=True, text=True)
    self.assertEqual(r.returncode, 0, msg=r.stderr[-2000:])
```

Add `Path` to the file's imports if absent.

Rejected alternatives (do not use): adding `tests/__init__.py` (flips pytest
import mode for all 282 tests); deleting the meta-test (drops the standalone
regression guard for `test_core`).

## Acceptance

- [ ] `python -m pytest tests/test_progress_regression.py -q` → all pass,
      INCLUDING running this file standalone (the guard's whole point)
- [ ] `python -m pytest tests/ -q` → 283 passed, 0 failed
- [ ] Diff touches only `tests/test_progress_regression.py`

## Commit

`test: run legacy-suite guard via subprocess in progress regression meta-test`

## Comments

- 2026-10-17 builder: implemented exactly as prescribed (5-line subprocess
  guard; `Path` already imported at line 4; subprocess/sys imported locally).
- `python -m pytest tests/test_progress_regression.py -q` → `38 passed`
  (standalone run, the guard's whole point).
- `python -m pytest tests/ -q` → `283 passed` (0 failed; baseline was
  282/283).
- Diff scope: only `tests/test_progress_regression.py` (+5/-7).
- Commit: `a654c1e` — `test: run legacy-suite guard via subprocess in
  progress regression meta-test`.
- Status: resolved.
- 2026-10-23, release verification relay: Resolved: the meta-test no longer recurses into itself and the distribution/meta checks run in a bounded subprocess. Covered by `tests/test_skill_distribution_sync.py`; the full suite passes. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
