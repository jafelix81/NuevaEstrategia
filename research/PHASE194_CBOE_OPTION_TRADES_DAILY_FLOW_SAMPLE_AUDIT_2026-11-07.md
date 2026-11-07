# Phase 194 — Cboe Option Trades daily-flow sample row audit

**Audit date:** 2026-11-07  
**Disposition at commit:** hosted row audit pending  
**Scope:** one public sample date (2026-01-07); no licensed history, return test or alpha test.

## Why this phase exists

Phase 170's first strict parser rejected all 197,158 CSV records because it required ISO market dates and full date-time strings. Phase 171/172 clarified that each of the two sample members has 74,999 populated rows and 23,580 completely blank trailing rows; the populated market dates use M/D/YYYY and match the filename. The quote_datetime field is a seven-character time-only shape, not the full timestamp specified in v1.3. Under an HH:MM.d range interpretation, 22,989 rows fall within conventional hour/minute ranges and 52,010 do not. No time semantics were established.

Phase 194 tests a narrower proposition: can the public sample support a daily, NBBO-side measurement if market_date is parsed correctly and quote_datetime remains opaque? This does not require inventing a timestamp or silently repairing the vendor's sample.

## Method

- Parse M/D/YYYY and ISO market dates and require every populated market date to match the dated filename.
- Verify all-column-empty records form only a trailing padding block; exclude them from trade-row aggregates but report their count.
- Parse contract, trade, exchange, condition and contemporaneous option NBBO fields using the Phase 170 schema contract.
- Classify only exact at-ask and at-bid prints as candidate buyer-/seller-initiated trades. Midpoint, inside-spread, outside-NBBO, missing, locked and crossed observations remain separate.
- Report candidate contract-volume imbalance and price-times-contracts arithmetic without multiplying by 100; adjusted roots may have non-standard deliverables.
- Count trade-condition IDs without interpreting them. No condition exclusions or multi-leg assumptions are introduced.
- Hash the canonical core fields in each member and require the 19-column and 25-column members to match.
- Keep quote_datetime opaque. Component-range counts are diagnostics only; neither HH:MM nor MM:SS semantics are assigned.

## Interpretation limits

A passing row gate would establish only that one public daily sample can support a reproducible measurement prototype. It would not establish historical coverage, inactive/delisted symbol coverage, stable contract identity, first file receipt, correction vintages, trade-condition semantics or legal bulk-use rights. The sample's execution timestamp is not knowledge time. No feature is PIT-admitted and no signed-flow strategy or return test is authorized.

## Hosted execution result

The latest Phase 194 workflow artifact is the canonical sample-level result. If the daily row gate passes, the next task is a versioned condition-code and adjusted-deliverable audit, not an alpha test. If it fails, retain the rejection and do not relax the parser to force a positive result.

## Controls

No raw trades, symbols, contracts or clock values are persisted. No vendor contact or purchase, no holdout use, no production change, and no baseline change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
