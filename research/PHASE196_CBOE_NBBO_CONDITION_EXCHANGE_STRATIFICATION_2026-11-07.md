# Phase 196 — Cboe Option Trades NBBO-side decomposition by condition and exchange

**Audit date:** 2026-11-07  
**Scope:** one public sample date, 2026-01-07; one underlying; descriptive measurement only.

## Objective

Phase 194 measured an exact-at-ask minus exact-at-bid candidate contract-volume proxy of -36,763 contracts in one sample day. Phase 195 established that the file contains materially different execution-condition categories, including automatic executions, intermarket sweeps, single-leg auctions/crosses, multi-leg trades and stock-option trades.

Phase 196 asks a narrow question: which condition and exchange labels contribute to that one-day aggregate? It does not attempt to identify institutional participants or predict returns.

## Method

- Re-download the same public sample and current official Cboe condition/exchange mapping files.
- Re-run Phase 194's two-member, row-quality and canonical-core-digest gate before stratification.
- Use only the 19-column base trade member after the 19/25-column pair has passed exact core-row reconciliation.
- Classify only exact trade-price equality with the contemporaneous option NBBO ask or bid. All other quote relationships remain unclassified categories.
- Aggregate print counts, contract volume, exact-at-ask volume, exact-at-bid volume, and price-times-contracts arithmetic without a 100 multiplier by condition, exchange, and condition×exchange.
- Keep the time-only quote_datetime opaque and unused.
- Reconcile every cross-tab to the Phase 194 row count, contract volume and exact-side totals.
- Persist mapping IDs/names, hashes and non-identifying aggregates only; never persist raw trades, symbols, contracts or clock values.

Condition buckets are descriptive groupings of current mapping names, not participant classifications. Exchange names identify the reported execution venue only.

## Hosted execution result

Pending the Phase 196 hosted workflow. The result JSON and metadata-only artifact will record the exact sample and mapping hashes, cross-tab totals and reconciliation checks.

## Admission decision

A passing decomposition is only a one-day, one-underlying measurement sensitivity. The current mapping files have no effective dates and were modified after the sample date; the condition workbook lacks message_type. This phase cannot establish that the mapping was historically valid, that the at-bid/ask side is a reliable aggressor label, or that any execution category represents institutional/informed activity.

No signed-flow feature, stock/option return test, PIT admission, holdout use or production change is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
