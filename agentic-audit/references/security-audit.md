# Security Guardrail Audit (Step 3)

## Contents
- Universal Security Checklist (all tools)
- Tool-Specific Security Checks
- Security Severity Escalation
- Real-World Incidents (reference)

**This is the highest-priority audit step.** Security findings are always High severity regardless of how many other findings exist. Run this step before all others that inspect individual files.

Sources: Anthropic Claude Code Security docs, OpenAI Codex Agent Approvals & Security, GitHub Agentic Workflows Security Architecture ("Zero-Secret Agents", "Staged Write Verification"), Anthropic prompt injection mitigation guide, Cursor CurXecute (CVE-2025-54135) and MCPoison (CVE-2025-54136) research.

## 3a. Universal Security Checklist (all tools)

Apply these checks across every config file, agent prompt, rules file, and instruction file found in Step 1.

### Minimal Privilege — Verify for every agent and rule

| Check | What to look for |
|-------|-----------------|
| **Read-only agents have no write tools** | Agents described as "investigation", "planning", "advisory", or "read-only" must NOT have Write, Edit, or Create tools in their frontmatter. Having these tools available — even if the prompt says not to use them — is a misconfiguration |
| **Write-capable agents gate every action** | Agents with Write, Edit, Bash, or MCP tools must have an explicit approval requirement: "MUST get explicit user approval before writing/editing/creating any file" — not just "be careful" |
| **Bash-capable agents restrict destructive commands** | Any agent with the Bash tool must explicitly prohibit (not just discourage) a set of destructive commands. See destructive operation guards below |
| **Tool set matches actual usage** | If an agent prompt uses no Bash commands, it should not have the Bash tool. If it never writes files, no Write tool. Unused tools expand the attack surface |

### Destructive Operation Guards — verify in every Bash-capable agent

The following commands must be **explicitly prohibited** (not just mentioned) in any agent that has the Bash tool:

```
MUST prohibit:
- git push --force / git push --force-with-lease  (to main/master/develop)
- git reset --hard*
- git checkout (branch switching) / git checkout . / git checkout -- <file> / git restore . / git clean -f
- git branch -D (force delete)
- rm -rf
- DROP TABLE / DROP DATABASE (any SQL destructive DDL)
- Any command that destroys uncommitted work
```

Flag agents that have Bash tool but no destructive command prohibitions.

### Prompt Injection Surface — identify all untrusted input channels

Prompt injection is ranked #1 (LLM01) in the OWASP Top 10 for LLM Applications 2025. Attackers don't break the model — they convince it. Map every place where untrusted external content enters agent context:

| Input source | Risk level | Required mitigation |
|-------------|------------|---------------------|
| Issue tracker content — Jira, Linear, GitHub Issues (title, description, comments) | High | Agent must not execute instructions found in ticket text; treat as data, not commands |
| PR title / description / body | High | Same — see RoguePilot and the GitHub MCP private-repo leak in Real-World Incidents |
| Web fetch / URL content | High | Use isolated context windows; never pipe web content directly to bash |
| File content from untrusted directories | Medium | Validate before acting on instructions found in files |
| User-provided file paths | Medium | Restrict to working directory; flag attempts to escape via `../` |
| Git commit messages / branch names from remote | Medium | Treat as untrusted data |

For each agent that processes any of the above: verify its prompt explicitly states that external content is treated as data, not instructions.

### Secrets and Credentials — scan all config files

Scan every file discovered in Step 1 for patterns that indicate hardcoded secrets:

```
Flag if any file contains patterns matching:
- API key patterns: long alphanumeric strings (32+ chars) in key/token/secret/password context
- Bearer tokens: "Bearer <token>", "Authorization: <value>"
- Connection strings: "mongodb://", "postgresql://", "mysql://" with credentials
- Private keys: "-----BEGIN ... PRIVATE KEY-----"
- Hardcoded credentials: username/password pairs
- AWS/GCP/Azure credentials: AKID*, service account JSON
```

Also verify:
- Any agent lessons/learnings file contains no secrets or customer data (if the project uses a per-entry data-safety marker, it is present on every entry)
- Memory files contain no tokens, credentials, or PII

### Write-Operation Approval Gates — cross-tool check

The "no write without explicit approval" principle must be present in EVERY tool's config:

| Tool | Where to check | What to look for |
|------|---------------|-----------------|
| Claude Code | `CLAUDE.md` (and anything it imports, e.g. `AGENTS.md`) | An explicit rule: no file writes without explicit user approval |
| AGENTS.md | Top of file | Equivalent write-protection statement for Codex/Copilot/Cursor |
| Cursor | `alwaysApply` rule | Prohibition on autonomous file editing without confirmation |
| Copilot | `copilot-instructions.md` | Instruction to propose changes, not auto-apply |

