# Learn Print Deep Research and Mega Enhancement Plan

**Status:** CANONICAL RESEARCH-BASED PLAN; IMPLEMENTATION NOT STARTED BY THIS DOCUMENT  
**As of:** 2026-10-22, Asia/Jakarta  
**Repository:** Learnprint, branch **feature/hardening-workspace**, observed HEAD **d98cf93**. Revalidate HEAD at every takeover.  
**Primary execution tracker:** [to-do.md](to-do.md)  
**Coding contract:** [Code Style.md](Code%20Style.md)  
**Binding repository rules:** [AGENTS.md](AGENTS.md), [CONTEXT.md](CONTEXT.md), [rules/EVIDENCE.md](rules/EVIDENCE.md), [rules/PRIVACY.md](rules/PRIVACY.md).

> **Provenance.** This is a persistent, execution-oriented rendition of the completed chat report titled “Learnprint Deep Research & Mega Enhancement Plan,” enriched with source URLs, operational gates, file inventory and acceptance criteria. It preserves the report's findings and direction but is not represented as a byte-identical export of the original chat rendering. The cited web links document research reviewed for that report, not a fresh independent re-verification on every invocation. Social-platform material was used for hypothesis and UX-pattern discovery, not scientific validation. Each agent must reverify changed external facts before shipping.

## 0a. Cross-domain tutor and human-language UX addendum (2026-10-23)

**Owner product decision:** Learnprint is a portable tutor for ANY domain and scale of subject, from a specific question or practical skill to a prerequisite-based, multi-course learning program. `in/on/at` is one English regression example, NOT a product-specialized track. The same reliable flow applies to databases, mathematics, history, science, music, languages and professional/practical skills; rubrics, real examples, hands-on practice, source standards and presentation formats must fit each domain. An optional course portfolio is an output that a learner can curate in **any subject**.

