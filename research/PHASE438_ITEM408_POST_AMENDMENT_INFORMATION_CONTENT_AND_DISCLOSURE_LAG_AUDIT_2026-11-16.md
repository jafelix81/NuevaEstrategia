# Phase 438 — Item 408 post-amendment information-content and disclosure-lag audit

**Audit date:** 2026-11-16 UTC  
**Disposition:** Reclassify Item 408 as a low-priority plan-lifecycle/context source, not a standalone Smart Money direction signal. Plan-termination returns measured from the private termination date are not tradable from the later periodic disclosure. No alpha, OOS or portfolio test was run.

## Executive finding

New literature materially narrows the Item 408 hypothesis.

A full-text October 2025 working paper by Sehwa Kim, Seil Kim and Shiva Rajgopal finds that the 2022 Rule 10b5-1 amendments substantially reduced opportunistic plan sales, including sales made soon after adoption. Its post-amendment plan-termination sample (311 cases, June 2023–May 2025) shows positive abnormal returns around the **termination date**, but the termination was disclosed an average of 82.4 days later (median 83 days). Only two cases in the sample were disclosed promptly on Form 8-K; most appeared in later 10-Q/K filings.

This creates a critical point-in-time distinction:

- **Economic termination date:** when the insider ended the plan; generally not public at that time.
- **Public disclosure date:** when the 10-Q/K or 8-K became public; this is the earliest admissible signal timestamp.
- Returns measured from the economic termination date cannot be treated as a tradable public signal if the disclosure arrived weeks or months later.

A separate 2026 journal article by Yun Ma reports that the predictive content of preplanned trades declined substantially after the amendments, while non-preplanned signals were confined to the short term. The accessible record is the abstract only; the full article is paywalled.

**Decision:** keep Item 408 for plan supply/lifecycle context and a narrowly defined public-disclosure event study. Do not call a plan termination a bullish Smart Money signal or use its undisclosed termination date as a feature. Form 4 transaction-level flow remains the more direct insider hypothesis, but its issuer/security identity bridge is still only 53/96 and below the 95% admission gate.

## 1. Repository and Actions preflight

