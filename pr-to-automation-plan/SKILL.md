---
name: pr-to-automation-plan
description: >
  Takes a pull request, branch, or diff in an iOS app repo and produces a written
  plan (a markdown file) for adding Appium/TestNG (or similar) UI automation
  coverage in a separate automation repo for whatever changed. Use this skill
  whenever the user gives a PR URL/number, a branch name, or "the changes on
  branch X" in an iOS app repo and asks to plan, scope, or design automation tests
  for it — even if they don't name the automation repo explicitly. Covers both the
  Swift-side accessibility-identifier gaps the diff introduces (designed
  concretely, not just flagged) and the automation-side Page Object / test-case /
  suite plan. Does not write any code in either repo — output is a plan file only.
license: MIT
---

# PR → Automation Plan

Turn a PR/branch in an **iOS app repo** into a single markdown plan for adding
UI automation coverage (typically Appium + TestNG/Java) in a **separate automation
repo**, including any Swift accessibility-identifier work the diff makes necessary.
The method: trace the real diff, verify every design decision against source instead
of assuming, then write the plan down.

**This skill is planning-only.** It never edits Swift or automation-repo source, never
creates branches, never commits. Its one output artifact is a markdown plan file —
writing that file is the deliverable the user is asking for by invoking this skill,
so it does not need a separate approval prompt. Everything else stays read-only.

## Inputs

