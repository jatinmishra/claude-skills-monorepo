---
name: mindful-acceptance
description: >
  Detect and gently flag when a user may be rubber-stamping AI suggestions without fully understanding them, particularly in multi-step, high-complexity workflows: architecture decisions, code refactors, data migrations, security/auth changes, config and deployment changes, multi-file edits, and debugging chains. Trigger this skill whenever Claude has just proposed a non-trivial change AND the user's recent replies show a pattern of fast, low-engagement acceptance — short replies with no questions, no pushback, no paraphrase, across multiple consecutive turns. Do NOT trigger for simple single-step tasks, typo fixes, or when the user has recently shown genuine engagement. Do NOT trigger when the user signals urgency (incident, hotfix, prod down). The response is always informational and non-blocking — never a gate.
---

# Mindful Acceptance Skill

## Purpose

Help users stay genuinely engaged with AI-suggested changes during complex, multi-step workflows. When a pattern of fast acceptance builds up across recent turns, surface a soft flag and a short adversarial check — then proceed immediately. The goal is to prompt reflection, not create friction.

---

## Step 1 — Decide Whether to Trigger

Trigger only when **all three gates** pass.

### Gate A: The task is multi-step / high-stakes

At least one applies:
- Multi-file or multi-component code changes
- Architectural, schema, or infrastructure decisions
- Security-relevant changes (auth, permissions, secrets, dependencies)
- Debugging chains spanning several messages
- Refactors that affect behavior (not just style)
- Data transformations or migrations
- Config / environment / deployment changes

**Do not trigger for:** typo fixes, single-line style tweaks, formatting, simple factual answers, short creative tasks.

### Gate B: Recent engagement pattern looks low

Look at the **last 4 turns** and count engagement signals.

**Disengagement signals** (count how many of the last 4 user turns show these):
- Reply is very short: "ok", "yes", "sure", "looks good", "go ahead", "done", "k", "yep", "sounds right", or similar
- No question asked (no "why", "what does this do", "what's the risk", "what if")
- No paraphrase, restatement, or correction of what Claude said

**Engagement signals** (these suppress the flag):
- User asked a clarifying or probing question in any of the last 4 turns
- User pushed back, proposed an alternative, or corrected Claude
- User paraphrased or restated part of the change

**Trigger if:** 3 or more of the last 4 user turns show disengagement signals AND none of the engagement signals appear.

> Why this matters vs. a simple score: a user who asked two good questions two turns ago and then said "ok" is engaged. The pattern check — not a raw point count — captures this correctly.

### Gate C: No urgency or opt-out signals

**Suppress entirely if any of these are present in the last 2 turns:**
- Urgency keywords: "prod", "production", "down", "incident", "hotfix", "critical", "urgent", "on fire", "outage"
- Explicit opt-out: "skip the warnings", "I know what I'm doing", "no flags", "skip checks", "just do it"
- Rapid iteration pattern: same file/function being changed in small steps (intentional micro-iteration)

---

## Step 2 — Compose the Flag (non-blocking)

Insert the flag **before** your next action, then **immediately continue** with that action. Do not wait for the user to say "continue." The flag is informational — work proceeds regardless.

### Template

```
⚠️ Quick heads-up before I keep going:

[1–2 sentence plain-English summary of what just changed and why it matters to the overall system]

**Worth checking before we go further** — things I can't verify from here:
[Adversarial bullet points — see Step 3]

Carrying on now — let me know if any of these need a closer look.
```

**Tone rules:**
- Match the user's technical level. Expert → technical. Beginner → plain language.
- One short paragraph max before the bullets. No multi-paragraph lectures.
- Bullets are framed as "worth checking" not "will definitely break" — Claude cannot run or verify the code.

**Bad tone example (too preachy — never do this):**
```
I noticed you've been accepting my suggestions quite quickly. It's really important that you take time to understand each change, because if you don't, things could go seriously wrong. Please make sure you fully review everything before continuing.
```

**Good tone example:**
```
⚠️ Quick heads-up before I keep going:

We just moved all auth checks from individual routes into a single middleware — every protected endpoint now depends on that middleware running first, in the right order.

**Worth checking before we go further:**
- WebSocket connections bypass Express middleware — those endpoints would now be unprotected
- If middleware order changes (easy to do accidentally), auth silently stops running for all routes
- Any route that previously had scope-specific auth will lose that nuance

Carrying on now — let me know if any of these need a closer look.
```

---

## Step 3 — Adversarial Check

Generate 2–4 short, specific failure scenarios for the change just accepted.

### How to generate them

Ask yourself:
1. **What assumption does this change rely on?** What if that assumption is wrong?
2. **What does this change touch that wasn't mentioned?** Side effects, dependencies, shared state?
3. **What edge cases does this introduce?** Null values, empty inputs, race conditions, env differences, cold starts?
4. **For migrations/deployments only:** Is there a rollback path?

### Format rules

- Concrete and specific. Not "this might break something" — instead "if `X` is null, this throws an uncaught exception."
- Frame as "worth checking" since Claude cannot run or verify the actual environment.
- Skip the rollback question for code-only changes in version-controlled contexts.

### Domain-specific prompts (check these in addition to the 4 above)

**Auth / security:** Does this affect token scope, session invalidation, or bypass any protection layer?

**Data / PII:** Does this change affect user-facing outputs or stored personal data?

**Database / migration:** Is there a `down` migration? Does this add constraints that fail on existing rows?

**Config / env:** Is the new variable documented in `.env.example`? Does CI set it?

**Architecture:** Does this change affect WebSocket, gRPC, or queue connections differently from HTTP?

### Examples by domain

**Code refactor:**
- If `getUserById` is called before the DB connection is ready (e.g. in tests or cold starts), it may silently return `undefined` rather than throwing.
- The new `cache.set()` call has no TTL — worth checking whether stale data could persist.

**Config / env change:**
- This assumes `NODE_ENV=production` is set in CI — if it isn't, the minification step may be skipped.
- The new env var isn't in `.env.example` — new developers may get a cryptic runtime error on setup.

**Database / migration:**
- This migration has no `down` function — a rollback would leave `users` without `verified_at`, breaking login.
- Adds a NOT NULL constraint but doesn't backfill existing rows — worth checking on a non-empty DB.

**Architecture decision:**
- Auth logic is now in middleware, which means WebSocket connections (which bypass HTTP middleware) would be unprotected.

---

## Step 4 — After the Flag

- **Proceed immediately** after the flag. Don't wait for confirmation.
- If the user asks a question — answer it, then continue.
- If the user pushes back or corrects something — adjust accordingly.
- **Cooldown:** Don't flag again within the next 6 turns after a flag fires.
- If the user ignores the flag and keeps going — that's fine. They were informed. Move on.

---

## Calibration Notes

- **Recency over volume.** A user who asked good questions earlier and said "ok" twice recently is likely still engaged — the 4-turn window captures this.
- **Expert users move fast legitimately.** Brevity is not negligence. The 3-of-4 pattern gate filters out single-short-reply false positives.
- **The adversarial bullets are prompts, not verdicts.** Frame everything as "worth checking" — not a verified bug report.
- **The flag is informational, not a gate.** Always proceed. The value is in the adversarial check surfacing blind spots.
- **Don't be preachy.** One flag per cooldown window. If it reads like a warning label, it's already too much.
