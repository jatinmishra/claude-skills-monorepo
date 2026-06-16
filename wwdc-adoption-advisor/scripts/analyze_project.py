#!/usr/bin/env python3
"""
analyze_project.py — Extract the structured facts about an iOS codebase that
gate WWDC/SDK-adoption suggestions.

The single most important output is the deployment floor: the minimum iOS
version the app ships to. It determines whether a new API is usable now,
usable behind an `if #available` gate, or only viable by raising the floor.

Everything here is deterministic and grep-level. Semantic judgement (does this
new API actually replace what you hand-rolled?) is left to the model consuming
this JSON — this script's job is to hand it accurate, structured inputs.

Usage:
    python3 analyze_project.py <project_root> [--json-out path]

Output: JSON to stdout (and optionally a file). stdlib only.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Directories that are build output / vendored code, not the app's own source.
SKIP_DIRS = {
    ".git", ".build", "DerivedData", "Pods", "Carthage", "node_modules",
    ".swiftpm", "build", ".cache", "fastlane", "vendor", "Generated",
}

# Representative set of Apple system framework module names. Not exhaustive —
# anything imported that is NOT here and NOT a known dependency is reported
# as "unclassified" so the model can decide.
APPLE_FRAMEWORKS = {
    "SwiftUI", "UIKit", "AppKit", "Foundation", "Combine", "CoreData",
    "SwiftData", "CoreGraphics", "QuartzCore", "CoreAnimation", "CoreImage",
    "AVFoundation", "AVKit", "MediaPlayer", "PhotosUI", "Photos",
    "MapKit", "CoreLocation", "WeatherKit", "HealthKit", "HomeKit",
    "StoreKit", "PassKit", "CloudKit", "CoreML", "CreateML", "Vision",
    "NaturalLanguage", "Speech", "SoundAnalysis", "Translation",
    "WidgetKit", "ActivityKit", "AppIntents", "BackgroundTasks", "BackgroundAssets",
    "UserNotifications", "Network", "MultipeerConnectivity", "WatchConnectivity",
    "CoreBluetooth", "CoreNFC", "CoreMotion", "Charts", "TabularData",
    "Accelerate", "Metal", "MetalKit", "SceneKit", "SpriteKit", "RealityKit",
    "ARKit", "GameplayKit", "GameKit", "Security", "CryptoKit", "AuthenticationServices",
    "LocalAuthentication", "Contacts", "ContactsUI", "EventKit", "EventKitUI",
    "MessageUI", "Messages", "Intents", "IntentsUI", "CallKit", "PushKit",
    "OSLog", "MetricKit", "Observation", "SwiftCharts", "VisionKit",
    "FamilyControls", "ManagedSettings", "DeviceActivity", "ScreenTime",
    "TipKit", "Symbols", "DataDetection", "FinanceKit", "MediaSetup",
}

# Modernization signals: (label, regex, what newer mechanism supersedes it).
# These are *hints* of legacy patterns, surfaced for the model to weigh.
SIGNAL_PATTERNS = [
    ("uses_combine",            re.compile(r"\bimport\s+Combine\b"),                 "async/await + AsyncSequence / @Observable"),
    ("uses_observableobject",   re.compile(r":\s*ObservableObject\b|@Published\b"),  "@Observable macro (Observation)"),
    ("uses_observable_macro",   re.compile(r"@Observable\b"),                        "(already modern)"),
    ("uses_swiftui",            re.compile(r"\bimport\s+SwiftUI\b"),                 None),
    ("uses_uikit",              re.compile(r"\bimport\s+UIKit\b"),                   None),
    ("uses_async_await",        re.compile(r"\bawait\b|\basync\b"),                  None),
    ("uses_actor",              re.compile(r"\bactor\s+\w+|@MainActor\b"),           None),
    ("uses_coredata",           re.compile(r"\bimport\s+CoreData\b"),               "SwiftData (for new models)"),
    ("uses_swiftdata",          re.compile(r"\bimport\s+SwiftData\b"),              "(already modern)"),
    ("manual_dateformatter",    re.compile(r"\bDateFormatter\(\)"),                 "Date.FormatStyle / .formatted()"),
    ("manual_jsonserialization",re.compile(r"\bJSONSerialization\b"),              "Codable"),
    ("nskeyedarchiver",         re.compile(r"\bNSKeyed(Un)?Archiver\b"),           "Codable + modern persistence"),
    ("manual_urlsession_cache", re.compile(r"\bURLCache\b|\bcachedResponse\b"),    "URLSession + modern caching APIs"),
    ("uikit_collectionview",    re.compile(r"\bUICollectionViewDataSource\b"),     "UICollectionViewDiffableDataSource / SwiftUI"),
    ("manual_layout_anchors",   re.compile(r"\bNSLayoutConstraint\.activate\b"),   "(context-dependent)"),
    ("uses_widgetkit",          re.compile(r"\bimport\s+WidgetKit\b"),             None),
    ("uses_appintents",         re.compile(r"\bimport\s+AppIntents\b"),            None),
    ("uses_storekit2",          re.compile(r"\bProduct\.products\b|\bTransaction\."),None),
]

IMPORT_RE = re.compile(r"^\s*(?:@preconcurrency\s+|@_exported\s+)?import\s+(?:struct\s+|class\s+|enum\s+|func\s+)?([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
DEPLOY_RE = re.compile(r"IPHONEOS_DEPLOYMENT_TARGET\s*=\s*([0-9]+(?:\.[0-9]+)?)")
SPM_PLATFORM_RE = re.compile(r"\.iOS\(\.v([0-9_]+)\)")


def iter_files(root: Path, suffixes):
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in suffixes:
            yield p


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def find_deployment_targets(root: Path):
    """Return distinct deployment targets and the binding minimum (the floor)."""
    versions = set()
    sources = []

    # .pbxproj and .xcconfig carry IPHONEOS_DEPLOYMENT_TARGET
    for p in iter_files(root, {".pbxproj", ".xcconfig"}):
        for m in DEPLOY_RE.finditer(read(p)):
            versions.add(m.group(1))
            sources.append({"file": str(p.relative_to(root)), "value": m.group(1)})

    # Package.swift uses major-only (.v17, .v26)
    for p in iter_files(root, {".swift"}):
        if p.name == "Package.swift":
            for m in SPM_PLATFORM_RE.finditer(read(p)):
                v = m.group(1).replace("_", ".")
                versions.add(v)
                sources.append({"file": str(p.relative_to(root)), "value": v})

    def key(v):
        parts = v.split(".")
        return tuple(int(x) for x in parts) + (0,) * (3 - len(parts))

    floor = min(versions, key=key) if versions else None
    return {
        "floor": floor,                       # the binding minimum across targets
        "distinct": sorted(versions, key=key),  # variance worth noting
        "evidence": sources[:50],
        "note": None if versions else "No IPHONEOS_DEPLOYMENT_TARGET found — ask the user for the min iOS version; suggestions are meaningless without it.",
    }


def find_dependencies(root: Path):
    deps = {"spm": [], "cocoapods": [], "carthage": []}

    for p in iter_files(root, {".resolved", ".json"}):
        if p.name == "Package.resolved":
            try:
                data = json.loads(read(p))
                pins = data.get("pins") or data.get("object", {}).get("pins", [])
                for pin in pins:
                    ident = pin.get("identity") or pin.get("package") or ""
                    state = pin.get("state", {})
                    ver = state.get("version") or state.get("revision", "")[:8]
                    if ident:
                        deps["spm"].append({"name": ident, "version": ver})
            except Exception:
                pass

    for p in iter_files(root, {".lock"}):
        if p.name == "Podfile.lock":
            text = read(p)
            in_pods = False
            for line in text.splitlines():
                if line.startswith("PODS:"):
                    in_pods = True
                    continue
                if in_pods:
                    m = re.match(r"\s+-\s+([A-Za-z0-9_./+-]+)\s+\(([^)]+)\)", line)
                    if m:
                        deps["cocoapods"].append({"name": m.group(1), "version": m.group(2)})
                    elif line.strip() and not line.startswith("  "):
                        break

    for p in iter_files(root, {".resolved"}):
        if p.name == "Cartfile.resolved":
            for line in read(p).splitlines():
                m = re.match(r'\w+\s+"([^"]+)"\s+"([^"]+)"', line)
                if m:
                    deps["carthage"].append({"name": m.group(1), "version": m.group(2)})

    return deps


def analyze_source(root: Path):
    import_counter = Counter()
    signals = {name: 0 for name, _, _ in SIGNAL_PATTERNS}
    swift_files = 0

    for p in iter_files(root, {".swift"}):
        swift_files += 1
        text = read(p)
        for m in IMPORT_RE.finditer(text):
            import_counter[m.group(1)] += 1
        for name, pattern, _ in SIGNAL_PATTERNS:
            if pattern.search(text):
                signals[name] += 1

    apple_used = {k: v for k, v in import_counter.items() if k in APPLE_FRAMEWORKS}
    other_used = {k: v for k, v in import_counter.items() if k not in APPLE_FRAMEWORKS}

    return {
        "swift_file_count": swift_files,
        "apple_frameworks_used": dict(sorted(apple_used.items(), key=lambda x: -x[1])),
        "unclassified_imports": dict(sorted(other_used.items(), key=lambda x: -x[1])),
        "legacy_signals": {k: v for k, v in signals.items() if v > 0},
        "signal_supersedes": {name: sup for name, _, sup in SIGNAL_PATTERNS if sup},
    }


def derive_architecture(source):
    sig = source["legacy_signals"]
    has = lambda k: sig.get(k, 0) > 0
    return {
        "ui": "mixed UIKit + SwiftUI" if has("uses_uikit") and has("uses_swiftui")
              else "SwiftUI" if has("uses_swiftui")
              else "UIKit" if has("uses_uikit") else "unknown",
        "concurrency": "async/await present" if has("uses_async_await") else "no async/await detected",
        "still_uses_combine": has("uses_combine"),
        "observation": "@Observable" if has("uses_observable_macro")
                       else "ObservableObject (pre-Observation)" if has("uses_observableobject")
                       else "none detected",
        "persistence": "SwiftData" if has("uses_swiftdata")
                       else "Core Data" if has("uses_coredata") else "none detected",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.exists():
        print(json.dumps({"error": f"path not found: {root}"}))
        sys.exit(1)

    source = analyze_source(root)
    result = {
        "project_root": str(root),
        "deployment_target": find_deployment_targets(root),
        "dependencies": find_dependencies(root),
        "source": source,
        "architecture": derive_architecture(source),
    }

    out = json.dumps(result, indent=2)
    print(out)
    if args.json_out:
        Path(args.json_out).write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
