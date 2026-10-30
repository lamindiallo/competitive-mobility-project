# Hypothesis_Register.md

**Document Version:** 6.1
**Status:** Active
**Last Updated:** 29 October 2026
**Governing Decision:** D014

---

# Purpose

Principle 7 requires that every conclusion remain falsifiable. A hypothesis stated after the results are known is not a hypothesis but a description.

This register records each hypothesis, its falsification condition and the test that will decide it, **before** the corresponding analysis is run.

**A hypothesis may not move to Registered until its falsification condition names a specific quantity and a specific threshold.**

---

# Registration Status

| Status | Count |
|---|---|
| **Registered** — condition specified, analysis not yet run | **1** (H7) — needs league revenue by decade |
| **Draft** — condition cannot yet be specified, reason recorded | **6** (H3, H5, H6, H10, H11, H12) |
| **Tested** | **5** — **H4 rejected** (D280), **H1 not rejected** (history dependence; causal reading not identified), **H2 rejected** (D242–D244), **H8 not rejected** (D249–D250), **H9 not rejected** (D251) |
| Withdrawn | 0 |

> **The four remaining Draft hypotheses are honest.** Each depends on a quantity whose scale is unknown until the index exists or the data is assembled. Setting a numerical threshold now would be arbitrary, and an arbitrary threshold is worse than a declared gap because it creates the appearance of pre-registration without the substance.

---

# Two Conventions Applying to All Registered Hypotheses

**1. Inference is by permutation or bootstrap, never by closed-form standard errors** (D049, D051). Where a significance level is stated below, it refers to a permutation p-value computed against the null constructed under D034.

**2. Statistical significance is necessary but not sufficient.** Every registered condition also carries a **magnitude requirement**, because with roughly 600 transitions per league a trivially small effect can clear a significance threshold. Where the magnitude threshold is expressed relative to the simulated null rather than as an absolute number, this is deliberate: **the null distribution is the only scale the project has that is not arbitrary.**

---

# Part I — Core Hypotheses

## H1 — Cumulative advantage

**Statement.** Competitive position exhibits cumulative advantage: a club's history of positions causally raises its probability of holding a high position in future, over and above the persistence explained by its current position and its resources.

**Sharpened by D041.** Increasing returns are neither necessary nor sufficient for path dependence. **Demonstrating path dependence requires showing that the *order* of past outcomes matters, not merely their sum.** A test showing only that current position predicts future position demonstrates *state* dependence and does not support H1.

**Test.** Anderson and Goodman (1957) likelihood-ratio test for the order of the chain, with **bootstrapped critical values** (D074), run on the pyramid-wide state space at K = 5.

> **Falsification condition. H1 is rejected if the first-order Markov property is not rejected at a bootstrapped p < 0.05, and the mover–stayer model does not improve on the homogeneous first-order chain by ΔBIC > 10.**

**Both limbs are required.** A first-order chain that fits adequately means the past beyond the current state carries no information — that is state dependence, not path dependence. The mover–stayer limb is included because a permanent-elite-plus-churning-remainder structure is a form of history dependence that a naive order test may miss.

**Status.** **Tested 8 October 2026 — NOT REJECTED** (`06 Analysis/H1_H2_Test_Results.md`, D242–D243).

> **Result.** The first-order property is rejected in all 30 configurations (permutation p ≤ 0.004; England four tiers 1958–2024: G² = 245.7 against a null mean of 38.7). The mover–stayer limb fails in 23 of 24 fits. **H1 survives on the order limb alone.**
>
> **Reading.** The dependence pulls clubs back towards their own past level — newcomers to the English top four stay 19% of the time, incumbents 75%; clubs just fallen out return 21% of the time, settled mid-table clubs 3%. **That is history dependence of the kind persistent club differences produce, not success breeding success. The causal claim in H1's statement is not identified by its registered test** and is not to be asserted. A resource-conditioned version requires the wage panel (D198).

---

## H2 — Declining mobility

**Statement.** Competitive Mobility in the scope leagues has declined over the study period.

**Sharpened by Block 1.** Buzzacchi, Szymanski and Valletti found open European leagues already less dynamically balanced than closed North American leagues in the early 2000s. **The project must demonstrate a trend, not merely a low level. A finding that mobility is low does not support H2.**