Accept any of:
- A GitHub PR URL or `owner/repo#123` shorthand (requires `gh`)
- A branch name in the local app-repo checkout (diffed against the repo's default/integration
  branch — detect it with `git symbolic-ref refs/remotes/origin/HEAD` or ask; don't assume `main`)
- A raw diff pasted by the user

Also needed: the **path to the local automation repo checkout**. If it isn't obvious from the
working directory or the user's message, ask for it.

If no diff source is given, ask for one — don't guess which branch/PR to plan for.

The user may volunteer some of the following up front. **Anything they don't
volunteer gets asked in Phase 2 — never silently defaulted.** Ground a *suggested*
answer in what the diff actually shows, but still put it in front of the user as a
question rather than assuming it:
- Entry path / screen path to drive the new flow through, if there's more than one
  plausible way to reach it
- Depth of assertions wanted (shallow/presence vs. exact-match)
- Where to save the output file
- Scope, if the diff plausibly touches more than one independently-testable flow

## Guardrails

- Read-only in both repos except for the one final `Write` of the plan file.
- Never run `git checkout`, `git commit`, `git push`, or any mutating git command.
  Diff against refs without checking them out: `git diff <base>...<branch>`,
  `git log <branch>`, `git show <branch>:<path>` all work without touching the
  working tree.
- Never fabricate an accessibility identifier as already existing — grep and read
  the real file. If a control has no identifier and needs one, *design* it (this
  skill's job), don't assume one exists.
- Never invent ticket IDs, test-management case IDs, or file paths in the automation
  repo — leave them as explicit open items if unresolved.
- If the diff touches no user-facing UI (pure refactor, data model only, build config),
  say so plainly and stop — don't force a test plan onto it.

## Workflow

### Phase 0 — Resolve the diff

```bash
gh pr view <pr>  --json title,body,additions,deletions,changedFiles,files   # PR input
gh pr diff <pr>
# or, for a branch:
git diff <base>...<branch> --stat
git diff <base>...<branch>
```

Capture: title/intent, full file list, and the diff itself. Note which modules/targets
are touched.

**Size/triviality gate:** if the diff is lockfile-only, `Package.resolved`-only,
comment/formatting-only, or touches no view/controller/ViewModel code with user-visible
behavior, report that plainly and stop — no plan needed.

### Phase 1 — Trace the flow and find accessibility-identifier gaps

For each screen/control touched by the diff:
1. Read the actual view code (SwiftUI or UIKit) to find its current accessibility
   identifier, if any — `.accessibilityIdentifier(...)`, `.accessibility(identifier:)`,
   `accessibilityIdentifier =`, or any project-specific helper/enum that wraps them. Do not
   assume from naming conventions; read the file.
2. Identify which convention the surrounding code already uses. Common shapes:
   - A **central identifier enum** shared across modules (e.g. an `AccessibilityID` enum plus a
     view-modifier/helper that applies it).
   - A **per-feature or per-module enum** of identifiers.
   - **Raw string literals** at the call site.

   Note the casing style (snake_case, kebab-case, camelCase) and mirror whichever convention the
   module already uses. If the module has none yet and needs several new identifiers, prefer
   creating a small per-module enum over sprinkling raw string literals.
3. For every control in the flow that lacks a stable identifier, **design one** — don't
   just flag the gap. Apply these rules, all non-negotiable:
   - **SwiftUI modifier order**: `.accessibilityIdentifier`/`.accessibilityLabel` must
     be applied *after* `.accessibilityElement(children: .combine)` in the modifier
     chain, or it silently never reaches the XCUITest tree. Verify the actual order in
     the file, don't assume it's already correct.
   - **Container propagation hazard**: a SwiftUI identifier on a multi-child container
     (`VStack`/`NavigationView`/anything with more than one interactive descendant)
     propagates to *every* leaf child, silently overwriting their own identifiers. Never
     put a "root screen" identifier there. If a root/scoping identifier is needed, put it
     on the `UIHostingController`'s `.view` in the UIKit bridge instead.
   - **List/`ForEach` rows**: key the identifier off a stable domain value already used
     as the `ForEach` identity (not display text — it may vary by lookup/render path —
     and not index — it depends on sort/filter state). If the same item can render in two
     places at once (e.g. a "Recent" section and the full list simultaneously), the
     identifier needs a section-scoped prefix — a bare shared id would be ambiguous to
     `findElement` and any assertion built on it would be meaningless.
   - **Distinct UI variants need distinct ids**: if a control's presented variant (e.g.
     Close vs Back button, depending on modal-vs-pushed presentation) is itself part of
     the behavior under test, give each variant its own identifier rather than one shared
     one — otherwise the variant regression is invisible to the suite.
   - **`name` vs `label`**: once an identifier is set, Appium's `name` attribute becomes
     that identifier and the human-readable text moves to `label`. Say this explicitly in
     the plan so the automation side knows to assert on `label`, not `name`, for text checks.
   - **Selection/state**: prefer existing traits (`.isSelected` → XCUITest `selected`
     attribute) over adding an identifier to a purely visual state indicator that lives
     inside a `.combine`d subtree — an id there is dead code.
4. Produce a **verification pass**: before finalizing the identifier table, re-read the
   actual source for anything you assumed rather than confirmed (existing dependencies
   between modules, what a field currently displays vs. what you assumed it displays,
   whether an entry path is live code or dead code). Write a short "corrections" table
   for anything your first pass got wrong — this catches real bugs (a dead-code entry path,
   a bad fixture choice, a root identifier on a container) before they reach the plan.

### Phase 2 — Clarification questions (mandatory, not optional)

**Do not proceed to Phase 3 on an assumption.** Ground each question in something
concrete you found in Phases 0–1, suggest a default so the user can confirm quickly
rather than write an essay, but always ask rather than silently picking the default
yourself. Skipping this phase because "there's only one obvious choice" is exactly
the failure mode this phase exists to prevent — an entry path that looks like the
only obvious choice can turn out to be dead code.

Use `AskUserQuestion`, grouped by priority (batch independent questions together where
the tool allows it):

**Blockers** — cannot proceed without an answer:
- Which flow to scope the plan to, if the diff plausibly touches more than one
  independently-testable user flow
- Which entry path to drive the flow through, if more than one navigation path
  reaches it (verify each candidate path isn't dead/unreferenced code before
  offering it as an option — grep for real call sites, don't assume a path is live
  because it exists)
- Any accessibility-identifier design decision in Phase 1 that has more than one
  defensible resolution (e.g. which existing convention to extend when a module
  genuinely uses both, or how to disambiguate a control with no clear stable
  domain key)

**Important** — has a reasonable default grounded in the diff, but still confirm:
- Depth of assertions (shallow/presence vs. exact-match) — suggest shallow if the
  diff has any live-rendered, timer-driven, or dataset-order-dependent text, and say
  why
- Target/app-variant scope — which app targets, schemes, or brands the plan covers,
  based on what the diff actually touches (don't assume "all variants" just because the
  module is shared)
- Whether the newly-designed Swift accessibility identifiers should be included in
  this same plan (default: yes, since Part 1 exists for this) or scoped out as a
  separate follow-up
- Where to save the output plan file

**Nice to know** — won't block the plan, but ask rather than guess:
- Whether a ticket ID exists for this work (many automation repos require one in commit
  messages; leave as an explicit open item only if the user genuinely doesn't have one yet)
- Priority relative to existing suite runtime (smoke vs. regression placement)

If the user answers "skip, use your judgment" on a Nice-to-know question, proceed
with the stated default and note that in the final plan's Context section so the
choice is traceable. Never do this silently for a Blocker or Important question —
if the user doesn't answer, stop and ask again rather than guessing forward.

### Phase 3 — Cross-reference the automation repo and build the test plan

If a dedicated automation-planning subagent is available in this environment, delegate
this phase to it and pass along everything Phases 0–2 already resolved (screen sequence,
modules, existing and newly-designed identifiers with file+line, and the user's confirmed
answers) so it doesn't re-derive the flow or re-ask settled questions. Otherwise, do it
directly:

1. **Existing coverage** — find Page Objects, test classes, and suites in the automation
   repo that already touch these screens. Reuse and extend before creating new ones.
2. **Conventions** — read 2–3 existing Page Objects and tests to learn locator strategy,
   base classes, wait helpers, naming, and package layout. Match them; call out any
   deliberate deviation and why.
3. **Test data** — find how existing tests set up fixtures (API helpers/managers, seeded
   accounts, deep links). Pick fixtures that make assertions deterministic.
4. **Suite placement** — find the suite XML/config files and decide where the new tests
   are registered (smoke vs. regression, per-platform suites).
5. **Dependency/risk analysis** — list flakiness sources visible in the diff (live-rendered
   or timer-driven text, device-state-dependent ordering, locale/timezone dependence,
   persisted local state across runs) and a concrete mitigation for each.
6. **Test case breakdown** — a matrix of cases: ID, scenario, preconditions, steps,
   expected result, locators used, priority.

If you surface a genuinely new blocker here, ask it — don't assume an answer.

### Phase 4 — Assemble and write the plan file

Combine into one markdown document, in this order:

1. **Context** — what the PR/branch does, why it needs coverage, decisions taken
   (scope, entry path, assertion depth), explicit "Status: planning only, not yet
   implemented" line.
2. **Corrections to earlier assumptions** — the Phase 1 verification-pass table, if
   anything was corrected. Omit if genuinely nothing was.
3. **Part 1 — Swift: accessibility identifiers** — the concrete per-file, per-control
   design from Phase 1: new/modified files, exact identifier strings, and the specific
   gotcha each one had to route around (propagation, modifier order, section prefix,
   variant splitting). Include an "expected compile break" note for any test that
   constructs the changed view directly.
4. **Part 2 — Automation suite** — the Phase 3 output: fixture/test-data choices,
   navigation path with locators, new/modified files, page object conventions and any
   deliberate deviations, the full test case matrix, the flakiness-source-to-mitigation
   table, what's deliberately not automated and why, suite placement/registration decision.
5. **Sequencing** — phased order (reconnaissance → Swift → automation in parallel where
   possible → integration testing → merge), noting the hard dependency: locators for
   anything new in Part 1 can't pass until that app build is installed.
6. **Verification** — how to confirm the identifiers actually work (Appium Inspector
   checklist, a page-source dump one-liner), how to control any environment-dependent
   flakiness source found (simulator locale/timezone/state pinning), the end-to-end test
   run command, and a concrete "definition of done."
7. **Open items** — anything left genuinely unresolved: ticket IDs, test-management case
   IDs, unresolved navigation questions, flag/config interactions with sibling branches.

Write this to the path resolved in Inputs (default: app repo root,
`<slug>-Automation-Plan.md`). If the repo already has a convention for design/plan docs
(e.g. an existing `docs/` folder or `*-Design.md` files), follow it instead of guessing.

## Output

End with a short summary (not the full plan re-stated): the file path written, a
one-line description of what it covers, and the count of open items still needing
the user's input before implementation can start.
