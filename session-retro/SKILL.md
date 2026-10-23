---
name: session-retro
description: >
  Session retrospective that analyzes the current conversation to propose improvements to AGENTS.md,
  agents, skills, and memory. Use when the user invokes /session-retro, asks for a retrospective,
  or wants to improve the agentic setup based on what happened in this session. Do NOT use for
  mid-session status checks or task progress questions.
---

# Session Retrospective

Analyze the current session and produce concrete, ready-to-apply proposals for improving the agentic setup.

## When to Use

- Consider offering it after a major task (multi-file feature, significant refactor, full plan-to-PR cycle) — never run it unasked
- Manually via `/session-retro`

## When NOT to Use

- Mid-session status checks or task progress questions
- Sessions with fewer than 5 meaningful interactions

## Gate Check — MUST Pass Before Analysis

Before running any analysis, verify the session meets ALL of these criteria:

1. **Minimum interaction depth**: The session has **5+ meaningful user messages** (not counting simple "yes"/"approved"/"go ahead" confirmations)
2. **Substantive work occurred**: At least ONE of the following happened:
   - Code was written or modified across 2+ files
   - A multi-step task plan was executed
   - A full plan-to-PR workflow was completed
   - A non-trivial bug investigation was performed

If the gate check fails, respond with: "Session too short for retrospective — no improvements identified." and stop. Do NOT proceed with the analysis framework.

## Analysis Framework

Copy this checklist and track progress:

```
Session Retro Progress:
- [ ] Gate check passed
- [ ] 1. Repeated Corrections analyzed
- [ ] 2. New Patterns Discovered analyzed
- [ ] 3. Agent Gaps analyzed
- [ ] 4. Skill Opportunities analyzed
- [ ] 5. Guardrail Near-Misses analyzed
- [ ] 6. Rule Effectiveness Audit analyzed
- [ ] 7. Memory Updates analyzed
- [ ] Proposals formatted and presented
```

Review the full session and evaluate each category:

### 1. Repeated Corrections

**Signal**: The user corrected you 2+ times on the same type of issue.
**Action**: Propose a new rule in the project's instruction files (CLAUDE.md / AGENTS.md, a coding-standards doc, or the relevant agent) to prevent recurrence. If the project keeps a lessons/learnings file for agents, also propose an entry there (trigger, root cause, prevention rule, validation status).

### 2. New Patterns Discovered

**Signal**: You encountered a codebase convention, architectural pattern, or workflow not documented anywhere in the project's instruction files (CLAUDE.md / AGENTS.md, project docs, coding standards) or agent definitions.
**Action**: Propose adding it to the appropriate file.

### 3. Agent Gaps

**Signal**: A task was handled in the main conversation that should have been delegated to an agent, or an existing agent lacked a capability it needed.
**Action**: Propose a new agent or an improvement to an existing one.

### 4. Skill Opportunities

**Signal**: A multi-step workflow was performed that could be reused in future sessions (e.g., a specific migration pattern, a review checklist, a deployment flow).
**Action**: Propose a new skill at `.claude/skills/<name>/SKILL.md` (or wherever the project keeps its skills) with the workflow captured, and register it in any skill-routing/index doc the project maintains.

### 5. Guardrail Near-Misses

**Signal**: You almost performed an action the user had to stop, or a guardrail was too loose/too strict.
**Action**: Propose tightening or adjusting the guardrail in the relevant agent or CLAUDE.md / AGENTS.md.

### 6. Rule Effectiveness Audit

**Signal**: An existing rule in CLAUDE.md / AGENTS.md or an agent was unhelpful, redundant, or actively got in the way during this session.
**Action**: Propose pruning, clarifying, or rewording the rule.

### 7. Memory Updates

**Signal**: A user preference, environment detail, or recurring decision was revealed that should persist across sessions.
**Action**: Propose an update to the memory directory.

## Output Format

Present findings as a numbered list of **concrete proposals**. For each:

```
### Proposal N: [Short title]

**Category**: [Repeated Correction | New Pattern | Agent Gap | Skill Opportunity | Guardrail | Rule Audit | Memory Update]
**What happened**: [1-2 sentences describing the session event that triggered this]
**Proposed change**:
- **File**: [exact file path]
- **Action**: [Add / Edit / Remove]
- **Content**: [the exact text to add, edit, or remove]
**Impact**: [What this prevents or improves in future sessions]
```

## Rules

- Only propose changes backed by concrete evidence from the session — no speculative improvements
- The gate check (above) is the primary filter — if it passed, proceed with analysis. Only produce "No improvements identified" if analysis genuinely finds nothing actionable
- Every proposal must include the exact file path and exact content to change — no vague suggestions like "consider adding a rule about X"
- Group proposals by file to minimize number of edits
- Do NOT apply any changes — present proposals and wait for explicit approval
- Limit to 5 most impactful proposals — don't overwhelm with minor tweaks
- Prioritize proposals that prevent repeated mistakes over nice-to-haves
