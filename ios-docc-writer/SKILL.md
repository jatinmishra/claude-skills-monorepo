---
name: ios-docc-writer
description: Researches any flow, module, or kit in an iOS codebase and generates a DocC catalog article for it. Works with any iOS project architecture (SPM, CocoaPods, MVVM, VIPER, Clean, etc.). Invoke with /ios-docc-writer or when the user asks to "create a docc for X", "write DocC documentation for X", or "document the X flow/module/kit".
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
---

You generate DocC documentation for iOS codebases. Given a flow, module, or kit name in `args`,
you research the codebase and produce a complete DocC catalog article viewable in Xcode's
Documentation viewer.

You make no assumptions about architecture, DI framework, or module system — you discover them.

---

## Phase 1 — Parallel Research (launch both subagents simultaneously)

Spawn **two subagents in a single message** so they run in parallel:

### Subagent A: Project Analyzer

Prompt it to discover the project's structure. It must NOT modify any files.

Ask it to report:

1. **Module system** — SPM (`Package.swift` files), CocoaPods (`Podfile`), or plain Xcode targets.
   For SPM: list every target name and its `path` (from all `Package.swift` files found under the
   working directory, excluding `.build/` directories).

2. **Existing `.docc` catalogs** — find every `.docc` directory in the project (excluding
   `.build/`). For each: the path, whether it has a root landing page (`.md` matching the target
   name), and what articles already exist.

3. **Architecture pattern** — infer from file/type naming:
   - Orchestration: broker, coordinator, manager, interactor, use-case, service, view-model
   - Dependency injection: Swinject assembly, Factory macro, manual init, environment values,
     service locator
   - Reactive: Combine publishers, async/await, delegation, NotificationCenter, RxSwift
   - Navigation: Coordinator, Router, NavigationStack, UINavigationController

4. **Naming conventions** — how are public protocols named vs implementations? (e.g. `FooManaging`
   protocol + `FooManager` concrete, or `FooInterface` + `Foo`, or `FooProtocol` + `FooImpl`)

5. **Testing setup** — XCTest, Swift Testing, or both? Where do test targets live?

### Subagent B: Flow Researcher

Prompt it with the user's request from `args`. It must NOT modify any files.

Ask it to report:

1. **Entry-point type** — find the type named in `args`. Report: file path, line number, type kind
   (class / struct / enum / protocol / actor), access level, and every method/property signature.

2. **Full call chain** — trace every type the entry point delegates to, down to the consumer-facing
   public API. For each hop:
   - Type name, file path, line number
   - How it is obtained (DI resolve, `shared` singleton, `init`, factory call, `@LazyInject`, etc.)
   - Key method(s) called across the hop

3. **Selection/factory layer** — if any factory, builder, or `make(for:)` function selects between
   implementations, list every condition → implementation mapping with exact match values.

4. **All concrete implementations** — for each implementation of the key protocol in the chain:
   - What it does differently from siblings
   - Any input → output mapping (e.g. config value → enabled features, role → permission set)
   - Any reactive subscriptions it sets up (publisher name, filter conditions, loop-prevention)

5. **The consumer-facing public API** — the type that callers outside the owning/orchestrating
   layer use. Report every public method, property, and publisher with:
   - Access modifier + signature
   - Thread-safety contract (lock type, actor isolation, or DispatchQueue)
   - Behaviour when called before the system is configured (default state, guard pattern)

6. **Consumer call sites** — find at least 3 concrete usages across different files. For each:
   - File path + line number
   - The exact pattern used (synchronous check, publisher subscription, both combined with another
     system such as feature flags)

7. **Lifecycle hooks** — if the entry-point participates in an app/module lifecycle (init,
   configure, purge, deinit, logout), list every hook and its effect.

8. **Reactive change propagation** — how does a mid-session state change (e.g. settings change,
   logs out, switches account) flow from origin to the UI? Trace the full publisher / delegation
   chain including any loop-prevention.

---

## Phase 2 — Synthesise and determine catalog path

Once both subagents return, combine their outputs:

1. Identify the SPM target (or Xcode framework target) that owns the consumer-facing public API
   found by Subagent B.

2. Using the target list from Subagent A, find that target's source path.

3. Set:
   - `CATALOG_DIR` = `<target-source-path>/<TargetName>.docc`
   - `LANDING_PAGE` = `<CATALOG_DIR>/<TargetName>.md`
   - `ARTICLE_PATH` = `<CATALOG_DIR>/Articles/<ArticleName>.md`
   where `<ArticleName>` is PascalCase derived from `args`
   (e.g. "auth token refresh flow" → `AuthTokenRefreshFlow`).

4. Check (via Bash `ls` or Read) whether `LANDING_PAGE` already exists. If it does, skip
   creating it and only write the article.

