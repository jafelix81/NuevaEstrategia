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

**PASS — daily sample row gate; time field quarantined.** Workflow [42418091879](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42418091879) completed successfully with 16/16 offline tests passing and a metadata-only artifact uploaded.

Both members (19-column and 25-column) contained 98,579 rows: 74,999 populated trade rows and 23,580 all-column-empty trailing padding rows. All 74,999 populated rows parsed; there were zero invalid rows, zero duplicate trade keys, and all market dates matched 2026-01-07. The two members had identical core-trade SHA-256 digest 4dd0e041ca3b1921a2f5a6a3825a9505be234947736232fb47f18e93c74d1b06. The sample represents one underlying and 308 option contracts, with 531,227 contracts of reported trade size.

Exact at-ask candidates: 24,649 prints / 172,313 contracts. Exact at-bid candidates: 27,697 prints / 209,076 contracts. The descriptive candidate signed contract-volume proxy is -36,763 contracts. Another 149,838 contracts were unclassified. Counts include 12,782 inside-spread, 8,754 midpoint, 625 locked-NBBO, 5 crossed/invalid-NBBO, 1 missing-NBBO, 231 above-ask and 255 below-bid prints. These are one-day descriptive counts, not predictive evidence or a validated net-flow signal.

The quote-time field remains opaque. 22,989 rows fit conventional HH:MM component ranges; 52,010 do not. All 74,999 fit a numeric 00–59 / 00–59 component range that could resemble MM:SS, but no MM:SS meaning is assigned. Raw clock values were not persisted. No same-day or intraday use is authorized.

This establishes that a daily sample-level NBBO-side measurement prototype is technically feasible without interpreting quote_datetime. It does not establish historical coverage, trade-condition semantics, adjusted deliverables, first file receipt, correction vintages or strict PIT. The next phase should audit condition codes, adjusted deliverables and actual file availability before any feature is admitted.

## Controls

No raw trades, symbols, contracts or clock values are persisted. No vendor contact or purchase, no holdout use, no production change, and no baseline change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
