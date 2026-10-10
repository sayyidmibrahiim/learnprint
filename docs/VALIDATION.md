# Validation and acceptance criteria

**This release is a functional starter, not a clinically validated assessment instrument, proven optimal learning method or cross-model-equal AI service.** The founder assessment is a single-person informal conversational sample, with task-order confounds and possible teaching leakage.

## Structural automated acceptance gates
- Two skill directories have valid `SKILL.md` and frontmatter, each <=8,000 characters.
- Founder default profile links every claim to evidence IDs, including reported vs observed separation.
- Empty local workspace cannot claim achievement (unknown means unknown).
- AI-only or synthetic grades cannot become confirmed mastery under strict report mode.
- Independent application + novel transfer can count toward immediate demonstrated coverage, while delayed result is required for maintained.
- Personal skill generation refuses unassessed/inadequate evidence and requires `--approve`; no file overwrite.
- Installer refuses existing skill directories and requires explicit `--approve` to mutate a project.

## Behavioral checks still required in live hosts
1. New learner (no experience): initial goal/prior knowledge, bounded test, evidence-linked profile, no invented diagnosis.
2. Intermediate learner (`in/on/at`): skip proven rules, identify phrasing/spontaneous production gap, meaningful diagram and syllabus.
3. Broad topic (DevOps): prerequisite DAG, staged units, sources, one hands-on task per unit, evidence gates.
4. Unfamiliar jargon: define before testing, close analogy with mapping and limitations.
5. Conflicting/dated sources: honest `unverified`, no fabrication; verified claims explicitly cited.
6. User declines filesystem: prompt-only fallback and copyable Learning State; no false claim of saved files.
7. No network: no false claim of browsing.
8. Two different models: same evidence schema and stop conditions, but compare accuracy separately (never assume identical output).

## Honest criteria
Passing automated unit tests means **file contract and calculations work** in tested cases. It does NOT mean an LLM will obey every instruction, that all cited claims are true, or that this is the best possible personal learning method. Complete a bounded human review of live sessions before declaring compatibility with each client.

## Founder assessment summary
- Repeated observation: asks for reasons behind constraints, uses real experience, improves after concrete/familiar analogies and precise feedback.
- Reported preference: functional diagrams and plain analogies.
- Controlled superiority of any one teaching order: **not established**.
- Current English issue in sample: time/place prepositions often correct, unnatural phrasing persists.
- Delayed multi-day retention of sample: **not established**.
