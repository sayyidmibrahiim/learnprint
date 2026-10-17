# 03 — Install privacy pre-commit hook

Status: ready-for-agent
Blocked by: none

## Problem

`.gitignore` is not a security boundary (stated in the Rev 5 hardening plan
and ADR-0001). This public repo must never receive learner data. The repo
already ships the guard: `scripts/install.py --hooks` writes a pre-commit
hook that rejects staged files under `Courses/` and the personal-skill paths.
Owner approved installing it in this checkout (decision D8).

## Change

Run:

```
python scripts/install.py --hooks --approve
```

Then VERIFY it actually rejects (do not trust a silent success):

1. `mkdir Courses` + `echo test > Courses/_hook_probe.txt`
2. `git add -f Courses/_hook_probe.txt` (force-add on purpose — this is the
   exact attack the hook must stop)
3. Attempt any commit; expect the hook to print its ERROR and exit non-zero
4. `git reset HEAD Courses/_hook_probe.txt` + delete the probe file + remove
   the empty `Courses/` dir

## Acceptance

- [ ] `.git/hooks/pre-commit` exists and is the learnprint privacy hook
- [ ] Probe file staged with `-f` is REJECTED by the hook
- [ ] No probe leftovers: `git status --short` clean, no `Courses/` dir

## Commit

None — the hook lives in `.git/hooks/` (untracked by design). If the run
produces any tracked-file diff, STOP and report instead of committing.

## Comments

- 2026-10-17 builder: hook installed + verified; probe rejected; cleaned up.
  Two findings filed (see below). No engine code touched.
- The literal ticket command `python scripts/install.py --hooks --approve`
  FAILS (exit 2: `--target` required; `--dest`/`--self` required). Adapted to
  the existing CLI surface: `python scripts/install.py --target opencode
  --self --hooks --approve` → `INSTALLED pre-commit privacy hook.` (exit 0).
  Discrepancy filed as ticket 08 (same abbreviated command quoted in
  spec D8, ADR-0001, rules/PRIVACY.md, old hardening plan).
- Post-install `git status --short`: no tracked-file diff produced (as the
  ticket required).
- `.git/hooks/pre-commit` exists and equals the learnprint privacy hook
  (HOOK_SCRIPT: rejects staged `^Courses/` and personal-skill paths).
- Probe: `git add -f Courses/_hook_probe.txt` → commit attempt printed
  "ERROR: Attempting to commit private learner data. Remove with: git reset
  HEAD <file>", exit 1; HEAD unchanged (`f5ee5ad`). REJECTED as required.
- Cleanup: probe unstaged (`git reset HEAD`) and deleted; `git status
  --short` shows only tracker-file bookkeeping — no probe leftovers.
- Finding B: `Courses/` ALREADY existed before the probe (`mkdir` failed:
  "already exists") and contains real Oct-11 learner data. Left completely
  intact; owner decision filed as ticket 09 (this is why the literal
  "no Courses/ dir" phrasing of the acceptance cannot be met by removal:
  the dir is not a probe leftover). Probe leftovers: none.
- Acceptance: hook exists ✓; force-staged probe rejected ✓; no probe
  leftovers ✓ (with the ticket-09 caveat above).
- Status: resolved with caveats (tickets 08, 09 open, both ready-for-human).
