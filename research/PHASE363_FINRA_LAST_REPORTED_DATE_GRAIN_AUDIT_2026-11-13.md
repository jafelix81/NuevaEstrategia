# Phase 363 — FINRA lastReportedDate row-grain diagnostic

**Date:** 2026-11-13 UTC  
**Branch:** `phase363-finra-last-reported-date-grain-audit`  
**Status:** `RETRIEVAL_PASS / DATA_GRAIN_FAIL_OR_REVIEW`

## Question

Phase 362 showed multiple LND aggregate rows for the same symbol/product, each with a different `lastReportedDate`. This phase tested whether `(issueSymbolIdentifier,lastReportedDate)`, with one aggregate product type, is a valid bridge between symbol aggregates and firm-grain rows.

## Retrieval and test result

- Complete 2025-01-06/T2 partition: **136,362 / 136,362 rows**, 28 pages.
- API `Record-Total` matched.
- Offline regression suite, including Phase 360/362/363 tests, passed.
- Retrieval gate: PASS.
- Overall data-grain gate: **FAIL_OR_REVIEW**.
- No returns, alpha, holdout, or F80 changes.

[GitHub Actions run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794) · [Metadata-only artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43432380794/artifacts/14041685255).

## Result by family

| Metric | ATS | OTC non-ATS |
|---|---:|---:|
| Aggregate rows / symbol-date groups | 7,907 | 8,770 |
| Firm rows | 105,367 | 14,130 |
| Shared symbol-date groups | 7,907 | 8,770 |
| Firm-only symbol-date groups | 11,948 | 175 |
| Exact share-and-trade matches | 1,338 / 7,907 (16.92%) | 8,608 / 8,770 (98.15%) |
| Mismatched groups | 6,569 | 162 |
| Duplicate aggregate symbol-date keys | 0 | 0 |
| Multiple product types within symbol-date | 0 | 0 |
| Duplicate participant keys within symbol-date | 0 | 0 |
| Missing `lastReportedDate` | 0 | 0 |

The date key removes duplicate aggregate keys in this partition, but it does **not** reconcile firm rows to aggregates universally. ATS has extensive mismatch and firm-only groups; OTC is much closer but still has 162 mismatches and 175 firm-only groups. A universal date-key bridge is rejected.

## LND result

LND's two OTC date groups reconcile exactly:
- 2025-01-08: 67,210 shares / 320 trades, one firm row, exact.
- 2025-01-10: 28,543 shares / 137 trades, one firm row, exact.

LND ATS is only partially reconciled:
- 2025-01-08: aggregate 5,226 shares / 144 trades versus firm sum 4,826 / 137 (short by 400 shares and 7 trades).
- 2025-01-10: aggregate 6,224 / 37 versus firm sum 6,224 / 37 (exact).

Thus the combined Phase 362 totals happened to match across all dates, but the date-level diagnostic reveals an ATS mismatch. This is why a matching combined total is insufficient to approve aggregation.

## Decision

**Kill `lastReportedDate` as a universal symbol-to-firm join key.** Retain it as a reporting/freshness field only; do not sum or deduplicate rows based on it. The exact source row grain remains unresolved for T2 ATS and partly unresolved for OTC.

This does not invalidate the clean T1 ATS samples from Phase 361, where all five sampled partitions passed the symbol bridge and participant-concentration readiness gate. It does mean T2 ATS must not be used for concentration features until a separate valid grain is established. T1 ATS remains only a conditional venue-level market-structure candidate, not a Smart Money or directional signal.

## Next gate

Do not spend more cycles trying to force a T2 join from `lastReportedDate`. Next, census the FINRA partition metadata across the full historic and current weekly datasets, including the separate OTCE tier, then sample a wider set of T1 ATS weeks. Check coverage, symbol continuity, publication/update dates and PIT before any economic test.

Official FINRA metadata describes `lastReportedDate` as the last time a firm sent an update contributing to the aggregate; it is not an exact first-receipt timestamp. `initialPublishedDate` and `lastUpdateDate` remain the conservative candidate availability fields. Documentation: https://developer.finra.org/docs (Weekly Summary metadata and Dataset Details).

No signal admitted. F80 remains frozen.
