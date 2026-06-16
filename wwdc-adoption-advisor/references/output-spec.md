# Output Spec & Feasibility Rubric

Two orthogonal axes. Every suggestion carries **both**:

- **Topic** (what kind of win): `customer-facing` · `dev-utility` · `performance` · `ui` · `other`
- **Feasibility** (what it costs): the profile below.

Keep topic and feasibility separate — a `performance` idea can be trivial or a
six-week refactor, and the engineer needs to see both at a glance.

## Feasibility profile (the part that earns trust)

Make every field concrete. No "moderate effort" vibes.

1. **Deployment delta** — the master lever. Exactly one of:
   - `usable-now` — API available at or below the project's deployment floor.
   - `availability-gated` — above the floor but additive; ship it behind
     `if #available(iOS <N>, *)` with a graceful fallback. Most new APIs land here.
   - `requires-floor-bump` — only viable by raising the minimum iOS version.
     This is a product/support decision, not a feature decision — flag it as such
     and state the current floor and the floor it would require.
2. **Change shape** — `additive` (new code path, nothing removed) vs
   `refactor` (replaces or migrates existing code). Name the file(s)/types touched.
3. **Surface area** — rough blast radius: one screen, one module, app-wide.
4. **Reversibility** — easy to pull behind a flag / hard to unwind.
5. **Effort** — t-shirt size (S / M / L) for the *MVP slice only*, not the full feature.
6. **Risk** — the one thing most likely to bite (e.g., "fallback path doubles the
   view code", "deprecated API still needed for the gated-out OS range").

## Output template — use exactly this

```
# WWDC Adoption Suggestions — <App name>

**Generated:** <date>
**Codebase floor:** iOS <floor>  ·  **WWDC range:** <years> (iOS <versions>)
**Architecture:** <one line from analysis>

## Contents
1. Codebase Snapshot
2. <iOS version> & <iOS version> — Adoptable Now
3. <iOS version> — Forward-Looking (Beta)   ← only if a beta WWDC is in scope
4. Major Initiatives                         ← only if any exist
5. Breaking Changes to Audit
6. Effort & Risk Analysis

---

## Codebase Snapshot

| Signal | Value |
|--------|-------|
| Swift files | <N> |
| Key legacy signals | <ObservableObject: N files>, <manual DateFormatter: N>, ... |
| Notable absent adoptions | <AppIntents: 0 files>, <ActivityKit: 0 files>, ... |
| Key 3rd-party deps | <list> |

---

## <iOS X> & <iOS Y> — Adoptable Now

### S<N> · <short imperative title>
- **Topic:** <customer-facing | dev-utility | performance | ui | other>
- **Idea:** 1–2 lines. What it is and why it's worth doing *for this app*.
- **Why now:** `<API symbol>` (<framework>, iOS <N>) — <source URL>
- **Replaces:** <hand-rolled code / dependency it could retire, or "net-new">
- **MVP slice:** the smallest shippable version — one screen, one entry point.
  NOT the end-to-end feature.
- **Feasibility:** deployment delta · change shape · surface area · effort (S/M/L) · risk

---

## <iOS Z> — Forward-Looking (Beta)

> <iOS Z> beta shipped <date>. All suggestions here require `if #available(iOS Z, *)`
> and should target a post-GA release. API surfaces may shift during the beta cycle.

### S<N> · <short imperative title>
(same card format as above; add explicit "Known issues:" bullet if the release notes list any)

---

## Major Initiatives

> Major initiatives require a new app target, a new server integration, or cross-functional
> alignment. They are listed here rather than in the ranked suggestion list.

### <W|M><N> · <initiative title>
(same card format as suggestions, but the MVP slice is broken into numbered steps)

---

## Breaking Changes to Audit

| # | Change | Files at risk | Required action |
|---|--------|---------------|-----------------|
| B1 | <change description> | <N files / which modules> | <what to do> |

---

## Effort & Risk Analysis

### Quick Reference Matrix

| # | Feature | Topic | Effort | Deployment delta | Risk |
|---|---------|--------|--------|-----------------|------|
| S1 | ... | ... | S/M/L | usable-now / availability-gated / requires-floor-bump | Low/Medium/High |

### Per-Feature Risk Breakdown

#### S<N> — <title>
**What breaks / what could go wrong:** ...
**Mitigation:** ...
**Dependency:** (other suggestion IDs this depends on, or "none")

### Recommended Implementation Sequence

```
Sprint 1 (low-risk, usable-now)
  S<N>  <title>  [S effort]
  ...

Sprint 2 ...

Post-GA (beta suggestions)
  S<N>  ...
```

> **Critical path:** call out explicit sequencing dependencies (e.g., "build S8 before W1
> so the Smart Stack surface lands before committing the full watch companion target").
```

Cap at **5–7 suggestions per WWDC section** (not total). A ranked short list the
engineer will actually read beats an exhaustive dump. Rank by value-to-effort, and
within that, prefer:

1. **Retire-your-own-code wins** — the codebase hand-rolls something the system
   now does (see `legacy_signals` / `signal_supersedes` in the analysis, and
   third-party deps that a new system API could replace). Highest trust, lowest risk.
2. `usable-now` over `availability-gated` over `requires-floor-bump`.
3. Genuinely new *customer-facing* capability over pure modernization — but only
   when it fits the app; don't suggest Live Activities for a calculator.

## Worked example (shape, not prescription)

> ### 1. Replace the hand-rolled date formatting with `Date.FormatStyle`
> - **Topic:** dev-utility
> - **Idea:** The app caches `DateFormatter` instances manually in 4 files. `formatted()` / `Date.FormatStyle` is locale-correct, value-typed, and removes the caching boilerplate.
> - **Why now:** `Date.FormatStyle` (Foundation, iOS 15) — <url>
> - **Replaces:** the manual `DateFormatter()` usage flagged in analysis.
> - **MVP slice:** migrate one screen's date rendering; leave the rest until the pattern is proven.
> - **Feasibility:** usable-now · refactor · ~4 files · effort S · risk: subtle locale/format string differences vs the old formatter — snapshot-test the strings.

## What NOT to produce

- No full implementations or end-to-end specs. Ideas + MVP slice + feasibility only.
- No suggestion that isn't grounded in a fetched API symbol (see `sources.md`).
- No suggestion that ignores the floor. If you can't place it on the deployment-delta
  axis, you haven't done the analysis.
- Don't pad to hit a count. Fewer, sharper suggestions.
- Don't bury breaking changes inside suggestion cards. They belong in the dedicated
  "Breaking Changes to Audit" table — they are required work, not adoption choices.
- Don't mix beta suggestions with adoptable ones. Separate section, separate framing.
- Don't present a watch companion app, a new server integration, or any other
  multi-sprint initiative as a single suggestion card in the ranked list. Use the
  Major Initiatives section with a step-by-step MVP slice.
