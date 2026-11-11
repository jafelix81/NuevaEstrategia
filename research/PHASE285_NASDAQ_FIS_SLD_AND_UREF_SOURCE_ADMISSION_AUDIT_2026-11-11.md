# Phase 285 — Nasdaq FIS Astec securities lending and U.S. retail flow admission audit

**Audit date:** 2026-11-11 UTC  
**Branch:** phase231-cboe-option-quotes-full-row-reparse  
**Status:** METADATA_FEASIBILITY_ONLY — conditional candidates; no raw-data admission, PIT admission or alpha test.  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Executive decision

Two Nasdaq Data Link products merit distinct, narrowly defined research roles:

1. **FIS Astec Analytics Securities Lending Data (SLD):** highest-priority conditional candidate for borrow-market state, loan additions/returns, utilization and borrow-cost pressure. Advertised daily history begins in 2013 (with the rate-dispersion table beginning in 2012), covers 45,000+ active and inactive securities across equity and fixed-income markets, and is updated at 12:30 UTC on weekdays with the previous trading day's data. It is Premium.
2. **Nasdaq U.S. Retail Equities Flow (UREF / UREFINT):** a potential control/interaction dataset for vendor-classified retail buying and selling, not an institutional-flow source. The 15-minute product advertises history from January 2016, 10,000+ U.S. stocks, ADRs and ETPs, and delivery within 30 minutes after each interval. It is Premium.

These are not evidence of informed trading and do not identify named funds, beneficial owners or individual accounts. The metadata claims are useful enough to justify a sample-admission decision, but neither source currently passes our data gates. No paid sample, API call, vendor contact, trial, license acceptance or data download was initiated.

**Priority is conditional on lawful existing access or explicit authorization for a sample/license.** The published product pages do not show a price without login, and the applicable rights for automated storage, derived features, backtesting and commercial use have not been established.

## 1. FIS Astec SLD — source semantics and history

Official product page: https://data.nasdaq.com/databases/SLD

The product page describes security-level lending information sourced from major custodians, banks, lender participants and borrower clients, anonymized and aggregated by security. It advertises 45,000+ active and inactive fixed-income and equity securities in more than 110 countries. The 45,000+ figure is **not** an equity-only count and must not be used as an estimate of our universe coverage.

### Tables and advertised history

| Table | Measurement | Advertised history |
|---|---|---:|
| FIS/POS | Position, loan volume, transaction count, age and rates | 2013-07-01 |
| FIS/U1 | Utilization result | 2013-07-01 |
| FIS/U2 | Lendable availability and availability market value | 2014-01-01 |
| FIS/R1 | Loan-rate dispersion by rate bin | 2012-01-02 |

The product is updated at **12:30 UTC each weekday** with statistics for the previous trading day. FIS/POS Date is the trading date on which loans are measured, as of end of business. This scheduled delivery is not a captured first-receipt timestamp and does not establish historical immutable vintages.

### Important field semantics

- FIS/POS uses a proprietary AstecID (6- or 8-digit) plus date and contract/loan-stage/collateral dimensions as its key. ISIN, CUSIP and TradingSymbol are nullable. A historical AstecID-to-security crosswalk and its effective dates are therefore essential.
- LoanStageID A means outstanding loans, N means new loans, and R means recalled or returned loans. FIS says it cannot distinguish a recall from an actual return in R. Do not label R as executed returns without qualification.
- POS Units is the number of units lent in the transaction group. The data provider adjusts lender- and borrower-side reports to reduce double counting, but the reported universe remains limited to participant coverage.
- RetailLoanRateAvg is a weighted average rate for the “retail” securities-lending segment. FIS defines that segment as loans from prime brokers to their clients, for example hedge funds. It does **not** mean loans to retail investors and does not identify the hedge fund or borrower.
- FIS/U1 UtilizationPercent_Units is calculated from loan volume and availability reported by the same lending programs. The provider explicitly says its availability sources are a subset of position-data sources.
- **Do not reconstruct U1 as POS Units divided by U2 Available_Units.** The provider's own FAQ gives an example where POS loan total is 700 units, reported availability is 500, but utilization is 80% because some borrower-side volume is not matched to the same lender-program availability denominator. U1, POS and U2 are related but not interchangeable.
- FIS/R1 NewUnits is a subset of R1 Units. R1 excludes term trades (overnight contract type only), whereas POS can include term loans. Do not add R1 Units to POS or expect the two tables to reconcile.
- Loan rates are a cost/borrow-market measurement, not proof that the associated loan was sold short. Securities loans also support settlement, market making and other uses.

