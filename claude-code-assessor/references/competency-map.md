# Claude Code Competency Map — Question-Generation Reference

> This file does NOT contain questions. It defines WHAT to assess.
> At runtime the model generates questions by combining these seeds with
> the official Claude Code docs (and, optionally, the changelog for the
> advanced tier). Anchored to Anthropic Academy course coverage.

## How the model should use this file
1. Pick a domain (weighted by the assessment's goal or adaptively by prior answers).
2. Take a `topic` seed from that domain and generate ONE question testing the underlying concept.
3. Verify the correct answer against official docs before scoring (https://docs.claude.com/en/docs/claude-code/overview).
4. Set difficulty per the bands below; escalate/de-escalate based on the person's last answer.
5. Prefer scenario/"what would you do" phrasing over recall. Avoid version-specific trivia unless in the Advanced tier.

## Difficulty bands
- **Beginner** — knows what a thing is and when to reach for it.
- **Intermediate** — applies it correctly in a realistic workflow; avoids common mistakes.
- **Advanced** — diagnoses failures, makes tradeoffs, knows the limits and when NOT to use it.

## Generation rules
- One concept per question. No multi-part traps unless probing Advanced.
- Do not reproduce course or doc text; test the idea in your own words.
- Reject any generated question whose answer you cannot confirm in the docs.
- Keep the volatile layer (Domain 9) optional and switchable off.

---

## Domains

### 1. Foundations & mental model
Probe: understands Claude Code as an agentic coding tool, not autocomplete.
Topics: what it is vs. IDE assistants; reading a codebase vs. snippet generation; where it runs; cost/usage awareness.

### 2. Core workflow (Explore → Plan → Code → Commit)
Probe: drives the loop deliberately instead of one-shotting.
Topics: when to explore first; planning before edits; scoping a task for an agent; committing in reviewable chunks; thinking vs. planning mode.

### 3. Context management
Probe: controls what the model sees and when to reset.
Topics: what to include/exclude; when to clear/compact; long-session degradation; referencing files vs. pasting; avoiding context pollution.

### 4. Project configuration
Probe: sets up a repo so the agent behaves well by default.
Topics: CLAUDE.md purpose and content; project vs. user memory; permissions/allowlists; settings; team-shared config.

### 5. Tools & MCP
Probe: extends Claude Code with external capabilities, safely.
Topics: what MCP is; when to add a server; configuring/scoping a connector; security implications of granting tool access.

### 6. Subagents & delegation
Probe: delegates to isolated agents to manage context and noise.
Topics: when a subagent helps vs. hurts; isolating context; parallel vs. sequential work; keeping the main session clean.

### 7. Agent Skills (SKILL.md)
Probe: knows what Skills are and how they differ from neighbors.
Topics: SKILL.md structure and triggering; Skills vs. CLAUDE.md vs. hooks vs. slash commands; when to author a Skill; distribution across a team.

### 8. Verification, debugging & recovery
Probe: doesn't trust output blindly; recovers when the agent goes wrong.
Topics: verifying generated code; reading errors back to the agent; reproducing failures; rolling back; git hygiene as a safety net.

### 9. Judgment & limits (advanced / mostly evergreen)
Probe: knows the boundaries.
Topics: tasks to delegate vs. do manually; when human judgment is required; recognizing when the agent is stuck; cost/effort tradeoffs.

### 10. Current features (VOLATILE — optional tier, OFF by default)
Probe: awareness of recent capabilities (only if testing currency).
Topics: pull dynamically from the changelog at runtime, pinned to the person's `claude --version`. Do not use for foundational scoring.
