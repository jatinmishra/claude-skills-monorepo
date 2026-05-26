---
name: pr-diff-mermaid
description: Visualize the structural changes in a GitHub pull request as a small set of focused Mermaid diagrams. Use this skill whenever the user provides a GitHub PR URL and asks to visualize, diagram, illustrate, explain, summarize structurally, or "see" the changes — even if they don't say "Mermaid" explicitly. This skill is tuned for iOS / Swift codebases in its v1 form; mention this if the PR is in another language. Do NOT use this skill for line-by-line diff review, code-quality feedback, or generic PR summaries that don't need a diagram.
---

# PR Diff Mermaid Visualizer (v1 — Swift / iOS)

Turn a GitHub PR into a small set of **focused** Mermaid diagrams that show *what changed in the system*, not what changed in the text. GitHub already shows the lines; the diagrams should show the structure.

## What this skill does and does not do

**Does:** fetch a PR via `gh`, read the diff, break it into 1–3 logical chunks, and produce one Mermaid diagram per chunk with a one-line caption. Outputs the raw Mermaid source so the user can paste it into a PR description.

**Does not:** review code, comment on quality, draw every file, or produce one giant hairball diagram. If there's nothing structural to show, say so plainly and stop.

## Inputs

The only supported input in v1 is a **GitHub PR URL** (or `owner/repo#123` shorthand). The `gh` CLI must be available. If the user pastes a diff or gives a local path, tell them v1 only supports PR URLs and ask for one.

## Workflow

Follow these steps in order. Don't skip the chunking step — it's where the value is.

### Step 1 — Fetch the PR

```bash
gh pr view <url> --json title,body,additions,deletions,changedFiles,files
gh pr diff <url>
```

Capture the metadata (title, file list, +/- counts) and the full diff. If `gh` errors (auth, not found, private repo), surface the error and stop — don't try to work around it.

### Step 2 — Size and language gate

Before doing anything else, check:

- **Total changed lines** (additions + deletions). If > 600, tell the user the PR is large and ask whether to proceed on a best-effort basis or focus on a subset of files. Don't silently produce a degraded diagram.
- **Languages present.** If the PR is not predominantly Swift (`.swift` files), say so explicitly: *"This skill is tuned for Swift/iOS in v1. I'll do my best with this <language> PR but accuracy may be lower."* Then continue.
- **Triviality check.** If the PR is *only* one of:
  - Lockfile / `Package.resolved` / `Podfile.lock` changes
  - Formatting, whitespace, or import reordering
  - Version bumps or string-only changes (e.g. localized strings)
  - A single file under ~50 lines with no new types or methods

  → **Do not draw a diagram.** Output a 1–3 sentence prose summary instead and stop.

### Step 3 — Read the diff and inventory changes

Read the diff carefully. Before drawing anything, produce an internal inventory (you can show this to the user too — it grounds the diagrams and catches your own mistakes). Group by file, but capture *Swift entities*, not lines:

- **Types added/removed/modified**: `class`, `struct`, `enum`, `actor`, `protocol`, `extension`
- **Members added/removed/modified**: methods, computed properties, initializers, cases of an enum
- **Protocol conformances** added or removed (e.g. `: SomeProtocol` appearing/disappearing in a declaration)
- **Property wrappers and attributes** when they signal architecture: `@MainActor`, `@Observable`, `@Published`, `@StateObject`, `@Environment`, `@ViewBuilder`
- **Call sites** between changed entities visible in the diff (don't invent calls you can't see)
- **Module-level changes**: new files, deleted files, files moved between targets
- **SwiftUI views**: a new `View` struct, or a body that gains/loses a child view

You are the parser here. Be careful and conservative — if the diff doesn't show it, don't draw it.

### Step 4 — Chunk the PR into 1–3 concerns

This is the most important step. **One diagram per concern**, not one diagram per PR. Look at the inventory and group changes by *what they're doing*. Common Swift/iOS chunk shapes:

| Chunk shape | Examples |
|---|---|
| Type / protocol restructure | New protocol + conformances; class → struct; splitting a god-object |
| New view hierarchy | New SwiftUI screen and its child views |
| New flow / sequence | New tap handler → ViewModel → service → network; new async function calling existing ones |
| Dependency / module rewire | A type moves modules; a service gets injected somewhere new; imports added across files |
| State / lifecycle change | New `@Observable` ViewModel replaces `ObservableObject`; new state enum drives navigation |

Aim for **1 chunk if the PR does one thing, 2–3 if it does several**. If you'd need 4+ chunks, the PR is doing too much for v1 to visualize well — pick the 2–3 most important and note in prose that you've omitted the rest.

For each chunk, pick the diagram type that fits:

