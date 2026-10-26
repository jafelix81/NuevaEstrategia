# Phase 36 — FINRA ATS / Options Data Feasibility Gate

Date: 2026-10-26
Branch: phase36-finra-ats-feasibility
Commit context: 6ba00d1c97d7b1dd423232c549c50ba2020cb99b

## Purpose

Evaluate whether Smart Money candidates have enough historical depth, point-in-time publication timing, universe coverage, and reproducibility to justify an economic test against the frozen F80/LTM baseline.

## FINRA ATS / off-exchange

### Confirmed facts

- FINRA publishes weekly security-level ATS and non-ATS OTC information.
- Official FINRA documentation states weekly reports began April 25, 2016.
- Tier-1 NMS information is published with a two-week delay; other NMS/OTC securities use a four-week delay.
- The current FINRA API exposes `weeklySummary` on a rolling 12-month basis and `weeklySummaryHistoric` on a rolling four-year basis. Data older than one year in the historical dataset are static.
- Therefore the current API alone cannot reconstruct the full 2016-present panel required for the research window.
- Current FINRA catalog/support documentation also distinguishes API datasets from other FINRA data sources, so API availability must not be treated as proof of full historical-file availability.

### Decision

**PUBLIC-DATA CANDIDATE — ARCHIVE ACCESS GATE OPEN.**

Do not run alpha tests until the historical downloadable archive (or another reproducible official FINRA archive) is demonstrated to reconstruct the frozen 335-name universe with explicit publication/knowledge dates.

### Required next gate

1. Locate and programmatically sample the historical weekly archive from 2016 onward.
2. Build a symbol-by-week coverage matrix for the frozen 335 names.
3. Record report week, initial publication date, and any revisions separately.
4. Use publication date, not report week, as the PIT knowledge boundary.
5. Verify that the archive can be re-downloaded reproducibly without manual intervention.
6. Only then define abnormal ATS-share / off-exchange participation variables.

### Economic hypotheses (not assumptions)

H1: abnormal ATS share of consolidated/off-exchange activity predicts future returns after controlling for LTM/F80, liquidity, size, volatility, and recent return.

H2: changes in ATS participation contain incremental information beyond the level of ATS participation.

H3: ATS block activity is more informative than raw ATS volume.

H4: any apparent predictive effect disappears after controlling for contemporaneous return/volume, which would classify it as return-chasing rather than informed behavior.

No hypothesis is admitted to production without chronological OOS confirmation.

## FINRA block-trade / large-trade candidate

Fresh official FINRA API documentation identifies a separate public `blocksSummary` dataset. It aggregates ATS trade activity in NMS stocks that meets defined share/dollar thresholds and includes fields such as block quantity, block count, average block size, ATS share, and initial publication date. FINRA documents `monthStartDate` as its historical partition field.

This is potentially more economically targeted than raw ATS volume because it isolates unusually large transactions rather than total venue activity. However, it is still an aggregate proxy and does not identify the ultimate investor or whether a block is informed.

### Decision

**NEW PUBLIC-DATA CANDIDATE — HISTORICAL/PIT GATE OPEN.**

Before any alpha test, audit:

1. historical partition start/end dates for `blocksSummary`;
2. frozen-universe symbol coverage by month;
3. whether `initialPublishedDate` is available consistently enough to enforce PIT;
4. threshold-definition stability across the historical window;
5. whether the aggregate fields can be reconstructed reproducibly from the API without manual intervention;
6. whether the dataset materially overlaps the ATS weekly panel or adds independent information.

### Economic hypotheses (not assumptions)

B1: abnormal ATS block share predicts future returns after controlling for LTM/F80, size, liquidity, volatility, and recent return.

B2: block-share changes add information beyond overall ATS participation.

B3: unusually large ATS blocks are more informative than ordinary ATS flow.

B4: any effect disappears after controlling for contemporaneous return/volume, indicating return-chasing rather than informed activity.

The block hypothesis should be tested as an incremental residual signal, not as a standalone replacement for F80/LTM.

## Options

### Confirmed facts

Current Cboe DataShop documentation reports historical availability materially earlier than previously recorded in this audit:

- Open-Close Volume Summary EOD C1: **January 2005**.
- Open-Close Volume Summary interval C1: **January 2011**.
- Option Quotes: **January 2010**.
- Option EOD Summary: **January 2010**.
- Option Trades: **January 2010**.
- Option Sentiment: **January 2012**.

Cboe's current product catalog describes Open-Close Volume Summary as option volume summarized by capacity (Customer, Pro-Customer, Broker, Firm, MM), available EOD and in 10-minute intervals on Cboe exchanges. This is a more direct participant-capacity signal than raw option volume, but capacity is not equivalent to “smart money”; it remains a hypothesis that must be tested.

Cboe also documents Option Trades and Option Quotes historical products. Option Quotes provide interval NBBO/size, OHLC and trade volume, with optional open interest and implied-volatility/Greeks calculations; Option Trades provide transaction-level prints with contextual market information and optional IV/Delta.

### Decision

**HIGHEST INFORMATION-DENSITY CANDIDATE — COMMERCIAL ACCESS GATE OPEN.**

Do not substitute a materially different free options feed and call it the same experiment.

### Preferred eventual test

If access is obtained, start with Open-Close + OI + IV/skew rather than raw option volume alone. Candidate features:

- abnormal customer/professional opening volume;
- opening buy/sell imbalance;
- change in open interest relative to volume;
- IV change conditional on underlying return;
- skew change conditional on underlying return;
- option activity residualized against underlying volume, volatility, size, and LTM/F80.

The key test is incremental information, not whether options activity correlates with stocks that are already moving.

Important classification caveat: Cboe capacity buckets identify participant capacity, not investor identity or informational sophistication. “Customer” and “professional customer” must therefore be treated as hypotheses about potentially informed positioning, not as assumed smart money.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No Smart Money source is permitted to modify the baseline until it passes the same chronological OOS, identical-exposure, cost, bootstrap/LOO, and return-chasing controls.

## Current ranking

1. Options Open-Close / OI / IV / skew — highest information potential; commercial access required. Historical depth is better than previously recorded, with current Cboe documentation showing core products back to January 2010 and Open-Close C1 EOD back to January 2005.
2. FINRA ATS block activity — new public candidate; requires historical partition and PIT coverage audit before testing.
3. FINRA ATS/off-exchange — strongest broad public candidate; historical archive gate required.
4. SEC 13D/13G — retained as secondary candidate; latest audit resolves 20,103/20,266 filings but only 303/335 universe names and has 163 SEC archive retrieval failures, so it is not yet eligible for an apples-to-apples alpha test.

## Official references

- FINRA OTC Transparency API/documentation: https://developer.finra.org/docs
- FINRA OTC Transparency catalog: https://developer.finra.org/catalog
- FINRA OTC Transparency historical specification: https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf
- Cboe DataShop FAQ / historical availability: https://datashop.cboe.com/faqs
- Cboe Data Products: https://datashop.cboe.com/data-products
- Cboe Option EOD Summary: https://datashop.cboe.com/option-eod-summary
- Cboe Option Trades: https://datashop.cboe.com/option-trades
- Cboe Option Quotes: https://datashop.cboe.com/option-quote-intervals