- Main HEAD before this report: `fa5a2dac98dd0a465788aa92494ac0318ff1025e`.
- Latest 100 Actions runs: 63 success, 36 failure, 1 cancelled; 7,674 total runs reported.
- Explicit `in_progress` and `queued` queries returned zero.
- Repository audit: 272 branches across three pages, 56 open PRs, 66 workflow files. No Phase 438 branch existed. No workflow was dispatched or duplicated.
- Latest research CI: [run 43889092341](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43889092341), one offline-regression job succeeded. Python compilation passed; 57/57 tests passed (Phases 433–437). No artifact was configured or expected.
- Latest SEC Form 144 capture: [run 43862500790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790). Both offline-regression and live-capture jobs succeeded; the offline suite passed 15/15. The live capture observed 55 feed rows (50 Form 144 + 5 Form 144/A), zero new accessions/events and zero signal-eligible events. Artifact [14223876987](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790/artifacts/14223876987), 1,181 bytes, SHA-256 `a1a806b330723ab6d8487727518b80fe70ea3ed93a9a30a93720a09f904d74aa`. The run committed no new feed event rows. The :37 hourly schedule remains best-effort; do not manually dispatch to fill apparent gaps.
- Latest CFTC run remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a 2026-11-13 push/bootstrap rather than the 2026-11-16 scheduled observation. It retained 3,035 historical warm-up rows, had zero signal-eligible rows, and made no persistent capture change. Artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705), 1,068 bytes, SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`. The next expected scheduled poll is 2026-11-16 22:15 UTC, after the CFTC calendar's 20:30 UTC release. No capture was run early.

## 2. New literature and its quantitative implications

### 2.1 Kim, Kim & Rajgopal (October 2025 working paper)

**Insider Trading After the 2022 Rule 10b5-1 Amendment** — [full working paper PDF](https://accounting.wharton.upenn.edu/wp-content/uploads/2025/10/KimKimRajgopal.pdf).

The authors use SEC DERA officer/director transactions from 2021–2024, with a pre-period of 2021Q1–2023Q1 and post-period of 2023Q2–2024Q4. They classify plan trades using Form 4 footnotes and the checkbox; the pre/post availability and voluntary nature of footnote disclosures create a measurement break that must be respected.

Reported findings:

- The proportion of plan sales made within 90 days of adoption falls from **31.1% to 1.7%** after the amendment.
- The proportion of insider sales classified as 10b5-1 falls from **52.5% to 50.3%**.
- Post-amendment 10b5-1 sales are less associated with subsequent negative abnormal returns and less likely to precede earnings misses.
- The authors find a reduction in opportunistic plan use rather than a material migration of those sales to non-plan channels; potential abusers reduced plan use by 8.6 percentage points more than other insiders.
- The paper notes a possible cost: firms more affected by the amendment show lower intraday price efficiency.

#### Plan terminations: positive event-time returns, but delayed disclosure

The paper identifies **311** post-amendment plan terminations disclosed in 10-Q/K filings from June 2023 through May 2025.

| Measure | Result |
|---|---:|
| Termination-to-disclosure lag, mean | 82.4 calendar days |
| Median | 83 days |
| 25th / 75th percentile | 63 / 101 days |
| Adoption-to-termination, mean | 212.6 days |
| Remaining plan duration at termination, mean | 246.2 days |

The reported abnormal returns around the **termination event date** are:

| Horizon from termination | Mean abnormal return | t-statistic |
|---|---:|---:|
| 30 sessions | +1.5% | 1.52 (not significant) |
| 60 sessions | +4.5% | 2.77 |
| 90 sessions | +6.8% | 2.53 |
| 180 sessions | +10.7% | 2.50 |

The authors state that only two terminations in their sample were disclosed promptly through an 8-K; most were disclosed much later in a periodic 10-Q/K. Their Figure 7 and Table 9 measure returns around the termination event, while the same paper separately documents the 82.4-day disclosure lag. These returns therefore must **not** be represented as returns available to an investor who first learns of the termination at the later filing.

The 82-day lag is a material staleness problem, not a small timestamp adjustment. The sample also lacks a comprehensive pre-amendment termination population, so it cannot establish a clean before/after causal effect for termination events.

### 2.2 Ma (2026), peer-reviewed journal publication

Yun Ma, **“The changing role of preplanned insider trades: Evidence from the SEC rule 10b5-1 amendments,” International Review of Economics & Finance, 110(C), 2026**, [DOI 10.1016/j.iref.2026.105650](https://doi.org/10.1016/j.iref.2026.105650); [bibliographic record and abstract](https://ideas.repec.org/a/eee/reveco/v110y2026ics105905602600763x.html).

The accessible abstract reports transaction-level data from 2000–2024. Before the amendments, both preplanned and non-preplanned trades exhibited contrarian behavior and predictive power, with non-preplanned trades more informative. After the reforms, preplanned predictive content declined substantially and non-preplanned signals were confined to the short term.

The full text was not accessible in this audit. Treat this as corroborating abstract-level evidence, not a substitute for reviewing the paper's full specification, sample construction, robustness and event timing.

### 2.3 Earlier evidence is regime-dependent

Yen-Jung Lee, **“Insiders’ Foreknowledge of Earnings Results and Rule 10b5-1 Sales Trades,” Journal of Accounting, Auditing & Finance, 38(1)**, [DOI 10.1177/0148558X20964642](https://journals.sagepub.com/doi/10.1177/0148558X20964642), reports that some pre-amendment plan sales preceded disappointing earnings and tended to be infrequent, irregular and close to plan initiation. This is useful historical context, but it should not be transported mechanically to the amended post-2023 regime.

The SEC's [December 14, 2022 final-rule announcement](https://www.sec.gov/newsroom/press-releases/2022-222) confirms the new cooling-off periods, restrictions on overlapping and single-trade plans, good-faith/certification conditions and new disclosures. Section 16 filers had to comply with amended Forms 4/5 for filings on or after April 1, 2023; periodic-report disclosure timing is staggered by issuer fiscal period and SRC status.

## 3. Cross-check against our actual Item 408 casebook

The Phase 436 CarGurus case independently illustrates the same disclosure-lag issue:

- Matthew Quinn's earlier plan was adopted 2023-12-05 and terminated 2024-03-04.
- The termination was disclosed in CarGurus' 2024 Q1 Form 10-Q, accepted 2024-05-09.
- The gap from the private termination date to public filing was **66 calendar days**.

The SEC's [filing index](https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/0000950170-24-056957-index.htm) records acceptance at 16:11:18 Eastern on May 9, 2024. The SEC's [R10 Item 408 rendered facts](https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/R10.htm) disclose the December 5 adoption and March 4 termination. The exact public-availability timestamp remains the EDGAR acceptance boundary, converted from Eastern to UTC; for conservative daily backtests, use the next eligible regular session.

This is one cross-source case, not a population estimate. It corroborates that a periodic Item 408 termination disclosure can arrive long after the economic event.

## 4. Revised source ranking and hypotheses

### Item 408 adoption

**Retain, low priority, as potential-supply/context information.** It can disclose an arrangement before some future sales, but the amount may be gross, conditional, net of withholding, a dollar amount, a purchase, or an exercise-and-sale. It is not an expected execution schedule. Use the filing's first public acceptance time, not adoption date. Do not infer that every plan is bearish or that a plan will be fully executed.

### Item 408 termination

**Downgrade as a real-time directional signal.** The economic termination date is not the tradable event date. The only admissible event timestamp is the first public 8-K/10-Q/10-K acceptance. A public-disclosure event study may still be warranted, but must measure returns after that disclosure, not after the undisclosed termination date.

A termination may indicate that planned future supply was removed, but the amount remaining, reason for termination, and whether the plan would otherwise have executed are often unknown. No bullish label is justified.

### Form 4

**Keep transaction-level Form 4 as the more direct insider-flow hypothesis**, with separate post-amendment regime treatment. AFF10B5ONE is a filing-level exclusion/context field, not a transaction-level signal. An unchecked flag is not proof of a discretionary trade; code P is open-market or private purchase and needs footnote adjudication. Current issuer/security identity coverage remains 53/96 (55.21%), below the required 95% gate; no return test is authorized.

## 5. If data coverage later passes: preregistered PIT test design

Do not run this until original filing bytes, identity and universe coverage pass.

1. Store separate `termination_effective_date`, `first_public_acceptance_utc`, `first_seen_utc`, accession, filing form/amendment, issuer CIK, person/plan key, source URL and raw hash.
2. Treat the effective termination date as a latent historical event, never as a tradable timestamp unless a contemporaneous public filing proves it was disclosed then.
3. Primary event clock: first public acceptance; enter no earlier than the next tradable session after verified availability. For historical filings without a first-seen receipt ledger, use the conservative next session after the filing date.
4. Compare event-time returns from the termination date (diagnostic only) with returns from public disclosure (tradable test). If the effect exists only from the private termination date and disappears after disclosure, kill the tradable hypothesis.
5. Predeclare 1-, 5-, 20- and 60-session descriptive horizons, with the strategy's eventual holding/exit policy determined separately; no holding-period constraint is imposed on the overall strategy.
6. Control for market/sector returns, recent momentum/run-up, earnings proximity, size/liquidity, plan type and the disclosure lag. Cluster inference by issuer and plan; account for overlapping event windows and multiple testing.
7. Test incremental information versus frozen LTM/F80 with identical exposure and costs, chronological splits, bootstrap/LOO and a genuinely untouched OOS period. No event study on a purposive handful of issuers can admit a signal.

## 6. Decision and controls

- Item 408 remains a low-priority plan-lifecycle/context source; no standalone directional Smart Money feature admitted.
- Plan termination's economic event date is explicitly non-tradable when only later disclosed.
- Form 4 remains blocked by identity coverage (53/96 versus 95% required).
- No new data were downloaded into the repository; external sources were reviewed through public SEC pages and published research.
- No return, alpha, OOS, bootstrap, LOO or holdout test was run.
- No workflow, capture cadence, trading code, signal, parameter, universe, capital, exposure or production setting changed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Sources

- Kim, S., Kim, S. & Rajgopal, S. (2025), *Insider Trading After the 2022 Rule 10b5-1 Amendment*, working paper: https://accounting.wharton.upenn.edu/wp-content/uploads/2025/10/KimKimRajgopal.pdf
- Ma, Y. (2026), *The changing role of preplanned insider trades: Evidence from the SEC rule 10b5-1 amendments*, IREF 110(C): https://doi.org/10.1016/j.iref.2026.105650
- Ma (2026) abstract/bibliography: https://ideas.repec.org/a/eee/reveco/v110y2026ics105905602600763x.html
- Lee, Y.-J. (2023), *Insiders' Foreknowledge of Earnings Results and Rule 10b5-1 Sales Trades*: https://doi.org/10.1177/0148558X20964642
- SEC 2022 Rule 10b5-1 amendments: https://www.sec.gov/newsroom/press-releases/2022-222
- CarGurus 2024 Q1 filing index: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/0000950170-24-056957-index.htm
- CarGurus Item 408 rendered facts: https://www.sec.gov/Archives/edgar/data/1494259/000095017024056957/R10.htm
