---
name: analyze-build
description: >
  Analyze an Xcode build log (.txt or .xcactivitylog export) and produce a build
  optimization report — slowest compilations, build-setting audit, script-phase and
  SwiftLint audit, cache invalidation causes, and ranked quick wins as an xcconfig
  snippet. Use when the user shares an Xcode build log, asks why their build is slow,
  or wants to speed up Xcode builds.
argument-hint: <path-to-build-log>
---

# Analyze Xcode Build Log

Analyze the Xcode build log provided as an argument (or ask the user for the path if none given) and produce a comprehensive build optimization report.

## Instructions

The user has provided a build log path: $ARGUMENTS

If no path was provided, ask: "Please provide the path to your Xcode build log (.txt or .xcactivitylog exported from Xcode's Report Navigator)."

Once you have the path, follow these steps:

### Step 1 — Identify log type

Before deep analysis, read the first 100 lines to determine:
- Is this a **pre-build only** log (contains only env vars and SwiftLint output, no `CompileSwift` lines)?
- Is this a **full build** log (contains `CompileSwift`, `Ld`, `GenerateDSYMFile`, `CodeSign` lines)?
- Is this an **incremental** or **clean** build (look for "stale file removal" lines)?

If it's a pre-build only log, inform the user:
> This log only captures the pre-build phase. For a complete analysis including per-file compile times, please do: **Product → Clean Build Folder (⇧⌘K)**, build, then in Report Navigator (⌘9) right-click → **Save Build Log** with "All Messages".

Proceed with whatever data is available.

### Step 2 — Read the full log

The file may be very large (200–500KB). Read it in chunks of 300 lines at a time from start to finish. You MUST read all chunks — do not stop early. The most important data (compile timings, link times) is in the middle and later sections.

While reading, track:

**Build metadata:**
- Total build time (look for "Build succeeded" line with duration, or start/end timestamps)
- Build configuration (Debug/Release/Staging, simulator vs device)
- Xcode version
- Number of targets

**Cache invalidation:**
- Count of "Remove stale file" lines → if > 1000, this is a full cache invalidation
- Any pre-action scripts listed that could be touching source files

**Build phases (in order):**
- `PhaseScriptExecution` — script name, target
- `SwiftLint` runs — count them, which targets, how many files
- `CompileSwift` — collect all, note file name and log-line gap to next entry
- `CompileC` / `CompileObjC` — same
- `Ld` — linker invocations, flags used
- `GenerateDSYMFile` — which targets, log-line size
- `CodeSign` — count of signing operations
- `CompileAssetCatalog` — asset compilation

**Warnings and errors:**
- Any `warning:` or `error:` lines
- Script phases with no declared outputs ("will be run during every build")
- Missing folders or files
- Deprecated flags or rules

**Build settings of interest** (from env var block at start):
- `ENABLE_CODE_COVERAGE`
- `DEBUG_INFORMATION_FORMAT`
- `EAGER_LINKING`
- `COMPILATION_CACHE_ENABLE_CACHING`
- `SWIFT_COMPILATION_MODE`
- `FUSE_BUILD_SCRIPT_PHASES`
- `EAGER_COMPILATION_ALLOW_SCRIPTS`

### Step 3 — Analyse findings

After reading the full log, produce the report with these sections:

#### A. Build Overview
- Total time, configuration, clean vs incremental
- Number of targets, source files compiled
- Whether build cache was used (incremental) or fully invalidated

#### B. Critical Issues (blockers / major slowdowns)
List issues that are causing the most waste, in priority order.

#### C. Top 20 Slowest Compilations
Separate Swift and ObjC tables. Use log-line gap as proxy for compile time (larger gap = slower). Note: if `-Xfrontend -debug-time-compilation` is in the flags, use actual timings instead.

#### D. Build Setting Audit
Table of key settings found vs recommended values for a development build:

| Setting | Current Value | Recommended | Impact |
|---|---|---|---|

#### E. Script Phase Audit
List all `PhaseScriptExecution` entries. Flag any that:
- Have no declared outputs (forced re-run every build)
- Run before compilation (blocking)
- Run on too many targets

#### F. SwiftLint Audit (if present)
- Total invocations
- Total files linted
- Any error-level violations (these may block the build)
- Deprecated rules
- Over-linting (same files covered by multiple invocations)

#### G. Recommendations Table
Ranked by estimated impact × ease:

| # | Fix | File/Setting | Est. Saving | Effort (Low/Med/High) |
|---|---|---|---|---|

Always include these checks regardless of what's in the log:
1. `ENABLE_CODE_COVERAGE` — should be `NO` for dev builds (adds instrumentation to every compile)
2. `DEBUG_INFORMATION_FORMAT` — should be `dwarf` not `dwarf-with-dsym` for simulator dev (eliminates dsymutil)
3. `EAGER_LINKING` — should be `YES` (overlaps link with late-stage compile)
4. `COMPILATION_CACHE_ENABLE_CACHING` — should be `YES` (Xcode 15+ module cache)
5. Cache invalidation root cause — if stale file count > 1000, flag this as #1 priority
6. Script phases with no declared outputs
7. SwiftLint scope and invocation count
8. Third-party heavy modules that could be pre-built XCFrameworks

#### H. Quick Wins
List all `Low` effort recommendations as a ready-to-apply xcconfig snippet:
```
// <Configuration>.xcconfig additions
SETTING = VALUE
```

#### I. Diagnostic Commands
If specific slow files were found, provide the Swift Other Flags to add temporarily to find exact bottleneck expressions:
```
-Xfrontend -warn-long-function-bodies=200
-Xfrontend -warn-long-expression-type-checking=200
```

### Step 4 — Save report

After presenting the analysis to the user, offer to save it as a markdown file at `Docs/BuildOptimisation-<date>.md` in the current project directory.

### Step 5 — Offer to apply fixes

After the report, ask:
> Would you like me to apply the quick-win build setting changes now? I can update the xcconfig files directly.

If yes, find the relevant xcconfig files using Glob, read them, and apply the recommended settings.