**Test.** Two limbs, both required.

1. **Trend.** Wild-bootstrapped OLS trend coefficient on the mobility index series per league, with a Mann–Kendall test as a distribution-free check.
2. **Matrix homogeneity.** Anderson and Goodman test for stationarity of the transition matrix across sub-periods, bootstrapped critical values.

> **Falsification condition. H2 is rejected if the trend coefficient is not significantly different from zero at bootstrapped p < 0.05 in a majority of scope leagues, or if the stationarity test fails to reject homogeneity of P across sub-periods at bootstrapped p < 0.05.**

**Magnitude requirement.** Even where significant, a trend is treated as substantively supporting H2 only if the implied change over the study period exceeds **one standard deviation of the index's simulated null distribution**. A statistically detectable drift smaller than sampling noise under a random process is not a decline in mobility.

**Status.** **Tested 8 October 2026 — REJECTED** (`06 Analysis/H1_H2_Test_Results.md`, D244–D246).

> **Result.** Primary configuration: a significant decline in only **2 of 5** leagues (England 1958–2024, Italy 1996–2024); homogeneity of P rejected in the same 2. Both limbs fail. **Rejected in 9 of 10 computable configurations**; the one survival fails the magnitude requirement for France and is configuration-dependent (D124).
>
> **What survives inside the rejection (D245):** England's long-run decline (2.8–5.3 null SDs, every prize-structure configuration, absent under equal quantiles — the closing is at the top); Italy since the mid-1990s; Spain borderline; Germany and France no decline — a change two-thirds the size of England's 1990s shift would have been detected with power ≥ 0.94, a change one-third its size only with 0.25–0.43 (D246). **No league shows rising mobility in any configuration.**

**Note.** Independent evidence already exists from Manasis and Ntzoufras: their composite index rose about 30 per cent across sixty English seasons, and clubs appearing in the top five over a five-season window fell from 15 in 1991 to six in 2008. **This makes H2 more likely than not, which is precisely why its falsification condition is registered before the project's own estimation.**

---

## H3 — Decision efficacy

**Statement.** Clubs can achieve durable improvements in competitive position through superior sporting and organisational decisions, independent of resource increases.

**Registered prior (D062).** The verified evidence currently runs **against** this hypothesis. Managerial rent is competed into manager salaries and diffuses by hiring; the post-dismissal bounce is regression to the mean; homegrown rules had very limited impact; the player-valuation environment is already efficient. **This prior is recorded so that a null result cannot later be presented as a discovery.**

**Intended test.** Residual-based, following the Demsetz efficiency-defence logic. Estimate resource-conditional performance, then test whether sustained positive residuals predict upward state transitions beyond current state and current resources.

**Why this remains Draft.** The residual's scale is unknown until the resource-conditional model is estimated, and the transition-probability difference that would count as "durable improvement" cannot be set without knowing the base rates in the estimated matrix. **A threshold set now would be a guess.**

> **Condition to be specified at Phase II completion**, once the state space is populated and base transition rates are known. The form is fixed: the difference in upward-transition probability between clubs in the top and bottom quartiles of sustained residual performance, compared against the permutation null.

**Status.** **Draft.** Blocked on the resource-conditional model.

---

## H4 — Convertibility

**Statement.** Sporting overperformance relative to resources converts into durable resource gains, such that a club that outperforms its wage bill for a sustained period subsequently occupies a permanently higher resource tier.

**Test.** Regress the change in relative wage bill on lagged cumulative resource-conditional residual performance, on the England and France panel (D026), with club and season fixed effects and bias-corrected LSDV (D073).

> **Falsification condition. H4 is rejected if the coefficient on lagged cumulative residual performance is not significantly positive at bootstrapped p < 0.05 at a three-year horizon, or if the effect does not persist at a five-year horizon.**

**The persistence limb carries the word "durable".** A conversion effect that decays within three years is a temporary reward, not a change of tier, and does not support H4.

**Status.** **Tested 29 October 2026 — REJECTED** (`06 Analysis/H4_Test_Results.md`, D280–D281). Under the registered specification the coefficient is negative at both horizons. Conversion appears only conditional on current payroll (robustness 2) at three years, not at five: configuration-dependent under D124. **The note below now applies: mobility from over-performance is temporary unless shown otherwise.**

