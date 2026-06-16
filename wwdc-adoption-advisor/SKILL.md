---
name: wwdc-adoption-advisor
description: >
  Cross-reference recent WWDC / iOS SDK releases against the current iOS codebase
  and propose grounded, MVP-scoped adoption ideas with a concrete feasibility
  analysis — broken down by customer-facing features, dev utilities, performance,
  and UI. Use this whenever the user wants to know "what new iOS/SDK capabilities
  could we adopt", "what from the last few WWDCs applies to our app", "what should
  we modernize", or asks for an SDK/WWDC adoption review, modernization audit, or
  feature-idea pass over an iOS project. Trigger even when WWDC isn't named
  explicitly but the user wants new-iOS-feature ideas scoped to their actual
  codebase. iOS / Swift / Xcode projects only.
---

# WWDC Adoption Advisor

Turn "what's new in recent iOS releases" into a short, ranked list of adoption
ideas that are real for *this* codebase — each with an MVP slice and an honest
feasibility profile. Output ideas, not implementations.

## Why this skill is shaped the way it is

- **The codebase cross-reference is the hard part, not the WWDC pull.** The
  pull is mechanical; the value is in matching new APIs against what the app
  already does and what it ships to. So spend effort on accurate inputs.
- **The deployment floor gates everything.** A capability the app can't reach
  without raising its minimum iOS version is a product decision, not a feature
  idea. Resolve the floor first.
- **Freshness is mandatory.** The requested WWDC range is usually past the
  model's training cutoff. Fetch live; do not invent APIs from memory.
- **The model is the matcher; the scripts are the harness.** Deterministic
  scripts extract structured facts; the model reasons over them. Quality is
  capped by how good the inputs are.

## Inputs (ask only if missing)

- **Project path** — required. The root of the iOS project/workspace.
- **WWDC count** — how many recent WWDCs to consider. Default **2**, max **3**. If the most
  recent WWDC shipped a beta less than ~3 months ago, cover it in a separate
  forward-looking section rather than mixing it with adoptable suggestions.

## Workflow

### 1. Analyze the codebase (deterministic)

Run the analyzer and keep its JSON as the ground truth for the rest of the run:

```bash
python3 scripts/analyze_project.py <project_path> --json-out /tmp/wwdc_analysis.json
```

This returns: the **deployment floor** (binding minimum iOS) and any variance,
dependency lists (SPM / CocoaPods / Carthage), the Apple frameworks the code
actually imports, unclassified imports, legacy-pattern signals with what
supersedes them, and a one-line architecture summary.

If `deployment_target.floor` is null, **stop and ask the user** for the minimum
iOS version. Suggestions are meaningless without it.

**Floor verification (critical for multi-target projects):** The analyzer
reports the lowest value found anywhere in the project file, which may be a
project-level default that every target overrides. If `deployment_target.distinct`
contains more than one value, grep the `project.pbxproj` to identify which
config list UIDs carry each floor value, then check whether those UIDs belong to
`PBXProject` (project default, typically overridden) or `PBXNativeTarget`
(authoritative per-target setting). Use the per-target minimum as the binding
floor. Note the distinction in the output header.

### 2. Resolve the WWDC range and fetch the SDK delta (live)

Read `references/sources.md` and follow it. In short: resolve the WWDC count to
iOS versions (verify against Apple's live release-notes index — don't trust the
table or training data for the newest year), read each version's release notes,
then fetch per-framework `?changes=latest_major` pages **scoped to the
frameworks the codebase uses plus the high-value shortlist**. Don't crawl
everything.

**Apple docs are JavaScript-rendered** — the standard `WebFetch` tool returns
only a page title for `developer.apple.com` HTML pages. Use the JSON API
endpoints instead (see `references/sources.md` § JSON endpoints). If a JSON
endpoint returns empty or 404, fall back to the HTML page and note degraded
sourcing on any affected suggestion.

**Beta WWDC handling:** If the most recent WWDC shipped an SDK that is still in
beta (typically within the first 3 months after the June announcement), collect
its suggestions but output them in a **separate forward-looking section** clearly
marked as beta. Do not mix beta suggestions with adoptable ones.

### 3. Cross-reference

For each candidate API from the delta, decide:

- **Does it fit this app?** Relevance to existing frameworks/features beats
  novelty. Don't suggest capabilities the app has no surface for.
- **Does it replace something the app hand-rolls?** Cross-check
  `legacy_signals` / `signal_supersedes` and the dependency list — these are the
  highest-trust, lowest-risk wins.
- **Where does it sit on the deployment-delta axis?** `usable-now` /
  `availability-gated` / `requires-floor-bump`, computed against the floor from
  step 1.
- **Is it grounded?** Every kept suggestion maps to a specific API symbol or
  release-note entry you actually fetched, with its URL. Drop anything you can't ground.

### 4. Scan for breaking changes

Before writing adoption suggestions, scan the release notes of every covered iOS
version for **behavioural changes and deprecations** that affect code the
codebase already has. These are not adoption opportunities — they are required
audits. Collect them into a separate "Breaking Changes to Audit" section using
the table format in `references/output-spec.md`. At minimum check for:
deprecated UI APIs (status bar, presentation traits), SwiftUI property wrapper
changes, new App Store submission requirements (launch screen, entitlements), and
removed framework APIs used by existing dependencies.

### 5. Produce the output

Read `references/output-spec.md` and follow the template and feasibility rubric
exactly. Tag every suggestion with both a **topic** (customer-facing /
dev-utility / performance / ui / other) and a concrete **feasibility profile**.
Cap at **5–7 per WWDC section** (not total), ranked by value-to-effort,
retire-your-own-code wins first. Each suggestion gets an **MVP slice** — the
smallest shippable version — never an end-to-end feature.

Some suggestions are better framed as **major initiatives** (e.g., a new
platform target like watchOS) rather than sprint-sized suggestions. If a
suggestion requires its own app target, a new backend integration, or
cross-functional alignment, call it out in a dedicated "Major Initiative"
section rather than cramming it into the ranked list.

After the suggestion sections, produce the **Effort & Risk Analysis** section
as defined in `references/output-spec.md`: a quick-reference matrix table plus
per-feature risk breakdown and a recommended implementation sequence with
explicit dependencies called out.

## Guardrails

- No ungrounded APIs. If it isn't in fetched content, it doesn't ship in the list.
- No implementations or full specs — ideas + MVP + feasibility only.
- No suggestion that ignores the floor.
- Don't pad to a count; fewer, sharper suggestions win.
- If sourcing was degraded (empty changes page, etc.), say so on the affected
  suggestion rather than overstating confidence.
- Never mix beta-only suggestions with adoptable ones — keep them in a separate
  section with a clear beta caveat.
- For beta suggestions, explicitly flag known issues from the release notes that
  affect the suggestion. If known issues are severe, recommend waiting for GA
  and say so.
- The floor used for the deployment-delta axis must be the **verified per-target
  floor**, not the project-level default (see Workflow step 1).
- A "major initiative" (new platform target, new server integration) belongs in
  its own section, not ranked alongside sprint-sized suggestions.

## Bundled resources

- `scripts/analyze_project.py` — deterministic project fact extractor (stdlib only).
- `references/sources.md` — how to resolve the WWDC range and fetch the SDK delta,
  including JSON endpoint formats and the high-value framework shortlist.
- `references/output-spec.md` — feasibility rubric, output template, breaking-changes
  table, effort/risk matrix, sprint sequencing, and worked examples.
