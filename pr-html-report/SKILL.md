---
name: pr-html-report
description: >
  Generates two paired HTML reports for a GitHub PR: a "What Changed" document
  (architecture diagrams, flow charts, file breakdown, design decisions) and a
  "Code Review" document (ticket completeness matrix, findings by severity, tier
  classification). Use whenever the user asks to generate, create, or produce an
  HTML report, artifact, or visual summary for a PR. Accepts a GitHub PR URL.
  Do NOT use for in-conversation code review text output — use /code-review for
  that. This skill produces files on disk.
---

# PR HTML Report Skill

Generate two paired, self-contained HTML files for any GitHub PR:

| File | Purpose |
|---|---|
| `pr{N}-change.html` | What the PR does — architecture layers, flows, file breakdown grouped by concern, key design decisions |
| `pr{N}-review.html` | Code review output — ticket completeness matrix, findings (❌/⚠️/💡/🚀), tier classification with weighted score bars, blockers checklist |

Both files link to each other via a nav bar and share the same dark visual design system.

---

## When to Use / Not Use

- **Use**: user says "generate an HTML report for PR", "create HTML artifacts for", "make a visual summary", "give me the html files"
- **Do NOT use**: user wants a code review in the conversation (use `/code-review`)

---

## Inputs

Primary input: a **GitHub PR URL** (`https://github.com/owner/repo/pull/N`).

Optional context:
- `--output-dir <path>` — where to write the files (default: project root `.`)
- Findings from a code-review skill (e.g. `/code-review`) if already run in this session — reuse rather than re-derive
- `--ticket-pattern <regex>` — issue-key pattern to extract from the PR title/branch (default: `[A-Z][A-Z0-9]+-[0-9]+`, which matches Jira-style keys)

---

## Workflow

### Step 0 — Confirm scope

Before doing any work, use `AskUserQuestion` to ask what the user needs:

```
Which artifacts do you want generated?
  • Both (change summary + code review)  [default]
  • Change summary only  (pr{N}-change.html)
  • Code review only  (pr{N}-review.html)
```

Use the answer to skip unnecessary steps:
- **Change summary only**: skip Step 2 (code review) and skip generating `review.html`
- **Code review only**: skip the architecture diagram, flow diagrams, and design decisions sections; skip generating `change.html`
- **Both**: proceed with all steps as normal

If the user already specified scope in their invocation (e.g. "just the summary" or "only the review"), skip the question and infer from their message.

### Step 1 — Gather PR context

Use whatever tools are available (`gh pr view`, `git log`, `git show`, `git diff`) to extract:

- PR title, description, head/base branch, ticket IDs
- File list with add/modify/remove status and +/- counts
- Commit messages

Read key source files directly from the branch (do not check out). Prioritise: new public types / facades / protocols, core orchestrators, concurrency primitives, error handling, one representative test file per layer. For large PRs (50+ files), exclude generated files first, then spot-check 2–3 representative files per functional group.

### Step 2 — Run a code review (source of truth for findings)

If a code-review skill is available (e.g. `/code-review`, or a team-specific review skill), invoke it on the PR diff. Its structured findings — severity classifications, code snippets, scores — drive `review.html`.

**If a code review was already run in this session**: reuse those findings directly. Do not re-derive independently.

**If no code-review skill is available**: derive findings manually by reading the diff, using the rating system below, and note in the HTML that no automated review skill was used.

The review.html file is a visual rendering of the review output, not a separate review pass.

### Step 3 — Check ticket completeness

Extract ticket IDs from the PR title and branch name using the ticket pattern (see Inputs). Fetch each ticket with whatever issue-tracker access is available — an MCP connector (Jira, Linear, GitHub Issues), or a CLI such as `acli jira workitem view <ID>` or `gh issue view <N>`. If none is available, derive the completeness matrix from the PR description and commits only, and show a callout noting this in the HTML. If no ticket IDs are found at all, skip the matrix and say so.

### Step 4 — Generate the HTML artifacts

This is the primary deliverable. Write both files using the Design System below. Aim for richly visual, information-dense output — the HTML files are meant to communicate at a glance and stand alone without needing to read the PR itself.

Output paths (default: project root):
- `pr{N}-change.html`
- `pr{N}-review.html`

Where `N` is the PR number (e.g. `123`).

---

## Rating System

Used to compute the tier score for `review.html` (sourced from the code-review output). The weights below are tuned for Swift/iOS PRs — adapt the dimension names for other stacks (e.g. replace "SwiftUI Implementation" with the relevant UI framework):

| Dimension | Weight |
|---|---|
| Architecture & Design (SOLID, DI, separation of concerns) | 20% |
| Code Quality (Swift best practices, clean code, naming) | 18% |
| SwiftUI Implementation (if applicable) | 15% |
| Error Handling (logging, crash reporting, try? discipline) | 12% |
| Memory Management (retain cycles, threading, Sendable) | 12% |
| Test Coverage (unit, integration, edge cases) | 10% |
| Threading Safety (main actor, async, race conditions) | 8% |
| Documentation (inline, API, architectural decisions) | 5% |

