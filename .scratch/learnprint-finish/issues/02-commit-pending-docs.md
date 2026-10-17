# 02 — Commit pending agent-workflow docs

Status: ready-for-agent
Blocked by: none

## Problem

A previous session authored repo-agent docs that were never committed:
`AGENTS.md` has an uncommitted +15-line "Agent skills" section; `CONTEXT.md`
(domain glossary) and `docs/agents/` (issue-tracker.md, triage-labels.md,
domain.md) are untracked. They reference each other (AGENTS.md points at the
two docs files), so they land as one commit. Commit them AS-IS — no edits.

## Change

Stage exactly these five paths (never `git add -A`):

- `AGENTS.md`
- `CONTEXT.md`
- `docs/agents/issue-tracker.md`
- `docs/agents/triage-labels.md`
- `docs/agents/domain.md`

## Acceptance

- [ ] `git status --short` no longer lists any of the five paths
- [ ] `git show --stat HEAD` contains exactly those five files
- [ ] No content edits to any of them

## Commit

`docs: add agent workflow references and repo domain glossary`
