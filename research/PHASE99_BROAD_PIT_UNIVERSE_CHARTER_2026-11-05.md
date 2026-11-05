# Phase 99 — Broad point-in-time universe charter

**Date:** 2026-11-05  
**Status:** DESIGN / DATA-FEASIBILITY GATE ONLY  
**Scope:** define a research universe architecture broader than the current 335-name F80 list. No vendor contact, purchase, data acquisition, forward-return calculation, alpha test or F80 modification is authorized by this phase.

## Executive decision

**User clarification (2026-11-05):** the 335 tickers were selected manually and arbitrarily by the user; there was no remembered or documented selection methodology. Therefore there is no historical selection rule to recover. Do not spend further research effort trying to reverse-engineer a nonexistent rule, and do not imply the 335 represent a statistically designed sample.

The 335 tickers are a frozen **F80 comparability universe**, not the ceiling of Smart Money Research. All future source audits and candidate-signal research may cover a broader historical population. A new broad-universe strategy must have its own name, immutable universe specification, point-in-time security identities and independent validation. It must never silently rewrite F80's historical universe or retroactively assign today's constituents to earlier dates.

The research should maintain distinct universe tracks rather than select one universe after seeing returns:

1. **Broad US primary-listed operating-equity universe (primary research candidate):** build from point-in-time listing/security records for a fixed set of major US exchanges. Include eligible common-equity listings, including companies that later delisted, merged, failed, changed tickers or changed share class. Preserve ADRs, REITs, BDCs and other special equity forms as explicit classifications so they can be analyzed separately; do not silently pool unlike instruments.
2. **Russell 3000 historical-membership universe (index-defined comparator):** use dated effective membership and permanent security IDs. Membership becomes eligible only on its effective date; an announcement-date strategy is a separate hypothesis and needs archived announcement timestamps.
3. **Nasdaq Composite historical-membership universe (secondary comparator):** separate from Russell 3000; do not use current membership retrospectively.
4. **Frozen F80 335-name universe (legacy control):** retain only for exact comparability with existing LTM/F80 results. It is not a comprehensive representation of the US equity opportunity set.

These tracks answer different questions. The broad primary-listed universe tests whether a signal generalizes across investable US equities. Russell/Nasdaq test index-defined populations. F80 tests comparability with the existing strategy. No universe is selected because it produces the best backtest.

## 1. Universe taxonomy and security eligibility

### Primary candidate: broad US primary-listed operating equities

Construct the eligible set from historical listing-level records, not a hand-curated current ticker file. At minimum retain:
- common shares and multiple share classes as distinct securities;
- ADRs/ADSs with explicit depositary-receipt flags;
- REITs and BDCs with explicit flags and separate performance strata;
- IPOs from the first date at which the preregistered listing-age and data-completeness requirements are satisfied;
- active, inactive, delisted, bankrupt, acquired, merged, relisted and ticker-changed securities;
- permanent listing/security/issuer identifiers and full corporate-action lineage.

Exclude from the primary operating-equity set by a written security-type rule: ETFs/ETNs, mutual/closed-end funds, preferreds, warrants, rights, units, when-issued instruments, options, debt and OTC-only securities. If any excluded category is studied, it gets a separate universe and independent results. SPAC common shares require an explicit rule and a distinct flag; never silently mix SPAC lifecycle observations with operating-company common equity.

A company may have multiple eligible share classes/listings. Do not collapse them by ticker or issuer without a preregistered aggregation rule. Use the actual tradable listing for execution and preserve issuer-level clustering for inference.

### Eligibility filters

- Apply price, market-cap, dollar-volume, spread and listing-age thresholds using only data available before the signal/formation boundary.
- Choose thresholds for realistic investability and data reliability, not to maximize returns. Freeze them before any strategy-return inspection.
- Preserve raw observations and report how many securities are removed by each rule, by year and security type.
- Do not require a security to survive to the end of the sample.
- Do not require current index membership or current availability of a ticker.
- Keep missing-data exclusions visible; never treat missing history as a zero return.

## 2. Time and identity rules

Every security record must distinguish:
- `effective_time`: when a listing, symbol, classification or status applied in the market;
- `record_known_time`: when the data source first recorded or published that version;
- `retrieval_time`: when our pipeline acquired the record;
- `event_time`: when the underlying corporate or market event occurred;
- `public_available_time`: when the relevant information became available to a market participant.

For mutable reference data, a valid historical reconstruction must use the version known at the relevant decision time, not simply today's corrected record with an old effective date. Where true record-known vintages cannot be obtained, use a documented conservative availability rule and label the resulting test as weaker; do not call it strict two-clock PIT.

Ticker is a display attribute, not a primary key. Never join historical prices, events, options, filings or holdings on ticker alone. Use permanent listing/security IDs and source-specific crosswalks with explicit valid-from/valid-to intervals. Resolve symbol reuse, CUSIP changes, ADR ratios, share-class transitions, mergers and relistings.

Index membership is effective only from its effective date. Do not trade a future addition on its announcement date unless the announcement itself is separately timestamped, archived and preregistered as the signal.

