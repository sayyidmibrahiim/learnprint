# Security policy

Learnprint is a local, standard-library Python toolkit. It reads and writes a
private `Courses/` workspace and can install an optional Git pre-commit hook.
It does not run a server and does not send learner data anywhere.

## Supported versions

| Version | Supported |
| --- | --- |
| `main` and the current release candidate branch | Yes |
| CPython 3.11 to 3.15 | Yes, tested in CI on Ubuntu, Windows and macOS |
| CPython 3.9 and 3.10 | No. End of life; source-grammar compatibility is best effort only |
| Older commits and tags | No |

## Reporting a vulnerability

Report privately through GitHub Security Advisories on this repository
("Security" tab, "Report a vulnerability"). Do not open a public issue for a
vulnerability and do not include real learner records, private course files,
assessment transcripts, tokens or absolute personal paths.

Include the affected command or file, the exact version or commit, a minimal
reproduction with synthetic data, and the impact you observed. We aim to
acknowledge a report within seven days. This is a volunteer project, so no
bounty or response guarantee is offered.

## Security-relevant behavior you should know

- **The installer never replaces an existing `.git/hooks/pre-commit`.** It
  writes a new hook only when the path is proven empty. A pre-existing hook,
  including an older Learnprint hook, must be inspected, archived and replaced
  manually by the owner. This is a deliberate fail-closed decision after
  cross-platform link-swap races; see `docs/research/2026-10-23-production-release-gates.md`.
- **Nothing is published automatically.** Portfolio export is local, opt-in,
  per-course and consent-gated. Staging, commit, push and publication are
  separate reviewed actions. `scripts/learnprint_publish_guard.py` inspects the
  Git index, but a scanner is not a confidentiality proof: Git history, forks
  and pull-request refs may retain content that was once pushed.
- **Learner content is data, not instructions.** Documents, web pages and
  pasted text are treated as untrusted input. The CLI never grades by itself
  and never invents evidence.
- **No dependency-supply-chain surface beyond the standard library.** CI uses
  only GitHub-maintained actions pinned to immutable commit SHAs.

## Known limitations

No independent adversarial security review has been completed. Automated tests
cover path traversal, symlink and reparse handling, private-file staging,
malformed manifests and hook races, but they are not a substitute for external
review. Portable path APIs cannot prove complete prevention of hostile
same-user concurrent directory swaps.
