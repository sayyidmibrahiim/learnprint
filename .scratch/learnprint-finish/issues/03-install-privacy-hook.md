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
