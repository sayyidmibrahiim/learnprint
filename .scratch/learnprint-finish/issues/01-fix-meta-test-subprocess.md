# 01 — Fix meta-test via subprocess guard

Status: ready-for-agent
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
