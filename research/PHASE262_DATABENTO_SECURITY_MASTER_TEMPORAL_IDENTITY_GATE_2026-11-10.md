# Phase 262 — Databento Security Master temporal-availability and identity gate

**Date:** 2026-11-10 UTC  
**Disposition:** conditional identity-reference candidate; **strict PIT not admitted**. No vendor account, API request, trial, contact, purchase, or raw data acquisition.

## Executive decision

Databento Security Master is potentially useful as an effective-dated identity/reference layer across listings, securities, and issuers. Its public documentation advertises history from 2005-01-01, 860,000+ listed and delisted securities, global coverage across 220+ exchanges, and listing-level records. That is attractive for crosswalking Form 144, Cboe, N-PORT, and the broader historical universe.

However, the documented timestamps do not by themselves prove when a customer could first retrieve a record:

- `ts_effective` = when the record details are effective.
- `ts_record` = when the record last changed.
- `ts_created` = when the record was added to Databento's database.

The official API example for AAPL shows a record with `ts_effective=2004-11-19`, `ts_record=2004-12-06`, but `ts_created=2024-11-11`. Therefore the historical effective/record dates cannot be treated as proof that the record was available to a customer in 2005. The strict rule is to require our own immutable first-observed receipt timestamp, raw-byte SHA-256, and an authorized license scope, in addition to vendor clocks not later than the decision time.

## 1. Historical coverage: promising, not yet measured against our universe

Documented product claims:

| Dimension | Public documentation | Research status |
|---|---|---|
| History | From 2005-01-01 to present | Announced, not independently sampled |
| Universe | 860,000+ listed and delisted securities | Global aggregate, not U.S. EQS count |
| Exchanges | 220+ worldwide | Global coverage |
| Granularity | Listing-level PIT records | Positive architecture |
| Delisted/relisted | Historical records retained; relisting tracked | Exact coverage/continuity still needs sample audit |
| Frozen 335 / 289 Form 144 CIK panel | No coverage percentage published | Not measured |
| U.S. common equity (`EQS`) by date | No per-date count in public docs | Not measured |

The security master can be filtered by country and security type. For our common-equity identity panel the initial filter should be `listing_country=US` and `security_type=EQS`; ETFs, ADRs, preferreds, warrants, units, and other security types must remain separate until their treatment is explicitly defined.

## 2. Three clocks — no-lookahead adjudication

The API supports `get_range(index="ts_effective")` and `get_range(index="ts_record")`. These are useful for effective-state and last-change histories, but neither is a first-customer-publication timestamp.

The documented AAPL example is decisive:

| Clock | Example |
|---|---|
| `ts_effective` | 2004-11-19 00:00 UTC |
| `ts_record` | 2004-12-06 15:09:30 UTC |
| `ts_created` | 2024-11-11 22:41:24.780487 UTC |

A 2005 backtest cannot use that row merely because it was effective in 2004 and last changed in 2004: the vendor says it was added to its database in 2024. Even for a 2025 decision, `ts_created` alone does not prove when an entitled customer could first retrieve the row.

**Strict PIT admission rule implemented in code:**

1. `ts_effective`, `ts_record`, and `ts_created` must parse as timezone-aware UTC and must not be later than the decision time.
2. Our own `first_observed_at` must exist and be no later than the decision time.
3. The first observation cannot precede the vendor's `ts_record` or `ts_created` timestamps for that captured version.
4. The original response bytes must have an immutable SHA-256.
5. The applicable license must explicitly authorize internal quantitative research in the intended environment.

Without our own first-observed capture, the record is not strict PIT eligible, even if all vendor clocks are historical. Prospective capture can establish a future knowledge clock; it cannot retroactively repair missing first-receipt history.

## 3. Identity hierarchy and known traps

Use the identifier that matches the entity level:

| Identifier | Correct level | Permitted use |
|---|---|---|
| `listing_id` | Individual exchange listing | Listing-level join |
| `security_id` | Security across listings | Security-level join |
| `issuer_id` | Issuer/company | Issuer-level grouping only |

Never substitute a ticker for a permanent identifier. The API documentation warns that a symbol may match multiple securities across a date range when a symbol is recycled.

Preferred external crosswalk fields are ISIN, U.S. CUSIP (`us_code`), and FIGI. The security-master guide documents a USNYSE suffix-normalization issue for class shares (e.g. a delimiter can be lost in the normalized symbol); do not fuzzy-normalize class suffixes. Join by a verified identifier instead.

The guide also says `listing_id`/`security_id` continuity does not extend across spin-offs or securities delisted and never relisted. Those must remain separate lineages; do not invent continuity. `issuer_id` is issuer-level and must not be mistaken for a fungible security identifier.

## 4. Documentation and licensing caveats

The dataset specification says the security master is updated once per week, while the product page says new data/upcoming events are appended four times daily. This cadence discrepancy is unresolved. Do not use either cadence as a deterministic publication clock until clarified and verified by captured responses.

The product page describes personal and commercial internal use, while prohibiting external redistribution. That is not enough to assume that our public GitHub Actions workflow, stored artifacts, or downstream derived outputs are within the exact entitlement we need. No account was opened, no API request was made, no trial or purchase was initiated, and no provider was contacted. License scope remains unverified.

## 5. Reproducible contract and tests

Added a fail-closed Python contract that:
- distinguishes effective, last-change, database-ingestion, and our own first-observed timestamps;
- rejects naive/non-UTC/future/missing timestamps;
- requires immutable raw SHA-256 and an authorized internal-research scope;
- enforces listing/security/issuer identifier levels without ticker fallback;
- keeps U.S. EQS separate from ETFs and non-U.S. listings.

The local unit suite passed **35/35** tests. The hosted workflow repeats the suite and validates the committed audit-result controls. This is a documentation/contract gate only; no Databento API request or data sample was made.

## 6. Decision and next gate

| Question | Decision |
|---|---|
| Identity-reference candidate | Retain conditionally |
| Strict PIT admitted | **No** |
| 335-name / 289-issuer coverage established | **No** |
| Delisted/relisted sample coverage verified | **No** |
| ADV20 price/volume source | **No** |
| Feature or alpha admission | **No** |
| Returns / bootstrap / LOO / OOS | Not run |
| Holdout | Not used |

Next, only if authorized access is separately approved, request a small stratified sample of U.S. `EQS` listings covering active, delisted, relisted, renamed, class-share, spin-off, and reused-symbol cases. Preserve the original response bytes, request parameters, response headers, receipt timestamp, record timestamps, and SHA-256. Compare coverage against the frozen universe and the Form 144 issuer sample. Clarify the update cadence and license scope before any automated GitHub processing.

This source may solve part of the identity problem shared by several research lines, but it is not a Smart Money signal and does not solve ADV20 market-data licensing.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, universe, capital, or model parameters changed.


## Official documentation references

1. Databento, [Security Master dataset specification](https://databento.com/docs/datasets/security-master) — history start, listed/delisted/global coverage, listing-level records, symbol suffix and continuity caveats.
2. Databento, [Security Master API reference](https://databento.com/docs/api-reference-data/security-master?lang=python) — `get_range` with `ts_effective` / `ts_record`, and the AAPL example showing historical effective/record dates with 2024 database creation.
3. Databento, [Security Master field schema](https://databento.com/docs/schemas/security-master) — definitions of `ts_effective`, `ts_record`, and `ts_created`.
4. Databento, [Security Master product page](https://databento.com/security-master) — product update cadence and internal-use / no-external-redistribution language. Its cadence statement conflicts with the dataset specification's weekly update frequency; the conflict is left unresolved.
