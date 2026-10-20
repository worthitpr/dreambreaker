---
name: dreambreaker
description: Adversarial idea destruction and existence check. Use when the user wants an idea, product, startup, feature or invention attacked before investing time or money - finds whether it already exists, scores 24 kill dimensions with evidence, applies weakest-link verdicts and compares the idea with historical failures and successes. Not for legal patentability or investment advice.
---

# DREAMBREAKER

Created by **Kritsia Quiñones (XXSELENEPRXX)** · Apache License 2.0

Make weak ideas die before they consume money, time, code or reputation, and avoid killing strong ideas for the wrong reason. Attack the **idea**, never the person. Reply in the user's language.

## Doctrine
- `INTERESTING != GOOD`
- `NO MATCH FOUND != NOVEL`
- `COMPETITION != AUTOMATIC DEATH`
- `DIFFERENT LABEL != DIFFERENT MECHANISM`
- `TECHNICALLY POSSIBLE != READY`
- `STATED INTEREST != DEMAND`
- `SURVIVES KILL TEST != MARKET VALIDATED`
- `ONE CRITICAL WEAKNESS CAN KILL; AVERAGES HIDE FATAL FLAWS`
- `A PRECEDENT IS A QUESTION, NOT A PERMISSION`
- `CHEAP DISPROOF BEFORE EXPENSIVE BUILD`
- `A KILL MUST SURVIVE APPEAL`

## Workflow
1. **Freeze the idea.** Write down the name, problem, user, buyer, mechanism, outcome, differentiators and assumptions. If something essential is missing, ask once, then continue with labeled assumptions.
2. **Existence check (search, never guess).** If web search is available, search these layers and record what was actually searched: exact name, synonyms, problem language, mechanism language, direct products, platform features of large companies, open source, patents, research papers, failed or shut-down products, workarounds people already use, and other languages. If search is unavailable, say so and return `UNKNOWN_INSUFFICIENT_SEARCH` for existence. Never claim "nobody in the world has this". The strongest claim allowed is "no close match found in the searched scope".
3. **Score the 24 kill dimensions** from 0 (no risk) to 100 (fatal): `problem_reality, frequency_severity, buyer_payer, direct_competition, substitutes, prior_art, platform_absorption, technical_feasibility, technology_readiness, security_privacy, regulatory, onboarding_friction, unit_economics, distribution, switching_cost, defensibility, data_advantage, ai_commoditization, timing, operational_burden, dependency_fragility, copyability, evidence_quality, market_proof`. Every score at or above 80 needs at least one concrete evidence reference (source, fact or search result). If a dimension cannot be judged, leave it out rather than inventing a number. An idea cannot get a "survives" verdict while dimensions are unscored, so either research them or score them 40 (neutral) with a written justification. Evidence must be real text references; empty or placeholder evidence does not count.
4. **Fatal assumptions.** List the assumptions that, if false, kill the idea. Count those that are unproven as `fatal_assumptions`.
5. **Run the engine.** Write the input JSON and run `python3 dreambreaker.py input.json`. If code execution is unavailable, apply the same rules by hand:
   - Any unproven fatal assumption → `KILLED_FATAL_ASSUMPTION`.
   - Any dimension ≥ 90 with evidence → `KILLED_CRITICAL_DIMENSION`; without evidence → `HOLD_CRITICAL_UNEVIDENCED`.
   - Any dimension 80–89 → `CRITICAL_REPAIR_REQUIRED`.
   - Any unscored dimension blocks a "survives" verdict → `HOLD_UNSCORED_DIMENSIONS`.
   - Otherwise use the average risk: ≥ 82 killed, ≥ 66 critical repair, ≥ 46 survives with major risk, below that survives.
   - **Precedent appeal:** if a historical success in `graveyard.json` survived *all* of the killing dimensions at a similar severity (no more than 5 points lower) and resembles the idea more than any failure does, change the kill to `HOLD_PRECEDENT_APPEAL` and state the lever the idea must prove it has.
6. **False-kill defense.** Before confirming a kill, look for strong counterevidence from independent sources. If you find it, return HOLD instead of KILL and explain why.
7. **Report.** If the engine flags a **borderline** dimension (within 5 points of 80 or 90), say the verdict is fragile and research that dimension more before deciding. Give the verdict first, then the critical weaknesses with their evidence, the three most similar historical cases (why they died or what saved them), the existence findings, and the **cheapest test** that could disprove the most dangerous assumption. A surviving idea earns one next test, not unlimited investment.

## Input format
```json
{"idea": "Name", "scores": {"substitutes": 90, "unit_economics": 70},
 "evidence": {"substitutes": ["Phone apps already do this for free (source)"]},
 "fatal_assumptions": 0}
```

## Truth boundary
- The graveyard profiles are approximate and assigned in hindsight. Similarity to a past case is a question to investigate, not a prediction.
- No verdict is market validation, a patentability opinion, freedom-to-operate advice, or investment advice.
- A kill means "do not invest more until this is solved", not "it will shut down soon". Well-funded products can live for a long time with a critical weakness.
- Products backed by very large resources often survive risks that would kill a small team. Say so when the backer is powerful.
- DREAMBREAKER is a pessimistic stress test, not a forecaster. In three sealed prospective rounds (22 resolved cases) it flagged 75% of real failures, but 60% of its alarms were false, and as a forecast it scored below a naive "everything survives" baseline (see VALIDATION.md). Always tell the user: the verdict shows where the idea is weak, not whether it will succeed.
- The verdict is only as good as the research and evidence behind the scores. Say clearly which parts were researched and which were estimated.
