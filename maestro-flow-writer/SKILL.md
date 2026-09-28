---
name: maestro-flow-writer
description: >
  Writes Maestro YAML UI-test flows for an iOS app codebase, grounded in real
  accessibility identifiers/text read from source rather than guessed
  conventions. Use this skill whenever the user asks to write, create, or add a
  Maestro test/flow for a feature in an iOS project, or to convert/port test
  cases from another test suite (e.g. a reference JS/TS package's own tests)
  into a Maestro flow.
license: MIT
---

# Maestro Flow Writer (iOS)

Writes `.maestro/**/*.yaml` flows for an iOS app. Every rule below is about
grounding selectors in how the codebase actually builds its UI and exposes
(or fails to expose) accessibility identifiers — not a generic Maestro
best-practice list.

**This skill is read-only in Swift/source, write-only for the `.maestro/`
YAML file(s) themselves.** Never edit app source to "make a selector work" —
if a needed identifier doesn't exist, say so and either use a text-based
fallback or ask whether to add one (that's a separate, approval-gated code
change, not something this skill does silently).

## Workflow

### Phase 1 — Trace the real navigation path in source, screen by screen

Don't guess the path from what the feature "should" look like from the UI.
Grep for where the target screen is actually presented/pushed from (the
coordinator/router/ViewModel/navigation call site), and walk backward one
screen at a time to the nearest stable entry point (usually a tab bar item).
For each screen in the chain, note: what data/state gates it being reachable
(e.g. a feature flag, a role check) — if the flow depends on account/role
state, say so in the flow's header comment rather than silently assuming a
happy-path account.

If a step's real path is genuinely unclear after a reasonable grep pass, use a
research agent/fork to trace it rather than asserting a guessed path with
confidence — a wrong assumption here compounds into every selector built on
top of it. A plausible-looking shortcut (e.g. assuming a feature is reachable
directly from a tab bar item) can silently skip real intermediate screens
(a list/detail row, an edit-mode toggle, a confirmation step) that only
surface once someone actually walks the flow on device or traces the real
call sites — verify the hop count, don't assume it from how the feature
"should" be reachable.

### Phase 2 — For every tap/assert target, find the REAL selector — never assume one exists

Grep the actual view code. Identifiers fall into two categories, and
conflating them is the most common mistake:

**A. Fixed code-level identifiers — reliable, cite file:line and use bare `id:`.**
Look for:
- Literal strings passed to `.accessibilityIdentifier("...")` / `accessibilityIdentifier = "..."`.
- Cases of a project-defined identifier enum (often `String`-raw-valued, e.g. `.tabBar(.settings)` → `"settings_tab"`) applied through a helper or view modifier. Resolve the enum case to its raw value by reading the enum definition — the identifier is a compile-time constant, not derived from any display copy. Highest confidence.

**B. Identifiers/text derived from localized display copy — best-effort only, always hedge.**
Look for patterns like `.accessibilityIdentifier(title.lowercased().replacingOccurrences(of: " ", with: "_"))`
or any place a screen's *visible text* is transformed into an id at runtime. Before trusting
the guessed id string:
1. Try to find the literal English copy in a checked-in `.strings`/`Localizable.strings` file.
2. If copy comes from a remote localization service (pulled at build time or runtime, not
   checked into the repo — e.g. Lokalise, Crowdin, Phrase), the literal copy is **not
   confirmable from source**. Treat the derived id as a *strong guess*, not a fact. Every such guess must
   ship with: `optional: true`, a text-based fallback step right after it (wrapped per the
   regex rule in Phase 3), and a header-comment citation of exactly which file/line the
   derivation pattern came from — so a future reader can tell "confirmed" from "guessed" at
   a glance.

Never write a selector — id or text — without having actually read the source line that
produces it. A selector that "should" exist based on naming convention, rather than one
confirmed by reading the view code, is the single most common source of a flow that looks
right and fails on device.

### Phase 3 — Maestro syntax rules learned the hard way

- **`text:` is a whole-string regex, not a substring/"contains" match.** If the rendered
  element combines more than the phrase you care about into one text node (e.g. a list row
  built as `"\(country) – \(city) (\(abbr))"`), a bare `text: "New Delhi"` requires the
  *entire* element text to equal exactly that and will never match. Always wrap:
  `text: ".*New Delhi.*"`. Read the actual SwiftUI `Text(...)` construction to confirm
  whether it's one combined string or several separate nodes before deciding how much
  context you need in the pattern.
- **A `when:` property directly on a command (e.g. `tapOn: { when: ... }`) is not a
  recognized property on all Maestro CLI versions** and fails with `Unknown Property: when`.
  Route conditional execution through `runFlow` instead:
  ```yaml
  - runFlow:
      when:
        notVisible:
          text: ".*Some marker.*"
      commands:
        - tapOn:
            text: ".*Fallback target.*"
            optional: true
  ```
- **`optional: true` does not mean "skip if an earlier optional step already succeeded."**
  Every listed step still executes regardless of whether a prior step found its target.
  A common failure shape: step N (`id:`-based, optional) succeeds and navigates forward;
  step N+1 (text-based fallback, also optional) then runs on the *new* screen and can
  accidentally match something else entirely there — a fallback pattern broad enough to
  catch its intended target on the *source* screen can just as easily match unrelated
  content already visible on the *destination* screen, silently tapping and acting on it
  (e.g. selecting a list row and dismissing a screen you meant to stay on). Guard every
  fallback step that follows a possibly-already-successful primary step with a
  `runFlow: when: notVisible:` check keyed on something that only appears once the *target*
  screen (not the source screen) is open.
- **Elements below the fold need `scrollUntilVisible` before `tapOn`, not after.** Give both
  the primary and fallback selector attempts their own scroll step, since only one of the
  two selectors will actually exist on a given build:
  ```yaml
  - scrollUntilVisible:
      element:
        id: "some_id"
      direction: DOWN
      optional: true
  - tapOn:
      id: "some_id"
      optional: true
  ```
- **Validate the YAML before handing it back.** If the `maestro` CLI and a booted simulator are
  available, run the flow. If not (e.g. no Java runtime), at least check the structure:
  ```bash
  python3 -c "
  import yaml
  with open('<path>.yaml') as f:
      docs = list(yaml.safe_load_all(f))
  print('doc count:', len(docs))   # expect 2: header dict, then the steps list
  print('num steps:', len(docs[1]))
  "
  ```
  This catches indentation/structure errors immediately, but it is **not** a substitute for
  actually running the flow — say so explicitly when reporting back, and point to
  `maestro studio` (interactive element inspector against a running simulator) as the way
  to confirm/correct any `optional`-guessed selector.

### Phase 4 — Porting assertions from another test suite (e.g. a reference package)

If the user wants existing tests from a reference implementation (a JS/TS package, a prior
platform's suite, etc.) converted into Maestro assertions:
1. Read the reference's own test file(s) for concrete `input → expected output` cases —
   these are far more valuable than re-deriving assertions from scratch, since they encode
   edge cases someone already found worth testing.
2. **Never port an assertion that depends on the reference's own dataset/fixture size**
   (e.g. "query X returns exactly 9 results") without independently verifying the same
   input against *this* codebase's own bundled data first — a different dataset size or
   content is exactly the kind of silent mismatch that produces a test that's "correct" for
   the wrong reason. Port the *behavioral* assertion (which specific items must/must not
   appear), not the incidental count.
3. If the reference is runnable (e.g. `npm install && npm run build`), prefer querying it
   live for ground truth over reading its source and assuming — source-reading can get an
   algorithm's shape right while missing subtleties (data differences, ordering, edge-case
   handling) that only show up in actual output. A cloned reference repo in `$TMPDIR` is
   fine for this; it doesn't need to be committed anywhere.
4. State in the flow's header comment which queries were ported from where, and that their
   expected results were re-verified against this repo's own data — not just assumed to
   carry over.

### Phase 5 — File conventions

- Location: `.maestro/<feature-name>/<flow-name>.yaml` at the repo root. If flows already
  exist under `.maestro/`, match their structure/naming rather than inventing a new one.
- Every flow file's header comment block should cover, in this order: (1) what the flow
  exercises and why, in terms of specific behaviors/bugs it locks in — not just "tests
  screen X"; (2) a "known-verified selectors" list with file:line citations (Phase 2A); (3)
  a "best-effort selectors" list with the same, explicitly flagged as guesses (Phase 2B); (4)
  any precondition the flow assumes but doesn't set up itself (e.g. an already-authenticated
  session — `launchApp: { clearState: false }` and a one-line note that login isn't automated
  by this flow, since fabricating a guessed login sequence is worse than leaving it explicit).
- `appId:` — check `PRODUCT_BUNDLE_IDENTIFIER` in the relevant `.xcodeproj/project.pbxproj`
  rather than assuming; many projects ship more than one bundle id (app extensions, white-label
  brands, staging/debug variants) across targets.

## Output

End with a short summary: the file path written, which selectors are confirmed vs.
best-effort (and why), and what the user should do to close the gap on the best-effort ones
(typically: run `maestro studio` once against a real build).
