# Phase 34 — Historical Equity-Options Feasibility Audit

Date: 2026-10-25

## Objective

Evaluate whether historical US equity-options data can support a reproducible Smart Money hypothesis test against the frozen F80_TOP20_PARTIAL50_BASELINE_C20 / LTM control.

No alpha claim is made in this phase. This is a data-feasibility gate.

## Required properties

1. Historical coverage long enough for chronological training/OOS testing.
2. Ex-ante availability: signal timestamp must be based only on information available at the time.
3. Broad coverage of the F80 universe, not just a handful of liquid names.
4. Contract-level fields sufficient to reconstruct economically meaningful features.
5. Reproducible contract identity across expiration/strike/right and corporate actions.
6. Stable timestamps / quote dates and explicit handling of open-interest publication lag.
7. Ability to distinguish predictive information from simple return-chasing.

## Sources audited

### Cboe Option Trades

Cboe DataShop documents complete trade-by-trade OPRA coverage, including trade price, size, exchange and prevailing NBBO; historical availability is January 2012-present. The dataset is commercial. This is the strongest candidate for true options-flow research because trade direction can potentially be inferred relative to NBBO and aggregated without assuming that every large trade is informed.

Decision: **FEASIBLE DATASET, ACCESS-BLOCKED**. Do not fabricate a test without historical access.

### HistoricalData.net EOD chains

Public documentation states US stock/ETF/index option EOD chains from February 2002, one row per contract, with bid/ask, volume, open interest, IV, Greeks, quote time, underlying close and related fields. A free sample is exposed publicly, but full historical universe access is commercial.

Decision: **HIGH-PRIORITY EOD CANDIDATE**. EOD flow/OI/IV/skew research is feasible if full historical access can be obtained. It is less informative than trade-level Cboe data for order-flow classification, but substantially easier to use for a PIT daily factor panel.

### Massive options API

Public documentation advertises historical options prices/trades and broad US-market coverage, plus stock darkpool/OTC history. Pricing/access is commercial.

Decision: **SECONDARY CANDIDATE** pending credentialed historical-coverage test. Do not assume coverage quality until a F80 universe audit is run.

### Alpaca historical options

Historical availability begins February 2024. This is too short for the project's preferred chronological training/OOS design.

Decision: **REJECTED for primary research** due to insufficient history, although potentially useful for later live-paper validation.

### Cboe public historical volume / put-call archives

Cboe provides long historical aggregate equity-option volume and put/call ratios, but these are aggregate statistics rather than contract-level flow/OI/IV information.

Decision: **REJECTED as primary Smart Money source**. Too coarse to identify incremental institutional/informed behavior beyond broad sentiment.

### Czar28

Public site advertises 12+ years of US equity-option EOD, intraday and trade history with a free 1,000-request tier. Provenance, historical universe coverage and reproducibility have not yet been independently validated.

Decision: **UNVERIFIED**. Do not use until a coverage/schema/PIT audit is independently reproducible.

## Registered hypotheses for eventual testing

If a credentialed contract-level dataset passes the coverage gate, test these ex-ante families without threshold optimization on OOS data:

1. **Abnormal OI build:** change in open interest relative to underlying ADV and prior OI, separated by calls/puts and normalized by underlying market cap/volume.
2. **IV/skew shock:** change in near-ATM put-call IV skew relative to its own historical distribution, controlling for realized-volatility changes.
3. **Options-volume imbalance:** call-vs-put volume imbalance normalized by total option volume and underlying share volume.
4. **Flow + OI confirmation:** option-volume shock that is followed by OI confirmation, rather than treating volume alone as opening institutional activity.
5. **Cross-sectional residual:** each feature residualized against LTM/F80/MOM120 before IC and decile testing.

No hypothesis will be labeled "smart money" until it demonstrates incremental OOS predictive power.

## PIT rules

- Signal date cannot use future open interest.
- Open interest is treated as available only according to the vendor's documented publication convention; if that convention cannot be established, OI-based signals are rejected.
- Intraday trade signals use only trades/quotes timestamped before the strategy decision time.
- EOD signals use the complete session only if the execution rule is explicitly next-session; no same-close lookahead.
- Contract expiry, corporate actions and ticker changes must be resolved using information available at the signal date.

## Acceptance gate

Before any economic test:

- >= 90% median F80 ticker coverage across the intended sample;
- >= 80% coverage in the worst OOS date bucket;
- reproducible contract identity;
- documented PIT availability;
- no silent survivorship filtering;
- sufficient observations for chronological train/test splits.

If these fail, archive the source as infeasible and do not optimize around the gap.

## Current decision

**Phase 34 is a feasibility pass for commercial contract-level options data, not an alpha result.**

Priority order:

1. Cboe OPRA trade-level history — strongest microstructure/flow candidate if access is available.
2. HistoricalData.net EOD chains — strongest practical EOD OI/IV/skew candidate if full history is available.
3. Massive — secondary cross-check / alternative provider.
4. Czar28 — unverified until provenance and historical coverage are independently tested.
5. Alpaca — rejected for primary OOS research because history begins only in 2024.

The frozen baseline remains unchanged.

## Research discipline

No positive result will be pursued merely because an options feature looks intuitive. Every candidate must beat the frozen LTM/F80 control on the same dates and exposure, survive chronological OOS evaluation, bootstrap/LOO checks, and economic-cost validation. Failed hypotheses will be archived rather than tuned until positive.
