# Phase 36 — FINRA ATS / Options Data Feasibility Gate

Date: 2026-10-26
Branch: phase36-finra-ats-feasibility
Commit context: 0d109eb6b1745e77cb247183baeb9bd8546a69a4

## Purpose

Evaluate whether Smart Money candidates have enough historical depth, point-in-time publication timing, universe coverage, and reproducibility to justify an economic test against the frozen F80/LTM baseline.

## FINRA ATS / off-exchange

### Confirmed facts

- FINRA publishes weekly security-level ATS and non-ATS OTC information.
- Official FINRA documentation states weekly reports began April 25, 2016.
- Tier-1 NMS information is published with a two-week delay; other NMS/OTC securities use a four-week delay.
- The current FINRA API exposes `weeklySummary` on a rolling 12-month basis and `weeklySummaryHistoric` on a rolling four-year basis. Data older than one year in the historical dataset are static.
- Therefore the current API alone cannot reconstruct the full 2016-present panel required for the research window.

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

## Options

### Confirmed facts

Cboe documents historical Option EOD Summary data from January 2012 to present, including option OHLC, trade volume, VWAP, open interest, NBBO snapshots, and optional point-in-time IV/Greeks.

Cboe also documents Option Trades and Option Quotes historical products from January 2012. Option Trades provides transaction-level prints; Option Quotes provides interval NBBO/size with optional open interest and IV/Greeks.

Cboe Open-Close Volume Summary is particularly relevant because it categorizes option activity by participant type (customer, professional customer, broker-dealer, market maker), action (buy/sell), and position (open/close). This is a stronger direct test of the Smart Money hypothesis than raw option volume.

### Decision

**HIGHEST INFORMATION-DENSITY CANDIDATE — COMMERCIAL ACCESS GATE OPEN.**

Do not substitute a materially different free options feed and call it the same experiment.

### Preferred eventual test

If access is obtained, start with EOD Open-Close + OI + IV/skew rather than raw option volume alone. Candidate features:

- abnormal customer/professional opening volume;
- opening buy/sell imbalance;
- change in open interest relative to volume;
- IV change conditional on underlying return;
- skew change conditional on underlying return;
- option activity residualized against underlying volume, volatility, size, and LTM/F80.

The key test is incremental information, not whether options activity correlates with stocks that are already moving.

## Frozen baseline

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No Smart Money source is permitted to modify the baseline until it passes the same chronological OOS, identical-exposure, cost, bootstrap/LOO, and return-chasing controls.

## Current ranking

1. Options Open-Close / OI / IV / skew — highest information potential; commercial access required.
2. FINRA ATS/off-exchange — strongest public candidate; historical archive gate required.
3. SEC 13D/13G — retained as secondary candidate; latest audit resolves 20,103/20,266 filings but only 303/335 universe names and has 163 SEC archive retrieval failures, so it is not yet eligible for an apples-to-apples alpha test.

## Official references

- FINRA OTC Transparency API/documentation: https://developer.finra.org/docs
- FINRA OTC Transparency historical specification: https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf
- Cboe Option EOD Summary: https://datashop.cboe.com/option-eod-summary
- Cboe Option Trades: https://datashop.cboe.com/option-trades
- Cboe Option Quotes: https://datashop.cboe.com/option-quote-intervals
- Cboe Open-Close Volume Summary: https://datashop.cboe.com/cboe-options-open-close-volume-summary
