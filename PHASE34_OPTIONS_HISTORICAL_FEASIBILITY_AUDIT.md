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

Public documentation states US stock/ETF/index option EOD chains from February 2002, one row per contract, with bid/ask, volume, open interest, IV, Greeks, quote time, underlying close and related fields. Its documentation explicitly states that `open_interest` reflects the **prior business day's close**, which is unusually useful for a clean PIT implementation. The public sample is independently reconciled and includes a fixed schema, but full historical universe access is commercial.

Decision: **HIGH-PRIORITY EOD CANDIDATE**. The documented T-1 OI convention materially reduces lookahead ambiguity. It is less informative than trade-level Cboe data for order-flow classification, but substantially easier to use for a PIT daily factor panel.

### HistoricalOptionData / DeltaNeutral

Current public documentation advertises 24+ years of US equity/ETF/index options history beginning in 2002, with **5,900+ optionable underlyings on a typical day and 14,110 symbols across the historical archive**, including delisted/retired securities. It explicitly states that obsolete symbols are retained, making it materially stronger on survivorship-bias control than a current-symbol-only feed. Level 2/3 datasets include volume, open interest, IV/Greeks, and Level 3 adds T-1 open interest plus IV-surface fields. Public documentation also states that the data are delivered in reproducible CSV/Parquet formats.

The provider exposes a small free historical sample, but it is intentionally a micro-subset (one symbol per month), so it is insufficient for the F80 coverage gate. Full-universe access is commercial.

Decision: **NEW HIGHEST-PRIORITY EOD CANDIDATE, ACCESS-BLOCKED**. Its historical breadth and explicit retention of delisted symbols make it a particularly strong candidate for a survivorship-aware cross-sectional options panel. The exact PIT semantics of each field still require verification against the purchased schema before any alpha test.

### Massive options API / flat files

Public documentation advertises historical options prices/trades with tick-level OPRA timestamps and history back to June 2, 2014, plus broad U.S. market coverage. Pricing/access is commercial.

Decision: **SECONDARY CANDIDATE** pending credentialed historical-coverage test. Do not assume F80 coverage quality until an actual universe audit is run.

### Alpaca historical options

Historical availability begins February 2024. This is too short for the project's preferred chronological training/OOS design.

Decision: **REJECTED for primary research** due to insufficient history, although potentially useful for later live-paper validation.

### Cboe public historical volume / put-call archives

Cboe provides long historical aggregate equity-option volume and put/call ratios, but these are aggregate statistics rather than contract-level flow/OI/IV information.

Decision: **REJECTED as primary Smart Money source**. Too coarse to identify incremental institutional/informed behavior beyond broad sentiment.

### Czar28

Public site advertises 12+ years of US equity-option EOD, intraday and trade history with a free 1,000-request tier. Public documentation now exposes EOD, intraday and trade endpoints, but historical provenance, complete F80 universe coverage and reproducibility have not yet been independently validated.

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
- For any vendor whose OI is explicitly T-1, the OI feature must be aligned to the prior business-day observation and never to a same-day value that could contain post-close information.

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

**Phase 34 remains a feasibility pass, not an alpha result.**

After the latest provider audit, the practical priority order is:

1. **HistoricalOptionData / DeltaNeutral Level 2/3** — best current EOD candidate because of 2002+ history, explicit retention of delisted/retired symbols, broad historical symbol coverage, and T-1 OI / IV-surface fields. Access is blocked pending full-universe data.
2. **HistoricalData.net EOD** — excellent alternative because its public schema explicitly documents prior-business-day OI and provides a large independently verified sample. Access is blocked pending full-universe data.
3. **Cboe OPRA trade-level history** — strongest candidate for true options-flow/microstructure inference, but commercial access is required.
4. **Massive** — strong secondary trade-level candidate, pending credentialed F80 coverage/PIT audit.
5. **Czar28** — unverified until provenance and historical coverage are independently tested.
6. **Alpaca** — rejected for primary OOS research because history begins only in 2024.

The frozen baseline remains unchanged.

## Research discipline

No positive result will be pursued merely because an options feature looks intuitive. Every candidate must beat the frozen LTM/F80 control on the same dates and exposure, survive chronological OOS evaluation, bootstrap/LOO checks, and economic-cost validation. Failed hypotheses will be archived rather than tuned until positive.

## 2026-10-25 provider-audit addendum

The latest external documentation review materially strengthens the EOD-options path. HistoricalOptionData now documents a survivorship-aware historical universe of 14,110 symbols, including 7,996 delisted/retired symbols, and Level 3 fields that include T-1 open interest and IV-surface metrics. HistoricalData.net independently documents 34 daily contract fields and states that its open-interest field reflects the prior business day's close. These are stronger PIT/data-quality properties than the earlier generic feasibility assessment implied.

This does **not** constitute an alpha result. The remaining blocker is credentialed access to a full-universe historical archive so the F80 coverage gate can be measured directly. The free samples from both providers are intentionally too small to substitute for that test.