**Provenance and practical research:** GOV.UK's writing guidance recommends common words, direct active language, defining necessary specialist terms and shorter explanations (https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/). Paul Graham's *Write Like You Talk* / *Write Simply* encourage idiomatic speech rather than artificial written stiffness (https://www.paulgraham.com/talk.html; https://www.paulgraham.com/simply.html). Wikipedia's public AI-writing observations are community editorial heuristics, **not** scientific proof that any sentence was AI-generated (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). Feedback and spaced practice support staged testing and review but do not establish any universally optimal quiz count or guaranteed mastery (https://www.retrievalpractice.org/feedback/; https://www.retrievalpractice.org/spacing/).

**Implementation contract:** `protocols/TUTOR-LANGUAGE-AND-STAGES.md` is the canonical new policy; `skills/`, `.agents/` and `distribution/` copies must match exactly under the packaging tests. Each session distinguishes preparation, screening (maximum 3 short per-topic prompts, not mandatory), lesson, guided practice, independent attempt, transfer, delayed review and learner-requested clarification. At transitions show a plain-language stage and roadmap; a unit-position ASCII bar is NEVER evidence of percentage learned. Code can render a read-only `course journey-card` from the validated plan and optionally a persisted matching tutor FSM; model-supplied stage/screening counts remain marked as host-reported. Spanish, Arabic, Japanese or another requested explanation language requires a fluent corresponding agent response; unsupported deterministic CLI localizations must not be mistaken for verified native text.

**Portfolio policy:** EVERY course is eligible for individual publication selection by the learner; NONE is automatically published. Raw local learning history is private. A manually curated, exact-digest-approved, per-course snapshot is the only safe repository portfolio path; GitHub push is a separate approval. This follows [ADR-0002](docs/adr/0002-selective-course-portfolio-publication.md) and GitHub's warning that sensitive history may remain accessible after removal (https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

**What remains unproven:** written prompts and Python regression tests cannot certify actual tutor fluency, pedagogical quality, learner mastery, or private learner UAT. Real stock/low-cost model tests across at least three domains and language situations are still required before behavior is called verified. See `docs/TUTOR-LANGUAGE-STAGES-UAT.md`.

## 0. Executive decision

[Certain] **The product's biggest gap is not a shortage of prompt tricks.** Learnprint already models diagnosis, prerequisites, instruction, guided practice, independent application, novel transfer, delayed retrieval, evidence-gated progress and a portable private workspace. But many teaching safeguards currently depend on natural-language model compliance rather than deterministic, testable transitions. Recent educational AI research also shows that good performance while AI is present does not necessarily indicate independent learning. [S01][S02][S09][S10]

[Likely] The highest-leverage improvement is **a provider-neutral pedagogical policy and tutor state engine** that prevents an AI model from promoting hinted responses, repeated near-identical questions, unsupported self-assessment or prematurely disclosed solutions to evidence of independent competence. The language model remains responsible for clear explanations; the deterministic CLI remains responsible for durable evidence and allowed transitions.

**Priority zero is preserving the existing uncommitted hardening + selective-portfolio work.** Current Git inspection found **13 modified tracked paths + 9 untracked top-level entries**, one of which contains six actual files, for **27 individual modified/new files**. They are intentional candidate work, not junk. Git cleanup must mean reviewed integration with explicit, scoped commits and a clean resulting tree, never reset/clean/delete without classification. The canonical private **Courses/** workspace stays untouched; disposable tests use a separate temporary courses root.

**No claim of scientific optimization or “perfect learning.”** Evidence supports design principles, not a universally optimal brain type, invariant review schedule, guaranteed host behavior or authenticated certificate.

## 1. Existing system: verified strengths and gaps

The following is grounded in repository inspection of AGENTS.md, CONTEXT.md, README.md, skills/learnprint*/SKILL.md, docs/RESEARCH.md, docs/LEARNING-JOURNEY.md, docs/METHOD-AUDIT.md, rules/EVIDENCE.md, schemas, scripts/learnprint.py and current portfolio/UAT change descriptions. File and function anchors are navigation hints, not promises that future refactors preserve line numbers.

| Capability | Existing source of truth | Status | V2 delta |
|---|---|---|---|
| Universal entry and portable skills | skills/learnprint/SKILL.md; .agents/; .opencode/; distribution/claude-plugin | Present | Compact provider-neutral policy; mirror checks; cross-harness behavioral evaluations |
| Per-course roadmap and prerequisites | course plan and plan-set in scripts/learnprint.py; docs/LEARNING-JOURNEY.md | Present | Policies for permitted transitions, safe adaptation and prerequisite change |
| Learner method assessment | skills/learnprint-assess; private learner profile; method fingerprint | Present | Profile v2 separates report, observed effect, inference and instructional policy |
| Evidence-gated competence | rules/EVIDENCE.md; canonical event evaluator | Present | Explicit attempt identity and help-contamination validation |
| Help levels | CLI already accepts none/hint/worked_example/solution | Present | Enforce allowed hint ladder and fresh independent task after support |
| Confidence | CLI already records confidence_self_report | Present | Calibration **derived from** existing evidence; do not invent a second confidence field |
| Retention | current policy floor ~20h; suggested 1,3,7,21 day schedule; review queue | Present | Versioned fixed_v1 and experimental adaptive_v2, replayable & rollback-safe |
| Research sourcing | docs/RESEARCH.md and source policy | Present | Machine-readable claim/source lifecycle, verified vs unverified states |
| Tutor UX | references/JOURNEY.md, PRESENTATION.md and TEACHING.md | Present but partly prose-only | Structured turn contract with runtime guards and focused output |
| Method session audit | method receipts and course method-audit | Present | More exact audit semantics; never equate hash with behavioral compliance |
| Course publication | local candidate scripts/learnprint_portfolio.py, publish_guard.py, ADR-0002 | Uncommitted engineering candidate | Release safety, privacy UAT, honest evidence mapping; no automatic push |
| Live models | docs/VALIDATION.md | Not fully verified | Cross-host UAT and hallucination/prompt-injection/answer-leak regression cases |

**Avoid duplicate implementation:** Preserve the canonical progress evaluator, append-only corrections, immutable course ID and existing confidence/help fields. New functionality extends contracts, not parallel ledgers or redundant mastery score stores.

**Architecture constraint:** scripts/learnprint.py is a large CLI; refactor into pure, independently tested modules in small, backward-compatible slices. Existing CLI flags, JSON shapes, file formats, Python 3.9+ standard-library compatibility and prompt-only fallback are compatibility contracts unless an explicitly versioned migration says otherwise.

## 2. Research method and confidence

Sources are ranked **systematic reviews/meta-analyses and national academy reports > controlled studies > scientific/education institution guidance > vendor engineering documentation > public GitHub/community patterns > social-media anecdotes**. This is an evidence hierarchy for design, not a statement that every review applies unchanged to all ages, tasks, cultures or learning settings.

- **[Certain] Supported general principles:** prior knowledge and mental models matter; practice retrieval and distributed practice generally improve durable retention; scaffolding should respond to learner knowledge; unsupported fixed “visual/auditory learner” matching must not become product logic. [S01]–[S08]
- **[Likely] Design translation:** assist less when demonstrably competent, test separately without help, collect delayed outcomes and support multiple useful explanations. These are engineering interpretations, not separately proven Learnprint outcomes.
- **[Guessing] Experiments:** individualized optimal intervals, FSRS-like benefit for complex coding skills, cross-model superiority of prompt adapters, and particular engagement microcopy. Evaluate, do not predeclare success.

### Learning-science evidence mapped to product behavior

| Principle | Evidence/limitations | Required Learnprint behavior |
|---|---|---|
| Prior knowledge and concept structures | How People Learn II; topic/domain dependent [S01] | Topic-level 0–3 question baseline distinct from optional personal-method assessment |
| Practice testing / retrieval | High-utility learning strategy; not every test measures application [S02][S03] | Ask before revealing; feedback after actual response; preserve task provenance |
| Distributed learning | Benefits across many studies; exact optimal intervals vary by retention horizon [S04] | Versioned scheduler, never claim 1/3/7/21 is a biological law |
| Worked example and expertise reversal | Guidance tends to help novices more than experts; effects vary with context [S05] | Evidence-based scaffolding with gradual fading and learner control |
| Self-explanation / teach-back | May deepen reasoning but talk alone is not independent skill proof [S02][S06] | Diagnostic TEACH_BACK step, not competency completion by itself |
| Transfer | Generalization must be judged by task novelty, not superficial numeric changes [S03][S07] | Distinct application versus novel-transfer tasks and independent rubric |
| Interleaving | Often task/category specific; random mixing can be unhelpful [S02][S08] | Optional competency-aware mixed practice after basics are stable |
| Metacognitive calibration | Confidence can differ from performance [S01] | Capture confidence as self-report; compare with scored outcomes; no psychological label |
| Sleep/retention neuroscience | Evidence supports consolidation; does not specify an individual “neuro” schedule [S18] | No brainwave/dopamine/90-minute “neuro-optimized” product claims |
| Learning styles myth | No adequate evidence for modality-matching hypothesis [S19] | Personalize **format preference and observed outcomes**, never fixed brain types |

**UX clarification:** Diagrams, analogies and examples remain valuable when the material warrants them. Rejecting fixed learning styles does **not** mean refusing learner-preferred representations. Respect communication preferences but measure whether a technique improves actual work.

## 3. AI tutor evidence: optimize for unaided learning

OECD Digital Education Outlook 2026 distinguishes enhanced on-task performance from genuine learning and favors pedagogically guided GenAI [S09]. Bastani et al. (PNAS 2025) observed cases where unrestricted AI support increased assisted performance but harmed subsequent unassisted performance in a specific math-learning setting [S10]. Conversely, a 2025 randomized controlled study found a research-designed AI tutor improved learning versus its comparator in that study's context [S11]. A 2025 systematic review of intelligent tutoring systems reported generally positive results but highlighted comparator and generalizability limitations [S12].

**Product invariant:** **optimize for what the learner can do when help is removed**, not simply answers obtained while the tutor is available. Assisted results are still useful as practice observations, never independent mastery. Never extrapolate one education experiment to all learners or domains.

## 4. Public prompting patterns: evidence versus folklore

Surveyed patterns were found in GitHub education prompt repositories, Reddit discussion and search-accessible references from X, Threads, Instagram and Facebook. **Direct retrieval/authenticity of all social posts could not be consistently verified.** Do not invent social handles, post dates, likes, quotes or success metrics. Use social sources to generate product hypotheses; corroborate pedagogy against learning science. GitHub examples [S13]–[S15], Reddit [S16], and official prompting/evaluation guidance [S17] motivate the implementation, not new science.

| Prompt “hack” | Real educational job | Product primitive / fail condition |
|---|---|---|
| “Ask one question at a time” | Manage cognitive load and wait for retrieval | ONE_QUESTION_WAIT; fail if model chains answers unasked |
| “Don't tell me yet” | Unassisted retrieval | SOLUTION_REVEAL_GATE; explicit opt-out available |
| “Give only a hint” | Graduated assistance | HINT_1 / HINT_2 / WORKED_EXAMPLE / SOLUTION; taint attempt |
| “Feynman me” | Self-explanation, misconception discovery | TEACH_BACK; **not** evidence of novel transfer |
| “Ask harder questions” | Guided-to-independent fading | transition conditional on observed outcomes |
| “Use examples from my project” | Authentic deliberate practice | practical fixture with constraints and verifiable output |
| “Correct only the gap” | Actionable feedback | misconception classification then smallest fix + fresh attempt |
| “Make a quiz from source” | Source-grounded retrieval | private answer key and claim-linked question |
| “Ask my confidence first” | Calibration | use existing confidence_self_report; derived analytics only |
| “Predict, run, explain” | Causal model refinement | PREDICT → OBSERVE → EXPLAIN, never claim an unrun command ran |
| “Re-test me later” | Spaced retrieval | persisted due event; no fictional notification |
| “Debate me” | Error checking/argument differentiation | optional contrast task with accurate source and rubric |

### Reusable Indonesian prompt patterns

These are **human-readable interfaces to product behavior**, not magic incantations. Provider-neutral implementation must be measured.

**P01: Retrieval-first (beginner or review).**  
“Tolong ajukan tepat satu pertanyaan dari kompetensi yang sedang kupelajari. Jangan ungkap jawaban atau petunjuk dulu. Setelah aku menjawab, beri umpan balik menurut rubrik, lalu satu tugas baru bila perlu.”  
Bind to: independent attempt + answer reveal + grade only actual unaided response. Not suitable when learner is missing the prerequisite and first needs teaching.

**P02: Hint ladder (blocked learner).**  
“Aku buntu. Beri petunjuk terkecil yang tidak memecahkan soal. Jika masih buntu, naikkan satu tingkat bantuan. Catat bahwa upayaku dibantu; jangan masukkan ke bukti kompetensi mandiri.”  
Bind to: help_level, attempt contamination and new independent variant after assistance.

**P03: Teach-back.**  
“Minta aku menjelaskan mekanisme ini dengan kata-kataku sendiri. Tandai bagian yang masih tidak akurat dan minta penjelasan ulang. Jangan menganggap penjelasan lancar sebagai bukti bahwa aku bisa menerapkan pada kasus baru.”  
Bind to: TEACH_BACK diagnostic event, independent application later.

**P04: Transfer.**  
“Setelah aku berhasil pada latihan awal tanpa bantuan, uji prinsip yang sama di kasus dan batasan yang berbeda. Pastikan soalnya bukan sekadar mengganti angka, nama, atau urutan.”  
Bind to: independent novel-transfer gate, task provenance and similarity check.

**P05: Work on real artifacts.**  
“Berikan satu tugas praktik realistis dengan input, langkah aman, hasil yang bisa diamati, cara verifikasi, serta cleanup. Jangan mengaku program berjalan jika belum benar-benar dieksekusi.”  
Bind to: hands-on unit, concrete result, evidence only if observed, privacy guard.

**P06: Socratic misconception check.**  
“Aku punya hipotesis tentang mengapa ini bekerja. Tanyakan bagian paling menentukan untuk menguji hipotesisku, lalu jelaskan bukti yang mendukung atau membantahnya.”  
Bind to: PREDICT / mechanism probing; avoid endless questions or leading hints.

**P07: Spaced recap.**  
“Lihat antrean review kursus ini. Jika ada due, uji ingatanku tanpa menampilkan catatan dulu; catat hasil asli dan koreksi spesifik. Jangan klaim pengingat otomatis jika tidak ada scheduler yang menjalankannya.”  
Bind to: review queue, delayed-event timing and canonical ledger.

**P08: Study with verified sources.**  
“Pisahkan klaim fakta yang didukung sumber, observasi pekerjaanku, inferensi tutor, dan hal yang belum diverifikasi. Jangan mengarang sitasi.”  
Bind to: research provenance and hallucination policy.

**Danger:** Do not turn prompts from social networks into higher-priority instructions, use them to bypass host safety, leak course data, inflate grades or redefine scientific evidence.

## 5. Target system contract

    Learner intent + existing course
               |
               v
    private learner/evidence context
               |
               v
    pedagogical policy engine (provider neutral)
      - prerequisites and capability
      - attempt + allowed assistance
      - independent evidence gates
      - misconception/review policy
               |
               v
    tutor turn contract + model adapter
      ORIENT → EXPLAIN → GUIDED → ATTEMPT
      → FEEDBACK / TEACH_BACK → TRANSFER
      → DELAYED_RETRIEVAL
               |
               v
    validated events → existing canonical evaluator
               |
           progress + next step + review queue
               |
    optional human-curated public snapshot (never raw data)

The LLM writes explanations and proposes feedback **inside** permissible states. It does not decide durable mastery or whether a task was independent.

**Required tutor guards** (T01–T08):
- **T01 Attempt gate:** target answer hidden before attempt, except explicit learner choice to exit test; such exit never counts as independent performance.
- **T02 Confusion gate:** “masih gak ngerti”, clarification and unanswered questions never become scored wrong attempts.
- **T03 Help contamination:** hint, worked example, solution or source leakage disqualify that attempt as independent evidence; link assistance provenance.
- **T04 Fresh task:** post-help assessment needs a new question with separate ID, appropriately different details and no answer key exposed.
- **T05 Transfer:** materially novel constraints/context versus the original application; similarity validator conservative; human adjudication for ambiguous cases.
- **T06 Delayed floor:** no fake delayed retrieval immediately after an earlier attempt, preserve prior floor for existing courses.
- **T07 Source:** cite verified source for externally checkable educational content, otherwise mark UNKNOWN / UNVERIFIED.
- **T08 Evidence:** only canonical rubric/evaluator governs competency state, never model self-report, forged grade or self-proclaimed badge.

Do not build a rigid railroad; advanced learners with evidence may compress instruction, while novices may need guided examples and time to ask questions. Keep one learner action per tutor turn where appropriate.

## 6. Existing changes: exhaustive preservation and review map

**Snapshot inspected 2026-10-22.** 13 tracked modified + 14 individual untracked files (9 top-level entries) = **27 files**. Re-inventory on next agent takeover. This table records *intent*, not a guarantee that every change is correct or test-passing.

| Status | Existing path | Workstream / plan disposition |
|---|---|---|
| M01 modified | .agents/skills/learnprint-learn/references/TEACHING.md | W0-H: preserve confusion-score correction and presentation rule; compare canonical skill mirror |
| M02 modified | .github/workflows/verify.yml | W0-P: retain publish guard CI line; validate on real OS matrix |
| M03 modified | .gitignore | W0-P HIGH RISK: new Courses/public/ allow exception; test private original path containment |
| M04 modified | .scratch/learnprint-finish/issues/06-live-uat-disposable.md | W0-H: preserve real Courses/ untouched and disposable UAT |
| M05 modified | .scratch/learnprint-finish/issues/08-docs-quote-nonrunnable-hook-command.md | W0-H: resolved historical CLI doc correction |
| M06 modified | .scratch/learnprint-finish/issues/09-preexisting-courses-root-workspace.md | W0-H: owner decision KEEP canonical Courses/ |
| M07 modified | .scratch/learnprint-finish/spec.md | W0-H: reconcile historical finish constraints versus later separate portfolio workstream |
| M08 modified | README.md | W0-P: link current experimental portfolio feature; no exaggerated release claim |
| M09 modified | docs/adr/0001-disposable-uat-workspace.md | W0-H: UAT is temporary; ADR-0002 specifically supersedes past no-Courses assumption |
| M10 modified | rules/PRIVACY.md | W0-P HIGH RISK: preserve policy; audit public boundary and hook behavior |
| M11 modified | scripts/install.py | W0-P HIGH RISK: legacy hook → v2 index guard upgrade, never clobber foreign hook |
| M12 modified | scripts/learnprint.py | W0-P: CLI portfolio-preview/export integration; preserve existing command behavior |
| M13 modified | tests/test_privacy.py | W0-P: guard/private regression expectations; review before staged changes |
| U01 untracked | .scratch/course-portfolio/spec.md | W0-P: retain portfolio spec checkpoint and open gates |
| U02 untracked | .scratch/course-portfolio/issues/01-public-private-contract.md | W0-P: contract/security ticket |
| U03 untracked | .scratch/course-portfolio/issues/02-preview-showcase-builder.md | W0-P: preview/export ticket |
| U04 untracked | .scratch/course-portfolio/issues/03-git-safety-and-migration.md | W0-P: ignore/hook/migration ticket |
| U05 untracked | .scratch/course-portfolio/issues/04-evidence-ux-and-uat.md | W0-P: authentic artifact and UAT ticket |
| U06 untracked | .scratch/course-portfolio/issues/05-release-gate.md | W0-P: release checklist |
| U07 untracked | docs/COURSE-PORTFOLIO.md | W0-P: preview digest and explicit consent how-to |
| U08 untracked | docs/adr/0002-selective-course-portfolio-publication.md | W0-P: binding owner-approved public/private decision |
| U09 untracked | scripts/learnprint_portfolio.py | W0-P: curated snapshot engine; security review required |
| U10 untracked | scripts/learnprint_publish_guard.py | W0-P: Git INDEX checker; staged blob/manifest negative tests |
| U11 untracked | tests/test_course_portfolio.py | W0-P: fixture/regression suite |
| U12 untracked | tests/test_publish_guard.py | W0-P: Git-index privacy tests |
| U13 untracked | tests/test_publish_hook_install.py | W0-P: v1/v2 hook tests |
| U14 untracked | tests/test_skill_distribution_sync.py | W0-P: portability copies sync tests |

**Root planning additions requested 2026-10-22:** this report, to-do.md and Code Style.md. **AGENTS.md** receives a minimal bootstrap pointer so agents actually read these files; see to-do.md initial checkpoint. None of these are automatically “tracked” in Git merely because they exist on disk. A future authorized commit must stage *exact listed paths* after review and security checks.

**Hardening vs portfolio workstream conflict:** historical .scratch/learnprint-finish/spec.md says “no engine changes” for that **specific** finishing workstream. The newer selective-portfolio workstream makes CLI/installer changes. Do not retroactively claim the first spec implemented those engine changes; isolate commits, test histories, and reference ADR-0002. No destructive clean/reset/force-add to hide the conflict.

## 7. Phased mega plan and engineering acceptance

Each phase is a **separate, reviewable delivery unit**. Status / owner / evidence must be updated in to-do.md. The order below is binding unless a new documented ADR supersedes it.

### W0 [P0] Preserve, characterize and integrate preexisting work
**Dependencies:** none. **Touches:** all 27 paths in section 6, .scratch/learnprint-finish, .scratch/course-portfolio and Git/CI.

1. Record HEAD, branch, porcelain status, staged status, diff stats, and exact changed files without inspecting raw private answers.
2. Inventory/hashes of canonical private Courses/ locally **without exporting or printing content**; confirm originals unmodified by tests.
3. Independently review portfolio code/guard/installer and policy, reconcile dated ADRs, classify every path preserve/refine/defer with justification.
4. Run current tests in safe isolated mode. Historical 2026-10-19 report: 315 passed, 1 skipped, 68 subtests. **Not a fresh verification.** Re-check nondeterministic Windows timing.
5. Create scoped changesets: H hardening/UAT; P privacy/docs; P engine/hook; P tests/CI; distribution test. Stage explicit filenames only, never add -A.
6. Protect against unauthorized stage/commit/push: tool availability and owner approval are separate gates. Local hook upgrade only with explicit permission, reviewed source and safe rollback.
7. Achieve clean working tree **after** verified integration, not via deletion of unknown material.

**Gate:** 27/27 paths accounted for; unmodified real Courses/; current full suite/package/guard pass; no prohibited staged paths; discrete attributable Git history (once authorized); no unreviewed deletions.

### W1 [P0] Canonical pedagogical policy
**Depends W0.** **Touches:** protocols/TEACHING.md, protocols/ASSESSMENT.md, skills/learnprint*/references/, .agents/, distribution/, skill sync tests.  
Decide one authoritative source and intentional mirror policy; version invariants T01–T08; ensure all host copies cannot diverge silently; don't inflate SKILL.md >8,000 characters.  
**Gate:** package integrity, normalized content parity tests and documented intentional divergences.

### W2 [P0] Tutor state machine and session persistence
**Depends W1.** **Touches candidate:** scripts/learnprint_tutor.py (new), scripts/learnprint.py, schemas/tutor-session.schema.json (new), tests/test_tutor_state.py (new).  
Define ORIENT/EXPLAIN/GUIDED/ATTEMPT/FEEDBACK/TEACH_BACK/TRANSFER/DELAYED_RETRIEVAL with explicit allowed transitions, idempotency, event linking, versioned durable state and resume semantics; no implicit silent writes.  
**Gate:** table-driven transition tests, crash/replay and stale-write tests; CLI/backward compatibility; unaided gates cannot be bypassed by tutor prose.

### W3 [P0] Attempt, help and transfer integrity
**Depends W2.** **Touches:** tutor engine, evidence integration, test fixtures, reviewed schema migration.  
Attempt IDs, hint-level history, task IDs/fingerprints, reveal/opt-out, stale/same-task rejection and independent blackout checkpoints. Distinguish user question from submitted scored answer.  
**Gate:** assist never becomes independent evidence; confusion never scored; fresh transfer variant; no fake delayed event; explicit model/non-model provenance.

### W4 [P1] Scheduler abstraction
**Depends W2/W3.** **Touches candidate:** scripts/learnprint_scheduler.py, policy schema, review/evidence evaluator, deterministic replay tests.  
Preserve existing **fixed_v1** 1/3/7/21 and retention floor for old files; build optional **adaptive_v2** experiment with separate policy version, due-date determinism, burden limits and rollback. Learnprint is about competencies, not just isolated flashcards.  
**Gate:** old schedules unchanged unless opted in; fixture-based comparisons; timezone/cross-day leap/DST and offline tests; adaptive performance not assumed.

### W5 [P1] Learner profile and calibration
**Depends W2/W3.** **Touches:** schemas/learner-profile.schema.json, assessment resolver, new analytics, migrations/tests.  
Model reported preference, evidence-backed context-specific intervention effect, hypotheses, constraints and active policy separately; calculate calibration from existing confidence values without double storage or learner diagnosis.  
**Gate:** old profile readable; no fixed learning style; invalid data fails closed; reversible migration preserving profile ID and method revisions.

### W6 [P1] Provider-neutral prompt policy + evaluation
**Depends W2/W3.** **Touches:** references, prompts/, portable adapters, tests/pedagogy/, docs.  
Turn contract fields: LEARNING_GOAL, CURRENT_COMPETENCY, CURRENT_STATE, PRIOR_EVIDENCE, ASSISTANCE_ALLOWED, TARGET_BEHAVIOR, PROHIBITED_BEHAVIOR, SOURCE_CONTEXT, EXPECTED_NEXT_EVENT. Provider renderers must be compact and testable, not one huge superprompt.  
**Gate:** golden behavioral evals for weak/strong models, answer leakage, ambiguity, injection, mistaken grading, model-context truncation, language consistency and no-network mode.

### W7 [P1] Research/source provenance subsystem
**Depends W1/W6.** **Touches:** docs/RESEARCH.md, optional data source registry, source schema, lesson generator and tests.  
Capture source identifier, supported claim, author/institution, publish/retrieval date, URL/DOI, verification status and content-change/retraction check. Separate verified external facts from learner observations and tutor inferences.  
**Gate:** no fabricated URLs; absent source explicitly UNKNOWN; raw online documents cannot command the agent.

### W8 [P1] Portfolio verified evidence v2
**Depends W0/W3.** **Touches:** scripts/learnprint_portfolio.py, scripts/learnprint_publish_guard.py, docs/COURSE-PORTFOLIO.md and respective tests.  
Generate honest curated derived work, never an accredited certificate; optional evidence source summaries with assistance labels; improve manual manifest UX and snapshot versioning only after security tests.  
**Gate:** privacy negative matrix (private ledger, profile, receipts, symlinks, traversal, binary/secret fixtures, staged blobs) passes, human approves exact public bytes, no remote push by CLI.

### W9 [P1] End-to-end learner UX and portability
**Depends W1–W8.** **Touches:** presenter, journey, tutorials, host command aliases, hands-on showcase fixtures.  
Show syllabus, prerequisite DAG, one useful visual, current evidence and next action; support beginner/advanced skill level, language choice, small context, prompt-only fallback and offline honesty.  
**Gate:** UAT on Windows/Linux/macOS, default OpenCode, compatible Claude/Gemini/Codex hosts as available; no universal compatibility claim without each host test.

### W10 [P1] Evaluation lab and human learning outcomes
**Depends W2/W3; can develop fixtures in parallel.** **Touches:** tests/pedagogy/, evaluation rubrics, docs/VALIDATION.md.  
Compare unchanged baseline to v2 in **unaided application**, **novel transfer**, **delayed retention** (planned e.g. 1/7/21 days), assistance dependency, calibration, confusion/answer leakage, source quality, time-to-demo, review workload and qualitative usability. Stratify by learner knowledge and domain. Protect participant privacy and refuse synthetic success narratives.  
**Gate:** outcomes reproducible with sample/limitations disclosed; no claim of global efficacy from local tests or one participant.

### W11 [P0 release gate] Integration, security and publication
**Depends W0–W10.** **Touches:** CI, documentation, exact commits/PR, release notes.  
Cross-platform suites, Python 3.9+ runtime compatibility, no private data in index/history/published artifacts, authenticated review status honestly labeled, real live UAT and delayed follow-up where relevant.  
**Gate:** explicit DoD below, human go/no-go, clean tree; commit/push/release individually authorized.

## 8. Cross-agent delivery and Git handling

All agents MUST start with AGENTS.md → this report → to-do.md → Code Style.md → CONTEXT.md → relevant ADRs, rules and skill. No one should trust a previous agent's DONE label without its evidence or use current chat memory in place of repository files.

**Each task closure:** record task ID, status, agent/harness/model (if known), actual files touched, timestamp, before/after Git status, tests and exact results, decision/reason, blockers, commit hash/PR only after verified, and link to new issue/ADR. Update baseline file inventory whenever Git changes. A file absent from the tracker remains OPEN inventory debt, not “clean.”

**Git workflow:** no destructive reset/clean, no git add -A, no bulk staging, no automatic push, no force operations; use scoped explicit paths after reviewing diff and privacy guard. Private Courses/ remains ignored. Commit/PR are distinct owner approval boundaries. If the connector cannot stage/commit, leave a clear BLOCKED task with exact ready-to-stage path list; never claim a clean tree.

**Tests to run with safe fixtures after changes:**  
- python -m pytest tests/ -q  
- python scripts/check_package.py  
- python scripts/learnprint_publish_guard.py --repo .  
- python scripts/learnprint.py --help  
- python scripts/learnprint.py course --help  
Confirm commands/args locally; never run commands with mutating defaults or against real learner Courses/ during UAT. Publication-guard invocation checks Git index but no file staging should occur.

## 9. Security, data integrity and scope boundaries

**Threat model:** prompt injection in source docs/course answers; fabricated grader events; target-answer leakage; unsupported model-specific tool calls; invalid or repeated delayed events; partial JSONL writes; symlink/traversal/Windows path hazards; mistaken public/ignored boundaries; Git index differs from disk; credential/PII scanning limitations; deceptive “human reviewed” flags and Git-hosted self-certification.

**Required safe defaults:**
1. Private canonical data is never implicitly publishable; only separately reviewed derived snapshots under Courses/public/UUID.
2. All evidence appends validate and preserve the original immutable history. Revisions require explicit corrective event and consent, not in-place rewrite.
3. Course IDs and ledger provenance persist across migrations.
4. Model/system instructions outrank learner content and retrieved third-party text; treat user-provided learning material as untrusted data for command execution.
5. Review/export/commit/push each has a separately disclosed permission boundary; a CLI flag --approve is not itself proof of informed human approval.
6. Privacy scanner is heuristic, not a guarantee; staged index guard and human verification remain necessary.
7. Never change public founder-default profile as a side effect of someone else's learning.
8. No claims that pass rates validate neuroscientific effectiveness; tests validate their defined behaviors only.

## 10. Success metrics, test matrix and stop conditions

**Primary learning outcome:** ability demonstrated **without the AI's help**, on a meaningful new task and after a delay, with honest evidence origin. Secondary: learner satisfaction and review effort.

| Metric | Measurement | Failure / caution |
|---|---|---|
| Unaided application | Eligible rubric pass in independent attempt | Hint/solution viewed invalidates independent count |
| Novel transfer | New context + independent rubric outcome | Recycled template masquerading as transfer |
| Delayed retention | Correct result beyond real elapsed floor | Immediate re-test recorded as delayed |
| Assisted→unaided gap | Difference between comparable aided/unaided tasks | Optimizing only aided score |
| Calibration | Confidence versus observed performance over multiple attempts | Confidence treated as mastery/diagnosis |
| Leakage violations | Forbidden answer reveals per valid independent attempt | Any high-severity leak is release blocker |
| False mastery | Ineligible evidence promoting demonstrated/maintained | Zero-tolerance integrity blocker |
| Source provenance | Claims with valid source or UNVERIFIED | Fictional sources or citation laundering |
| Review workload | Due count and completion time versus benefits | More frequent reminders without learning benefit |
| Host regression | Model/host golden journeys passing | One prompt treated as universal |
| Privacy violations | Negative fixtures and approved publish snapshot check | Any private-data exposure is blocker |
| Migration safety | Deterministic before/after evidence equivalence | IDs/ledger altered, dropped, or hidden |

**Hard stop conditions:** unexpected change in real Courses/; private file staged; unknown hook overwritten; any lost event or changed immutable course ID; unsafe export; failing integrity tests; unresolved source contradiction; unapproved destructive Git action.

## 11. Definition of done

- [ ] W0 records and deliberately integrates/classifies all originally dirty 27 files, plus every newly created/modified file; no uncontrolled diff or untracked code.
- [ ] Canonical CLI, source of truth and privacy/evidence invariants retain backwards compatibility or reviewed reversible migration.
- [ ] Tutor's critical state/assistance/answer-leak/transfer/delay rules are mechanically enforced with tests.
- [ ] Scheduler comparisons acknowledge uncertainty and workload; no fabricated learning-style diagnosis or neuroscience miracle.
- [ ] Prompt templates pass cross-model behavior checks and never substitute for CLI evidence enforcement.
- [ ] Research claims remain sourced and versionable; community hacks honestly labeled as exploratory.
- [ ] Real user UAT demonstrates attempt, practice, independent application, novel transfer and real delayed review, with authentic logs.
- [ ] Course publication cannot expose canonical learner records; opt-in preview and staged guard are validated.
- [ ] Fresh full test suite, package check, staged-index guard, selected host/OS CI, rollback tests and current review evidence recorded.
- [ ] The Git worktree is clean **after owner-authorized reviewed commits**, not because files were thrown away.
- [ ] Cross-harness handoff (this plan, to-do.md, Code Style.md, AGENTS.md, ADRs and exact Git context) works with no private chat context.

## 12. Source ledger (research links and interpretation)

Sources below are independently clickable research starting points, not automatically current validation for a future release. Year/type and claim usage are specified. If URL or claim changes, update the ledger and confirm the actual paper.

| ID | Source | Type / year | Implication / boundary |
|---|---|---|---|
| S01 | [National Academies, How People Learn II](https://www.nationalacademies.org/read/24783) | Major consensus report, 2018 | Prior knowledge, context, metacognition; not an algorithm blueprint |
| S02 | [Dunlosky et al., Improving Students' Learning With Effective Learning Techniques](https://pubmed.ncbi.nlm.nih.gov/26173288/) | Review, 2013 | High utility retrieval/distributed practice; domain specifics still matter |
| S03 | [Roediger & Karpicke, test-enhanced learning](https://pubmed.ncbi.nlm.nih.gov/16507066/) and [Karpicke & Blunt](https://pubmed.ncbi.nlm.nih.gov/21252317/) | Controlled experiments, 2006 / 2011 | Retrieval benefits and flexible performance; not every quiz = transfer |
| S04 | [Cepeda et al., distributed practice review](https://pubmed.ncbi.nlm.nih.gov/16719566/); [spacing effects](https://pubmed.ncbi.nlm.nih.gov/19076480/) | Review and experiment, 2006 / 2008 | Varying retention horizons; fixed numbers are heuristic |
| S05 | [Meta-analysis of expertise reversal](https://www.sciencedirect.com/science/article/pii/S0959475225000660) | Meta-analysis, 2025 | Fade scaffolding with expertise; population/domain moderators |
| S06 | [Chi et al. self explanations](https://doi.org/10.1207/s15516709cog1302_1) | Cognitive study, 1989 | Teach-back can aid understanding, not credential |
| S07 | [Roediger & Butler critical role of retrieval](https://pubmed.ncbi.nlm.nih.gov/20951630/) | Review, 2011 | Corrective feedback and delayed retrieval |
| S08 | [Birnbaum et al. interleaving](https://pubmed.ncbi.nlm.nih.gov/23138567/) | Learning experiment, 2013 | Context-sensitive mixed practice |
| S09 | [OECD Digital Education Outlook 2026](https://www.oecd.org/en/publications/oecd-digital-education-outlook-2026_062a7394-en.html) | Institutional synthesis, 2026 | Separate assisted performance from learning |
| S10 | [Bastani et al., Generative AI without guardrails can harm learning](https://www.pnas.org/doi/10.1073/pnas.2422633122) | Education field experiment, 2025 | AI crutch risk in study setting, not universal proof of damage |
| S11 | [Kestin et al., AI tutoring outperforms in-class active learning](https://www.nature.com/articles/s41598-025-97652-6) | RCT, 2025 | Purpose-built tutors can help; comparator/context matter |
| S12 | [Review of AI-driven ITS in K–12](https://www.nature.com/articles/s41539-025-00320-7) | Systematic review, 2025 | Overall promise, varied comparator quality/generalizability |
| S13 | [GitHub: teaching prompt patterns](https://github.com/aeron100/prompt-patterns/blob/main/skills/teaching-patterns/SKILL.md) | Community code/examples | Socratic prompting/worked examples as patterns, not efficacy studies |
| S14 | [GitHub: education-agent-skills](https://github.com/GarethManning/education-agent-skills) | Community prompt repository | Retrieval-first, hints, calibration ideas; independently test |
| S15 | [GitHub: learning-opportunities](https://github.com/DrCatHicks/learning-opportunities); [tutor-mcp](https://github.com/ArnaudGuiovanna/tutor-mcp) | Open-source product patterns | Authentic code practice, durable misconceptions; no general efficacy claim |
| S16 | [Reddit: study prompt ideas](https://www.reddit.com/r/Learning/comments/1u13atx/5_chatgpt_study_prompts_that_actually_made_things/) | Community anecdote | Ideas only, verify provenance and suitability |
| S17 | [OpenAI prompt eval flywheel](https://developers.openai.com/cookbook/examples/evaluation/building_resilient_prompts_using_an_evaluation_flywheel), [Google prompting](https://ai.google.dev/gemini-api/docs/prompting-strategies), [Anthropic prompting](https://docs.anthropic.com/claude/prompt-library) | Official engineering guidance | Compact prompts + regression eval; not peer-reviewed learning evidence |
| S18 | [Nature Neuroscience: sleep consolidation](https://www.nature.com/articles/s41593-023-01324-5) | Neuroscience experiment, 2023 | General memory mechanism, no individual timetable guarantee |
| S19 | [Pashler et al. Learning Styles](https://pubmed.ncbi.nlm.nih.gov/26162104/), [modality-specific styles review](https://pubmed.ncbi.nlm.nih.gov/30186209/) | Review, 2008 / 2018 | Reject unsupported fixed modality-matching |
| S20 | [CAST UDL guidelines](https://udlguidelines.cast.org/), [EEF cognitive science review](https://educationendowmentfoundation.org.uk/education-evidence/evidence-reviews/cognitive-science-approaches-in-the-classroom/) | Practitioner synthesis | Agency/accessibility and real-world learning, not all features mandated |
| S21 | [Anki algorithm docs](https://docs.ankiweb.net/faqs/what-spaced-repetition-algorithm), [Anki deck options](https://docs.ankiweb.net/manual/deck-options) | Software documentation | FSRS-like scheduling is an experiment, not universal learning science |
| S22 | [OpenAI study mode](https://openai.com/index/chatgpt-study-mode/) | Product precedent | Guidance, Socratic and hints as UX, not comparative effectiveness proof |
| S23 | [Git ignore](https://git-scm.com/docs/gitignore), [GitHub sensitive history](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), [OWASP upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [Open Badges 3.0](https://standards.1edtech.org/open-badges/specifications/standards/v3p0) | Normative/docs | Publication guard and honest certificate semantics |

**Direct-source limits:** The research explored Instagram, X, Threads and Facebook via discoverable indexed material, but did not validate specific posts at a reliability level that warrants listing them as authoritative sources. No invented “viral hacks” are included. Any future agent claiming direct social validation must supply an accessible exact permalink, timestamp and reviewed content.

---

**Authority:** This plan sets intended work; **AGENTS.md, applicable ADRs, user consent and actual repository behavior** still govern execution. On contradiction, stop, record a decision and require review. Keep to-do.md synchronized with real Git status and evidence at every handoff.