Flag any tool that has no write-operation approval gate in its always-loaded config.

### MCP Security

MCP servers dramatically expand agent attack surface. For any MCP server configured (in `.claude/settings.json`, `.codex/config.toml`, or Cursor settings):

| Check | Requirement |
|-------|------------|
| **Source trustworthiness** | Server is from a known, trusted provider — not an unknown community package |
| **Version pinning** | Server version is pinned, not floating (`latest`) — floating versions enable supply chain attacks |
| **Scope justification** | Each MCP server has a documented reason for being included; unused servers are removed |
| **No automatic tool-chaining** | Agent configs do not allow MCP tools to automatically invoke each other without human checkpoint |
| **New server approval** | Adding new MCP servers requires explicit team approval (tracked in version control) |

Treat MCP toolchains like a supply chain: every node requires vetting. See MCPoison and the GTG-1002 campaign in Real-World Incidents.

### Audit Trail

| Check | What to look for |
|-------|-----------------|
| **Cursor rules in git** | `.cursor/rules/` files are committed, not in `.gitignore`. Untracked rules = unauditable AI behavior |
| **Agent-authored commits are reviewable** | No CI automation that auto-merges agent-generated commits without human review |
| **ConfigChange hooks** | Claude Code settings should configure a `ConfigChange` hook if organizational audit logging is required |
| **Codex telemetry** | If compliance is required, OTel integration is configured in `.codex/config.toml` |

## 3b. Tool-Specific Security Checks

### Claude Code

- **Sandbox mode**: Is `/sandbox` or `devcontainer` used for high-risk operations? If agents run bash freely without sandboxing, flag it
- **Command allowlist review**: Allowlisted commands in `.claude/settings.json` should be reviewed — overly broad allowlists (e.g., `bash *`) defeat the permission system
- **MCP trust verification**: New MCP servers require explicit trust (`claude mcp add` with review) — verify no MCP servers are added silently
- **Web fetch isolation**: Agents that fetch external URLs should use isolated context; direct `curl | bash` patterns are prohibited
- **Write scope**: Agents must only write within the working directory — no `../` escape paths
- **Fail-closed**: Unrecognized commands should default to requiring approval (fail-closed), not silently allowed

### OpenAI Codex

- **Sandbox bypass prohibited**: Whatever auto-approve policy the team allows for file edits should be stated explicitly in AGENTS.md. `--dangerously-bypass-approvals-and-sandbox` (removes ALL sandbox constraints) should be prohibited.
- **Approval policy is not `never`**: `.codex/config.toml` `approval_policy` must not be set to `never`. Recommended: `on-request`
- **Network access is restricted**: `network_access = true` should only appear where explicitly required, documented, and reviewed
- **Protected paths remain read-only**: `.git/`, `.codex/`, and any shared agent-config folder must not be writable by agent tasks
- **Secrets excluded from agent phase**: Cloud execution removes secrets before the agent phase — verify local workflows follow the same pattern (no credentials in environment at agent runtime)

### GitHub Copilot

- **Zero-secret principle**: `copilot-instructions.md` and all `.github/instructions/` files must contain zero credentials, tokens, or authentication material
- **Treat repo content as untrusted**: Instructions must not tell Copilot to automatically execute actions derived from PR descriptions, issue text, or file content — these are RoguePilot-class attack vectors
- **No passive prompting**: Copilot should not be configured to automatically initiate actions based on repository events without human trigger
- **Symlink restriction**: Instructions must not direct Copilot to follow symlinks outside the workspace
- **Token lifetime**: Any GitHub token used by Copilot agents should be scoped to minimum required permissions and short-lived

### Cursor

- **Auto-accept policy is explicit**: If auto-accept / YOLO mode for file edits is allowed, that policy is stated in AGENTS.md or team config. Git push should always require explicit user permission.
- **MCP config write protection** (CurXecute — CVE-2025-54135): MCP configuration files must not be writable by AI agents. A malicious prompt summarized by Cursor can rewrite MCP configs and achieve arbitrary code execution. Verify `.cursor/mcp.json` is not in any `@file:` write directive
- **No team-poisoning via shared config** (MCPoison — CVE-2025-54136): A committed `.cursor/mcp.json` approved once can later be silently swapped for a malicious command. Changes to shared MCP config must go through code review, and Cursor must be ≥ 1.3. Apply the same scrutiny to `alwaysApply: true` rules — shared rules load for every team member
- **Dependency installation guardrail**: At least one rule must explicitly state: never install packages, dependencies, or tools based solely on AI suggestion — always verify with `npm audit` / `socket.dev` / human review
- **High-risk shell command guardrail**: Rules must explicitly flag or prohibit: recursive file deletion, force git operations, direct database mutations, and production environment commands
- **Public rule hygiene**: Rules files must contain no sensitive business logic, proprietary algorithms, internal URLs, or credentials that would be exposed if the repo becomes public

