# Learnprint owner walkthrough: any topic → trustworthy course → optional GitHub portfolio

Status: merged to `main` at `1b9b785`; all 15 cross-platform CI jobs are green on the merge commit (run `39908358179`), and the Windows suites pass locally. Cross-host human UAT remains a separate open gate. Updated 2026-10-23. Start from the **repository root**. Commands below are examples, not commands already run on your actual courses. Do NOT paste private learner answers into GitHub issues or logs.

## 1. Explore without writing
```sh
python scripts/learnprint.py learner status
python scripts/learnprint.py course overview
python scripts/learnprint.py course portfolio-options
```
If an existing course is present, **resolve/resume** it; do not reinitialize your actual `Courses/` or create a duplicate. Course IDs are permanent, and `Courses/.learnprint/events.jsonl` is private.

## 2. New learner or topic
After explaining scope and receiving learner consent, for an **empty temporary test workspace**:
```sh
python scripts/learnprint.py course init --courses-root TEMP_COURSES --approve
python scripts/learnprint.py course create --courses-root TEMP_COURSES --category technology --title "DNS Lookup" --goal "Trace a DNS query safely" --approve
```
The create command prints the newly assigned `course_id`. Reuse that UUID in subsequent commands. The category and title are examples; learning may be math, music, history, Japanese, SQL, safety, programming or any narrow question.

## 3. Build and review the prerequisite-based syllabus
First read the effective learner method, then preview the existing course and plan:
```sh
python scripts/learnprint.py learner method --courses-root TEMP_COURSES
python scripts/learnprint.py course plan --courses-root TEMP_COURSES --course-id YOUR-UUID
```
The `course scope-set` command accepts a validated JSON list of competencies; `course plan-set` accepts a validated JSON array of ordered units. The public CLI validates prerequisites and IDs. Generate these based on your actual goals, not a canned English template. Preview before mutating and preserve the old course:
```sh
python scripts/learnprint.py course plan-set --courses-root TEMP_COURSES --course-id YOUR-UUID --from-file PRIVATE-UNITS.json --dry-run
python scripts/learnprint.py course plan-set --courses-root TEMP_COURSES --course-id YOUR-UUID --from-file PRIVATE-UNITS.json --approve
```
Changing private state requires the authorized learner's actual approval; a synthetic automated test uses its own disposable root.

## 4. See your roadmap and persist the tutor phase
```sh
python scripts/learnprint.py course journey-card --courses-root TEMP_COURSES --course-id YOUR-UUID
python scripts/learnprint.py course tutor-init --courses-root TEMP_COURSES --course-id YOUR-UUID --approve
python scripts/learnprint.py course tutor-status --courses-root TEMP_COURSES --course-id YOUR-UUID
python scripts/learnprint.py course tutor-transit --courses-root TEMP_COURSES --course-id YOUR-UUID --to EXPLAIN --event-id lesson-start-01 --approve
python scripts/learnprint.py course journey-card --courses-root TEMP_COURSES --course-id YOUR-UUID
```
Initialization happens **once** per existing tutor session. A phase change updates the private FSM but never manufactures assessment evidence. The bar is the unit's *position*, not a mastery percent. The first screening uses **at most 3** short prompts, not an obligation to ask three.

When a genuinely independent attempt is due, open `ATTEMPT` (or `TRANSFER` for genuinely new constraints) using `tutor-transit` with a unique task ID and task author. The evidence writer then checks that task against the persisted FSM.

