# Phase 37 — FINRA Short Interest / Short-Sale Volume Feasibility Gate

Date: 2026-10-26

## Purpose

Evaluate whether FINRA short-interest and short-sale-volume data provide a reproducible, point-in-time, security-level Smart Money hypothesis that can be tested incrementally against the frozen F80/LTM baseline.

## New finding

FINRA distinguishes two related but different datasets:

- **Reg SHO Daily Short Sale Volume:** daily aggregated short-sale volume by security for short-sale trades reported to FINRA trade-reporting facilities. The current API production dataset is rolling 12 months, but FINRA separately documents historical daily/monthly short-sale-volume files.
- **Short Interest:** a twice-monthly snapshot of open short positions. FINRA explains that short interest is not equivalent to daily short-sale volume; the former measures open positions at reporting dates while the latter measures short-sale transactions on trade dates.

FINRA's historical rule materials state that the Daily Short Sale Volume File began in 2009 and includes date, symbol, short volume, total volume and market. FINRA's 2019 notice confirms that the Daily File covers off-exchange short-sale volume and that the Monthly Short Sale Transaction File began with August 2009 data.

FINRA's January 2023 release notes state that its Consolidated Short Interest dataset provides five years of history and, as of June 2022, includes short-interest data from all exchanges. Current documentation says consolidated short interest is available by 4:40 PM ET on the publication date.

## Repository audit before new testing

The repository already contains a dedicated **Phase 25A/25B/25C FINRA short-interest line**, including an 80-business-day walk-forward. Therefore Phase 37 must not simply rerun the same short-interest experiment under a new phase number.

The existing Phase 25C implementation is diagnostic and uses `KnowledgeDate = settlementDate + 7 US business days` as a conservative proxy. It selects the best short-interest feature from historical training correlations and then evaluates the selected feature on subsequent 80-business-day signal dates. This is useful prior evidence, but it does **not** establish the actual FINRA publication timestamp as the information boundary, and it does not test the economically distinct combination of daily short-sale flow followed by persistent short-interest change.

Consequently, Phase 37 is re-scoped as a **data/PIT correction plus flow+position incremental test**, not a duplicate of Phase 25C.

## Research interpretation

Short selling is **not assumed to be smart money**. The economic hypotheses are:

H1. Abnormally high short-sale volume relative to total volume predicts subsequent returns after controlling for recent return, volatility, liquidity and F80/LTM.

H2. Changes in reported short interest predict subsequent returns after controlling for recent return and baseline factors.

H3. The combination of **flow + position** is more informative than either alone: abnormal short-sale flow followed by persistent increases in short interest.

H4. Any apparent predictive power disappears after controlling for preceding/contemporaneous returns, indicating return-chasing or mechanical hedging rather than incremental information.

H5. The strongest candidate is not necessarily the highest short interest. A residualized change in short interest relative to recent returns, volatility, float/liquidity and prior short interest may be more informative.

H6. If short-flow and short-interest features each have weak marginal information but their interaction survives the same controls, the combined signal may represent persistent positioning rather than transaction churn.

## PIT requirements

Use only the publication/availability timestamp that was actually known at the time. For short interest, the designated settlement/reporting date is the economic observation date, but the **publication date/time** is the knowledge boundary. For daily short-sale volume, trade date is the economic observation date and actual publication availability must be used for PIT.

Do not backfill later corrections into earlier information sets. If historical archives contain revisions, preserve original-publication and correction dates separately.

The existing Phase 25C seven-business-day rule may remain as a **conservative sensitivity case**, but it must not be described as the actual publication timestamp.

## Coverage gate

Before any alpha test, audit:

1. historical availability of the security-level short-interest archive;
2. historical availability of daily/monthly short-sale-volume files;
3. frozen-335 ticker coverage by observation date;
4. identifier continuity across ticker changes;
5. publication-date reproducibility;
6. whether listed-stock short interest can be obtained consistently for the entire frozen universe, rather than only OTC names;
7. overlap between short-sale-flow and short-interest histories;
8. survivorship and delisting coverage;
9. correction/revision behavior in historical files;
10. whether the combined flow+position panel has enough common observations for chronological OOS testing.

A five-year window is potentially adequate for a complementary OOS experiment, but it is **not automatically equivalent to the full baseline research window**. The source must first demonstrate sufficient universe coverage and a usable chronological training/OOS split.

## Required corrected experiment if the gate passes

Do not select a feature using the full sample. Within each chronological training window, estimate only transformations available up to that date. Candidate variables should include:

- abnormal short-sale ratio (`short_volume / total_volume`) relative to each ticker's own history;
- short-flow change/acceleration;
- change in reported short interest;
- short-interest level normalized by history and, where available, float/liquidity;
- residualized short-interest change after prior-return/volatility/liquidity controls;
- interaction of abnormal short flow with subsequent persistent short-interest increase.

The primary economic comparison must be:

1. frozen F80/LTM exposure alone;
2. F80/LTM + one short feature at a time;
3. F80/LTM + flow+position interaction;
4. residualized versions controlling for return-chasing.

All candidates must use identical exposure, costs, chronological walk-forward/OOS, bootstrap confidence intervals, leave-one-out sensitivity and a pre-specified holdout period. No production change is permitted from in-sample or exploratory results.

## Priority decision

**PUBLIC CANDIDATE — GATE OPEN, BUT DUPLICATE TESTING PROHIBITED.**

Phase 25C already supplies a prior diagnostic short-interest experiment. The next useful work is a live historical coverage/PIT audit and, only if it passes, an independent flow+position experiment using actual publication availability. If the data cannot provide reproducible PIT timestamps or adequate frozen-universe coverage, kill the candidate and archive the reason.

## Current ranking after this gate

1. Options Open-Close / OI / IV / skew — highest information potential; commercial access required.
2. FINRA security-level ATS/off-exchange weekly panel — strongest broad public candidate; historical archive remains the gate.
3. **FINRA short interest + short-sale flow — public candidate; Phase 25 duplication avoided; corrected flow+position PIT test required.**
4. SEC 13D/13G — secondary; current audit has only 303/335 universe names.
5. FINRA `blocksSummary` — killed for stock selection because it has no security/ticker dimension; retain only as a possible market-regime descriptor.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No short-interest or short-flow feature is admitted to the strategy without passing the same chronological OOS, identical-exposure, cost, bootstrap/LOO and return-chasing controls.

## Official references

- FINRA Developer Center: https://developer.finra.org/docs
- FINRA dataset catalog: https://developer.finra.org/catalog
- FINRA Reg SHO Daily Short Sale Volume: https://developer.finra.org/docs/api-explorer/query_api-equity-reg-sho-daily-short-sale-volume
- FINRA Short Interest explanation: https://syndication.finra.org/content/short-interest-what-it-what-it-not
- FINRA January 2023 release notes: https://developer.finra.org/release-notes/january-2023-release-notes
- FINRA 2019 short-sale-volume notice: https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf
- FINRA 2009 short-sale-volume rule filing: https://www.finra.org/sites/default/files/RuleFiling/p120246.pdf