**Note.** H4 remains the project's analytical hinge. **If overperformance is not convertible, then mobility is temporary by construction, and the distinction between temporary and permanent mobility becomes the central finding rather than a technical detail.**

---

## H5 — Institutional causation

**Statement.** Identifiable governance decisions are associated with measurable changes in Competitive Mobility.

**Constrained by D065 and D066.** Financial Fair Play is not identifiable. The only available causal design is **staggered domestic regulation** — the German licensing system, the French DNCG, the Italian Co.Vi.So.C., the English Championship rules of 2012 and 2015, and the EFL Salary Cost Management Protocol.

**Intended test.** Callaway and Sant'Anna group-time average treatment effects on a club-tier-season panel, with not-yet-treated controls, multiplier bootstrap, and Rambachan and Roth sensitivity bounds.

**Why this remains Draft.** The adoption dates and tier coverage of the domestic regimes **have not yet been assembled** — this is an outstanding documentary research task recorded in `Block_08_Statistical_Methodology.md` §9. Until the treatment timing is known, the number of groups and periods is unknown, and no meaningful threshold can be set.

> **Condition to be specified once the regulation adoption panel is assembled.**

**Status.** **Draft.** Blocked on documentary research.

---

# Part II — Hypotheses Derived from Industrial Organization

## H6 — Contestability failure through sunk costs

**Statement.** An open league can exhibit formal openness while displaying no contestability, because the sunk component of competitive investment is high.

**Why this is the project's primary structural explanation.** It accounts for the Buzzacchi paradox — equality of opportunity without equality of outcome — **without any appeal to governance failure**. Under Principle 4 it is therefore the null against which governance explanations are tested, not an alternative alongside them.

**Why this remains Draft.** Testing it requires an estimate of the **sunk share of competitive investment** — what proportion of transfer fees and wage commitments is unrecoverable on exit. **No such estimate exists in the literature and the project has not established that one is constructible from available data.**

> **Condition to be specified only if a sunk-share estimate proves feasible.** If it does not, H6 is **withdrawn as an empirical hypothesis and retained as a theoretical interpretation**, clearly labelled as such. That outcome must be declared rather than allowed to blur.

**Status.** **Draft.** Feasibility not established.

---

## H7 — Bounded concentration under endogenous sunk costs

**Statement.** The growth of broadcast revenue has **not** reduced concentration at the top of European leagues, because clubs competed the additional revenue away in a wage arms race rather than allowing it to fund a fringe of new challengers.

**Test.** A **bounds test on the lower envelope** (D040), not a regression. Plot top-club concentration against total league revenue across leagues and decades, and test the shape of the lower envelope. Sutton's theory delivers a bound, not a prediction of the mean; **fitting OLS through the cloud tests the wrong thing.**

> **Falsification condition. H7 is rejected if the lower envelope of top-club concentration is significantly declining in real league revenue** — that is, if the fitted lower-envelope slope is negative at bootstrapped p < 0.05 across the pooled league-decade observations.

**Secondary prediction, tested but not decisive.** The bound should be tighter in leagues where resources map more reliably onto position. Failure of the secondary prediction weakens but does not falsify H7.

**Status.** **Registered.** **This is the most directly testable hypothesis in the register and among the most consequential for Phase IV** — because it bears on whether redistributing revenue would change anything.

---

## H8 — Asymmetric erosion

**Statement.** Competitive advantage erodes **slowly at the top and quickly at the bottom** — the mirror image of the asymmetry found in the industrial persistence-of-profits literature.

**Test.** Estimate the persistence parameter separately by position band, using bias-corrected estimation (D038), on the pyramid-wide state space. Equivalently, compare state-specific diagonal retention probabilities in the estimated transition matrix.

> **Falsification condition. H8 is rejected if the persistence parameter for the top state is not greater than that for the bottom state, or if the difference does not exceed the 95th percentile of the difference under the permutation null.**

**Why the magnitude limb matters here particularly.** Some top-versus-bottom asymmetry arises mechanically from boundary effects — the top state has no state above it to fall from symmetrically. **The permutation null absorbs exactly that mechanical component**, which is why the threshold is expressed against it rather than as an absolute difference.

**Status.** **Tested 8 October 2026 — NOT REJECTED** (`06 Analysis/H8_H9_Test_Results.md`, D249–D250).