## 3. Return and delisting treatment

- Use total-return-consistent prices and corporate actions.
- Include delisting returns, cash/stock merger consideration, bankruptcy outcomes and terminal distributions where applicable.
- Define execution price, signal cutoff, next executable session, suspensions, stale prices, halts and untradeable observations before testing.
- Do not drop terminal observations because a security lacks a later ordinary close.
- Avoid double counting issuer and listing returns when multiple classes or listings exist.
- Keep issuer-clustered inference even when listing-level positions are traded.

## 4. Data feasibility gates (before any return test)

### Gate A — historical population and listing coverage
For 2016-01-01 through the latest complete usable date, document:
- exchange coverage and gaps by year;
- active and inactive/delisted security counts;
- IPO, delisting, relisting, merger and symbol-change counts;
- historical security-type and exchange classifications;
- permanent ID continuity and multiple-listing handling;
- Russell 3000/Nasdaq membership continuity for comparator tracks.

### Gate B — point-in-time provenance
For each mutable field, establish source, effective timestamp, record-known/publication timestamp, update cadence, backfill/correction behavior and archived-vintage availability. Distinguish event/effective time from when a participant could know the record. A source that only exposes current corrected history cannot independently pass strict PIT.

### Gate C — return and corporate-action integrity
Verify splits, dividends, spin-offs, mergers, delistings and terminal returns against an independent source on a stratified positive-control sample. Include active and inactive securities, symbol reuse, dual classes, ADRs and hard failures.

### Gate D — coverage and reproducibility
Report coverage by year, exchange, issuer, security type, market-cap and lagged-liquidity decile. Require stable reproducible IDs, raw-file hashes, source versions, retrieval timestamps and deterministic transformations. Establish licensing, retention and GitHub Actions ingestion feasibility before acquisition.

### Gate E — preregistration
Only after A–D pass, freeze:
- exact universe definition and exclusions;
- listing/issuer mapping rules;
- liquidity/price/listing-age thresholds;
- signal availability and execution boundary;
- development, validation and untouched final-OOS dates;
- benchmark and exposure-matching rules;
- costs, borrow constraints, bootstrap/LOO and multiple-testing controls.

No forward-return or alpha test is authorized before Gate E is signed off in a separate preregistration.

## 5. Candidate-source roles (not vendor endorsements)

- **CRSP:** preferred return, corporate-action and inactive/delisted validation source if access is available; verify product vintage, share codes, delisting-return treatment and licensing.
- **Databento Security Master:** promising two-clock identity/reference layer via `ts_record` and `ts_effective`; resolve history-start discrepancy, US listing/class-share coverage and record-revision semantics.
- **Norgate:** promising Russell/Nasdaq daily constituent and delisted-security cross-check; effective membership is not announcement-time membership, and exclusions/OTC coverage must be measured.
- **AlgoSeek ASID:** lifecycle crosswalk candidate; do not treat effective ticker ranges as proof of record-known PIT vintages.

Use at least two independent sources for critical identity/terminal-return positive controls where practical. A security master alone does not supply a complete return history; a price history alone does not reconstruct the historical eligible population.

No vendor contact, trial activation requiring a commitment, purchase, new data entitlement or external sharing is authorized without explicit user approval.

## 6. Research comparisons and reporting

Every surviving signal should be reported across the broad primary universe, relevant index-defined comparators and the frozen F80 control when data permit. These are parallel tests, not one pooled universe. Report:
- coverage and missingness before returns;
- net and gross returns, risk, drawdowns and tail behavior;
- liquidity, turnover, capacity and realistic costs;
- results by year, regime, size/liquidity, exchange and security type;
- issuer-clustered block bootstrap and leave-one-issuer-out;
- results with and without ADRs, REITs, BDCs and other special categories;
- survivorship/delisting sensitivity and universe-construction sensitivity.

A signal that works only in F80 is not automatically generalizable. A signal that works in the broad universe may be a standalone challenger even if it has no incremental value when mechanically added to F80. Do not force a blend.

## 7. Immediate next steps

1. Stop attempts to reconstruct the original 335 selection rule; the user confirms it was arbitrary/manual and no formal rule existed.
2. Treat F80's historical results as conditional on this manually selected set. Preserve the 335 only to reproduce and compare the legacy F80 strategy; do not use it as the primary sample for claims about the US equity market.
3. Run a non-purchase feasibility design for CRSP, Databento and Norgate against the gates above. Do not infer a vendor's coverage from marketing headline counts.
4. Create a small, stratified, locally reproducible identity test plan covering IPOs, delistings, symbol reuse, share classes, ADRs, REITs, BDCs, mergers and relistings. Actual vendor sample acquisition/contact still requires user authorization.
5. Keep all current signal hypotheses gated from broad-universe returns until the population and security-identity gates pass.

**Phase 99 decision:** Smart Money Research is no longer restricted to the 335 F80 tickers. The 335 remains a frozen legacy comparison set. The broad-universe track is authorized for specification and public-documentation/data-feasibility work only; no vendor purchase or return test is authorized.
