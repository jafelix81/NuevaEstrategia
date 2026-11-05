# Phase 94 — DOOD exact-formula correction and replication gate

**Date:** 2026-11-04 local research cycle  
**Branch:** phase94-dood-exact-replication-spec  
**Status:** formula specification corrected; deterministic unit tests added; data gate NOT passed; no return test or alpha claim.

## 1. Why this correction is necessary

The Phase 60 preregistration had inserted a contract multiplier into the primary DOOD equation. The original OptionMetrics paper does not show that multiplier. This is not an exact replication and must be corrected before any vendor sample is processed.

The paper states that, for each option symbol i, delta is multiplied by net volume (Total Ask Volume minus Total Bid Volume), summed across the full option chain, and scaled by the underlying stock's daily volume.

**Published formula:**

DOOD(s,t) = SUM_i [ Delta(i,t) * (TotalAskVolume(i,t) - TotalBidVolume(i,t)) ] / UnderlyingDailyShareVolume(s,t)

There is no contract multiplier in the published formula. The project will reproduce this expression first, using the vendor's original field units and signed-delta convention.

A separate sensitivity may calculate delta-equivalent shares using the historical multiplier/deliverable. It must be labelled multiplier-adjusted DOOD and must never be presented as the published metric.

Primary paper: https://optionmetrics.com/wp-content/uploads/2023/05/Demand-for-Option-Order-Delta-DOOD.pdf

## 2. Important sign and unit rules

- Preserve the signed option delta supplied by the validated IvyDB field. A put delta is negative; do not invert the put sign again.
- Buyer-initiated volume contributes positively for positive-delta calls and negatively for negative-delta puts.
- Seller-initiated volume contributes with the opposite sign through Ask minus Bid.
- Do not convert midpoint, unknown, complex, or unclassified volume into buyer or seller volume unless the vendor's documented methodology explicitly assigns it.
- Use the paper's underlying daily share-volume denominator for the exact replication. Prior-20-day ADV is a separately preregistered normalization sensitivity.
- Keep raw contract volume, delta, ask volume, bid volume, midpoint volume, unknown volume, and any multiplier/deliverable fields separately.
- Do not silently assume a 100-share multiplier for adjusted contracts.

The new deterministic helper in research/phase94_dood.py implements both the exact published formula and a separately named multiplier-adjusted sensitivity. Unit tests explicitly check signed put delta, seller-initiated flow, midpoint exclusion, denominator validation, and adjusted-contract treatment.

## 3. Published-result audit

The paper reports:
- Sample: January 2016 through March 2022.
- Rebalance horizon: five trading days.
- High-minus-low DOOD spread: 0.32% per week.
- Weekly three-factor alpha: 0.26%, described as significant at 5%.
- Volatility-targeted Sharpe: 1.15.

There is an internal Sharpe discrepancy in the paper: the abstract reports 1.08 for the long/short portfolio, while the detailed Table 2 discussion reports 1.03. The project must preserve this discrepancy rather than select whichever number looks better. For any reproduction table, report both claims and use the actual table's underlying calculation only after its source data/table is reconciled.

The paper's filters are also part of the replication target: exclude ETFs and indices; require optionability; retain the upper 90% of market capitalization at each formation date; price above $5; implied volatility below 300%; and at least 1,000 contracts of ask volume. The study uses equal-weighted weekly deciles.

This vendor-produced result is a prior hypothesis, not independent OOS evidence. Its sample ends in March 2022 and it does not establish net incremental value over frozen F80/LTM.

## 4. Product-history and methodology-version gate

The historical input used by the paper was IvyDB US plus IvyDB Signed Volume. The current OptionMetrics website describes IvyDB TradeFlow as an evolution of Signed Volume and claims every US option every day since January 2016, with 5-minute, 30-minute and EOD snapshots. It also describes added trade-description codes, exchange venue, VWAP-based classification, NBBO-relative aggressiveness and retail/institutional analytics.

However, the January 2020 Signed Volume launch announcement described its available history as beginning in March 2018. This differs from the current website's January 2016 statement and from the DOOD paper's January 2016 sample. It may reflect a later historical backfill, but that cannot be assumed.

Official/current sources:
- DOOD paper (2022): https://optionmetrics.com/wp-content/uploads/2023/05/Demand-for-Option-Order-Delta-DOOD.pdf
- Current IvyDB TradeFlow product page: https://optionmetrics.com/ivydb-tradeflow/
- Current Signed Volume page: https://optionmetrics.com/signed-volume/
- January 2020 launch announcement: https://www.tradersmagazine.com/departments/options/optionmetrics-launches-ivydb-order-flow-tracker/

