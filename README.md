# Claude Skills

A collection of [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills), mostly aimed at iOS development, PR workflows, and keeping an agentic setup healthy.

Each skill is a self-contained folder with a `SKILL.md` (plus optional `references/` and `scripts/`).

## Skills

### iOS development

| Skill | What it does |
|---|---|
| [`analyze-build`](analyze-build/SKILL.md) | Analyzes an Xcode build log and produces a build-optimization report with ranked quick wins. |
| [`ios-docc-writer`](ios-docc-writer/SKILL.md) | Researches a flow/module/kit in an iOS codebase and writes a DocC catalog article for it. |
| [`wwdc-adoption-advisor`](wwdc-adoption-advisor/SKILL.md) | Cross-references recent WWDC / iOS SDK releases against your codebase and proposes MVP-scoped adoption ideas. |
| [`maestro-flow-writer`](maestro-flow-writer/SKILL.md) | Writes Maestro YAML UI-test flows grounded in real accessibility identifiers read from source. |

### Pull requests

| Skill | What it does |
|---|---|
| [`pr-diff-mermaid`](pr-diff-mermaid/SKILL.md) | Turns a GitHub PR into 1–3 focused Mermaid diagrams of what changed structurally. |
| [`pr-html-report`](pr-html-report/SKILL.md) | Generates paired "What Changed" and "Code Review" HTML reports for a GitHub PR. |
| [`pr-to-automation-plan`](pr-to-automation-plan/SKILL.md) | Plans Appium/TestNG UI-automation coverage for an iOS PR, including accessibility-identifier design. |

### Agentic workflow

| Skill | What it does |
|---|---|
| [`agentic-audit`](agentic-audit/SKILL.md) | Audits a multi-tool AI setup (AGENTS.md, Claude Code, Copilot, Cursor, Codex) for security and context-engineering issues. |
| [`session-retro`](session-retro/SKILL.md) | Runs a retrospective on the current session and proposes improvements to instructions, agents, skills, and memory. |
| [`mindful-acceptance`](mindful-acceptance/SKILL.md) | Gently flags when a user may be rubber-stamping complex AI-suggested changes. |
| [`claude-code-assessor`](claude-code-assessor/SKILL.md) | Adaptive interview that assesses Claude Code proficiency and produces a learning plan. |

## Installation

Copy (or symlink) any skill folder into one of:

- `~/.claude/skills/` — available in all your projects
- `<project>/.claude/skills/` — available only in that project

```bash
git clone https://github.com/jatinmishra/claude-skills-monorepo.git
cp -r claude-skills-monorepo/pr-diff-mermaid ~/.claude/skills/
```

Claude picks up skills automatically based on their `description`, or you can invoke one directly with `/<skill-name>`.

## Requirements

Some skills depend on external tools:

- **GitHub CLI (`gh`)** — `pr-diff-mermaid`, `pr-html-report`, `pr-to-automation-plan`
- **Python 3** — `wwdc-adoption-advisor` (stdlib only), `maestro-flow-writer` (YAML validation, needs PyYAML)
- **Maestro CLI** (optional) — to run flows produced by `maestro-flow-writer`

## License

[MIT](LICENSE)
