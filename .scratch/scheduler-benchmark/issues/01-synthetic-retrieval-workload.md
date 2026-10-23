# W4-03: Deterministic synthetic retrieval/workload benchmark

Status: resolved
Date: 2026-10-22 (Asia/Jakarta)
Owner: GPT-6 relay via CodexProLatestFix
Scope: New benchmark module, tests, this issue, and to-do.md.

## Purpose

Compare the existing fixed_v1 and opt-in adaptive_v2 scheduler on **simulated** learner journeys. The benchmark is a reproducible engineering diagnostic, not evidence of human learning gains.

## Acceptance

- No read/write of original Courses or learner records.
- Seeded deterministic outcomes, transparent toy forgetting model.
- Both policies use the actual scheduler API.
- Report synthetic retention probability proxy, number of reviews, accuracy proxy, peak daily reviews, overdue backlog.
- Validate inputs, bound run length, test replay, positive/negative/boundary cases and fixed-v1 compatibility.
- Explicitly refuse empirical superiority claims.
- Preserve adaptive_v2 as opt-in.
- Record exact tests and next gates below.

## Verification outcome (2026-10-22)

Implementation: `scripts/learnprint_scheduler_benchmark.py`; tests: `tests/test_scheduler_benchmark.py`.
- Focused scheduler + benchmark: **23 passed, 23 subtests**.
- Full suite: **464 passed, 2 skipped, 226 subtests** in 151.45 seconds.
- Packaging: PASS. Publication guard: PASS (0 private indexed).
- Example toy-model result (seed 7, 90 days, 8 competencies): fragile fixed 152 reviews / retention proxy 0.385281; adaptive 213 / 0.504520. Durable fixed 58 / 0.948525; adaptive 55 / 0.898965.
- Simulation is NOT human evidence. No real-world superiority demonstrated. Adaptive remains opt-in.
- Final observed status: 18 tracked modifications, 50 untracked files, 0 staged. Concurrent W9 protocol files and a W10 evaluation module appeared after the full suite; preserve them. W6-W10 work was not independently reviewed by this task.
- Next: independent review of toy assumptions, consented human retention evaluation and cross-platform verification. Task claim released.

## Comments

- 2026-10-22 15:29 WIB: Scope claimed after branch/status preflight: feature/hardening-workspace; 18 tracked modified, 42 untracked, 0 staged. Exact HEAD could not be refreshed because read-only Git command was blocked by connector. No active W4-03 claim found. No actual learner data or Git operations in scope.
- 2026-10-23, release verification relay: Resolved as an engineering diagnostic: `scripts/learnprint_scheduler_benchmark.py` with `tests/test_scheduler_benchmark.py` compares fixed_v1 and opt-in adaptive_v2 on seeded simulated journeys. It claims no human learning gain, and none is implied by the green suite. Evidence at head `cecda70`: local `python -m unittest discover -s tests` exit 0, 519 tests OK (3 skipped); `python -m pytest tests/ -q` exit 0, 516 passed, 3 skipped, 385 subtests passed; GitHub Actions runs `39890427415` (push) and `39890434260` (pull_request) report 15/15 jobs success on CPython 3.11-3.15 across Ubuntu, Windows and macOS. Engineering evidence does not substitute for real learner or human tutor acceptance.