- **classDiagram** — type/protocol restructures, conformance changes, SwiftUI view composition shown as containment
- **sequenceDiagram** — new flow across 2+ types (user action → ViewModel → service → result)
- **flowchart** — module/file-level rewiring, dependency edges, or anything that doesn't fit the above

Don't force a diagram type. If a chunk is best expressed in two short sentences of prose, do that and move on.

### Step 5 — Draw each diagram

Apply these rules to every diagram:

**Scope rules**
- Include only entities that changed, plus their *immediate* neighbors mentioned in the diff.
- Hard cap: **30 nodes per diagram**. If you'd exceed this, collapse unchanged siblings into a single `...N others` node or split the chunk.
- Every diagram needs a one-sentence caption above it explaining what it shows.

**Visual diff encoding (use these exact `classDef`s every time)**

```
classDef added fill:#d4f4dd,stroke:#22863a,color:#000
classDef removed fill:#ffd7d5,stroke:#cb2431,color:#000,stroke-dasharray: 5 5
classDef modified fill:#fff5b1,stroke:#b08800,color:#000
classDef context fill:#f6f8fa,stroke:#6e7781,color:#000
```

Apply with `class NodeID added` (or `cssClass NodeID added` inside a `classDiagram`). Unchanged neighbors get `context`. Same palette across every diagram so the user only learns it once.

**Per-diagram-type guidance**

`classDiagram`:
- Use `class Name { +method() +property: Type }` form. Show only the members that changed; don't dump every member.
- Protocol conformance: `Protocol <|.. Type` (dashed = realizes). Inheritance: `Parent <|-- Child`.
- For SwiftUI view composition, you can use containment: `ParentView *-- ChildView`.
- Apply colors with `cssClass NodeID added` lines at the bottom.

`sequenceDiagram`:
- Participants are types or layers (e.g. `View`, `ViewModel`, `Service`, `API`). Don't put individual functions as participants.
- Use `->>` for sync calls, `-->>` for returns, `->>+` / `-->>-` to show activation when it clarifies.
- Add a `Note over X: new in this PR` to flag what's added rather than coloring (sequence diagrams have weaker color support).

`flowchart`:
- Default to `flowchart TD` (top-down). Use `LR` only for long pipelines.
- Nodes are files or modules. Edges are imports or "uses".
- Apply colors with `class NodeID added`.

**Self-check before output** (do this for every diagram, silently):
- First line declares the diagram type (`classDiagram`, `sequenceDiagram`, `flowchart TD`).
- Every node referenced on an edge is defined.
- Arrow syntax matches the diagram type (`-->` in flowchart, `->>` in sequence, `<|--` / `*--` / `..>` in class).
- Node IDs have no spaces or reserved characters; labels with spaces are quoted (`A["My Label"]`).
- Every `classDef` you reference is defined; every `class X added` references a defined `classDef`.
- Node count ≤ 30.

If something's borderline, prefer the simpler/more common syntax over the clever one.

### Step 6 — Present the result

Structure the response as:

1. **One-sentence PR summary** — what the PR does, in plain prose. Not a restatement of the title.
2. **For each chunk (1–3 total):**
   - A short heading naming the chunk (e.g. "Auth refactor: strategy pattern")
   - The one-line caption
   - The Mermaid diagram in a ` ```mermaid ` fenced block
3. **What's omitted** — if you chunked aggressively or skipped trivial files, say so in one line at the end.

Don't add a "Conclusion" or restate things. The diagrams are the deliverable.

## Examples of decisions

**PR adds a new `LoginViewModel`, a `LoginView` that uses it, and an `AuthService` protocol with two implementations.**
→ 2 chunks: (a) `classDiagram` showing the protocol + its two implementations + ViewModel's dependency on it; (b) `sequenceDiagram` showing `LoginView → LoginViewModel → AuthService → API`.

**PR replaces `ObservableObject` with `@Observable` across 6 ViewModels.**
→ 1 chunk: `classDiagram` showing the 6 ViewModels with the modified attribute, marked `modified`. One-sentence caption explaining the macro migration.

**PR is a `Package.swift` version bump and one comment fix.**
→ No diagram. 1-sentence prose summary, stop.

**PR adds a feature flag check in 14 different files.**
→ 1 chunk if there's a common pattern (`flowchart` with the flag as a hub node and the 14 sites as leaves, capped at the most representative ones). Note the rest in prose.

## What "good" looks like

A user pastes a PR URL and gets back: a one-line summary, 1–3 small diagrams they can immediately understand, and the Mermaid source ready to paste into the PR description. They don't need to read the diff to know what changed structurally — the diagrams already told them.

A user pastes a trivial PR URL and gets back: a two-sentence summary and no diagram, because there's nothing structural to show. That's a success, not a failure.