### PIT, identity and coverage blockers

| Gate | Current evidence | Disposition |
|---|---|---|
| Historical depth | Table-level history starts 2012–2014 | Promising metadata claim; raw continuity unverified |
| Delivery | 12:30 UTC weekday schedule, previous trading day | Scheduled lag only; no historical first-receipt log |
| Revisions/vintages | No immutable as-published history established | Not PIT-admitted |
| Security identity | Proprietary AstecID; ISIN/CUSIP/ticker can be null | Effective-dated crosswalk required |
| Universe coverage | 45,000+ mixed asset-class securities | Exact F80 overlap unknown |
| Delisted names | Product advertises active and inactive coverage | Actual retention and identifier continuity unverified |
| License/access | Premium; price not publicly visible | No access or derived-use rights established |
| Beneficial-owner identity | Data anonymized/aggregated by security | No named fund or manager inference |

## 2. UREF / UREFINT — retail-flow control, not “smart money”

Official pages:
- 15-minute product: https://data.nasdaq.com/databases/UREFINT
- Daily and 30-minute product: https://data.nasdaq.com/databases/UREF

### 15-minute UREFINT history and fields

The intraday product advertises history from January 2016 and 10,000+ U.S. stocks, ADRs and ETPs. Securities priced below USD 1 are excluded. Historical data are split into yearly tables UREF/FFIH16 through UREF/FFIH24; the ongoing table UREF/FFI starts 2025-01-02.

The documented 15-minute row key is date + minute + ticker. Fields include volume_buy, volume_sell, update_time and is_healthy.

- Delivery is advertised within 30 minutes after each interval, with intervals scheduled from 13:30 to 20:00 UTC during the trading day.
- update_time is the record-generation time in Eastern Time and is populated only from 2022-06-01. It is not documented as an immutable first-receipt timestamp.
- is_healthy is populated only from 2021-08-02. It describes whether overall retail dollar volume for the interval is within a normal range; all tickers in that interval should share the same value. It is not a ticker-specific completeness guarantee.
- Nasdaq documents a small number of incomplete dates before 2021. The affected-date/ticker list must be acquired and applied before any historical panel is admitted.
- Ticker symbology is described as point-in-time. The product does not provide a permanent security identifier in the documented row schema; an effective-dated ticker/security crosswalk is still required.
- The 13:30–20:00 UTC schedule, Eastern-time minute field, early closes and daylight-saving transitions must be reconciled against XNYS sessions before assigning executable availability.

### Do not conflate separate UREF products