> **Result.** Equal-size position bands (primary): top-band retention exceeds bottom-band retention by more than the permutation null's 95th percentile in England 1958–2024 (D = +0.105, null 95th percentile 0.041, p = 0.0005) and in 4 of 5 two-tier series. Survives in 4 of 5 configurations; the prize-structure (K = 5) rejection is mechanical, since limb 1 there compares a 4-club state with a 12–48-club one. **Germany is the exception** in every equal-band configuration without exits.

**Note.** Independent support already exists: Manasis and Ntzoufras find relegation-end mobility markedly higher than top-end mobility across sixty English seasons, and conclude the promotion-relegation rule contributes more than the champion to dynamic balance.

---

## H9 — Churn without contestability

**Statement.** Promotion and relegation turnover is largely orthogonal to whether the elite is contestable. Movement among clubs continuously present in the top tier, not entry and exit, drives changes in concentration at the top.

**Test.** Decompose the mobility index into (i) movement among clubs continuously present in tier 1 across the window and (ii) movement attributable to promotion and relegation (D036). Compute the correlation between the two components across leagues and rolling windows.

> **Falsification condition. H9 is rejected if the correlation between the promotion-relegation component and the elite-tier component exceeds 0.5 in absolute value at bootstrapped p < 0.05.**

**The 0.5 threshold is a judgement and is declared as such.** It is set at the level above which the two components could not sensibly be described as telling different stories. **It is registered now precisely so that it cannot be adjusted after the correlation is seen.**

**Status.** **Tested 8 October 2026 — NOT REJECTED** (`06 Analysis/H8_H9_Test_Results.md`, D251).

> **Result.** Pooled r = −0.13 between elite-tier movement and promotion–relegation churn breadth (10-season windows, five leagues, 150 windows); bootstrap 95th percentile of |r| = 0.44. Not rejected in all six configurations; one is inconclusive. In England, elite movement fell by about a third after 1992 while churn breadth did not change. Components defined in `H8_H9_Test_Protocol.md` §2.1 before computation, since D036 did not define them.

**Note.** Manasis and Ntzoufras observed this asymmetry but did not draw the inference that an aggregate index therefore conflates two regimes (D093). That inference is the project's.

---

## H10 — Superstar mechanism

**Statement.** Concentration of resources at the top is driven by joint consumption and imperfect substitutability of talent (Rosen) rather than solely by accumulated supporter attachment (Adler).

**Why it matters for policy.** The two mechanisms imply different interventions. **If Rosen dominates, redistributing playing talent is the relevant lever. If Adler dominates, the advantage lies in accumulated attention and would survive talent redistribution untouched.**

**Why this remains Draft.** Separating the two requires a measure of accumulated supporter attachment independent of current performance. **The project has not established that such a measure is constructible from the available data**, and the obvious candidates — attendance, social following, historical support — are all endogenous to past success, which is the very thing being separated out.

> **Condition to be specified only if an exogenous attachment measure proves feasible.** If it does not, H10 is **withdrawn and the policy implication reported as unresolved**, which is itself a finding worth stating to UEFA.

**Status.** **Draft.** Feasibility not established.

---

## H11 — Conversion window (added 8 October 2026, D206)

