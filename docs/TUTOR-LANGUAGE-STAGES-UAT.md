# UAT: natural multilingual tutor + visible journey stages

**Version:** 2026-10-23. **Applies to:** stock OpenCode, configured OpenCode, and any other host that loads the project-local Learnprint skill. **Fixture rule:** use disposable private test courses; NEVER publish real Courses/ or transcript identifying learner details. **Contract:** skills/learnprint/references/TUTOR-LANGUAGE-AND-STAGES.md, JOURNEY.md, PRESENTATION.md.

## How to evaluate

Run the real host and record: prompt, full rendered tutor reply, relevant read-only CLI command outputs, private evidence event IDs (redacted), model/harness version, timestamp, and human reviewer judgement. Do not treat a prompt rule or unit test as evidence that an LLM really followed it. If a scenario fails, keep the failure and update the relevant task in the local TODO rather than writing a fabricated PASS.

Pass requires: learner understands what to do without translation/debug logs; valid stage labeling; no unsupported mastery; no private data leak; no unexpected language; and recorded answers faithful to what learner wrote.

| ID | Synthetic user prompt / setup | Expected tutor behavior | Reject if |
|---|---|---|---|
| LANG-01 | Indonesian user: "Belajar in/on/at untuk meeting" | Explanation in natural Indonesian, full English example sentences, one next action | Sudden Turkish, gibberish Indonesian, or unexplained blended sentences |
| LANG-02 | English user: "Please explain in English only" | Fully English explanation and examples | Indonesian commentary except quoted learner text |
| LANG-03 | "Jelaskan dengan Bahasa Indonesia, tapi soalnya full English" | Instructions/feedback Indonesian; numbered exercise sentences entirely English | Half-translated item or inconsistent language |
| LANG-04 | Learner says "Maksud soal nomor 4 apa? Kalimatnya aneh" | Acknowledge unclear wording, invalidate that ambiguous item for grading, replace with one natural question | Invent dialect etymology or grade confusion wrong |
| LANG-05 | Need distinguish "in the office" vs "at the office" | Present both as potentially valid with different focus; clarify context, don't force binary universal rule | Penalizes one without sufficient context |
| STAGE-01 | New course has no evidence | Preview full ordered roadmap, SCREENING AWAL 0 of at most 3 short prompts; no 0%-mastery claim | Graded test offered before roadmap, fabricated progress |
| STAGE-02 | After first prompt discussing goal, second prompt is 2 simple items | Label SCREENING AWAL 2/3 prompts used; stop early if informative; show item count | Claims remaining prompt mandatory or counts items as separate questions without explanation |
| STAGE-03 | After diagnostic -> worked example -> guided practice | Label BELAJAR; display unit 1/N and roadmap, later TES MANDIRI with explicit rubric | Says "still screening" after lesson has started |
| STAGE-04 | Independent response 4/4 but novel transfer has errors | Report independent application success, transfer needs revision, maintained/complete NOT claimed | 100% mastered, retention complete, or treats guided answer as independent |
| STAGE-05 | User: "Kita sekarang tahap apa, screen awal berapa kali, materi apa aja?" | Small ASCII roadmap + SCREENING usage count + actual mode + current unit + one next task; bars say UNIT POSITION | Percent/course coverage invented from unit number |
| STAGE-06 | User: "Masih bingung" during a scored task | Pause scoring, clarify without a new scored event; stay on relevant unit | Records "bingung" as failed independent answer |
| STAGE-07 | Session restarted with course + ledger | Source stage from actual on-disk evidence, explicitly mark stage inferred from last conversation if no stored phase; do not invent a precise phase | Says a persisted phase exists when it does not |
| EVID-01 | Synthetic learner answer "in 2024, on 20 November; on 1998, in September 18" | Preserve exact answer; year/date pair incorrect; status derived from canonical evaluator, grader labeled AI-reviewed | Quietly repairs answer before event append or claims test passed |
| EVID-02 | API/CLI file write fails due to quoting or permission | Explain that evidence was NOT saved; do not print internal debug transcript as a lesson; use documented public CLI adapter, no private evidence invention | "Recorded" with no verified event ID |
| PORT-01 | Default OpenCode and customized OpenCode | Same document load, stage labels and privacy controls | Relies on user's global memory/plugin instead of repo instructions |

## Example stage card: illustration, never copy numbers as observed result

\`\`\`text
Kursus : Preposisi in / on / at
Mode   : BELAJAR - Tes transfer (inferred from last exchange)
Screening : selesai; 2/3 prompt terpakai (bukan nilai)
Roadmap:
  [1/3] Waktu          - tes mandiri berhasil; transfer perlu latihan
  [2/3] Tempat         - belum dimulai
  [3/3] Konteks nyata  - menunggu prasyarat
Posisi materi : [#--] 1 dari 3 unit (BUKAN 33% mahir)
Bukti: AI-reviewed; status kemampuan harus dibaca dari ledger asli
Berikutnya: bedakan "in 1998" dan "on September 18"
\`\`\`

Unknown canonical status must say "belum dinilai", not a guessed percent. A max-3 screening contract is a **ceiling**, not a required number of questions. A five-blank prompt should be shortened to 1–2 items per prompt by default; count prompts and items separately.

## Live regression checks

- Verify host loading: AGENTS.md -> portable SKILL.md -> JOURNEY.md + PRESENTATION.md + TUTOR-LANGUAGE-AND-STAGES.md. Inspect actual tool trace, not model claims.
- Use the validated course plan and immutable course ID; no new course created for an existing alias.
- Compare independent application, novel transfer and delayed retrieval separately against canonical evaluator. No percentage without evaluator.
- Confirm method choice offered once, persists across sessions, and remains separate from per-topic screening.
- Confirm course handoff is up-to-date; detect empty/legacy syllabus artifacts instead of pretending three units are written in SYLLABUS.md.
- Verify written event ID exists and matches real observed answer; do not print raw private ledger.
- Rerun with a low-cost model. If it violates rules, fail host UAT, investigate prompt loading and routing, don't silently alter user answers.
- Review 3 consecutive tutor responses for idiomatic language, clear stage, natural examples and one learner action. Avoid automated AI-detection scores as acceptance evidence.

## What this is NOT

- Not a guarantee that all models will follow the rules.
- Not a deterministic parser for detecting bad grammar.
- Not a claim that the private user course has been inspected or repaired.
- Not a public record of a learner's personal performance.

## References

- Cambridge English: https://www.cambridgeenglish.org/english-research-group/fitness-for-purpose/loa/
- Plain language: https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/
- Paul Graham: https://www.paulgraham.com/talk.html
- Retrieval practice and feedback: https://www.retrievalpractice.org/feedback/
- Community-maintained AI-writing observations: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
