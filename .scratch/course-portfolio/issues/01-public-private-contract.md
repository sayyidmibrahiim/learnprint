# 01 — Inventory & freeze public/private file contract

Status: ready-for-agent
Blocked by: none

## Task

Audit all CLI read/write paths in scripts/ and exact per-course files (including HANDOFF, state, logs, sessions, attachments and hands-on outputs). Define schema-compatible per-course visibility and public artifact manifest, ownership and evidence provenance mapping, and release-level privacy boundaries. Confirm whether exporting by copy or through an allowlisted public view minimizes drift and data leakage. Use ADR-0002.

## Acceptance

- [ ] Complete matrix of existing artifact paths by sensitivity and purpose.
- [ ] Stable schema and public artifact allowlist with private exclusions.
- [ ] Safe default, opt-out and old-course migration described.
- [ ] Naming/presentation does not imply accredited certificates.
- [ ] Tests explicitly cover forbidden fields, mixed content, Git history caveat.
- [ ] No real course files changed; no ignore/hook relaxation.

## Comments
