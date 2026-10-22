# ADR-0002: Selective course-portfolio publication

Status: accepted product decision; engineering candidate implemented, release gated
Date: 2026-10-19
Related: ADR-0001 (disposable learner UAT remains binding).

## Owner decision

`Courses/` is a learner-owned learning workspace **and** a potential GitHub portfolio, not disposable application state. Courses can showcase lessons, source code, hands-on projects and honestly labeled evidence; users may keep selected courses private. Keep existing real course history in place, with immutable IDs and no unauthorized cleanup.

User consent to learn is not consent to publish. No automatic GitHub network operations.

## Private/public split

```text
Courses/
  .learnprint/                          # PRIVATE: registry, profile, events, approvals
  technology/database-sql-interview-sprint/
    state.json                          # PRIVATE: source of truth
    HANDOFF.md                          # PRIVATE: tutor memory
    method-sessions.jsonl               # PRIVATE: method receipts
    hands-on/                            # PRIVATE original learner files
  public/
    <course-uuid>/                      # Explicitly approved derived snapshot
      README.md                         # Curated outcome + real artifact hashes
      EVIDENCE.md                       # Claims with honest self-declared basis
      PUBLICATION.json                  # Approved content hashes + preview digest
      hands-on/                          # Only specifically allowlisted text files
```

Public snapshots never contain the raw ledger, assessment answers, learner profile, private handoff, notes, backups, or arbitrary other files. Existing original course folders remain ignored by Git.

## Privacy mechanism

1. Safe initial state: no publication unless a public manifest identifies one exact course, an explicit hands-on artifact allowlist, and user-reviewed claims.
2. Read-only preview revalidates source files, checks names/content/size, and yields a SHA-256 digest over the public snapshot. A subsequent explicit export revalidates against that digest before creating a new destination. Originals are not modified.
3. Root `.gitignore` ignores all canonical private folders while permitting the `Courses/public/<uuid>/` namespace. This follows Git's parent-directory exclusion semantics. The only allowed committed files under that namespace are those checked by the Git index publication guard.
4. The staged-index guard compares exact staged blobs against a published SHA-256 manifest. Forced additions of private paths, unlisted files and modified approved blobs fail. Existing hooks are only upgraded when their content matches a known Learnprint legacy version; unknown user hooks are preserved.
5. Publishing Git commit/push remains a separate human permission boundary. A local hook can be bypassed, CI detects policy failures after push, and neither protects against all private content automatically.
6. Users may append `/Courses/public/<uuid>/` at the end of the root `.gitignore` to make an untracked snapshot private. Already-tracked history requires a separate untracking/history review and cannot be guaranteed erased from clones/forks.
7. Live learner UAT, packaging and CI across Windows/Linux/macOS are required before release. The actual human tutor behavior cannot be demonstrated solely by CLI tests.

## Credential integrity

GitHub is a hosting platform, **not** an issuer that certifies a learner's knowledge. README/EVIDENCE claims have explicitly identified self-reported, AI-reviewed or human-reviewed bases but no independently authenticated reviewer identity. Do not use the words accredited or verified certificate for these snapshots. Formal Open Badges 3.0 requires issuer identity, cryptographic proof and verification design, outside this workstream.

## Engineering limits and further work

- Text-only, bounded, allowlisted work examples. No executables, archive/PDF/media publishing in the first candidate; common file upload threats and malicious content require human review.
- No automated Git commits/push or destructive operations.
- Existing public snapshots are intentionally not overwritten; content updates need a separately reviewed immutable revision/versioning design.
- Publication metadata is learner-declared, not a cryptographically attested claim or canonical progress export.
- This ADR does not authorize any change to the user's real `Courses/` beyond a separately approved public snapshot operation.
- ADR-0001's disposable test-workspace design remains in force: tests must not modify original learner data.

## Research provenance

- Git parent ignore rules: https://git-scm.com/docs/gitignore
- GitHub sensitive data/history limitations: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- OWASP file upload controls: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- 1EdTech Open Badges 3.0: https://standards.1edtech.org/open-badges/specifications/standards/v3p0