**Statement.** Revenue-indexed spending rules (the SCMP's wage-to-turnover ratio; Profitability and Sustainability loss limits) protect incumbents because they bind on investment made *ahead of* the revenue that over-performance eventually earns. They therefore shorten the window in which a temporary decision advantage can be converted into a lasting resource gain.

**Origin.** Interim resource-conditional findings on a transfer-spend proxy: over-performance relative to resources barely persists (D202) but converts into resources at about 0.6 places per place, two seasons later, via promotion (D203, D211). **Durable Mobility is conversion efficiency (D205).**

**Why Draft.** The falsification condition needs the lag between over-performance and recorded revenue, which requires per-club revenue (D198).

> **Provisional form, to be fixed before the test is run:** H11 is falsified if, among over-performing clubs, the lag from over-performance to recorded revenue gain is no longer than one season — because a rule indexed to revenue cannot then bind before the revenue arrives.

**Status.** **Draft.** Blocked on the wage and revenue panel.

---

## H12 — Crowding (added 8 October 2026, D222)

**Statement.** At equal resources, entry to the top four is harder where more incumbents hold near-elite resources.

**Origin.** On the transfer-spend proxy, England's top spenders are the most evenly matched in the Big Five, yet at equal relative spend English clubs break into the top four significantly less often than Spanish, French or German ones (D220, D221). Crowding is one explanation; a wage-based elite advantage invisible to transfer spend is the other.

**No novelty is claimed.** In multi-prize contest models (e.g. Clark and Riis, 1998) crowding is a standard comparative static.

> **Provisional form, to be fixed before the test is run:** H12 is falsified if, once wages replace transfer spend, England's league effect in the reach model is no longer negative at equal relative resources — that would make the transfer-spend result a measurement artefact rather than crowding.

**Status.** **Draft.** Blocked on wages. **Weakened by an exploratory test on the proxy** (Part III, E1).

---

# Part III — Registration Discipline

No hypothesis may be added after the analysis bearing on it has been run. Where analysis generates a new proposition, it is recorded as an **exploratory finding**, clearly distinguished, and requires independent confirmation on data not used to generate it.

| ID | Exploratory finding | Generated from | Confirmation status |
|---|---|---|---|
| E1 | **Crowding does not explain England's conversion cliff on the transfer-spend proxy**: near-elite count +0.06 (p = 0.39), near-elite rivals above +0.01 (p = 0.92); England's league disadvantage unchanged. Bears on H12; does not test it | `03 Data/resource_proxy/xc_crowding_output.txt` (D238) | **Unconfirmed** — requires wage data |
| E2 | **The first-order Markov chain overstates outsiders' prospects, more so the more closed the elite** (model ÷ observed ten-season top-four reach 0.80 before 1992, 0.45 in 2003–14). Bears on H1's mover–stayer limb | `08 Policy/Club_Values_Specification_Draft.md` §4 (D231) | **Consistent with the H1 order test** (history matters beyond the current state); **not captured by the mover–stayer model**, which finds no stayers in the top state (D242) |
| E3 | **Two or three fixed club types do not fully reproduce the second-order dependence found by the H1 order test**: a 2-type mixture of first-order chains leaves it unexplained in every series (p ≤ 0.013); 3 types come close for Spain, Italy and Germany (p = 0.03–0.06), not for England or France (p ≤ 0.01). A continuous spread of club quality is untested | `02 Framework/code/hyp/e3_mixture.py`, `03 Data/hypothesis_tests/e3_mixture.jsonl` (D243) | **Unconfirmed** — exploratory; bears on how H1's survival is read |

---

# Part IV — The Null Model Requirement

Applying to every hypothesis in Parts I and II.

> **An observed mobility value is uninterpretable without knowing what a purely stochastic process would produce for the same number of clubs, the same state structure and the same number of seasons.**

Only one paper in the sports literature benchmarks against a null (Buzzacchi, Szymanski & Valletti, 2003), and its benchmark is now reconstructible (D090).

**Requirement (D034, D049).** For every headline statistic, simulate synthetic league histories under a no-persistence permutation null with the same parameters, compute the same statistic on each replication, and report the observed value against that distribution.

**This is also the scale against which the magnitude requirements above are set.** Without it, the thresholds in this register would have no units.

---

# Part V — What Would Make the Project Wrong

Recorded because Rule Zero requires it, and because a register that cannot say what failure looks like is not doing its job.

**The project's central premise fails if:** H2 is rejected — mobility has not declined — **and** H1 is rejected — position dependence is first-order state dependence with no historical component.

In that case European football's hierarchy would be persistent but not self-reinforcing, and stable rather than closing. **The correct conclusion would be that the system is functioning as an open meritocracy with high but non-increasing persistence, and that no intervention is warranted on mobility grounds.**

That conclusion would contradict the project's working hypothesis, the author's expectation, and the entire premise of a submission to UEFA.

> **Status after testing (8 October 2026, D248).** **H2 is rejected; H1 is not.** The condition above is therefore **not met**. But H1 survives only as history dependence of unidentified cause, so the project does not rest on it. **The general premise — European football is closing — is rejected. The defensible premise is narrower: closing at the top in England (robust) and Italy, borderline in Spain, absent in Germany and France.**

> **It would nonetheless be the finding, and it would be reported as such.**