The separate UREF daily product has UREF/DF daily data (updated by 10:00 UTC Tuesday–Saturday with the previous trading day's data, including pre/post-market) and UREF/IF 30-minute data during the continuous session. Those are not the same table or frequency as UREFINT's 15-minute UREF/FFI and FFIH16–FFIH24 tables. Keep them as separate source contracts.

### PIT, identity and coverage blockers

| Gate | Current evidence | Disposition |
|---|---|---|
| Historical depth | 2016 onward | Promising; raw continuity and affected dates unverified |
| Intraday delivery | Less than 30 minutes after each interval | Scheduled latency, not captured first receipt |
| Generation timestamp | update_time from 2022-06-01 | No row-level generation time before that date |
| Health metadata | is_healthy from 2021-08-02 | Interval-level quality flag only |
| Coverage | 10,000+ stocks, ADRs and ETPs; under-USD-1 excluded | Exact F80 overlap unknown; selection bias risk |
| Symbology | Point-in-time ticker claim | Permanent identity/corporate-action bridge needed |
| License/access | Premium | No access or derived-use rights established |
| Economic role | Vendor-classified retail buy/sell activity | Control/interaction only; not named institutional flow |

## 3. Research hypotheses — preregister before any return test

The following are hypotheses, not assumed directional effects:

### H1 — Borrow-demand and supply stress

Use FIS/POS new-loan units, outstanding-loan units and recalled/returned units as separate fields; use FIS/U1 utilization and FIS/R1 rate dispersion as distinct measurements. Test whether changes in borrow demand, utilization and borrowing cost forecast:
- downside continuation;
- asymmetric upside squeeze/reversal risk; or
- only contemporaneous/past-return chasing.

Do not assume the sign. Do not net LoanStage N and R until row grain, contract/collateral scope and recall-versus-return semantics are verified.

### H2 — Retail-flow control

Construct UREF retail net-flow and imbalance measures only after validating interval timestamps, healthy intervals, missing-date lists, and market-volume denominators. Use UREF to test whether any FIS signal remains incremental after controlling for retail flow, prior returns, volatility, liquidity and market/sector effects. UREF buy/sell volume is retail-classified volume, not total market volume; it cannot by itself produce a retail share-of-market-volume denominator.

### H3 — Borrow/retail divergence

Test whether FIS borrow-market changes and UREF retail-flow changes interact or diverge. Separate long-horizon underlying-stock outcomes from option outcomes. A divergence feature is admitted only if it adds out-of-sample information beyond frozen LTM/F80 and survives issuer/date clustering, leave-one-out and realistic costs.

### Falsification

Reject a hypothesis if it is dominated by a few hard-to-borrow names, fails after costs, has poor point-in-time coverage, merely follows prior returns, is unstable across market regimes, or fails independent chronological OOS. No parameter tuning against the consumed legacy holdout.

## 4. Admission plan

Before any sample is acquired:

1. Confirm that an existing entitlement or explicitly authorized sample/license permits automated retrieval, storage, derived features, backtesting and intended use. Do not accept terms, start a trial, contact a vendor or purchase data without explicit authorization.
2. Obtain a small stratified sample spanning early, middle and recent history, including active and inactive/delisted names and different liquidity/borrow-cost regimes.
3. Preserve original bytes, source URL/table, extraction time, response metadata, SHA-256, schema version and every later revision. Require actual first-receipt capture prospectively; do not substitute a vendor's nominal schedule for a receipt log.
4. Measure FIS table-by-table missingness, AstecID continuity, optional-identifier rates, F80 overlap, inactive-security coverage, participant coverage proxies and revisions. Reconcile POS/U1/U2/R1 without assuming common denominators.
5. Measure UREF affected-date/ticker missingness, ticker changes, sub-dollar exclusions, DST/early-close alignment, interval-generation time and actual receipt latency. Treat pre-2022-06-01 update_time and pre-2021-08-02 is_healthy as unavailable, not false or healthy.
6. Freeze a new prospective holdout before outcomes are examined. Use actual knowledge time and executable next-session prices; do not backdate historical rows from a schedule claim.
7. Only after every gate passes, compare FIS alone, UREF as control, and their interaction against frozen LTM/F80 with identical exposure and costs, chronological OOS, date/issuer-clustered block bootstrap, issuer leave-one-out and multiplicity controls.

## 5. Current decision

| Candidate | Research role | Priority | Admission |
|---|---|---:|---|
| FIS Astec SLD | Borrow demand, availability, utilization and cost/crowding | 1, conditional | Metadata only; not PIT or alpha |
| Nasdaq UREFINT | Retail flow control / divergence interaction | 2, conditional | Metadata only; not PIT or alpha |
| Nasdaq UREF daily / 30-minute | Lower-frequency retail-flow cross-check | 3, conditional | Separate product contract; not PIT or alpha |

**No raw market data were downloaded. No API key was used. No vendor was contacted. No paid product, trial or terms were accepted. No backtest, return test, bootstrap, LOO, holdout or alpha test was run.** F80, production, universe, capital and parameters are unchanged.

## 6. Official source references

1. Nasdaq Data Link, FIS Astec Analytics Securities Lending Data: https://data.nasdaq.com/databases/SLD
2. Nasdaq Data Link, Intraday US Retail Equities Flow (UREFINT): https://data.nasdaq.com/databases/UREFINT
3. Nasdaq Data Link, US Retail Equities Flow (UREF): https://data.nasdaq.com/databases/UREF
4. Nasdaq Data Link API metadata documentation: https://docs.data.nasdaq.com/

This phase is a metadata and source-semantics audit only. It does not admit either product into the research dataset.
