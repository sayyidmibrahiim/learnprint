# Learnprint course routing

## Order of operations for "Belajar: <topic>"
1. `course resolve --query "<topic>"` — found / ambiguous / not_found.
2. found → load state + HANDOFF + profile, resume.
3. ambiguous → ask the user to pick (list candidates, never guess).
4. not_found → classify with FULL context (Step 3.2b: subject ABOUT vs
   language medium vs capability outcome; conversation language is not the
   subject), then `course create` with `--approve`.

## Classification guidance (guidance, not enforcement)
- Prefer reusing an existing course or category over creating.
- "vocabulary DevOps" is Technology, not Languages. "grammar Python" is
  Technology, not Languages. "grammar bahasa Indonesia" and "grammar bahasa
  Jepang" are separate branches.
- A typo ("Grammer") is never silently corrected: the gate returns
  candidates, the agent reuses, registers an alias, or asks.
- Narrow needs inside an existing course's domain become MODULES of that
  course, not new courses. Wording variation alone never justifies a course.

## Deterministic guarantees (enforced by script, not by prompt)
- `course_id` is an immutable UUIDv4; rename/move never break evidence.
- Matching is exact normalized/alias only; duplicates and alias collisions
  are refused with precise errors.
- New category segments need `--confirm-new-segment`; new top-level roots
  need `--approve-new-category` plus user confirmation.
