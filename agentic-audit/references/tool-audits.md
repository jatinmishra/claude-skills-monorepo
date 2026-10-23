# Tool-Specific Audits (Steps 4–7)

## Contents
- Step 4 — Audit Claude Code Setup
- Step 5 — Audit OpenAI Codex Setup
- Step 6 — Audit GitHub Copilot Setup
- Step 7 — Audit Cursor Setup

## Step 4 — Audit Claude Code Setup

Read: `CLAUDE.md` (and anything it `@`-imports), `AGENTS.md`, all agent definitions (`.claude/agents/*.md`), all skills (`.claude/skills/*/SKILL.md`), and any project-context or coding-standard docs these reference. If agents/skills live in a shared folder (e.g. `.agents/`) and are symlinked into `.claude/`, verify the symlinks resolve.

**For each agent, verify:**
- **Guardrails**: Explicit guardrail section exists and is appropriate for the tools granted (security check in Step 3 covers detail)
- **Tool scoping**: Tools declared in frontmatter are the minimal viable set. If the agent body uses a tool not declared in frontmatter, flag it — the tool won't be available
- **Role clarity**: Trigger is unambiguous — no routing overlap between agents
- **Instruction altitude**: Actionable and specific. Avoids both extremes — not brittle step-by-step for simple tasks, not hand-wavy platitudes for complex ones
- **Token efficiency**: No bloated instructions, no rules the model follows by default, no redundant context already in AGENTS.md
- **Sub-agent isolation**: Delegating agents return condensed summaries (1–2K tokens), not raw dumps
- **Broken references**: Every file path referenced in agent prompts actually exists (verify with Read/Glob)
- **Read directives placement**: "Read X first" directives appear at the top of the file, not buried at the bottom

**For CLAUDE.md, verify:** (if CLAUDE.md just imports `@AGENTS.md`, apply these checks to the AGENTS.md content it imports)
- **Conciseness**: No rules Claude already follows by default — every line must earn its tokens
- **No redundancy**: No contradictory or duplicated rules across CLAUDE.md, AGENTS.md, and any project-context or coding-standard docs
- **Agent orchestration**: All agents AND skills listed in the routing table with unambiguous triggers
- **Compaction readiness**: A "Context Management" section explicitly lists what MUST survive context compaction (active task state, unresolved decisions, architectural constraints)
- **Just-in-time retrieval**: Prefers lightweight identifiers (file paths, module names) over pre-loaded content

**For coding standards, verify:**
- Rules are clear, specific, and enforceable
- No duplication with linter rules (the linter config is the source of truth for style)
- Security rules are comprehensive (covered in Step 3 — cross-reference)
- No over-specification of things the model handles well by default

---

## Step 5 — Audit OpenAI Codex Setup

Read: the project's agent lessons/learnings file (if present), `.codex/config.toml` (if present)

**For a lessons/learnings file, verify:**
- Each lesson follows a consistent format (e.g. trigger, root cause, prevention rule, validation status)
- No entry contains secrets, credentials, or customer data (security — Step 3 cross-reference)
- Stale or unvalidated entries are periodically reviewed and closed
- Lessons are promoted to skills or always-loaded rules only after recurring across separate tasks

**For `.codex/config.toml`, verify:**
- `project_doc_max_bytes` is set appropriately if total AGENTS.md chain is large
- Approval policy and `default_permissions` profile match the project's safety requirements (security — Step 3 cross-reference); only documented keys are used — unknown keys are silently ignored
- `.codex/rules/default.rules` mirrors `.claude/settings.json` `ask`/`deny` — verify with `codex execpolicy check --rules .codex/rules/default.rules -- git push`
- MCP server connections are documented and justified

---

## Step 6 — Audit GitHub Copilot Setup

Read: `.github/copilot-instructions.md`, all `.github/instructions/*.instructions.md`, any `.github/prompts/*.prompt.md`

**For `.github/copilot-instructions.md`, verify:**
- **Length**: ≤ ~2 pages. Critical: Copilot code review reads only the first 4,000 characters — the most important rules must appear early in the file
- **Content coverage** — all five elements should be present:
  1. Project overview — what the app does, audience, key features
  2. Tech stack — languages, frameworks, APIs, testing frameworks
  3. Coding guidelines — style, naming conventions, testing requirements
  4. Project structure — key directories with brief purpose descriptions
  5. Available resources — scripts, automation tools, MCP servers
- **Format**: Short imperative directives; markdown headings + bullet points; no narrative paragraphs
- **No linter duplication**: Style rules enforced by the project linter should not be restated
- **No cross-tool duplication**: Content already authoritative in AGENTS.md should be referenced, not copied verbatim
- **Priority ordering**: When space is tight, prioritize: validated build/test sequences > architecture > structure > snippets

**For `.github/instructions/*.instructions.md`, verify:**
- Each file has valid YAML frontmatter with an `applyTo` glob pattern
- Glob patterns are precise — `**/*` for everything defeats the purpose of path scoping
- `excludeAgent` used where instructions don't apply to coding agent or code review (valid values: `code-review`, `coding-agent`)
- No file exceeds ~2 pages for a single instruction scope

**For `.github/prompts/*.prompt.md`, verify:**
- Each prompt is a reusable, task-specific snippet — not a duplicate of instructions
- Variable syntax is correct (if using parameterized prompts)
- No prompts duplicate content already in `copilot-instructions.md` or `AGENTS.md`

---

## Step 7 — Audit Cursor Setup

Read: all `.cursor/rules/*.mdc` (or `.md`), `.cursorrules` (if present)

**If `.cursorrules` exists at repo root:**
- Flag as legacy format — migrate content to `.cursor/rules/*.mdc`
- Legacy file lacks rule-type scoping, forcing all rules into always-on mode and increasing token waste

**For each rule file in `.cursor/rules/`, verify:**
- **Length**: ≤ 500 lines per rule file
- **Rule type used appropriately** (controlled by frontmatter properties):

  | Type | Frontmatter | When to use |
  |------|-------------|-------------|
  | **Always Apply** | `alwaysApply: true` | Truly global rules only. Overusing this makes everything equally prominent = nothing is special |
  | **Apply Intelligently** | `description: "..."` (no globs, alwaysApply false) | Agent reads description and decides relevance. Description must be specific enough for AI to judge — vague descriptions = unreliable activation |
  | **Apply to Specific Files** | `globs: ["**/*.swift"]` | File-type or directory-specific rules; preferred for most rules |
  | **Apply Manually** | No description, no globs, alwaysApply false | Rarely-needed rules invoked via `@rule-name` in chat |

- **Frontmatter validation**:
  - `Apply Intelligently` rules MUST have a clear, specific `description`
  - `Apply to Specific Files` rules MUST have precise `globs` — not `**/*`
  - `Always Apply` rules should be rare and small — each one consumes tokens on every prompt
- **References files, doesn't copy them**: Points to canonical examples in the codebase rather than pasting content. Copied content goes stale
- **No linter duplication**: Rules enforced by the project linter are not restated
- **Evidence-based**: Rules exist because the agent made a repeated mistake — not added preemptively
- **Checked into git**: Rule files are version-controlled, not in `.gitignore` (also required for audit trail — Step 3)
