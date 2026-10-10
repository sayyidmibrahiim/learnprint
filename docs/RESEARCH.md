# Research and evidence ledger

Review date: 2026-10-10. Summaries are design rationales, not proof that Learnprint outperforms alternatives.

| Claim guiding design | Evidence | Implementation | Caveat |
|---|---|---|---|
| Matching fixed visual/auditory learning-style labels lacks adequate scientific support | Pashler et al., *Learning Styles: Concepts and Evidence* (2008), https://pubmed.ncbi.nlm.nih.gov/26162104/ | Avoid fixed learner types; ask what concretely helps and measure performance | Individual preferences are still legitimate UX requirements. |
| Prior knowledge and mental models influence learning | National Academies, *How People Learn II* (2018), https://www.nationalacademies.org/read/24783 | Short per-topic diagnostic and dependency map | Learner profile from prior conversation is not a substitute for topic-level pretest. |
| Novices often benefit from more instructional assistance; expertise changes optimal scaffolding | 2025 meta-analysis, https://doi.org/10.1016/j.learninstruc.2025.102142 | Adaptive support, reduce worked examples only after demonstrated application | Moderated by learner group and domain, not a universal rule. |
| Retrieval testing and distributed practice generally support retention | Dunlosky et al., *Improving Students' Learning With Effective Learning Techniques* (2013), https://doi.org/10.1177/1529100612453266 | Spaced retrieval is default; new items, corrective feedback, review queue | Repeated reading and arbitrary calendar intervals are not sufficient. |
| Self-explanation can support conceptual understanding | Chi et al. 1989, https://doi.org/10.1207/s15516709cog1302_1 | Ask why a mechanism produces an outcome; require independent examples | Quality of explanation and prerequisite knowledge matter. |
| Useful analogies highlight structural relations, but can mislead when correspondence is oversimplified | Gentner 1983, https://doi.org/10.1207/s15516709cog0702_1 | Explicit analogy-to-reality mapping and limits | Analogy preference is self-reported; not proof of faster learning. |
| Evaluating skills needs observed test cases, not good-looking prompts | OpenAI developer guidance, https://developers.openai.com/blog/eval-skills | Test fixtures, schema guards, human review of content | Static tests don't verify real models or personal learning outcomes. |

## Evidence policy
1. Facts about the world require an attributed, relevant source (when available), not an unverified confident assertion.
2. Facts about a learner require their actual answer/observed task outcome, time and origin; self-report is labeled `reported`, not converted to measured mastery.
3. When tools are unavailable, state what was **not verified** and rely on conservative, stable knowledge with uncertainty.
4. Distinguish **source quote**, **assistant inference**, and **grading decision** in different fields.
5. Never convert a one-time correct answer into a global numerical “100% mastered” claim.
6. For disputed/up-to-date topics use official sources and at least one cross-check where practical; stop with `unverified` if unable.
7. Assessments are educational observations, not IQ, neurology, attention-disorder, or clinical diagnoses.
