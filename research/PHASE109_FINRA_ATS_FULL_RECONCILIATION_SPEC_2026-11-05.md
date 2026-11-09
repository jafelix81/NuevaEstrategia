# Phase 109 — FINRA ATS full-field aggregation and cohort reconciliation

**Date:** 2026-11-05  
**Status:** preregistered data-feasibility audit; no return test authorized.

## Objective

Extend the Phase 108 targeted probe to all ten Phase 100 week/tier partitions. Determine whether symbol-level ATS and OTC aggregates can be reconciled deterministically to symbol-by-firm rows without double counting, using the expanded fields and lastReportedDate.

This is a source-integrity test, not an alpha hypothesis. No prices, forward returns, LTM/F80 features, or portfolio outputs are used.

## Frozen sample

Five weeks × two NMS tiers:

- 2022-01-03: T1, T2
- 2023-01-09: T1, T2
- 2024-01-08: T1, T2
- 2025-01-06: T1, T2
- 2025-10-20: T1, T2

The weeks and tiers are inherited from Phase 100; no date or partition is selected after seeing a return result.

## Fields

The query requests the Phase 108 expanded field set: symbol/name, firm CRD, MPID, participant name, tier, summary start date, weekly trade/share quantities, product and summary types, week start, first publication, last update, and last-reported date.

The workflow records each response page hash, request ID, offset, body row count, Record-Total, and retry count. Every partition must reconcile exactly to Record-Total.

## Falsifiable aggregation diagnostic

FINRA's definitive natural-key and revision semantics are not assumed.

For each symbol and family (ATS or OTC):

1. Group symbol-only rows (ATS_W_SMBL / OTC_W_SMBL) by lastReportedDate, summing across product types for that date.
2. Group symbol-firm rows (ATS_W_SMBL_FIRM / OTC_W_SMBL_FIRM) by lastReportedDate.
3. Sort the symbol-only aggregate dates. For each aggregate date, compare its quantity and trade count with the symbol-firm rows whose report dates are after the previous aggregate date and on/before the current aggregate date. The first aggregate date absorbs all firm report dates up to and including that date.
4. Compare total symbol-only and symbol-firm quantities/trade counts across the full week as a second independent check.
5. Preserve unmatched firm rows after the final aggregate date, missing dates, missing symbols, invalid values, negative values, and duplicate candidate keys as explicit failures; do not silently discard or assign them.

This interval rule is a hypothesis suggested by the LND Phase 108 example. It is not treated as a FINRA specification unless the full ten-partition evidence is consistent. Exact-date and total-week comparisons are retained as diagnostics through the per-date and total fields.

## Required outputs

- summary.json: source, timestamp, ten partition outcomes, field set, no-alpha declaration, and raw data hash.
- raw_rows.csv.gz: complete returned rows with requested week/tier, for reproducibility.
- page_hashes.csv: page-level provenance and content hashes.
- partition_summary.csv: compact integrity metrics by week/tier.
- cohort_reconciliation.csv: every aggregate-date cohort comparison.
- symbol_reconciliation.csv: per-symbol/family totals and full-reconciliation status.
- reconciliation_mismatches.json: all symbol/family keys that do not fully reconcile.

## Pass / fail gates

A source-level aggregation pass requires:

- all ten partitions complete;
- exact Record-Total reconciliation on every partition;
- zero week/tier mismatches;
- no unclassified summary types or unexplained missing-symbol records;
- zero duplicate symbol/firm candidate keys, or an explicitly resolved documented key;
- non-negative, valid quantities and trade counts;
- complete first-publication, last-update and last-reported dates for symbol aggregates;
- symbol-only vs symbol-firm reconciliation at the per-cohort and total-week levels, with every unmatched symbol/family explained.

A pass would establish a reproducible aggregation convention only for the sampled weeks and current endpoint values. It would not establish a complete historical revision ledger, original first-publication vintages, permanent security identity, broad universe coverage, inactive/delisted return coverage, or informed trading.

## PIT and interpretation constraints

- lastReportedDate is not assumed to be the trade date.
- lastUpdateDate later than initialPublishedDate remains a revision/vintage issue. The latest returned value must not be backfilled to the first publication date.
- Symbol-only and symbol-firm rows are alternative aggregation levels; they must never be added together.
- ATS/OTC volume does not reveal aggressor direction, beneficial ownership, client identity, or whether a participant was informed.
- FINRA historic weeklySummaryHistoric has a rolling history window; it is not a complete 2016-present series.
- No 335-name overlap threshold is used. The legacy 335 were manually/arbitrarily selected and remain only a frozen F80 comparability control.

## Next gate

Only if Phase 109's reconciliation is clean should a separate PIT/security-identity audit be designed. Any subsequent feature must use a documented conservative knowledge date, a permanent/effective-dated security ID, a broad historical universe including inactive/delisted names, and an ex-ante execution boundary. No forward-return test is authorized by this phase.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