Before acquisition, obtain written confirmation of:
1. Whether the exact legacy Signed Volume fields used in the 2022 paper are available continuously from January 2016, including the 2016–2018 period.
2. Whether TradeFlow is a replacement dataset, a restatement, or an additional layer; whether legacy ask/bid/midpoint values remain reproducible.
3. Whether TradeFlow's new VWAP, trade-condition, venue, NBBO-aggressiveness and retail/institutional fields are historically backfilled to 2016 or only available from later dates.
4. Methodology/version dates, historical restatements, corrections, busted trades and patch policy.
5. Exact timestamp, cutoff, file publication/delivery time, and whether archived historical files preserve original publication vintages.
6. Historical permanent security and contract IDs, expired contracts, adjusted deliverables, ticker changes, mergers and delisted underlyings.
7. Business-use licensing, internal storage/retention, derived-feature rights, and sample/quote pricing.

Do not treat a modern proprietary participant classifier applied retrospectively as a point-in-time historical label without version evidence.

## 5. Data-feasibility gates

No forward-return calculation is authorized until all gates pass:

- Sample dates spanning 2016, 2017, 2018, 2019, 2021, 2023, 2025 and 2026.
- Sample includes representative F80 names, high- and low-liquidity names, and historical delisted/predecessor securities.
- Full option chains, not selected contracts or top-volume truncations.
- Exact option-symbol-to-permanent-contract and underlying-security mapping.
- Historical optionability and active-universe status, effective-dated point in time.
- Delta field convention, timestamp and model documented.
- Ask/bid/midpoint/unknown volume definitions and correction rules documented.
- Independent underlying daily stock volume with consistent corporate-action treatment.
- File release/availability timestamps or conservative next-session knowledge date.
- At least 95% coverage of historically optionable eligible issuer-days in each tested period; report by year, issuer, liquidity and market-cap strata.
- Data license permits the intended research and storage.

The current 335 ticker list is not a historical universe. Phase 70's missing original membership rule remains a limitation; a current ticker list must not be represented as survivorship-free historical membership.

## 6. Point-in-time and execution policy

Until the vendor supplies reproducible historical release timestamps, use the next trading session as KnowledgeDate for end-of-day files. Execute no earlier than the close of that next session, consistent with the frozen strategy's end-of-day execution convention. Do not use signal-date close after observing an overnight EOD file.

Intraday 5-minute/30-minute snapshots are a separate data product and require their own exact cutoff, delivery and vintage audit. Snapshot timestamps alone do not prove the strategy could access the file at that time.

## 7. Preregistered replication and incremental tests

Stage A — exact vendor-method diagnostic:
- Reproduce the published DOOD formula without multiplier.
- Reproduce the paper's optionability, market-cap, price, IV and ask-volume filters.
- Reproduce the five-session equal-weighted decile diagnostic for January 2016–March 2022, with exact sample membership and transaction-cost limitations clearly stated.
- Reconcile the paper's reported 1.08 versus 1.03 Sharpe discrepancy.

Stage B — untouched later-period test:
- Lock all definitions before viewing 2023–2026 forward returns.
- Use chronological development/validation and a locked 2023–2026 OOS period, subject to data completeness.
- No random splits. Purge/embargo overlapping forward labels.

Stage C — F80 incremental value:
- Compare baseline and DOOD-augmented F80/LTM under identical universe, exposure, entry/exit timing, costs, turnover and missing-data rules.
- Control prior 1/5/20/60-session returns, same-day momentum, volatility, market/sector exposures, liquidity, earnings and option-chain composition.
- Report standalone cross-sectional rank IC and high-minus-low spreads only as diagnostics; the promotion decision depends on incremental portfolio value.
- Examine 1/2/5/10/20/40-session decay profiles only within nested chronological validation. There is no imposed maximum or minimum holding period.
- Use block bootstrap, issuer-clustered uncertainty, leave-one-issuer-out and regime sensitivity; correct for all tested variants/horizons.

Competing explanations remain separate:
- private-information / directional demand;
- dealer inventory and gamma-hedging feedback;
- return-chasing or contemporaneous momentum;
- volatility/skew or event-risk demand.

If prior returns explain the signal, if the effect reverses before next-session execution, or if net incremental OOS performance fails robustness, kill the hypothesis without retuning.

## 8. Current decision

- DOOD remains a high-priority research hypothesis.
- No OptionMetrics data has been purchased or downloaded.
- No vendor contact has been sent.
- No forward returns or alpha tests have been run.
- The exact formula correction and synthetic unit tests are methodological only.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