## 3c. Security Severity Escalation

All security findings are **High severity** by default. Escalate to **Critical** for:
- Hardcoded secrets or credentials found in any config file
- Read-only agent with Write/Edit tools in frontmatter
- `approval_policy: never` (removes all approval gates) / Git push without explicit user permission
- Agent that ingests external content with no prompt injection mitigation
- MCP server from unverified source or with floating version

## Real-World Incidents (reference)

Use these to explain *why* a finding matters in the Rationale field. Cite only incidents from this list or ones you have verified from a primary source — never invent CVE numbers or dates.

| Incident | Date | What happened | Lesson for audits |
|----------|------|---------------|-------------------|
| [GitHub MCP private-repo leak](https://invariantlabs.ai/blog/mcp-github-vulnerability) (Invariant Labs) | May 2025 | A malicious issue in a public repo hijacked an agent using the GitHub MCP server, which then pulled private-repo data into context and leaked it via an auto-created PR in the public repo. Architectural, not a code bug. | Treat issue/PR text as untrusted data; scope MCP tokens to the minimum repos; require approval before agent-created PRs or cross-repo reads. |
| [Amazon Q Developer extension — CVE-2025-8217](https://aws.amazon.com/security/security-bulletins/AWS-2025-015/) | Jul 2025 | An over-scoped GitHub token in CI let an attacker commit a prompt instructing the assistant to wipe local machines and AWS resources into v1.84.0 of the VS Code extension. A syntax error kept it from executing. | Agent prompts and tooling are supply chain; least-privilege CI tokens; destructive-command guards must exist even if "nobody would ask for that". |
| [CurXecute — CVE-2025-54135](https://www.tenable.com/blog/faq-cve-2025-54135-cve-2025-54136-vulnerabilities-in-cursor-curxecute-mcpoison) (Cursor) | Aug 2025 | Prompt injection could get the agent to write to the MCP config file, achieving arbitrary code execution. | MCP configuration files must not be agent-writable. |
| [MCPoison — CVE-2025-54136](https://www.tenable.com/blog/faq-cve-2025-54135-cve-2025-54136-vulnerabilities-in-cursor-curxecute-mcpoison) (Cursor) | Aug 2025 | Once a collaborator approved an MCP server in a shared repo, its command could be silently swapped for a malicious one with no re-prompt. Fixed in Cursor 1.3. | Shared/committed MCP and rules config needs review on every change, not just first approval. |
| [GitHub Copilot RCE — CVE-2025-53773](https://www.tenable.com/cve/CVE-2025-53773) | Aug 2025 | Prompt injection in source files, web pages, or issues got Copilot to set `"chat.tools.autoApprove": true` in `.vscode/settings.json`, disabling confirmations and enabling command execution. | Agents must not be able to edit their own permission/approval settings; protect editor and agent config paths. |
| [GTG-1002 AI-orchestrated espionage campaign](https://assets.anthropic.com/m/ec212e6566a0d47/original/Disrupting-the-first-reported-AI-orchestrated-cyber-espionage-campaign.pdf) (Anthropic report) | Sep 2025 (reported Nov 2025) | A state-sponsored group built an attack framework around Claude Code and MCP tools against ~30 organizations, with the model doing most of the tactical work under light human supervision. | Agent + tool access is a force multiplier for attackers too; vet every MCP server and keep humans in the loop for consequential actions. |
| [RoguePilot](https://orca.security/resources/blog/roguepilot-github-copilot-vulnerability/) (Orca Security, GitHub Codespaces) | Feb 2026 | Hidden instructions in a GitHub issue were fed to Copilot when a Codespace was opened from it, leading to exfiltration of the privileged `GITHUB_TOKEN`. Patched by Microsoft. | Never auto-feed issue/PR content to an agent with tool access; treat symlinks and remote schema fetches as exfiltration paths. |

Further reading: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) — especially LLM01 Prompt Injection and LLM06 Excessive Agency.
