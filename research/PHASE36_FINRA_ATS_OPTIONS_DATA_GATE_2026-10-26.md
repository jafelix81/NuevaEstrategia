# Phase 36 — FINRA ATS / Options Data Feasibility Gate

Date: 2026-10-26

## Purpose

Evaluate whether Smart Money candidates have enough historical depth, point-in-time publication timing, universe coverage, and reproducibility to justify an economic test against the frozen F80/LTM baseline.

## FINRA ATS / off-exchange

### Confirmed facts

- FINRA publishes weekly security-level ATS and non-ATS OTC information.
- Official FINRA documentation states weekly reports began April 25, 2016.
- Tier-1 NMS information is published with a two-week delay; other NMS/OTC securities use a four-week delay.
- The current FINRA API exposes `weeklySummary` on a rolling 12-month basis and `weeklySummaryHistoric` on a rolling four-year basis. Data older than one year in the historical dataset are static.
- Therefore the current API alone cannot reconstruct the full 2016-present weekly security-level panel required for the research window.

### Decision

**PUBLIC-DATA CANDIDATE — ARCHIVE ACCESS GATE OPEN.**

Do not run alpha tests until the historical weekly archive (or another reproducible official FINRA archive) is demonstrated to reconstruct the frozen 335-name universe with explicit publication/knowledge dates.

## FINRA `blocksSummary` — live schema audit

A live GitHub Actions audit was run against the production FINRA API on 2026-10-26. The endpoint returned HTTP 200 for metadata, partitions, and a sample query. Artifact: `phase36-finra-blocks-live-audit`, run `40340466922`, artifact `12658048654`.

### What the live audit established

- `blocksSummary` is a public FINRA OTCMARKET dataset.
- Historical partitions are available from **2016-06-01 through 2026-08-01**, 123 monthly partitions at the time of capture.
- The dataset has a PIT field `initialPublishedDate`; FINRA describes it as the first Monday or next business day of the following month.
- The dataset contains ATS-level aggregate fields such as `ATSBlockCount`, `ATSBlockQuantity`, `averageBlockSize`, ATS share percentages/ranks, `MPID`, `marketParticipantName`, and `summaryTypeCode`.
- Critically, the live metadata contains **no security/ticker identifier** (no `issueSymbolIdentifier` or equivalent). The sample rows are by ATS/MPID and month, not by stock.

### Decision — block hypothesis

**KILL AS A DIRECT STOCK-ALPHA SOURCE.**

The original B1-B3 hypotheses required symbol-level block activity to predict individual-stock returns. The live schema makes that impossible from `blocksSummary`: there is no ticker dimension to join to the frozen 335-name universe. Testing it as stock alpha would require inventing a mapping that does not exist in the source and would violate the research design.

Do not run a stock-level economic test on `blocksSummary`.

### What remains potentially useful

The dataset may still be useful as a **market/ATS-regime descriptor** (e.g., aggregate block intensity, ATS participant concentration, or market-wide block activity), but that is a different hypothesis and must be tested only as a broad market/regime variable with proper OOS controls. It is not a Smart Money stock-selection signal and is therefore not prioritized ahead of the security-level ATS panel or options data.

### Hypotheses killed

- B1: abnormal ATS block share predicts individual-stock future returns — **KILLED: no stock identifier**.
- B2: changes in stock-level block share add information — **KILLED: no stock identifier**.
- B3: unusually large stock-level ATS blocks are more informative — **KILLED: no stock identifier**.
- B4: return-chasing diagnosis for stock-level blocks — **NOT TESTED: prerequisite stock-level data do not exist in this dataset**.

This is a feasibility failure, not evidence that large ATS blocks are economically useless in aggregate.

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
2. FINRA ATS/off-exchange security-level panel — strongest broad public candidate, but historical 2016+ archive reconstruction remains the gate.
3. SEC 13D/13G — retained as secondary candidate; latest audit resolves 20,103/20,266 filings but only 303/335 universe names and has 163 SEC archive retrieval failures, so it is not yet eligible for an apples-to-apples alpha test.
4. FINRA `blocksSummary` — **killed for stock selection** after live schema audit; retained only as a possible future market-regime descriptor.

## Official references

- FINRA OTC Transparency API/documentation: https://developer.finra.org/docs
- FINRA OTC Transparency catalog: https://developer.finra.org/catalog
- FINRA OTC Transparency historical specification: https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf
- Cboe DataShop FAQ / historical availability: https://datashop.cboe.com/faqs
- Cboe Data Products: https://datashop.cboe.com/data-products
- Cboe Option EOD Summary: https://datashop.cboe.com/option-eod-summary
- Cboe Option Trades: https://datashop.cboe.com/option-trades
- Cboe Option Quotes: https://datashop.cboe.com/option-quote-intervals
