# DREAMBREAKER — Validation record / Registro de validación

## 1. Pre-registered prospective test / Prueba prospectiva pre-registrada (2026-10-20)
Eight real products were scored using only knowledge available before June 2026. The predictions were sealed with SHA-256 **before** any outcome was searched:
`8bdb0522024acfe7650ceb07caadfa607c76efb2ae75de51340cdf8558b27183`.
Outcome rules were also fixed in advance. An alarm verdict (kill, critical repair or hold) predicts PROBLEMS; a survives verdict predicts HEALTHY.

| Product | DREAMBREAKER | Real outcome (public reports) | Result |
|---|---|---|---|
| Friend AI pendant | KILLED (privacy) | ~3,000 units sold by fall 2025; relaunched July 2026 at double the price after weak sales | ✅ |
| Meta Ray-Ban Display | SURVIVES | Strong US demand; global rollout delayed because of supply shortage | ✅ |
| OpenAI Sora app | CRITICAL REPAIR (competition, costs) | Discontinued, announced March 2026 | ✅ |
| Cluely | CRITICAL REPAIR (copyable, no moat) | Rebranded as a meeting note-taker; CEO retracted revenue claims (March 2026) | ✅ |
| Plaud | SURVIVES | Reported >$250M ARR (June 2026) | ✅ |
| Perplexity Comet | KILLED (platform absorption) | Third-party estimates show strong growth (~18M MAU, Q1 2026) | ❌ |
| 1X NEO | KILLED (technology readiness) | Consumer deliveries not confirmed by October 2026 | Unresolved |
| Daylight DC-1 | SURVIVES WITH MAJOR RISK | No reliable 2026 information found | Unresolved |

**Resolved: 5 of 6 correct.**

**Limits / Límites:**
- The sample is small (6 resolved).
- Some outcomes happened inside the scorer's training period. The hash proves the predictions were not changed after searching. It cannot prove the scorer had no memory of those outcomes.
- The Comet miss shows that a strong platform threat does not kill a well-funded, fast-growing product in the short term.


## 1b. Round 2 pre-registered test / Ronda 2 (2026-10-20)
Sealed before searching: `ef22be610e53a6d8c32abdb6f6cee1d83d29598cc20ce3d802f59f699d636ee9` (file `round2_predictions.json`; round 1 is `round1_predictions.json`).

| Product | DREAMBREAKER | Real outcome | Result |
|---|---|---|---|
| ChatGPT Atlas | CRITICAL REPAIR | Third-party estimates: ~11M MAU, growing (Q1 2026) | ❌ |
| Rivian R2 | CRITICAL REPAIR | Record Q3 2026 deliveries, guidance raised | ❌ |
| Bluesky | CRITICAL REPAIR | Active users down by about half from peak (Aug 2026) | ✅ |
| Threads | SURVIVES | 500M MAU (June 2026) | ✅ |
| Pebble (Core Devices) | SURVIVES | Time 2 delayed 4–6 months | ❌ |
| Zoox | CRITICAL REPAIR | Moving to paid service in Las Vegas, expanding | ❌ |
| Alexa+ | SURVIVES | Over 1M users, gradual US rollout | ✅ |
| Slate Auto | CRITICAL REPAIR | Price rose, deliveries still pending | Unresolved |
| Light Phone III | SURVIVES | No reliable 2026 information | Unresolved |
| Brilliant Labs Halo | CRITICAL REPAIR | No reliable 2026 information | Unresolved |

## 1c. Round 3: out-of-sample test of a proposed fix / Ronda 3: prueba fuera de muestra de un arreglo propuesto
Sealed before searching: `20012d9e0e6b08c0effd12aaa1277cce3dffedf2f07c9719c76fc53de1417ac7` (`round3_predictions.json`).
After round 2, a "short-term survival outlook" was designed from a stated principle ("money buys time, reach and losses; it does not buy demand, working technology, trust or legality") and sealed together with the verdicts.

| Product | Verdict | Real outcome | Verdict result |
|---|---|---|---|
| Valve Steam Machine | SURVIVES | Delayed from early 2026 to summer 2026; price rose with memory costs | ❌ |
| Lovable | CRITICAL REPAIR | Reported $300M ARR (Feb 2026) | ❌ |
| Character.AI | CRITICAL REPAIR | Filed for bankruptcy (Oct 2026) after lawsuits | ✅ |
| Lucid Gravity | KILLED | Q3 2026 production down 38%; second shift eliminated | ✅ |
| Tesla Cybercab | CRITICAL REPAIR | Production started April 2026; paid rides from Sept 2026 (NHTSA review opened) | ❌ |
| Nex Playground | SURVIVES | Approaching 1M units; raised over $150M | ✅ |
| Granola | CRITICAL REPAIR | Raised $125M at a $1.5B valuation (Mar 2026) | ❌ |
| Rabbit R1 | KILLED | Still shipping and updated in 2026 | ❌ |
| Ultrahuman (US) | HOLD | Returned to the US with a redesigned ring (Mar 2026) | ❌ |
| Sesame | CRITICAL REPAIR | No reliable outcome found | Unresolved |

- Verdict: 3/9. **Survival outlook: 2/9. The fix FAILED out of sample and was removed from the public release.**

## 1d. Combined honest score, 3 sealed rounds / Resultado combinado honesto (22 resolved)
| Predictor | Correct |
|---|---|
| DREAMBREAKER verdict as a forecast | 11/22 (50%) |
| Naive "everything survives" | 14/22 (64%) |

| As a problem detector | Result |
|---|---|
| Real problems flagged | **6 of 8 (75%)** |
| False alarms | 9 of 15 alarms (60%) |

**Conclusion / Conclusión:** DREAMBREAKER is **not a forecaster**. As a short-term predictor it is worse than assuming everything survives. It is a deliberately **pessimistic stress test**. It flagged most real failures (Character.AI, Sora, Friend, Cluely, Bluesky, Lucid) at the cost of many false alarms, especially in hot markets and for well-funded teams that kept going despite real weaknesses. Use it like a smoke detector: it tells you where the weaknesses are, not whether you will win.

Known limits: small sample; some outcomes fell inside the scorer's training period; all scores came from one AI scorer, who tended to rate risks high.

## 2. Robustness to scoring error / Robustez ante errores de puntuación
28 profiles, each with 500 random perturbations of every score.

| Noise | Same alarm/no-alarm verdict |
|---|---|
| ±5 points | 96% |
| ±10 points | 92% |
| ±15 points | 87% |

Verdicts become fragile when a score sits close to a threshold (80 or 90). The engine now flags those dimensions as **borderline**. Because one high score is enough to raise an alarm, scoring noise tends to add alarms rather than remove them.

## 3. Historical backtest / Backtest histórico
Leave-one-out over the 20 graveyard cases:
- Failures flagged: average-only scoring 0/11, DREAMBREAKER 11/11.
- Successes not killed: average-only 9/9, DREAMBREAKER 7/9.

Cases were scored knowing the outcome, so this checks coherence, not prediction.

## 4. Unit tests
`python3 test_dreambreaker.py`: 36/36.

## 5. Stress test / Prueba de estrés
- 20,000 random and hostile inputs: 0 crashes.
- 50,000 metamorphic pairs (raising a risk must never improve the verdict): 0 violations after fixes (2 before).
- Found and fixed: blank or placeholder evidence counted as evidence; leaving a dimension unscored let an idea survive (the CLI silently filled missing scores); negative fatal-assumption counts lowered the risk; inflating a risk could buy a precedent appeal; malformed graveyards crashed with unclear errors.
- Performance: about 1.4 ms per evaluation, about 9 KiB peak memory.