## 5. Record a real answer with no Windows quoting loss
Create a **private, untracked** JSON file, e.g. `TEMP_COURSES/answer.json`. The content below is a format example, **not** an actual learner answer or verified mastery:
```json
{
  "event_id": "example-event-001",
  "topic": "YOUR-UUID",
  "course_id": "YOUR-UUID",
  "competency": "your-competency-id",
  "task_id": "unique-task-from-ATTEMPT",
  "task_type": "independent_application",
  "answer": "COPY THE LEARNER'S ACTUAL RESPONSE, UNCHANGED",
  "rubric": {"concept": null, "mechanism": null, "application": 2, "transfer": null},
  "expected": "The independently registered evaluation criteria",
  "feedback": "Actual honest grader feedback",
  "grader": "ai_reviewed",
  "grader_source": "agent",
  "help_level": "none"
}
```
Only after the learner answers and approves the record:
```sh
python scripts/learnprint.py record --workspace TEMP_COURSES --from-file TEMP_COURSES/answer.json --approve
```
A matching tutor session requires the recorded `task_id`, correct phase and truthful help level. If the learner requests an explanation, there is no scored answer; a hint-assisted answer cannot be stored as unassisted. Evidence is provisional if only AI-reviewed, regardless of a pretty progress bar.

## 6. Update derived documents without destroying manual notes
```sh
python scripts/learnprint.py course docs-preview --courses-root TEMP_COURSES --course-id YOUR-UUID
```
If this fails because `SYLLABUS.md`, `MAP.mmd`, or `HANDOFF.md` is handmade, that is an intentional safety guard. Do not delete the file. If all items are known/generated or untouched stubs, copy the exact displayed `preview_digest` and use:
```sh
python scripts/learnprint.py course docs-sync --courses-root TEMP_COURSES --course-id YOUR-UUID --preview-digest DIGEST --approve
```
Each changed previous document gets a private backup. The canonical `state.json`, ledger and course UUID are not rewritten by docs-sync.

## 7. Curate a course as GitHub proof-of-work, or keep it private
All courses are **selectable as portfolio candidates by default**. That does not make any of them public. The learner chooses exactly which course and which real files to share, or chooses none.
```sh
python scripts/learnprint.py course portfolio-options --courses-root TEMP_COURSES
python scripts/learnprint.py course portfolio-preview --courses-root TEMP_COURSES --course-id YOUR-UUID --manifest PRIVATE-PUBLICATION-MANIFEST.json
```
A manifest uses schema_version `1`, the actual UUID, `visibility: "public"`, a real title/summary, explicit safe `hands-on/...` allowlisted text files and truthful claimed achievements. Review original authorship, license, secrets, personal data and the **exact preview bytes**. `visibility: "private"` means do not export.

For a deliberately selected public course:
```sh
python scripts/learnprint.py course portfolio-export --courses-root TEMP_COURSES --course-id YOUR-UUID --manifest PRIVATE-PUBLICATION-MANIFEST.json --output-dir TEMP_COURSES/public/YOUR-UUID --preview-digest DIGEST --approve
```
This creates a **derived local snapshot only**. It does NOT stage, commit, push, or create a GitHub certificate. Original learner answers, profile, notes, private handoff, raw state, and ledger must never be published. Supported v1 artifacts are bounded, allowlisted UTF-8 text. For an existing approved snapshot revision, read `docs/COURSE-PORTFOLIO.md`; do not overwrite or invent public version directories.

## 8. Review public Git changes and release
```sh
python scripts/check_package.py
python scripts/learnprint_publish_guard.py --repo .
python -m unittest discover -s tests
```
Only carefully reviewed *public* snapshot files may be staged by explicit path, **not** `git add -A` or a forced add of private source files. Inspect staged blobs with the privacy guard again before commit, then push only with the learner's explicit publication authorization. Review GitHub Actions status for the real remote branch. Note: `.gitignore` never untracks an already-tracked private file; Git history/forks may retain leaked content.

## 9. What qualifies as complete?
A local test PASS means the tested software path worked. It does **not** certify real tutor fluency, a person's independent understanding, user consent, a GitHub credential, or a safe publicly pushed portfolio. Use `docs/TUTOR-LANGUAGE-STAGES-UAT.md` and `docs/research/2026-10-23-production-release-gates.md` for real host and release acceptance criteria.
