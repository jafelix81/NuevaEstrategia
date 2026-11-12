# Phase 345 — SEC Form 4 multi-quarter identity replication

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — historical replication confirms a useful 2023+ identity path, but the 95% admission gate is not met  
**Research class:** source feasibility, event/security identity and point-in-time controls; no return or alpha test.

## Executive decision

Phase 345 reprocessed five immutable SEC quarterly Form 3/4/5 bulk archives and reused the already verified 2026Q3 Phase 343 raw audit. It reconciled **413 candidate transaction rows across six non-contiguous cohorts**, retrieving all **262/262 original Form 4 accessions** and reconciling the Form 4 issuer symbols to the bulk records in all 262 accessions.

The same-context \`TradingSymbol\` + \`Security12bTitle\` + \`SecurityExchangeName\` method works well in the 2023Q1–2026Q3 cohorts, but it is not sufficient as a universal historical method:

- 2023Q1, 2023Q2, 2025Q3 and 2026Q3: **273/301 rows (90.70%)** have event-time identity; **159/173 issuer-CIK × filing-date event units (91.91%)** are complete.
- Requiring the periodic identity anchor to predate the actual transaction, not merely the Form 4 filing, reduces coverage to **263/301 rows (87.38%)** and **152/173 event units (87.86%)**.
- 2006Q1 and 2012Q1: **0/112 rows and 0/51 event units** resolve through the current same-context target-fact method. In 2012, the parser retrieved prior periodic primary documents, but found no target facts in those documents/instance paths; this is a method/coverage limitation, not evidence that the issuers had no ticker or listed security.

The project's prior **95% exact-coverage admission gate is not met**. Do not start the insider return study yet. Do not use the 67.74% aggregate field emitted by the original Phase 345 JSON as a 2023+ coverage rate: its label says “XBRL era excluding 2006” but its denominator also includes the 2012Q1 cohort, which has zero target-fact identity. The corrected period-based aggregates above are used in this report.

## Reproducibility

- GitHub Actions run: [43290739469](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43290739469) — **SUCCESS**.
- Job: \`multiquarter-identity-audit\`, job ID \`131436006065\`.
- Offline regressions: **7/7 passed**.
- Artifact: [13978077938](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43290739469/artifacts/13978077938).
- Artifact ZIP: 205,917,652 bytes; SHA-256 \`7f8fe1191661be514cb2bc4c9551d07644516cfe9a4b9d52fa44dd59b950dcfd\`.
- Artifact contains 1,182 files, including the immutable Phase 342/343 inputs, source archives, SEC responses and row-level audit outputs.
- All six source archive SHA-256 checks passed. 2026Q3 raw Form 4 retrieval was reused from Phase 343; it was not fetched again.
- No active Phase 345 run remains. A later duplicate push was skipped by the one-shot workflow guard; the queued duplicate was cancelled.

## Cohort results

| Period | Candidate rows | Form 4 accessions | Event units | Unique exact XML transaction rows | Event-time identity rows | Event-time complete units | Transaction-date identity rows | Transaction-date complete units |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2006Q1 | 10 | 8 | 8 | 10 | 0 | 0 | 0 | 0 |
| 2012Q1 | 102 | 47 | 43 | 91 | 0 | 0 | 0 | 0 |
| 2023Q1 | 59 | 41 | 32 | 58 | 56 | 29 | 54 | 27 |
| 2023Q2 | 92 | 63 | 57 | 85 | 83 | 55 | 76 | 51 |
| 2025Q3 | 65 | 44 | 36 | 64 | 62 | 34 | 61 | 33 |
| 2026Q3 | 85 | 59 | 48 | 85 | 72 | 41 | 72 | 41 |
| **2023+ subtotal** | **301** | **207** | **173** | **292** | **273** | **159** | **263** | **152** |
| **All six cohorts** | **413** | **262** | **224** | **393** | **273** | **159** | **263** | **152** |

“Unique exact XML transaction rows” are the candidate rows that matched exactly one non-derivative Form 4 XML row at the SEC bulk source precision. The remaining 20 rows were not silently accepted: 11 in 2012Q1 had multiple identical XML matches; 1 in 2023Q1, 7 in 2023Q2 and 1 in 2025Q3 had no unique exact match. All unique exact rows passed the raw XML/footnote purchase-screen revalidation.

The 2023+ event-time and transaction-date aggregates are descriptive only. The six cohorts are non-contiguous and were selected by prior screening rules; they are not a probability sample and cannot estimate market-wide prevalence.

## Point-in-time and identity interpretation

1. **Event-time identity** requires a supported periodic filing strictly before the Form 4 filing date, no older than 365 calendar days, and an exact same-context symbol/title/exchange triple.
2. **Transaction-date identity** separately requires that the periodic filing also predate the transaction date. Same-day and post-transaction anchors are excluded. This is the appropriate stricter identity requirement before attaching a transaction to a historical price series.
3. The 2023+ transaction-date coverage loss is explainable: 10 rows have an event-time-valid anchor that is same-day or later than the transaction date (2 in 2023Q1, 7 in 2023Q2 and 1 in 2025Q3). These rows remain excluded from transaction-date identity.
4. The 2006Q1 sample has 8 event units: 5 with a selected prior periodic anchor, 4 fresh within 365 days, 1 stale, and 3 without a prior anchor. The seven selected primary documents produced no target facts in the current parser path.
5. The 2012Q1 sample has 43 event units: 38 with a selected prior periodic anchor, all 38 fresh within 365 days, and 5 without a prior anchor. The 95 candidate rows with a selected anchor point to primary documents classified \`PRIMARY_HTML_NO_TARGET_FACTS\`; no same-context target-fact triple was found.
6. Form 4 \`issuerTradingSymbol\` is an event-level issuer symbol, not a permanent security key. Form 4 \`securityTitle\` is not by itself proof of a ticker/share-class relationship. Do not promote either field into a historical security master without the missing class/listing bridge and corporate-action continuity.

## Effective-date control for Rule 10b5-1 checkbox

The SEC bulk checkbox regime was applied by each Form 4 filing date:

- Before the checkbox effective date, a missing \`AFF10B5ONE\` value remains **unknown**, not false, and is not used as a failing condition.
- On/after the effective date, the screen requires an explicit false value.
- All 242 post-effective candidate rows across 2023Q2, 2025Q3 and 2026Q3 required the gate; none had an unknown bulk value.
- 2023Q1 and earlier cohorts were correctly treated as pre-effective. The 52 unknown 2023Q1 bulk values were not converted to false.

## Decision and next gate

- Keep the SEC Form 4 XML as the primary event source, with exact accession, issuer CIK, reporting-owner, transaction, footnote and acceptance-time reconciliation.
- Do not admit the current XBRL context method as a universal security master; 2023+ coverage is below the 95% gate and pre-2023 cohorts are unresolved.
- Next test a **legacy same-row class/exchange bridge** in the 2006/2012 primary filing HTML: extract only rows with explicit “Title of each class” and “Name of each exchange” columns, match Form 4 \`securityTitle\` conservatively, and keep the Form 4 \`issuerTradingSymbol\` separate. A ticker must not be inferred from prose or an exchange name. If the issuer has multiple possible common-equity classes and no direct symbol-to-class link, quarantine the event.
- In parallel, retain CRSP as the preferred historical identity/return benchmark if access becomes available; Massive date snapshots are a lower-cost candidate but are not record-time historical versions; no vendor purchase is authorized.
- After identity, survivorship-aware universe membership and delisted price coverage pass, preregister the insider-event study using conservative next-full-session availability and multiple economically justified horizons.

## Frozen controls

- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- No return/alpha test, chronological OOS, bootstrap/LOO or holdout use.
- No production, universe, capital, parameter or stop change.
- No security master or new signal admitted.
- No vendor contacted, no data purchased and no paid entitlement assumed.
