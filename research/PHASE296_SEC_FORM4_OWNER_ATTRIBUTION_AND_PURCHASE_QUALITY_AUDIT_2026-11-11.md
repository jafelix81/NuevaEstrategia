# Phase 296 — SEC Form 4 owner-attribution and purchase-quality feasibility audit

**Date:** 2026-11-11  


> **Correction notice (Phase 297, 2026-11-11):** the Phase 296 conservative Table I cohort omitted the transaction-level TRANS_FORM_TYPE=4 condition. Its 15,590-row count included 115 type-5 rows. Use the corrected **15,475-row** Table I cohort from [Phase 297](PHASE297_FORM4_TRANSACTION_FORM_TYPE_RECONCILIATION_2026-11-11.md) for subsequent research. Phase 296 remains the historical record of the original audit; its uncorrected count must not be used for modeling.

**Input:** six raw SEC Form 345 archive ZIPs in Phase 294 artifact [13884014630](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43083625013/artifacts/13884014630)  
**Method:** offline table joins and transaction/footnote diagnostics; no network requests, price returns or alpha test.

## Raw archive provenance

| Quarter | ZIP bytes | SHA-256 |
|---|---:|---|
| 2006Q1 | 17,306,804 | `62becdadbe5eaff68f03edefe2ba2357c8bb498a1f825b697003e087cf98e6ce` |
| 2012Q1 | 14,219,288 | `0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357` |
| 2023Q1 | 13,882,049 | `0b476188f52a0862e71886eb31a81f6345fc6616403b52188484aef0438cfcfb` |
| 2023Q2 | 10,742,628 | `7e636787231ae0f00accf5c3627298402dedd1aefffd7c50fb48292e5d3a8fbb` |
| 2025Q3 | 7,956,025 | `9c57f272b7230500771f661bc1fe181527ed6b76a6f45d23a910c7fc7e9fcfa4` |
| 2026Q3 | 8,660,776 | `a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3` |

These are six purposive quarters, not a continuous or representative census of all 83 published quarterly archives.

## Owner attribution

The six archives contain **317,267** Form 4/4-A accessions:

| Accessions | Count | Share |
|---|---:|---:|
| Exactly one reporting owner | 310,561 | 97.89% |
| Multiple reporting owners | 6,706 | 2.11% |
| No reporting owner | 0 | 0.00% |

The bulk `NONDERIV_TRANS` table is keyed by accession and transaction sequence, not reporting-owner CIK. Therefore multi-owner filings cannot be assigned to individual insiders from the bulk join alone. Keep them quarantined unless the original XML/footnotes provide a defensible attribution.

## Candidate purchase rows

A broad candidate row required all of:

- `NONDERIV_TRANS.TRANS_CODE = P`;
- `TRANS_ACQUIRED_DISP_CD = A`;
- `DIRECT_INDIRECT_OWNERSHIP = D`;
- positive `TRANS_SHARES` and positive `TRANS_PRICEPERSHARE`.

This yielded **27,902 rows** across **17,475 accessions** and **4,366 issuers**. Of these, **25,997 rows** were in single-owner accessions and **1,905** in multi-owner accessions. The issuer ticker as filed was present on 27,857/27,902 rows (99.84%); this does not establish effective-dated security-class identity.

A conservative data-quality subset further required original Form 4 (not Form 4/A), exactly one reporting owner, and a transaction date 0–2 calendar days before filing. It contains:

- **15,590 rows**;
- **11,088 accessions**;
- **3,243 issuers**;
- **6,728 unique reporting owners**;
- issuer ticker as filed present on all 15,590 rows.

This is a candidate event panel size, not a validated signal sample or an estimate of population coverage.

## Timing and plan-status quality

For the 27,902 broad candidate rows, transaction-to-filing calendar lag had median 2 days, p90 20 days, p95 94 days, p99 715 days and maximum 7,308 days. Seven rows had a transaction date after the filing date. This long tail is a material stale-event/correction risk; the 0–2-day subset is a conservative screen, not proof of actual public availability or market execution.

The SEC readme defines `TRANS_TIMELINESS` values as E = early, L = late and blank = on-time. In this purposive candidate sample there were 525 E, zero L and 27,377 blank rows. Do not substitute this flag for explicit transaction-date/filing-date checks.

In the 15,590-row conservative subset, submission-level `AFF10B5ONE` was:

| Status | Rows | Interpretation |
|---|---:|---|
| Explicit false (`0` or `false`) | 6,995 | Not flagged as a 10b5-1 transaction |
| Explicit true (`1` or `true`) | 201 | Affirmative 10b5-1 flag |
| Unknown / blank / field absent | 8,394 | Must remain unknown |

The field was absent in the 2006Q1 and 2012Q1 archive schemas in this sample. Blanks in later periods are also not false. The flag applies at submission level, not individually to every transaction row.

## Footnote diagnostics

The SEC data dictionary defines transaction code P as **“Open market or private purchase of non-derivative or derivative security.”** It is not an open-market-only label. A lexical screen of footnotes referenced by 28,663 P/acquired/direct rows found 11,762 rows with at least one footnote. Overlapping keyword hits included:

| Footnote text pattern | Rows hit |
|---|---:|
| Explicit open-market language | 671 |
| Private purchase/placement language | 147 |
| Public-offering language | 233 |
| Weighted-average price language | 3,339 |
| Trust/indirect/beneficial-ownership language | 1,697 |
| 10b5-1 language | 1,249 |
| Option/exercise language | 477 |
| Gift/donation language | 3 |

These are overlapping text-screen counts, not mutually exclusive classes or a definitive open-market classifier. Manual/structured adjudication is still needed for private placements, registered offerings, weighted-average executions, trusts, indirect ownership, 10b5-1 plans and amended filings.

## Decision and next gates

**Decision:** Form 4 is a credible public-data candidate for a broad insider-transaction hypothesis. It is not yet an admitted signal. The sample demonstrates enough single-owner candidate events to justify continuing feasibility work, but it does not demonstrate predictive value.

Before any return test:

1. Expand Phase 295's clock sample to deliberately include after-22:00 ET acceptances, next-business-day index sightings, Form 4/A amendments and PAC corrections.
2. Parse original XML and footnote references; quarantine multi-owner accessions and classify P transactions conservatively. Treat explicit 10b5-1 affirmative, unknown and negative as separate strata.
3. Build effective-dated issuer/security-class identity and measure historical price coverage for the full issuer universe; do not limit the search to the arbitrary 335-ticker universe.
4. Preregister the signal definition and event aggregation before returns. Use next-full-XNYS-session entry, identical costs/exposure to F80, chronological walk-forward, issuer/owner clustering, bootstrap/LOO and a new untouched holdout.

No return test, alpha, bootstrap/LOO, holdout use, production change, universe change, capital change or parameter change occurred. F80 remains frozen.
