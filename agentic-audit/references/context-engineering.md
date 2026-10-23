# Context Engineering & Quality Safety (Steps 9–10)

## Step 9 — Context Engineering Checklist

Evaluate the **full setup across all tools** against these universal principles:

| # | Principle | What to check |
|---|-----------|---------------|
| 1 | **Token efficiency** | Is every instruction earning its tokens? Remove anything the model does well by default. Are always-loaded files under budget? |
| 2 | **Altitude calibration** | Are instructions at the right abstraction? Two failure modes: (a) brittle — hardcoded if-else for things the model can judge, (b) vague — platitudes without concrete behavioral signals |
| 3 | **Tool minimalism** | Minimal tool set per agent; no ambiguous routing overlap. "If a human engineer can't definitively say which tool to use, an AI agent can't do better" |
| 4 | **Just-in-time retrieval** | Does the setup prefer dynamic loading (file reads, tool calls) over pre-loading large context blocks? |
| 5 | **Compaction safety** | Will critical state survive context window resets? Are preservation rules explicit? |
| 6 | **Sub-agent boundaries** | Clean context separation; summaries (1–2K tokens) returned, not raw data dumps. Sub-agents do NOT inherit parent context |
| 7 | **Example quality** | Canonical examples provided where behavior is ambiguous. Quality over quantity — no laundry lists of edge cases |
| 8 | **Progressive disclosure** | Can the agent incrementally discover context through exploration rather than front-loading everything? |
| 9 | **No context pollution** | Blocks that rarely apply but always consume attention — move to on-demand retrieval |
| 10 | **Structured note-taking** | Persistent memory (memory directory, lessons.md) supports long-horizon tasks |

---

## Step 10 — Quality Safety Check

For every token-saving proposal, verify it won't degrade agent output:

| # | Risk | Mitigation |
|---|------|------------|
| 1 | **Reference vs inline** | When replacing inline rules with a file reference, the agent must reliably load that file. Use mandatory first-step directives ("Before doing X, read Y") — not passive references |
| 2 | **Sub-agent context boundary** | Sub-agents do NOT inherit parent context. Verify the agent has the Read tool AND the directive is imperative, not informational |
| 3 | **Actionable details in workflows** | When slimming documentation, check if specific details (URL patterns, fallback instructions, example formats) are still reachable. Don't remove the only copy of a workflow detail |
| 4 | **Always-loaded vs on-demand** | Content removed from always-loaded files (CLAUDE.md, copilot-instructions.md, `alwaysApply` Cursor rules) is safe only if the authoritative copy lives in a file loaded when needed |
| 5 | **Semantic preservation** | After condensing, verify every behavioral constraint from the original is still present. Shorter is only better if meaning is preserved |
| 6 | **Cross-tool breakage** | AGENTS.md is shared by multiple tools. Removing content may leave Copilot, Cursor, or Codex without that guidance. Check every tool that reads it before proposing changes |
| 7 | **Security regression** | Any change that removes a guardrail — even for token savings — requires explicit verification that the protection is preserved elsewhere. Never trade security for brevity |
