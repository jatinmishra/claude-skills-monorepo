# SDK Delta Sourcing

The hard input problem. Apple does not publish a clean machine-readable "what
changed" feed, and the old color-coded API-diff browser has been degraded. So
treat sourcing as a layered fetch, most-reliable source first. **Never rely on
training knowledge for what a recent WWDC shipped — fetch live every run.** The
model's cutoff is almost always behind the requested WWDC range.

## Step A — Resolve the WWDC range to iOS versions (verify live)

Map the configured number of WWDCs back from the current year. Anchors below
are hints only — **confirm against the live release-notes index** because
Apple's versioning changed and the newest year may not be in training data.

| WWDC | iOS version |
|------|-------------|
| 2023 | iOS 17 |
| 2024 | iOS 18 |
| 2025 | iOS 26  (year-based rename began here — not iOS 19) |
| 2026 | confirm live (expected iOS 27) |

To confirm, fetch the release-notes index and read the available versions:
`https://developer.apple.com/documentation/ios-ipados-release-notes`

Default range if the user gives no number: the last **2** WWDCs (current + one
prior). 3 is the sensible max — older than that and the deployment-floor filter
usually kills most suggestions anyway.

## Step B — Pull the high-level "what's new" per version

**Apple's documentation site is JavaScript-rendered.** The standard `WebFetch`
tool returns only a page title from HTML URLs. Use the JSON API endpoints
instead — they return the full content:

```
# Release notes (replace <N> with the iOS version number, e.g. 18 or 26):
https://developer.apple.com/tutorials/data/documentation/ios-ipados-release-notes/ios-ipados-<N>-release-notes.json

# Per-framework reference:
https://developer.apple.com/tutorials/data/documentation/<lowercase-framework-name>.json
# Examples:
https://developer.apple.com/tutorials/data/documentation/swiftui.json
https://developer.apple.com/tutorials/data/documentation/activitykit.json
https://developer.apple.com/tutorials/data/documentation/watchconnectivity.json
```

If a JSON endpoint returns 404, fall back to the HTML page — the tool may still
extract partial content. Note degraded sourcing on any suggestion that relies on
the fallback.

Fetch release notes JSON for each iOS version in the WWDC range first. These
give the full picture (additions, behaviour changes, deprecations) and are the
most reliable signal.

## Step C — Pull per-framework API changes, scoped to the codebase

Do NOT crawl every framework. Scope the fetch to:
1. Every Apple framework in `apple_frameworks_used` from the project analysis
   (highest relevance — the app already lives there), plus
2. The high-value shortlist below (where net-new capability tends to land).

For each, fetch the framework JSON endpoint (see Step B). If a framework JSON
is sparse, also try:
`https://developer.apple.com/documentation/<framework>?changes=latest_major`
(use `latest_minor` for point releases) — this HTML page may still yield partial
content via `WebFetch` and is worth the attempt.

Note in the output when a suggestion's grounding is weaker because the full
framework reference was unavailable — don't paper over it.

## High-value framework shortlist

Where adoptable, high-leverage capability tends to appear. Check these even if
the codebase doesn't import them yet — they're the source of genuinely new
*customer-facing* ideas rather than mere modernization:

- **AppIntents / App Shortcuts / Spotlight** — surface app actions to Siri, Spotlight, Shortcuts,
  Action button, Apple Pencil Pro. Zero AppIntents usage in a codebase is almost always the
  highest-ROI gap for any app with primary user actions.
- **ActivityKit (Live Activities)** — Lock Screen, Dynamic Island, StandBy, watchOS Smart Stack,
  macOS Menu Bar. Highest value when the app has real-time or time-bound activity (calls,
  deliveries, timers, live events) and already has push infrastructure or a WidgetKit extension.
- **WidgetKit** — complications, Smart Stack widgets, Control Center controls (iOS 18+).
  Check whether the codebase already has a widget extension target that can host new surfaces.
- **WatchConnectivity / watchOS** — companion app opportunity. Strongest when the codebase already
  has glanceable surfaces (`UserNotifications`, `WidgetKit`, Live Activities) the watch could
  extend. Treat this as a **major initiative**, not a sprint suggestion.
- **SwiftUI** — new containers, scroll APIs, animation, layout, `@Entry` macro each year.
- **SwiftData / Observation** — persistence + state modernization; `@Observable` replaces
  `ObservableObject`; count `uses_observableobject` in `legacy_signals`.
- **Foundation** — `Date.FormatStyle` (replaces manual `DateFormatter`), regex, async sequences.
  Count `manual_dateformatter` and third-party date libs in the dependency list.
- **Translation** — `TranslationSession` / `translationPresentation()`. High value for any app
  with user-generated text content (notes, chat, comments) or an international user base.
- **StoreKit** — `SubscriptionStoreView`, `SubscriptionOfferView`, subscription bundles.
  Check for an existing IAP module and the `uses_storekit2` legacy signal.
- **Foundation Models / CoreAI** — on-device LLM (`LanguageModelSession`) and custom ML
  inference (`AIModelCache`). iOS 26+ only; requires Apple Intelligence eligible devices.
- **TipKit** — in-app feature discovery. High value for apps with feature flags / plan gating.
- **MetricKit / OSLog** — diagnostics & performance. Low `OSLog` usage in a large codebase is
  a signal that MetricKit is also absent.
- **BackgroundTasks / BackgroundAssets** — refresh, prefetch, localized asset delivery.
- **VisionKit / DataDetection** — live text, data scanning, QR codes.

## Grounding rule

Every suggestion must point to a **specific API symbol or release-note entry**
that appears in fetched content, plus its source URL. If you cannot ground it in
something you actually fetched, drop it. Hallucinated APIs are the primary
failure mode of this skill and the fastest way to lose the engineer's trust.