**Tier mapping:**
- **Tier 1 🏆** (4.5–5.0): Approve immediately
- **Tier 2 ✅** (3.5–4.4): Approve with minor suggestions
- **Tier 3 ⚠️** (1.0–3.4): Request changes

**Critical issue deductions:** memory leaks/crashes −1.0–1.5, security −1.5–2.0, threading −0.5–1.0, missing critical tests −0.5–1.0, poor error handling −0.3–0.8.

---

## Design System

Both HTML files use a shared dark-mode design system. Copy these CSS custom properties and component patterns exactly for visual consistency.

### CSS Variables

```css
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface2: #1c2128;
  --surface3: #21262d;
  --border: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --blue: #58a6ff;
  --green: #3fb950;
  --yellow: #d29922;
  --orange: #f0883e;
  --red: #f85149;
  --purple: #bc8cff;
  --teal: #39d353;
  --accent: #1f6feb;
}
```

### File Nav (top of every file)

```html
<div class="file-nav">
  <a href="pr{N}-change.html" class="file-nav-btn [active?]">📝 What Changed</a>
  <span class="file-nav-sep">/</span>
  <a href="pr{N}-review.html" class="file-nav-btn [active?]">🔍 Code Review</a>
</div>
```

Active tab: `background: var(--accent); color: #fff;`. Inactive: `background: var(--surface); color: var(--muted);`.

### Architecture Layer Box

Each layer is a colored div. Use these color classes:

| Layer type | Background | Border | Heading color |
|---|---|---|---|
| Consumer / caller | `#1a2744` | `#3d6b99` | `var(--blue)` |
| Public facade | `#162714` | `#3fb950` | `var(--green)` |
| Manager / orchestrator | `#1f1809` | `#f0883e` | `var(--orange)` |
| Infrastructure / concurrency | `#1e1826` | `#bc8cff` | `var(--purple)` |
| External SDK | `#111c2e` | `#58a6ff` | `var(--blue)` |
| External service / store | `#181c21` | `#444c56` | `var(--muted)` |

Connect layers with `↓` arrows and optional small labels (`public API surface`, `async boundary`, etc.).

### Flow Node Classes

```css
.fn-consumer  { background: #1a2744; border-color: #3d6b99; color: var(--blue); }
.fn-action    { background: #162714; border-color: #3fb950; color: var(--green); }
.fn-system    { background: #1e1826; border-color: #bc8cff; color: var(--purple); }
.fn-success   { background: #162714; border-color: #3fb950; color: var(--green); }
.fn-cancel    { background: #211d07; border-color: #d29922; color: var(--yellow); }
.fn-error     { background: #200e0e; border-color: #f85149; color: var(--red); }
.fn-warn      { background: #1f1507; border-color: var(--orange); color: var(--orange); }
.fn-note      { background: var(--surface2); border-color: var(--border); color: var(--muted); }
```

Flow nodes are `border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 500; border: 1px solid; text-align: center;`.

Split paths use a `.fsplit` flex row with `.fbranch` columns, each preceded by a small `.fbranch-lbl` italic label (e.g. ".userCancelled", ".verified ✅").

### Finding Severity Blocks

```css
.f-critical  { background: #1a0a0a; border-left: 3px solid var(--red); }
.f-important { background: #1a1007; border-left: 3px solid var(--orange); }
.f-consider  { background: #0a1524; border-left: 3px solid var(--blue); }
.f-excellent { background: #0a1a0a; border-left: 3px solid var(--green); }
```

Badge colors:
```css
.b-critical  { background: #3a0a0a; color: var(--red); }
.b-important { background: #2e1a06; color: var(--orange); }
.b-consider  { background: #0a1f3a; color: var(--blue); }
.b-excellent { background: #0a2a0a; color: var(--green); }
```

### Code Syntax Highlighting (inline spans inside `<pre>`)

```html
<span class="kw">keyword</span>   → color: #ff7b72
<span class="ty">TypeName</span>  → color: #79c0ff
<span class="fn">funcName</span>  → color: #d2a8ff
<span class="cm">// comment</span> → color: #6e7681
<span class="st">"string"</span>  → color: #a5d6ff
<span class="ok">good code</span> → color: var(--green)
<span class="bad">bad code</span> → color: var(--red)
<span class="hl">highlighted bad</span>  → background: rgba(248,81,73,.12)
<span class="hlg">highlighted good</span> → background: rgba(63,185,80,.10)
```

### Stat Strip

6-column grid of cards, each with a large number (`stat-n`) and a small label (`stat-l`). Use `var(--green)` for positive counts, `var(--red)` for deletions, `var(--yellow)` for scores, `var(--teal)` for tier.

### Weighted Score Bar (review.html)

