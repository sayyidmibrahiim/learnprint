# Course portfolios: staged publication with private evidence

Status: **implementation candidate**, locally tested; live learner UAT and cross-platform CI not yet verified. Design: [ADR-0002](adr/0002-selective-course-portfolio-publication.md).

## Select per course (default: selectable, never auto-public)

Every course, in **any domain**, can be considered for GitHub portfolio publication. This does NOT automatically make it public. Each learner chooses the courses and individual artifacts to publish, or keeps any course private. Listing choices is read-only:

```sh
python scripts/learnprint.py course portfolio-options
```

A course with no shareable hands-on evidence is eligible to prepare but **not ready for an evidence portfolio** until genuine proof-of-work is available and reviewed. Only an explicit `portfolio-preview` plus matching `portfolio-export --approve` creates a curated local snapshot; Git commit/push requires separate owner authorization. The CLI never publishes to GitHub by itself.

## What Learnprint publishes

The real course stays under `Courses/<category>/<course>/`, with private raw evidence in `Courses/.learnprint/`. This canonical state is always ignored by Git. A separate, *derived* and human-reviewed snapshot can be exported to `Courses/public/<course-uuid>/`, where Git can track approved proof-of-work.

A snapshot contains a generated `README.md`, `EVIDENCE.md`, `PUBLICATION.json` with SHA-256 hashes and the exact selected `hands-on/` text artifacts. It deliberately omits `state.json`, `HANDOFF.md`, profiles, assessment answers, ledgers, session receipts, private notes and backups. An AI/learner claim is **not** an independently issued certificate. Metadata `human_reviewed` is a learner-declared label, not authenticated proof of review.

## Preparation and preview

Register the course normally; do not re-initialize old `Courses/`. Save actual reproducible work (and only work you own or may share) under its `hands-on/` directory. Create a private JSON manifest with the exact course UUID:

```json
{
  "schema_version": "1",
  "course_id": "REPLACE-WITH-EXISTING-UUID",
  "visibility": "public",
  "title": "SQL Practice Portfolio",
  "summary": "Practiced SQL grouping on a local sample dataset.",
  "artifacts": [
    {"path": "hands-on/queries.sql", "origin": "learner_authored"}
  ],
  "achievements": [
    {"claim": "Wrote an aggregation query",
     "evidence_path": "hands-on/queries.sql",
     "basis": "self_reported"}
  ]
}
```

Supported artifact `origin` values: `learner_authored`, `ai_assisted`, `third_party`. The `basis` field may be `self_reported`, `ai_reviewed`, or `human_reviewed`. **These are declarations and not verified identities or grades.** A `private` manifest cannot be exported. Default behavior is never to export unless the user explicitly invokes the export command.

From repository root:

```sh
python scripts/learnprint.py course portfolio-preview --course-id YOUR-UUID --manifest PATH-TO-PRIVATE-MANIFEST.json
```

This read-only command shows all output paths, hashes and `preview_digest`. Review both content and licenses; the scanner is heuristic and does not prove the files are harmless or anonymous. The manifest must be kept in an ignored/private location.

## Stage an approved portfolio into Courses/

Only after the user has inspected the preview and explicitly approved the export:

```sh
python scripts/learnprint.py course portfolio-export --course-id YOUR-UUID --manifest PATH-TO-PRIVATE-MANIFEST.json --output-dir Courses/public/YOUR-UUID --preview-digest DIGEST-FROM-PREVIEW --approve
```

The export rechecks source and digest, creates a **new** snapshot without overwriting existing ones, and leaves all original course data untouched. It does **not** commit or push anything. A different output folder outside `Courses/` also works, but its own Git repository needs appropriate independent safety controls. Only valid, canonical lowercase UUIDs may be used for the per-course public directory. The tool uses LF-normalized UTF-8 text so Windows Git line-ending conversion does not invalidate hashes.

**Offline re-editions:** To preserve an earlier export, use a *different empty destination outside the public Git namespace* for each new revision (for example, `offline-portfolio-v1/` then `offline-portfolio-v2/` in a separately reviewed local folder). Re-run preview after editing a source artifact and explicitly approve export using its **new** digest. The old directory is immutable: reusing it fails, and the previous digest cannot approve changed content. These folders are local, unpublished review candidates, **not** a supported revision layout under `Courses/public/<uuid>/`. Publishing multiple revisions in Git requires a separately approved schema/path/guard design under ADR-0002; do not add version subfolders to the existing public namespace and assume the Git index guard accepts them.

Current limits: 32 listed source artifacts, 256 KiB per file, approximately 1 MiB total; unsupported binaries, hidden/config files, paths with traversal, symlinks, reserved Windows names, suspicious credentials and many private paths fail closed. No scanner can detect every private detail or license issue.

## Git release safety (user-controlled)

The root `.gitignore` excludes canonical private course folders but makes `Courses/public/<uuid>/` visible to Git. The index checker reads **staged Git blobs**, not potentially different working-directory copies. Do not `git add -A` for this workflow.

1. Install or upgrade the repository's Learnprint pre-commit hook after verifying its source:
   `python scripts/install.py --target opencode --self --hooks --approve`.
   It only upgrades an exact known legacy Learnprint hook; it refuses unrelated/custom hooks. If the host prevents hook installation, **do not publish until equivalent verification is installed**.
2. Stage only the exact, approved public snapshot files, explicitly by path, including `PUBLICATION.json`. Do not stage canonical source-course files or other private records.
3. Run `python scripts/learnprint_publish_guard.py --repo .`. Any tracked private course data, unexpected indexed file, modified hash, or unknown publication manifest blocks the check.
4. Inspect the staged diff and Git history before committing; remote push/PR is a **separate user-approved operation**. Neither a local hook nor GitHub secret scanning provides absolute privacy protection.

### Keep a course private

Leave `visibility` set to `private`, and do not export. If there is already a public snapshot, add this specific line at the **end** of the repository root `.gitignore`:

```gitignore
/Courses/public/YOUR-UUID/
```

This excludes untracked files from future staging. If a snapshot is **already tracked**, `.gitignore` does not untrack it: a separately reviewed `git rm --cached -r` operation and a commit are required to stop tracking, and prior pushes/history/forks may still expose it. Do not delete the canonical private course or its original evidence.

## Verification, scope, and remaining gates

- Engineering tests: `pytest -q`, including disposable Git-index/hook tests.
- Build package integrity: `python scripts/check_package.py`.
- Local index check: `python scripts/learnprint_publish_guard.py --repo .`.
- CI: multi-platform Python 3.9/3.12 suite plus publication-index guard on push/PR.
- Human: real learner UAT for teaching, creating a genuine hands-on artifact, comparing public preview, and choosing private/public correctly. This is **NOT VERIFIED** until performed.
- Security: no blind publishing, no silent file copy of private records, no remote network operation from the CLI.

References: [Git ignore behavior](https://git-scm.com/docs/gitignore), [GitHub history cleanup caveats](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [Open Badges 3.0](https://standards.1edtech.org/open-badges/specifications/standards/v3p0).
