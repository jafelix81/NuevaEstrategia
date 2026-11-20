# Phase 378 — CFTC TFF holiday-shifted weekly-slot reconciliation

**Date:** 2026-11-19  
**Status before hosted rerun:** implementation and deterministic tests prepared; corrected full-snapshot validation pending.  
**Parent:** Phase 377 full CFTC TFF Futures Only coverage and contract-key audit.  
**Scope:** source-grain/coverage correction only; no feature or return test.

## Why this correction is required

Phase 377 run [43497266092](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43497266092) retrieved 47,322 rows across 90 fields, reconciled the before/after row counts and metadata update stamp, and found 1,065 distinct report dates. For each of the three primary index contracts (13874A, 209742, 124603), the original helper returned 100.0% `coverage_pct` while also reporting 14 missing Tuesday anchors, 14 non-Tuesday report dates and an 8-day maximum gap.

The old function generated an exact 7-day date grid anchored to the first report date. It therefore treated holiday-shifted Monday/Wednesday report dates as both a missing Tuesday and an extra date, while its coverage numerator still counted all dates. That made the percentage misleading.

## Phase 378 correction

- Group report dates by ISO year/week, not by an assumed Tuesday date.
- Keep non-Tuesday report dates visible as shifted-date diagnostics.
- Detect multiple report dates in the same ISO week.
- Calculate actual missing ISO weeks, maximum weekly gap, longest contiguous run and latest contiguous run.
- Keep the three primary contracts separate from Russell 2000 (239742), whose full-span history was only 601 rows / 1,065 slots (56.431925%) with a 3,255-day maximum gap in Phase 377.
- Preserve the natural key `(report_date_as_yyyy_mm_dd, cftc_contract_market_code)`; missing contract-weeks remain missing, never zero or forward-filled.

The CFTC Historical Viewable page states that its dates are report dates, not release dates, and lists holiday-shifted examples including July 3, 2006; January 3, 2007; December 24, 2007; January 2, 2008; December 22, 2008; July 3, 2023; and November 10, 2025. This is corroboration of report-date shifts, not a historical publication timestamp source.

## Hosted validation gate

The Phase 377 branch workflow reruns the complete 47k-row public snapshot. Acceptance requires:
1. Existing row-count, metadata stability, schema, category, candidate-code and natural-key gates remain intact.
2. No duplicate ISO-week slots for the four candidate contracts.
3. The primary index contracts 13874A, 209742 and 124603 have complete ISO-week coverage across their observed history.
4. Russell's incomplete history is explicitly quantified by latest/longest contiguous runs, not silently treated as a continuous 2006–2026 series.

## PIT and research interpretation

CFTC's report date is the position/as-of date, not the knowledge date. The usual release is Friday at 3:30 p.m. ET, with holiday delays and exceptional backlog periods. The 2025 shutdown/catch-up schedule demonstrates that actual availability can be many weeks after the report date. Historical actual release dates beyond the current official window remain unverified; no backtest may use report dates as if known then.

TFF categories are self-reported business-purpose classifications, not verified informed-investor identities. The source remains a conditional **macro equity-index positioning/regime** candidate, not stock-specific institutional flow.

## Controls

No raw rows/IDs retained, no forward returns, no alpha, no OOS, no bootstrap/LOO, no holdout, no vendor purchase, and no change to `F80_TOP20_PARTIAL50_BASELINE_C20`, production, universe, capital, exposure or parameters.
