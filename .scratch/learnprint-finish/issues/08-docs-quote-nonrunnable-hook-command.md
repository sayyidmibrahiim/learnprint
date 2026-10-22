# 08 — Docs quote a non-runnable hook install command

Status: resolved
Blocked by: none (non-blocking; hook itself is installed and verified)
Found during: ticket 03 (2026-10-17)

## Problem

The documented install command `scripts/install.py --hooks --approve` does NOT
run with the current CLI. Real output:

```
usage: install.py [-h] --target {antigravity,claude,codex,gemini,kiro,opencode}
                  [--dest DEST] [--self] [--personal-skill] [--source SOURCE]
                  [--hooks] [--dry-run] [--approve]
install.py: error: the following arguments are required: --target
EXIT=2
```

`--target` is `required=True` (scripts/install.py:140) and `--dest` or `--self`
is required (scripts/install.py:152), so no invocation with only
`--hooks --approve` can install the hook.

The same abbreviated command is quoted in:
- `.scratch/learnprint-finish/spec.md` D8
- `docs/adr/0001-disposable-uat-workspace.md` line 29
- `rules/PRIVACY.md` line 16 (reads as a literal instruction)
- `plan/learnprint-hardening-workspace.md` line 1836

## Verified workaround (used by ticket 03; hook IS installed)

```
python scripts/install.py --target opencode --self --hooks --approve
```

(`--target` value is unused on the `--hooks` path — early return at
scripts/install.py:156-157.)

## Options (owner decision)

1. Fix docs: quote the full command (add `--self`, any `--target`).
2. Engine change: make `--target` optional for the `--hooks` path (frozen for
   this plan — needs its own approval).
3. Leave as-is, treat the quote as shorthand.

## Acceptance

- [x] Owner picked an option; docs and/or CLI updated accordingly in
      follow-up workstream (not inline in this plan)

## Commit

Folded into the tracker evidence commit
`docs: record finishing-plan ticket evidence (01-04) and file tickets 08-09`.

## Comments

- 2026-10-17 builder: filed from ticket 03; no inline fix applied (D7
  discipline; docs/ and scripts/ untouched by this plan).

- 2026-10-19: Selected option 1 (documentation-only correction). Updated
  rules/PRIVACY.md, docs/adr/0001-disposable-uat-workspace.md and the
  active finish spec to the tested CLI invocation; historical ticket text
  remains as evidence. No installer API change was made.
