# Learnprint privacy and git policy

## Default: private
- The entire `Courses/` tree is gitignored and never committed, pushed, or
  force-added (`git add -f` on learner data is forbidden).
- Generated personal skills live in gitignored paths only.
- Raw learner answers stay in `events.jsonl`; skill artifacts carry the
  profile and protocols, never raw answers.

## Boundaries
- No learning workflow authorizes publishing, global installs, evidence
  deletion, writes outside `Courses/`, destructive git, or network access.
- Never upload learning histories, identifiers, tokens, or private paths.

## Defense in depth (optional)
- Install the pre-commit hook (`scripts/install.py --hooks --approve`) to
  reject staged files under `Courses/` or personal-skill paths.
- `.gitignore` is a convention, not a security boundary; the hook and these
  instructions back it up. Host permissions remain authoritative.
