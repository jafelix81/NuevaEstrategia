# Phase 353 — Cboe daily Open-Close flow + OPRA option-context feasibility

**Date:** 2026-11-13 UTC  
**Status:** PASS_SAMPLE_SCHEMA_AND_SPEC_SEMANTICS_NO_PIT_NO_ALPHA  
**Run:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474/artifacts/14014015757  
**Draft PR:** https://github.com/jafelix81/NuevaEstrategia/pull/40

## Research question

Can a daily participant-capacity/open-close feature be paired with broad OPRA option context for a swing strategy, without relying on cumulative intraday snapshots and their historical correction-vintage problem?

## 1. Source roles and official semantics

### Cboe Open-Close EOD v1.3

- Daily option-series rows by exchange with Firm, Broker-Dealer, Market Maker, Customer and Professional Customer capacity buckets.
- Customer and Professional Customer are split by contract-size bucket; each has buy/sell and open/close fields.
- The subscription specification describes one preliminary and one final file per day, typically delivered 00:30–01:00 U.S. Eastern the next morning.
- The preliminary file takes total-industry volume and open interest from OPRA; the final file takes authoritative values from OCC. Any future archive must preserve both versions, and only the final version should be used for OCC-sourced OI/industry volume.
- Product-page history starts at 2005-01-03 for C1 EOD and 2018-01-02 for BZX/C2/EDGX EOD.
- The product page says C1 includes RTH and GTH. Option EOD Summary is specified as RTH-only; session alignment remains unresolved.

### Option EOD Summary v1.1

- OPRA-listed U.S. stock, ETF and index options; product-page history starts January 2012.
- 15:45 ET NBBO snapshot and optional 15:45 IV/Greeks; EOD quote, volume, VWAP and start-of-day OCC open interest.
- Open interest is SOD, not EOD.
- IV may be zero when model inputs are insufficient, the option is below intrinsic value, or the model's acceptable IV range is exceeded. Zero IV is not a valid zero-volatility observation.
- On early-close days, the field named 1545 represents 12:45 ET.
- The Option EOD schema has no S/N/F series-type field matching Open-Close EOD. Do not blindly join nonstandard/Flex series using only root, expiry, strike and put/call.

## 2. Public sample audit

The final hosted run passed **11/11 offline regression tests**, downloaded both official PDFs and product pages, parsed the public sample archives, and passed all documentation and no-alpha gates. Only hashes and aggregate metadata were uploaded; no raw rows or symbol-level data were retained in the artifact.

### Open-Close EOD sample

- The public bundle includes EOD, 10-minute and 1-minute examples. The audit correctly selected only the EOD subdirectory.
- EOD sample: 2025-03-28, C1, 20% sample; **23,179 option-series rows**, **1,553 underlying symbols**, 86 columns.
- 0 duplicate series keys, 0 row-width errors, no missing identity/required cells, and all 34 participant-volume fields present.
- Every sample row had a nonzero value in at least one participant-volume field.
- Series type: S 23,080; N 11; F 88. The nonstandard/Flex share is small in this sample but must not be assumed away.

This is one date and a 20% C1 sample, not representative full-market history or PIT coverage.

### Option EOD Summary sample

- Market date: 2023-08-25.
- Two sample variants (no-CGI subscription and CGI/historical); each has **32,672 series rows across 4 underlyings**, 34 columns, 0 duplicate series keys, 0 row-width errors and no missing required cells.
- All seven optional calc columns were present in both variants.
- IV was zero on 2,368 rows (7.25%) in one variant and 2,854 (8.74%) in the other. Delta was zero on 396 (1.21%) and 325 (0.99%) rows. These are not independent dates; the variants must not be pooled as separate observations.
- SOD OI was zero on 7,449 rows (22.80%); trade volume was zero on 19,489 (59.65%). Zero OI/volume may be legitimate for a series with no open positions or no trades; do not automatically convert them to missing.

The sample has only four underlyings and cannot establish broad-universe coverage.

### Linked 1-minute sample

- The product page's new-sample link returned a 2026-09-30 file with **123,022 rows and 88 lowercase columns**.
- The new fields trading_dt and trading_segment are present, so the sample does show the new header schema.
- Its market date predates the 2026-11-08 v1.8 effective date. It does not validate the post-cutover live correction/removal behavior. The product page's "effective November 8" label and the pre-cutover filename are a sample-date inconsistency, not evidence that the live feed failed to change.

## 3. Point-in-time and identity ruling

The next-morning 00:30–01:00 ET schedule is a useful documented delivery convention, but the word "typically" is not a per-file first-receipt SLA. Historical backfills do not prove what version was actually available at the time. Historical PIT remains closed.

A prospective archive, if later authorized, must preserve preliminary and final files separately, record first-receipt UTC, exchange, market date, file name/version and SHA-256, and retain any later replacement as a new immutable object. The execution boundary must be after the final file's observed receipt.

The daily paired full four-venue history cannot begin before 2018-01-02; C1-only Open-Close EOD starts in 2005, while Option EOD context starts in 2012. The C1 RTH/GTH mismatch and S/N/F contract-class crosswalk must be resolved before constructing normalized joined features.

## 4. Candidate feature families — no returns test authorized

If the remaining data gates pass, keep hypotheses separate:
- Firm and Broker-Dealer opening net buy/sell volume;
- Market-Maker buy/sell activity;
- Customer and Professional-Customer opening flow by size bucket;
- closing activity as a separate unwind/cover hypothesis;
- puts and calls separately;
- normalized flow only after the denominator is proven time- and session-aligned;
- 15:45 IV/Greeks and SOD OI as companion context, not as proof of informed flow.

Control for prior underlying returns/momentum, volatility, liquidity, earnings, market/sector beta, optionability and dealer-hedging alternatives. Any later comparison must use identical exposure and costs versus frozen LTM/F80, chronological validation, a new untouched holdout, clustered bootstrap, LOO and multiplicity controls.

## 5. Decision and controls

**Decision:** prioritize the daily EOD pair for the next feasibility gate over the 1-minute cumulative-snapshot route. The source has a workable sample schema and a documented next-morning process; it is not yet admitted as historical PIT or alpha.

- Historical coverage and inactive/delisted option-root continuity: not established.
- Historical first-receipt/vintage PIT: not established.
- Prospective capture: not activated.
- Licensing: not confirmed. Cboe raw data is internal-use only; external distribution of derived data requires additional approval/licensing.
- No vendor contact, trial, purchase, license acceptance or data subscription.
- No return/alpha/OOS/bootstrap/LOO test; no holdout used.
- No production, universe, capital or parameter changes.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
