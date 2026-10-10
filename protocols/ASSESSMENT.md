# Learnprint Assessment Protocol v1 — bounded, evidence-gated

**Purpose:** make a learner-specific *operating profile* and standalone skill from observable evidence, not infer innate learning types.

## Start
Ask for learning goal, practical environment, existing knowledge and an example of a past successful and difficult learning experience. Ask ONE question at a time; do not retest an already established fact. Record verbatim user answers in private evidence notes, not the public repo.

## Assessment blocks
1. **Goal/constraints (≤2 exchanges):** concrete capability and environment; identify language/accessibility needs and time budget. If enough info present, skip.
2. **Prior-knowledge probe (≤3 tasks):** explain a known concept, solve a small novel variant, name unknowns and confidence. Mark prior knowledge by *topic*, not person globally.
3. **Model-building probe (≤2 tasks):** a tightly specified unfamiliar mechanism. Test purpose, terms, conditions and causal explanation. Only correct after recording initial attempt.
4. **Instruction-comparison (optional; ≤4 tasks across two matched pairs):** use two comparable micro-concepts with measured prior knowledge, counterbalance teaching order (AB then BA), equal information/time and equivalent transfer questions. If matching fails, label `inconclusive` rather than nominate a winning format. Compare performance, not just learner preference.
5. **Performance and calibration (≤2 tasks):** independent application + novel transfer. Record help level and learner confidence when useful. Delayed retrieval is scheduled; it does not block profile creation.

**Task budget:** max **12 substantive learner responses** across blocks, with ≤2 replacements if a prompt is objectively ambiguous or invalid. Total maximum 14. A response containing multiple subanswers counts once but must not hide multiple unrelated questions. If no meaningful information remains or learner wants to stop, stop immediately. Never prolong indefinitely to force a conclusion.

## Scoring rubric (pre-register for each item)
Each test has 4 separate observations, scored `0` incorrect/absent, `1` partial/assisted, `2` independent/correct; `unknown` if unscorable. Dimensions: `concept`, `mechanism`, `application`, `transfer`. Record exact observed answer and rubric anchors. Do not sum unknown as zero. Track `help_level`: `none`, `hint`, `worked_example`, `solution`. Any hinted answer cannot prove independent transfer.

## Explicit stop rule
Stop when (a) a real learner goal and constraints are known, (b) at least 2 different task types provide grounded observations on strengths/gaps, (c) a conservative teaching plan is actionable; OR the max task budget is reached, whichever comes first. The profile's `evidence_quality` is `strong|moderate|limited` based on breadth and contamination risk; `strong` never means optimal style scientifically proven. Unobserved aspects remain `unknown`.

## Profile generation
- Summary of **observed** behavior, **reported preferences**, **inferences/hypotheses**, each distinguished.
- Each claim has at least one `evidence_id` pointing to retained learner answer/task feedback. Do not invent IDs.
- Produce specific tunable instructional defaults: relevant prior-knowledge probe, glossary before novel terms, goal/constraints, close-to-experience analogy **with limitations**, diagram selected by causal/state/prerequisite structure, worked example and hands-on/production, fade hints, transfer/retention.
- The profile is a starting setting, not a universal treatment. Update from learner performance for every topic.
- Persist generated personal skill **locally**, only after learner approves writing. Leave founder template unmodified. No auto-push, no global filesystem mutation.

## Failure handling
- If the learner misunderstands a question, inspect prompt ambiguity first; rewrite *one* unclear task and invalidate the old result.
- If strong performance occurs only after explanation, record as learning gain, not baseline.
- If unavailable browsing/tools, state the limitation; never claim verified research that did not occur.
- If assessment cannot achieve sufficient evidence, output a provisional profile and explicit unknowns; do not claim a uniquely proven best method.
