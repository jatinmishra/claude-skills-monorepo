---
name: claude-code-assessor
description: Assess a person's Claude Code proficiency through an adaptive interview, then produce a skills gap report and a personalized learning plan. Use this whenever someone wants to test, evaluate, gauge, or benchmark their (or their team's) Claude Code skills, asks "how good am I at Claude Code," wants to know what to learn next, or needs an onboarding/skill check for Claude Code — even if they don't use the word "assessment."
---

# Claude Code Assessor

Run an adaptive, conversational assessment of how well someone uses Claude Code, then tell them exactly where they stand and what to learn next. Questions are NOT pre-written — generate each one at runtime from the competency map plus the live docs. Deliver every question through the **AskUserQuestion** tool as multiple choice, so answering is one tap and scoring is unambiguous.

## What you need before starting

1. Read `references/competency-map.md`. It defines the domains, probes, seed topics, and difficulty bands. It is the source of WHAT to assess.
2. Have the official docs available to verify answers: https://docs.claude.com/en/docs/claude-code/overview. You may also pull from the changelog ONLY for the optional volatile tier (Domain 10), pinned to the person's `claude --version` if you can read it.

Never reproduce course or doc text verbatim in questions. Test the underlying concept in your own words.

## The flow

Three phases: **Calibrate → Assess (adaptive loop) → Report.** Keep the whole thing to roughly 8–12 questions unless the person asks for more or fewer. State the rough length up front so it doesn't feel open-ended.

---

### Phase 1 — Calibrate

Open with one AskUserQuestion call (you can ask up to a few questions at once here, since these aren't adaptive) to set scope. Gather:

- **Goal**: certification-style check / find my gaps / team onboarding / just curious.
- **Self-rated level**: never used it / occasional / daily driver / power user.
- **Focus** (optional, multi-select): which domains matter most to them, or "cover everything."

Use the answers to set the starting difficulty (self-rated level) and domain weighting (focus). Don't trust the self-rating for scoring — it only sets where the first question lands.

---

### Phase 2 — Assess (the adaptive loop)

Repeat until coverage and length targets are met. One question per AskUserQuestion call here, because you need to see each answer before choosing the next.

**1. Pick the next domain.** Spread across domains 1–9. Weight by the person's stated focus, and give domains 8 (verification/debugging) and 9 (judgment/limits) extra weight for anyone above beginner — that's where real skill separates from recall. Don't repeat a domain until others have been covered.

**2. Generate one question.** Take a seed topic from that domain in the competency map and write a single question testing the concept. Strongly prefer scenario framing ("You're mid-task and X happens — what's the best move?") over definition recall. Then write four options: one correct, three plausible distractors that reflect real misconceptions. Keep options mutually exclusive and similar in length so the answer isn't guessable from shape.

**3. Verify before you ask.** Confirm the correct answer against the docs. If you cannot confirm it, discard the question and generate another. Never score against an answer you're unsure of.

**4. Deliver via AskUserQuestion.** Present the question as the prompt and the four choices as options. Give each option a short label and let the description carry the full text. Add a brief neutral header naming the domain (e.g., "Context management") so the person has context, but don't hint at the answer.

**5. Score and adapt.** Record correct/incorrect against the domain. Then adjust difficulty for the next question:
- Correct at current band → step up one band (Beginner → Intermediate → Advanced).
- Incorrect → step down one band and note the gap.
- Two misses in the same domain → mark it a priority gap and move on; don't grind.

Keep a running tally per domain (band reached, hits/misses). Do not reveal correctness mid-assessment unless the person asks — it changes how they answer later. Save the teaching for the report.

**Stop when** you've touched the focus domains, covered a reasonable spread (aim for 6+ distinct domains), and hit the length target. If answers are consistently strong, you can stop early at the top band; if consistently weak, stop early to avoid discouragement and move to the plan.

---

### Phase 3 — Report

Produce a written report (not via AskUserQuestion — this is prose the person keeps). Use this structure:

```markdown
# Your Claude Code Assessment

## Overall level
[Beginner / Intermediate / Advanced] — one-paragraph honest summary.

## Strengths
[Domains where they reached Intermediate/Advanced. Be specific about what they got right.]

## Priority gaps
[The 2–4 weakest domains. For each: what the gap is, why it matters in practice, and the misconception their answers revealed.]

## Learning plan
[Ordered by impact. Map each gap to a concrete next step:
 - the relevant Anthropic Academy course (Claude Code in Action, Claude Code 101,
   Introduction to subagents, the Agent Skills course) — link to https://anthropic.com/learn
 - the specific docs page for the concept
 - one hands-on exercise they can try in a real repo this week]

## Quick wins
[1–2 habits they could adopt immediately for outsized improvement.]
```

Be honest but encouraging. The point is direction, not a grade. Tie every recommendation to something they actually missed — no generic "read the docs."

---

## Guardrails

- **Generate, don't recite.** Questions are written fresh each run. Never paste course material or doc passages; test the idea.
- **Verify before scoring.** A wrong answer key is worse than no question. Confirm against docs first.
- **Keep volatile content optional.** Domain 10 (current features) is off by default. Only include it if the person explicitly wants a currency check, and never let it drive the foundational level rating.
- **Adapt, don't interrogate.** If someone is clearly struggling, ease difficulty and head to the plan. The goal is a useful map of where to grow, not a gotcha.

## Reference files

- `references/competency-map.md` — the domains, probes, seed topics, difficulty bands, and generation rules. Read it at the start of every assessment.
