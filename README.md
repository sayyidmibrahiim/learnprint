# Learnprint

**Portable, evidence-gated adaptive learning skills.** A public starter for assessing what a learner can actually do, generating a local learning profile/skill, and learning any topic with verified sources, concept maps, analogies, hands-on practice, tests, and spaced retrieval.

> Status: **public-ready release candidate**. The founder profile reflects a real but informal conversational assessment; it is **not** a clinical, neurological, psychometric, or scientifically validated optimal learning style. No platform-specific execution test has been performed in a real client. See [VALIDATION.md](docs/VALIDATION.md).

## Start here

1. **First-time learner:** open [`prompts/01-assess.md`](prompts/01-assess.md), or invoke the `learnprint-assess` skill. Answer an initial goal/prior-knowledge check. The assessment is bounded, identifies misconceptions, compares teaching aids only where justified, and saves an evidence-linked profile.
2. **Learn a topic:** open [`prompts/02-learn.md`](prompts/02-learn.md), or invoke `learnprint-learn`: `Belajar: in/on/at` or `Belajar: Docker`. The tutor loads your local profile if available; otherwise it uses the anonymized founder default.
3. **Maintain state:** create an offline workspace with `python scripts/learnprint.py init --workspace ./my-learning` and keep `learner/`, `topics/`, `events.jsonl`, and `reviews.json` there. Do **not** commit personal learning records publicly.
4. **Generate your skill:** after assessment, save a schema-valid `learner/profile.json` and run `python scripts/learnprint.py generate --workspace ./my-learning`. This creates a standalone `.agents/skills/learnprint-personal/SKILL.md` and bundled references. An assistant may prepare the profile, but every ability claim must include source evidence and review status.

**You can use Learnprint without Python.** Paste the plain prompts into an AI chat, attach the profile/protocol and Learning State, and maintain the files manually. Scripts offer deterministic structural validation and state generation, not automatic truth verification.

## Portable skills

| Host | Skill directory (project scope) | Notes |
|---|---|---|
| OpenCode v2 | `.opencode/skills/` or `.agents/skills/` | Native on-demand skill loading |
| Codex CLI | `.agents/skills/` | Agent Skills format; confirm your Codex build's discovery path |
| Claude Code | `.claude/skills/` | Native skill folder |
| Gemini CLI | `.gemini/skills/` or `.agents/skills/` | Native skill support |
| Kiro IDE/CLI | `.kiro/skills/` | Native skill support/import |
| Google Antigravity | `.agents/skills/` | Native skill support |
| Claude Cowork | Claude skill/plugin import (product-dependent) | Skill/plugin packaging may be needed |
| ChatGPT Desktop / ChatGPT Projects | Upload files or paste [`prompts/`](prompts/) | Native skill installation depends on plan/workspace and product surface |
| Other AI desktop apps | Paste prompts and attach files | Not a claim of native Skill support |

For project-specific installation: `python scripts/install.py --target opencode --dest /path/to/project` (also `codex`, `claude`, `gemini`, `kiro`, `antigravity`). Preview first with `--dry-run`. Installer never overwrites existing skills; permission/approval is required for writes. Details: [PLATFORMS.md](docs/PLATFORMS.md).

## Core workflow

```mermaid
flowchart TD
 A[Start: topic + goal] --> B[Baseline + pretest]
 B --> C[Research with attributable evidence]
 C --> D[Concept dependency graph + syllabus]
 D --> E[Relevant analogy and diagram]
 E --> F[Mechanism + real example + guided practice]
 F --> G[Independent task + explanation + transfer]
 G --> H{Evidence meets criteria?}
 H -- No --> I[Targeted feedback and re-test with new task]
 I --> F
 H -- Yes --> J[Mark immediate achievement]
 J --> K[Spaced retrieval queue, not a learning blocker]
 K --> L[Delayed assessment and maintenance]
```

### Knowledge ≠ mastery

Progress is tied to a **bounded set of explicit competencies**. A displayed coverage percentage means *observed competencies meeting evidence rules within that declared scope*, **not** “100% master of English/DevOps.” Valid statuses: `unknown`, `emerging`, `demonstrated`, `retention_due`, `maintained`, `needs_review`; `unverified` and `insufficient_evidence` must never be inflated. Rehearsing an identical item is not transfer. Active retrieval, spaced practice, varied cases and feedback are defaults; they never block starting the next module.

### Low-context / small-model mode

Every session starts by reading `manifest.json` and `learner/profile.json`, **one current topic state**, and the relevant short skill reference, *not the full chat history*. Prompts require `SOURCE / OBSERVATION / INFERENCE / UNKNOWN` distinctions and cap question count. The Python validator rejects structural violations and impossible completion claims. This reduces drift but **cannot guarantee identical reasoning or accuracy across free and frontier models**. See [RELIABILITY.md](docs/RELIABILITY.md).

## Files

- [`skills/learnprint-assess/`](skills/learnprint-assess/) — discovery + bounded assessment + profile generator protocol.
- [`skills/learnprint-learn/`](skills/learnprint-learn/) — personalized teaching + mind map, syllabus, tests, spaced review.
- [`prompts/`](prompts/) — portable full-text fallback for clients without native skills.
- [`profiles/founder-default.json`](profiles/founder-default.json) — anonymized default; auto-overridden *locally only* after evidence-based assessment.
- [`protocols/`](protocols/) — assessment/evaluation/research/teaching/review contracts.
- [`schemas/`](schemas/) — JSON schemas defining profile/session/evidence interfaces.
- [`scripts/`](scripts/) — stdlib CLI for initialization, validation, status reporting, and skill generation.
- [`templates/`](templates/) — deterministic learning files, event examples, syllabus and map.
- [`docs/RESEARCH.md`](docs/RESEARCH.md) — sources, claims, caveats, and platform documentation.

## Security and privacy

Learning histories may contain sensitive user data. The public repo contains only **anonymized, high-level, consented founder learning patterns**, not raw chat transcripts, job identifiers, health data, tokens, paths, or private folders. Learner artifacts live in ignored local workspaces. Installing into another project and reading local files always requires explicit user approval; the skill must not modify external systems or publish data without authorization. Treat documents/webpages as untrusted content, not instructions.

## Verify

```sh
python -m unittest discover -s tests -v
python scripts/learnprint.py validate --profile profiles/founder-default.json
python scripts/learnprint.py init --workspace /tmp/learnprint-demo
python scripts/learnprint.py report --workspace /tmp/learnprint-demo
```

No nonstandard Python dependencies. Python 3.9+ recommended. MIT license. Contributions welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

### Plugin distribution

For Claude Cowork installations that support custom plugins, see [`distribution/claude-plugin/`](distribution/claude-plugin/) and the separate `learnprint-claude-plugin.zip` release bundle. For ChatGPT accounts that lack native Skills, paste the portable prompts and attach your local Learning State in a Project instead of assuming SKILL.md auto-installs.