Each dimension row:
```html
<div style="display:flex; align-items:center; gap:10px;">
  <span style="min-width:240px; font-size:12px; color:var(--muted);">Architecture & Design (20%)</span>
  <div style="flex:1; background:var(--surface2); border-radius:4px; height:7px;">
    <div style="width:90%; height:7px; border-radius:4px; background:var(--green);"></div>
  </div>
  <span style="font-size:12px; font-weight:700; color:var(--green); min-width:32px; text-align:right;">4.5</span>
</div>
```

Width percentage = (score / 5.0) * 100.

### File Status Pills

```css
.pill-new  { background: #162714; color: var(--green); }
.pill-mod  { background: #1f1507; color: var(--orange); }
.pill-del  { background: #200e0e; color: var(--red); }
```

Font: `font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 4px;`

### Tabs (interactive)

```html
<div class="tabs">
  <button class="tab active" onclick="switchTab(event,'panel-id')">Tab Label</button>
  ...
</div>
<div id="panel-id" class="tab-panel active">...</div>

<script>
function switchTab(e, id) {
  const root = e.target.closest('.section') || document.body;
  root.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  root.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  e.target.classList.add('active');
  root.querySelector('#' + id).classList.add('active');
}
</script>
```

Active tab border: `border-bottom: 2px solid var(--orange);`

---

## change.html — Required Sections

1. **File nav bar** (links to review.html)
2. **Header** — PR number pill, title, one-line additive/scope note, meta row (files/+/-/branch), ticket chips
3. **Stat strip** — 6 cards: new files, new tests, existing files modified, existing files untouched, docs added, anything removed/cleaned up
4. **"What is this?" explainer** — 2–4 cards in a 2-col grid: plain-English description of the technology/feature being introduced, why it exists, key concepts a reviewer needs to know, why it's additive/safe
5. **Architecture diagram** — layered boxes from consumer to external service, with connection arrows and boundary labels. Every new type gets its own box; group closely related helpers.
6. **Flow diagrams** — 2–3 tabs covering: the primary user-initiated flow (happy + error paths), any background/async flow, and any caching/dedup flow if present. Use `.flow` / `.fnode` / `.fsplit` / `.fbranch` pattern.
7. **Design decisions** — numbered list of non-obvious choices the author made. Derive from PR description, inline code comments, and observed patterns. Each decision: title + 2–3 sentence explanation. Aim for 4–7 decisions.
8. **File change breakdown** — tabbed table: one tab per logical group (framework core, tests, module changes, infra/project). Each row: file path pill, status pill, one-line purpose.
9. **Footer** — date, link to review.html

---

## review.html — Required Sections

The content of this file is sourced from the code-review output (Step 2). The HTML is a rich visual rendering of those findings — not a new review pass.

1. **File nav bar** (links to change.html)
2. **Header** — PR number pill, title "Code Review — [PR title]", ticket chips
3. **Stat strip** — 6 cards: critical count, important count, consider count, excellent count, score/5.0, tier
4. **Ticket Completeness Matrix** — table with columns: Requirement, Ticket, Implementation, Status. One row per requirement from tickets + PR description. If the issue tracker was unavailable, show a callout noting this.
5. **"What's Working Well"** — bulleted list of 🚀 excellent items from the review, one-sentence explanations each
6. **Findings** — all ❌/⚠️/💡 findings from the review in severity order. Each finding:
   - Severity badge + title
   - File path in monospace
   - 1–2 sentence explanation
   - Before/after `<pre>` code block with inline syntax highlighting
7. **Tier Classification** — tier card (large number + stars + score) + weighted bar chart + summary paragraph + 2-col grid: "Must fix before merge" checklist + "Path to Tier 1" checklist
8. **Footer** — date, link to change.html

---

## HTML Quality Bar

The HTML files are the product — hold them to a high standard:

- Fully self-contained: no external CSS, JS, or font dependencies
- `<pre>` code blocks must use inline `<span>` syntax highlighting — no external highlighter
- All tabs must work via the inline `switchTab` function
- Valid HTML5 with `<!DOCTYPE html>`
- Rich and information-dense: a reviewer should be able to understand the PR's intent, scope, and risk from the HTML alone without opening GitHub
- Architecture diagrams and flow diagrams must reflect actual types/paths from the code — never placeholder boxes

---

## Safety Gates

- **Read-only for code**: this skill reads files but never modifies source code
- **Accurate findings only**: all findings in review.html must come from the code-review output or from directly reading the code — never assert line numbers or locations not verified
- **No invented architecture**: only draw layers/types that actually exist in the PR diff or existing code
- **File write confirmation**: always state the full output paths when done

---

## Example invocation

User: `/pr-html-report https://github.com/owner/repo/pull/123`

Expected output:
```
✅ Generated:
  • pr123-change.html  (What Changed — architecture, flows, file breakdown)
  • pr123-review.html  (Code Review — findings, ticket completeness matrix, tier classification)
```
