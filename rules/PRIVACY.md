# Learnprint privacy and Git policy

## Universal publication eligibility, selective consent

All course subjects and sizes can be *considered* for a future portfolio. The default is **eligible for learner choice**, NOT publicly visible, Git-tracked, or pushed automatically. The learner must choose each specific course, choose each shareable hands-on artifact, inspect the exact derived preview, explicitly authorize local export and independently authorize GitHub push. Courses they do not select remain private. No course or source data is automatically sent over the network.

## Canonical learner data stays private

- The canonical `Courses/<category>/<course>/` folders, `Courses/.learnprint/`, learner profiles, raw answers, progress/event ledger, private method receipts, tutor notes and backups are ignored and **must not** be committed or pushed.
- A curated, explicitly approved copy of selected learning work may be staged under `Courses/public/<canonical-course-uuid>/`. This is a derived snapshot, not the canonical state, and is not an accredited certificate.
- A course without approved public export remains private. A manifest with `visibility: private` is not exportable.
- Generated personal learner skills remain ignored in all supported host discovery paths.

## Git defense in depth

- Root `.gitignore` ignores all of `Courses/*` except the `Courses/public/` publication entry point. The public snapshot directory is **not** permission to publish arbitrary files.
- All Git-indexed Courses/ paths must pass `scripts/learnprint_publish_guard.py`: only validated UUID-scoped public snapshots whose hashes match `PUBLICATION.json` are allowed. Force-added canonical learner records and personal skills are rejected.
- Install or upgrade the local pre-commit hook with `python scripts/install.py --target opencode --self --hooks --approve`. The installer refuses unknown existing hooks; do not silently override collaborator protections.
- CI runs the index guard on every push/PR. Local hooks can be bypassed, GitHub secret scanning cannot detect every credential, and Git history/third-party clones can preserve removed content.
- For an unpublished/private snapshot, add `/Courses/public/<uuid>/` to the **end** of the root .gitignore. If already tracked, ignoring it does not untrack it: removal from the index, Git history and any remotes is a separate, user-reviewed operation.
- Never use `git add -f` on real learner data. Review exact staged paths/content before any manual commit. Publishing to a remote always requires separate explicit user approval.

## Boundary of authorization

- Standing consent for ordinary study writes never grants consent to share, publish, commit, push, delete learner data, install global skills, or use external systems.
- Portfolio-preview is read-only. Portfolio-export requires an explicit preview digest and separate `--approve`, but that CLI flag is not independent evidence the user consented in chat.
- Never copy a full original course tree to a publication folder. Keep a human final review for real personal data, licenses and authorship because heuristic scans cannot prove safety.
- Do not present AI-graded, learner-reported or Git-hosted work as independently accredited proof of mastery. Document basis and limitations.

References: [ADR-0002](../docs/adr/0002-selective-course-portfolio-publication.md), [Git ignore](https://git-scm.com/docs/gitignore), [GitHub sensitive-data removal](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), [OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