---

## Phase 3 — Approval gate

Present to the user — **wait for explicit approval before writing any file**:

```
Files to create:
  1. <CATALOG_DIR>/<TargetName>.md   (landing page — or "skipped, already exists")
  2. <CATALOG_DIR>/Articles/<ArticleName>.md

Article sections:
  • Overview — what the system does and its key module/layer boundary
  • <Entry-point type> — role, lifecycle table, key invocation patterns
  • <Factory/Selection layer> — condition → implementation table
  • <Each implementation> — input→output table, reactive setup, loop-prevention
  • <Consumer-facing API> — method/property table with thread-safety + not-yet-ready behaviour
  • Consumer Patterns — 4 code examples (sync check, publisher subscription, combined check, UI wiring)
  • Full Event Sequence — ASCII trace from trigger to UI effect
  • Adding a New <Feature/Key/Entry> — numbered checklist
```

---

## Phase 4 — Write files

After approval, write both files using the templates below.

### Landing page (`<TargetName>.md`)

Only create if it does not already exist.

```markdown
# ``<TargetName>``

<One sentence from the target's README, top-level comment, or inferred from Subagent A.>

## Overview

<2-3 sentences: what the module/kit provides, where it sits in the architecture.>

## Topics

### Articles
- <doc:<ArticleName>>

### <Logical group — e.g. "Essentials", "Core Types", "Observing State Changes">
- ``<PublicType>``
- ``<PublicType>``

### <Another logical group>
- ``<PublicType>``
```

### Article (`<ArticleName>.md`)

Fill every section from the research. Do not leave any placeholder text.

```markdown
# <Human-readable title>

<One sentence: what this article explains.>

## Overview

<3-4 paragraphs:>
- What the system does and why it exists
- The key architectural boundary (which layer writes state vs which layer reads it)
- ASCII layer diagram showing the full chain from entry point to consumer

## <Entry-Point Type Name>

<Role in the system.>

<Lifecycle table if applicable:>
| Lifecycle call | Effect |
|---|---|
| ... | ... |

<Explanation of any parameter/flag that significantly changes behaviour.>

<Code example: the two most important invocation patterns.>

## <Factory / Selection Layer> (omit section if there is no factory)

<How implementations are selected.>

| <Condition> | <Implementation> |
|---|---|
| ... | ... |

## <Implementation Name> (one H3 per concrete implementation)

<What this implementation does and how it differs from siblings.>

<Input → output table if applicable (e.g. role → permissions).>

<Reactive subscription setup and any loop-prevention.>

## <Consumer-Facing API>

<Role: who writes/configures it and who reads from it.>

| API | Caller | Purpose |
|---|---|---|
| ... | ... | ... |

<Thread-safety contract.>

<Note on behaviour before the system is configured, if the API has a "not yet ready" state.>

## Consumer Patterns

### <Pattern 1: Synchronous check>
```swift
// concrete example from call sites found by Subagent B
```

### <Pattern 2: Reactive subscription>
```swift
// concrete example
```

### <Pattern 3: Combined with a second system>
```swift
// e.g. feature flag + entitlement check, or role check + permission gate
```

### <Pattern 4: UI-layer wiring>
```swift
// SwiftUI modifier, UIKit container view, or equivalent
```

## Full Event Sequence

<ASCII trace from the user-facing trigger to the final UI effect.
 Cover both the launch path and the mid-session change path if they differ.>

## Adding a New <Feature / Key / Permission / Entry>

1. <Where to add the new case/type>
2. <Where to update the mapping/logic>
3. <Where to add the check at call sites>
4. <What tests to write and why the static/pure function makes this testable>
```

---

## Quality Rules

- **No placeholder text.** Every table cell, every code snippet, every section must come from
  actual research. If Subagent B could not find 3 consumer call sites, use what was found and
  note the gap explicitly.
- **Accurate types and strings.** Plan descriptions, key raw values, publisher names — copy the
  exact literals from source files. Do not paraphrase.
- **Compilable Swift snippets.** Every code block must use real types. Adapt from the actual call
  sites, not from memory or imagination.
- **Adapted structure.** If the flow has no factory layer, omit that section. If there are 5
  implementations instead of 3, include all 5. Follow the evidence, not the template rigidly.
- **ASCII diagrams must match package boundaries.** If two types live in different SPM targets,
  the diagram boundary must reflect that.
- **No emoji.** DocC renders in Xcode — keep it professional.
- **No trailing summary.** End the article after the last section.

---

## After writing

Tell the user:

> Build documentation in Xcode: **Product → Build Documentation** (⌃⇧⌘D), then navigate to
> `<TargetName>` in the Documentation viewer to see the rendered article.
