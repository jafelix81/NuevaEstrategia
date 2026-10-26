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

## Research interpretation

Short selling is **not assumed to be smart money**. The economic hypotheses are:

H1. Abnormally high short-sale volume relative to total volume predicts subsequent returns after controlling for recent return, volatility, liquidity and F80/LTM.

H2. Changes in reported short interest predict subsequent returns after controlling for recent return and baseline factors.

H3. The combination of **flow + position** is more informative than either alone: e.g. abnormal short-sale flow followed by persistent increases in short interest.

H4. Any apparent predictive power disappears after controlling for preceding/contemporaneous returns, indicating return-chasing or mechanical hedging rather than incremental information.

H5. The strongest candidate is not necessarily the highest short interest. A residualized change in short interest relative to recent returns, volatility, float/liquidity and prior short interest may be more informative.

## PIT requirements

Use only the publication/availability timestamp that was actually known at the time. For short interest, the designated settlement/reporting date is the economic observation date, but the **publication date/time** is the knowledge boundary. For daily short-sale volume, trade date is the economic observation date and actual publication availability must be used for PIT.

Do not backfill later corrections into earlier information sets. If historical archives contain revisions, preserve original-publication and correction dates separately.

## Coverage gate

Before any alpha test, audit:

1. historical availability of the security-level short-interest archive;
2. historical availability of daily/monthly short-sale-volume files;
3. frozen-335 ticker coverage by observation date;
4. identifier continuity across ticker changes;
5. publication-date reproducibility;
6. whether listed-stock short interest can be obtained consistently for the entire frozen universe, rather than only OTC names;
7. overlap between short-sale-flow and short-interest histories;
8. survivorship and delisting coverage.

A five-year window is potentially adequate for a complementary OOS experiment, but it is **not automatically equivalent to the full baseline research window**. The source must first demonstrate sufficient universe coverage and a usable chronological training/OOS split.

## Priority decision

**NEW PUBLIC CANDIDATE — FEASIBILITY GATE OPEN.**

Do not run a return test yet. The next step is a live GitHub Actions audit of historical security-level coverage for the frozen 335 names, followed by a PIT timestamp audit. If coverage is adequate, test short-flow, short-interest and combined residual features against the frozen F80/LTM baseline with identical exposure, costs, chronological OOS, bootstrap/LOO and return-chasing controls.

This candidate is independent enough from ATS block aggregation to justify investigation, while remaining entirely separate from the commercial Cboe options path.

## Current ranking after this gate

1. Options Open-Close / OI / IV / skew — highest information potential; commercial access required.
2. FINRA security-level ATS/off-exchange weekly panel — strongest broad public candidate; historical archive remains the gate.
3. **FINRA short interest + short-sale flow — new public candidate; historical security-level coverage audit required.**
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
