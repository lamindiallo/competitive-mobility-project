# Registered_Tests_Sensitivity_D304.md

**Date:** 30 October 2026
**Status:** Sensitivity check, **not a re-test**. Author decision taken 31 October 2026 (option (a), see end). The registered verdicts (D241–D252) stand as registered. This note reports whether they move when the inputs are corrected or extended, and D012 applies: everything is reported as found.
**Code:** `analysis/hyp/` is unchanged except for one new option: `common.py` gains `FR_ENG4`, which lets a prepared four-tier England ladder be used instead of the one rebuilt from source. The seeds are the registered ones.
**Outputs:** `03 Data/hypothesis_tests/sensitivity_D304/`, with one folder per input set, plus logs.

> **Headline.** H1, H8 and H9 do not move. **H2 does.** On the registered data it is rejected (9 of 10 configurations). On the corrected data with England's full series (set SPLICE), **the primary configuration no longer rejects H2**: England, Spain and Italy decline, and three leagues reject stationarity. H2 survives in 3 of 10 configurations and is rejected in 7. Under D124 that is configuration-dependent, so it is not support for H2. But "H2 rejected" is no longer a clean statement once the data corrections are applied. **This needs an author decision (see the end of this note).**

---

## Input sets

| Set | Two-tier ladders (ESP, ITA, GER, FRA, ENG-2) | England, four tiers | Change against the registered run |
|---|---|---|---|
| **REG** | `03 Data/ladders`, as registered (to 2024/25) | Rebuilt from engsoccerdata, 1958–2024 | None. This is a reproduction check |
| **REP** | REG plus the D295 key repairs only: Athletic Club B (4 rows), 1860 München (10), Hoffenheim (1), and four French keys (1 row each) | As REG; there are no English repairs | Club identity only |
| **SITE** | The website's ladders, 1992/93–2025/26: repairs, official tables (D163 tie-breaks, deductions, titles taken away) and 2025/26 added | The website's ladder, **1992–2025 only** | Everything above, but England's long series is cut to its post-1992 part, so England's pre/post-1992 break cannot be seen |
| **SPLICE** | As SITE | engsoccerdata 1958–1991, then the website ladder 1992–2025 | **The corrected data in full.** The join was checked: for 1992–2024 the two English sources agree on every club key, and differ in only 10 positions, all from official corrections (Middlesbrough's 1996/97 deduction, Everton's 2023/24 deductions) |

**Reproduction.** REG reproduces the registered statistics closely but not exactly. England's G² is 245.9 here against 245.7 registered. Bootstrap p-values differ in the second or third decimal: for example, Spain's primary wild p is 0.071 here against 0.068. **Every registered verdict is reproduced.** The small differences most likely come from re-ordered random draws and the D213/D239 ladder updates made after 8 October. They have not been traced further.

---

## H1 — Cumulative advantage (registered: NOT REJECTED, order limb only)

| | REG | REP | SITE | SPLICE |
|---|---|---|---|---|
| Order test rejects first order (p < 0.05) | 30 / 30 | 30 / 30 | 30 / 30 | 30 / 30 |
| Mover–stayer limb passes (ΔBIC > 10) | 1 / 24 | 1 / 24 | 1 / 24 | 1 / 24 |
| **H1 rejected in** | **0** | **0** | **0** | **0** |

**Unchanged.** In every set, the only mover–stayer pass is England's four-tier series at K = 4.

## H2 — Declining mobility (registered: REJECTED)

**Verdict rule, as registered.** H2 is rejected if fewer than 3 of 5 leagues show a significant decline (wild bootstrap p < 0.05), or if fewer than 3 of 5 reject stationarity. "Common" means England's 1992–2024 two-tier series replaces the four-tier series.

| Configuration | REG | REP | SITE | SPLICE |
|---|---|---|---|---|
| **K5, W = 4, primary** | **Rejected** (declines: ENG, ITA; stationarity rejected: 2) | **Rejected** (ENG, ITA, GER; 2) | **Rejected** (ESP, ITA; 3) | **Not rejected** (ENG, ESP, ITA; 3) |
| K5, W = 4, common | Rejected | Rejected | Rejected | Rejected |
| K5, W = 6, primary | Survives, but the magnitude test fails for FRA | Rejected | Rejected | Rejected |
| K5, W = 6, common | Rejected | Rejected | Rejected | Rejected |
| K5, W = 8 | Not computable | Not computable | Not computable | Not computable |
| K6, W = 4, primary | Rejected | Rejected | Survives | **Survives** (ENG, ESP, ITA, GER; 5) |
| K6, W = 4, common | Rejected | Rejected | Survives | **Survives** (ESP, ITA, GER; 5) |
| K4, W = 4, primary / common | Rejected / Rejected | Rejected / Rejected | Rejected / Rejected | Rejected / Rejected (4 and 3 declines, but stationarity rejected in only 2) |
| Equal quantiles, primary / common | Rejected / Rejected | Rejected / Rejected | Rejected / Rejected | Rejected / Rejected |
| **Rejected in (of 10 computable)** | **9** | **10** | **8** | **7** |

