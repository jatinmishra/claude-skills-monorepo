---
name: agentic-audit
description: >
  Audits the full multi-tool agentic setup (AGENTS.md, Claude Code, GitHub Copilot, Cursor, Codex)
  against context engineering and security best practices. Covers cross-tool consistency, security
  guardrails, prompt injection surfaces, destructive command guards, and token efficiency. Use when
  the user invokes /agentic-audit, adds new agents/skills, onboards a new AI tool, or does periodic
  health checks on the agentic setup.
disable-model-invocation: true
---

# Agentic Setup Audit

## When to Use

- User invokes `/agentic-audit`
- After adding new agents, skills, or onboarding a new AI tool
- Periodic health checks on the agentic setup

## When NOT to Use

- Mid-session code reviews or task progress checks
- Single-file edits that don't touch agent/skill configuration

Perform a comprehensive audit of the full multi-tool AI configuration against context engineering and security best practices. Sources: Anthropic Claude Code Security docs, OpenAI Codex Agent Approvals & Security, GitHub Agentic Workflows Security Architecture, Anthropic "Effective Context Engineering for AI Agents" guide, Cursor security guidance, and the AGENTS.md open standard.

## Core Principle

> Find the smallest set of high-signal tokens that maximize the likelihood of the desired outcome — across every tool in the stack. And ensure no agent can take an action the developer did not explicitly approve.

Context is finite. Agent authority is a liability until constrained. Both must be managed deliberately.

---

## Audit Workflow

Copy this checklist and track progress:

```
Audit Progress:
- [ ] Step 1: Discover and Measure
- [ ] Step 2: Audit AGENTS.md
- [ ] Step 3: Security Guardrail Audit
- [ ] Step 4: Audit Claude Code
- [ ] Step 5: Audit OpenAI Codex
- [ ] Step 6: Audit GitHub Copilot
- [ ] Step 7: Audit Cursor
- [ ] Step 8: Cross-Tool Consistency
- [ ] Step 9: Context Engineering Checklist
- [ ] Step 10: Quality Safety Check
- [ ] Step 11: Present Findings
```

| Step | What | Reference |
|------|------|-----------|
| 1 | **Discover and Measure** — scan all tool config files, detect active tools, measure token budget | Below |
| 2 | **Audit AGENTS.md** — cross-tool standard validation | Below |
| 3 | **Security Guardrail Audit** — highest priority | `references/security-audit.md` |
| 4 | **Audit Claude Code** — agents, skills, CLAUDE.md, coding standards | `references/tool-audits.md` |
| 5 | **Audit OpenAI Codex** — instructions, lessons, config | `references/tool-audits.md` |
| 6 | **Audit GitHub Copilot** — instructions, prompts, copilot-instructions | `references/tool-audits.md` |
| 7 | **Audit Cursor** — rules, rule types, legacy .cursorrules | `references/tool-audits.md` |
| 8 | **Cross-Tool Consistency** — convention alignment across all tools | Below |
| 9 | **Context Engineering Checklist** — 10 universal principles | `references/context-engineering.md` |
| 10 | **Quality Safety Check** — verify optimizations don't degrade output | `references/context-engineering.md` |
| 11 | **Present Findings** — structured output format | `references/findings-format.md` |

---

## Step 1 — Discover and Measure

### 1a. Scan for all tool config files

| Tool | Config files |
|------|-------------|
| **AGENTS.md** | `AGENTS.md`, `AGENTS.override.md` at any directory level |
| **Claude Code** | `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`, `.claude/commands/*.md`, `.mcp.json`, plus any files these import or reference (project-context docs, coding-standard docs — wherever the repo keeps them, e.g. `docs/` or a shared `.agents/` folder) |
| **Codex** | `.codex/config.toml`, `.codex/agents/*.toml`, `.codex/rules/default.rules`, any lessons/learnings file the project keeps for agents |
| **Copilot** | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `.github/prompts/*.prompt.md` |
| **Cursor** | `.cursor/rules/*.mdc` (or `.md`), `.cursor/cli.json`, `.cursorignore`, `.cursorrules` (legacy) |
| **Gemini** | `GEMINI.md` |

### 1b. Detect which tools are actively used

A missing config file is a finding only if that tool is actively used. Check for activity signals: `.claude/` directory, `.codex/config.toml`, `.github/copilot-instructions.md`, `.cursor/` directory, `GEMINI.md`.

### 1c. Measure token budget

For every always-loaded file, estimate token count (~1 token per 4 chars) and report a budget table. **Flag any always-loaded file exceeding 1,500 tokens** — context rot research shows accuracy degrades with token count even within the supported window. Exception: `AGENTS.md` is the single source of truth and is judged against the 32 KiB limit in Step 2, not this threshold.

---

## Step 2 — Audit AGENTS.md (Cross-Tool Standard)

`AGENTS.md` is the most impactful file — read by 30+ tools including Copilot, Cursor, Codex, Devin, Jules, Gemini CLI.

**Content completeness** — all six elements should be present:
1. Project overview — what the app does, audience, key features
2. Repository layout and key directories
3. Build, test, and lint commands (validated by actually running them)
4. Engineering conventions and architecture rules
5. Constraints and restrictions (security, deployment targets, framework policies)
6. Routing map to skill/instruction files for deeper context

**Size**: Total combined AGENTS.md chain ≤ 32 KiB (Codex default `project_doc_max_bytes`).

**Hierarchy integrity**: Nested `AGENTS.override.md` files specialize (not contradict) the parent.

**No duplication**: AGENTS.md owns cross-tool conventions. Tool-specific content belongs in that tool's own config.

---

## Step 3 — Security Guardrail Audit

**Read `references/security-audit.md` for the full checklist.** This is the highest-priority step — run before individual tool audits.

Covers: minimal privilege, destructive operation guards, prompt injection surfaces, secrets scanning, write-operation approval gates, MCP security, audit trail, and tool-specific security checks for Claude Code, Codex, Copilot, and Cursor.

---

## Steps 4–7 — Tool-Specific Audits

**Read `references/tool-audits.md` for detailed checklists** covering Claude Code (Step 4), OpenAI Codex (Step 5), GitHub Copilot (Step 6), and Cursor (Step 7).

---

## Step 8 — Cross-Tool Consistency Check

After auditing each tool individually, check for consistency across all tools present:

| Check | What to look for |
|-------|-----------------|
| **Convention alignment** | Do all tools agree on branch naming, commit format, PR conventions? |
| **Testing policy** | Do all tools agree on the testing framework and conventions? |
| **Platform version policy** | Do all tools agree on deployment target and language version baseline? |
| **Architecture rules** | Do all tools agree on module boundaries, DI patterns, inter-module communication? |
| **Security policy** | Is the security ruleset consistent and present across tools? |
| **Write-gate consistency** | The "no write without approval" principle must be present in every tool's always-loaded config |
| **Content ownership** | Is each convention owned by exactly one file? No duplication |
| **Coverage gaps** | Is a critical convention missing from ALL tools? |
| **Shared file awareness** | AGENTS.md is read by multiple tools — verify no tool-specific content leaked in |

---

## Steps 9–11 — Context Engineering, Quality Safety, and Findings

**Read reference files for detailed guidance:**
- `references/context-engineering.md` — 10 universal context engineering principles + quality safety checks
- `references/findings-format.md` — output format, severity levels, priority rules

## Rules

- This is a read-only audit — do NOT modify any files
- Security findings are never deprioritized for token savings
- Only flag real issues backed by evidence
- Every finding must reference a specific principle from Step 3 or Step 9
