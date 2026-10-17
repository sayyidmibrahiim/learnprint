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

## Comments

- 2026-10-17 builder: staged exactly the five named paths; committed AS-IS
  (zero content edits; AGENTS.md diff was the +15-line "Agent skills"
  section, verified before staging).
- `git show --stat HEAD` → AGENTS.md +15, CONTEXT.md +33, docs/agents/domain.md
  +51, docs/agents/issue-tracker.md +30, docs/agents/triage-labels.md +15;
  exactly those five files, 144 insertions.
- `git status --short` no longer lists any of the five paths.
- Commit: `bf5cff1` — `docs: add agent workflow references and repo domain
  glossary`.
- Status: resolved.
