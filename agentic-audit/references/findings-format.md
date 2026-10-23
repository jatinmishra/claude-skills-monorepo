# Findings Format (Step 11)

## Step 11 — Present Findings

Group findings: **Security findings first** (always), then by tool, then by file. Limit to 10 most impactful findings total, but security findings are never dropped to meet the limit.

**Priority order**: secrets in config > missing write-gate > missing destructive guards > prompt injection exposure > cross-tool contradictions > token waste > broken references > missing documentation > style

## Output Format

For each finding:

```
### Finding N: [Short title]

**Severity**: [Critical | High | Medium | Low]
**Category**: [Security | Context Engineering | Cross-tool Consistency]
**Tool**: [AGENTS.md (cross-tool) | Claude Code | Copilot | Cursor | Codex | Gemini | Cross-tool]
**Principle violated**: [Security principle from Step 3 OR context engineering principle from Step 9]
**File**: [exact file path]
**Issue**: [What's wrong or missing — backed by evidence, not assumption]
**Proposed fix**:
- **Action**: [Add | Edit | Remove]
- **Content**: [the exact text to add, edit, or remove]
**Rationale**: [Why this matters. For security findings: describe the attack vector this enables. For removals: explain what will NOT break]
```

## Rules

- This is a read-only audit — do NOT modify any files
- **Security findings are never deprioritized for token savings** — the only acceptable trade is moving a guardrail to a different file while verifying it's still loaded
- Only flag real issues backed by evidence — do not invent problems for completeness
- Every finding must reference a specific principle from Step 3 (security) or Step 9 (context engineering)
- When proposing removals, explain what will NOT break
- For cross-tool findings, name all affected tools
- Include the token budget table from Step 1c in the report header
