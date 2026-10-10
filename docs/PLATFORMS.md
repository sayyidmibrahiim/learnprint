# Platform deployment and capability matrix (checked 2026-10-10)

The **portable unit** is a skill directory with `SKILL.md`, frontmatter `name` and `description`, and optional bundled `references/`, `scripts/`, and `assets/`.

| Surface | Discovery / installation path | How to use | Caveat |
|---|---|---|---|
| OpenCode v2 | `.opencode/skills/<name>/SKILL.md`; also `.agents/skills` | native `skill` tool | Permissions may hide skills. |
| Codex CLI | `.agents/skills/<name>/SKILL.md` | native SKILL.md discovery where enabled | Verify exact installed version and workspace/global behavior. |
| Claude Code | `.claude/skills/<name>/SKILL.md` | native skills | Follow current CLI permission settings. |
| Gemini CLI | `.gemini/skills/<name>/SKILL.md`; supports `.agents/skills` alias | native skills | Confirm active skill with `/skills`. |
| Kiro | `.kiro/skills/<name>/SKILL.md`; import from skill subfolder | native skills | Workspace overrides global; some interfaces differ. |
| Antigravity | `.agents/skills/<name>/SKILL.md` | native skills | Tool execution and filesystem scope governed by host. |
| Claude Cowork | Imported/plugin skill | use available skill/plugin UI | Plugin distribution is not identical to copying local folders. |
| ChatGPT desktop/projects | Paste portable prompt and upload files | start a ChatGPT Project; attach profile, learning state, and prompt | Native Skills feature is gated by account/workspace eligibility. Do **not** promise that dropping a SKILL.md on disk auto-installs. |
| Other desktop models (incl. free) | Text prompt + local files | manual | File persistence and tool access may be missing. |

**Install rule:** copy the two packaged skill directories to a location supported by the target. Keep supporting references adjacent to SKILL.md. The optional generated personal skill is separate and must be explicitly installed; if it shadows the generic skill, document precedence. Use `scripts/install.py --dry-run` before writing and seek the user's permission for project/global modifications.

## Official sources
- https://agentskills.io/specification
- https://opencode.ai/docs/skills
- https://developers.openai.com/api/docs/guides/tools-skills
- https://code.claude.com/docs/en/skills
- https://geminicli.com/docs/cli/creating-skills/
- https://kiro.dev/docs/cli/skills/
- https://www.antigravity.google/docs/skills
- https://claude.com/resources/guides/claude-cowork-product-guide/extending-claude-cowork-with-plugins
- https://help.openai.com/en/articles/20001066-skills-in-chatgpt/
- https://help.openai.com/en/articles/10169521-projects-in-chatgpt

**Status:** Official docs confirm formats, not that this package was live-tested in each app. Check actual installed versions before reporting working compatibility.

## Claude Cowork plugin-ready bundle
The source also contains `distribution/claude-plugin/` with `.claude-plugin/plugin.json` and two component skills. A zip of that folder is available as a release attachment for import where custom Claude plugins are supported. The manifest follows the [Anthropic plugin format](https://platform.claude.com/docs/en/manage-claude/plugins-api). This packaging is **not** a verified live installation in Cowork.