**What drives the change: Spain.** Run on its own, configuration K5, W = 4:

| Spain's input | Wild p (trend) | Mann–Kendall p | Stationarity p | Decline? |
|---|---|---|---|---|
| Registered keys, repaired (REP) | 0.070 | 0.030 | 0.18 | No (borderline) |
| Website ladder, **to 2024/25 only** (official positions, no new season) | **0.032** | 0.003 | 0.26 | **Yes** |
| Website ladder, to 2025/26 | **0.021** | 0.006 | **0.015** | **Yes**, and non-stationary |

The official-position corrections are mostly head-to-head tie-breaks, which LaLiga uses and the results-based table ignores. **They alone make Spain's decline significant.** Adding 2025/26 shifts the four-season blocks (Spain's series now starts in 1993, not 1996) and makes Spain's matrix non-stationary. Every decline passes the magnitude requirement.

**England's long-run decline holds on the corrected data.** In SPLICE, England's four-tier decline is significant in every prize-structure configuration (wild p 0.001–0.011), at 2.6–5.1 null SDs. It is absent under equal quantiles (0.1 SD), exactly as registered (D245): the closing is at the top. Italy's decline also holds.

## H8 — Asymmetric erosion (registered: NOT REJECTED)

| Configuration | REG | REP | SITE | SPLICE |
|---|---|---|---|---|
| EQ5 (primary) | 5 / 6 not rejected (Germany rejected) | 5 / 6 | 5 / 6 | 5 / 6 |
| EQ4 | 4 / 6 (Germany and France rejected) | 4 / 6 | 5 / 6 (France now passes, p = 0.034) | 5 / 6 |
| EQ6 | 5 / 6 | 5 / 6 | 5 / 6 | 5 / 6 |
| EQ5 + exit | 6 / 6 | 6 / 6 | 6 / 6 | 6 / 6 |
| K5 (a mechanical rejection, D250) | 0 / 6 | 0 / 6 | 0 / 6 | 0 / 6 |

**Unchanged.** Germany remains the exception in every equal-band configuration without exits.

## H9 — Churn without contestability (registered: NOT REJECTED)

| Series and window | REG r | REP r | SITE r | SPLICE r |
|---|---|---|---|---|
| England 4 tiers, 10 seasons, R (primary) | −0.13 | −0.14 | −0.29 (inconclusive) | −0.11 |
| England 4 tiers, 10 seasons, Rp | +0.05 | +0.05 | +0.29 | +0.06 |
| England 4 tiers, 8 / 12 seasons | −0.10 / −0.12 | −0.11 / −0.14 | −0.23 / −0.30 (inconclusive) | −0.06 / −0.10 |
| England 2 tiers, 10 seasons, R | −0.32 (inconclusive) | −0.33 (inconclusive) | −0.29 (inconclusive) | −0.29 (inconclusive) |

**Not rejected in any set.** No |r| reaches 0.5.

---

## Consequences

1. **H1, H8 and H9:** no change. They can be cited as registered.
2. **H2:** the registered verdict (rejected) is what the registered test gave on the registered data, and it stays on the record. But the project's own later corrections (D163 official positions, D295 keys), together with one more season, move the primary configuration to "not rejected". Across all configurations the result is mixed (3 survive, 7 reject). On D124's rule this is **configuration-dependent: neither a rejection nor support.**
3. **What survives in every version:** England's top closed after the early 1990s; Italy's has closed since the mid-1990s; Germany and France show no robust decline; no league shows rising mobility. **What changes:** Spain moves from "borderline" to "declines" on the corrected data.

## Author decision (D304, decided 31 October 2026): option (a)

The registered verdict stays on the record and is shown as "No, as registered". Next to it, the website, the Findings Summary and the UEFA brief now say that, on the corrected tables, Spain also declines, so a wider decline cannot be ruled out. Germany and France show no change on either version.
