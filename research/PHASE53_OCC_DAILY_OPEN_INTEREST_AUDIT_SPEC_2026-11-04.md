# Phase 53 — OCC daily open-interest feasibility audit
Date: 2026-11-04
Branch: phase53-occ-daily-open-interest-audit
Status: preregistered data-feasibility audit only; no alpha test.

## Why this source is being re-opened

The earlier Phase 24B audit found that several public OCC endpoints returned empty/insufficient data on sampled dates. It did not establish whether the dedicated Daily Open Interest batch endpoint has the same historical limitation. The OCC currently documents a direct CSV download endpoint for Daily Open Interest. The Volume Query batch endpoint separately exposes daily options volume by Customer, Firm and Market Maker account types.

Official OCC pages:
- Daily Open Interest: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/daily-open-interest
- Volume Query batch processing: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-query-batch-processing
- Volume Query UI (states a 24-month window): https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-query

The Daily Open Interest page documents `reportDate`, `action=download`, and `format=csv`, but does not state historical retention or a historical publication timestamp. Those are the primary audit questions.

## Fixed samples

Daily OI sample dates:
- 2018-01-03
- 2020-01-03
- 2022-01-03
- 2023-04-14
- 2024-01-03
- 2025-01-03
- 2026-01-05
- 2026-11-02

Volume Query probes:
- Dates 2024-01-03 (older-than-24-month boundary), 2025-01-03 and 2026-11-02.
- Underlyings AAPL, NVDA and TSLA.
- Account types Customer (C), Firm (F) and Market Maker (M).
- Equity options only; daily report; calls and puts.

## Required diagnostics

- HTTP status, response bytes, content type, last-modified header, SHA-256 and exact CSV header for each request.
- Contract row count, non-null OI count, unique underlyings, total OI, and exact overlap with the current frozen 335 tickers for each OI date.
- Volume-query response row count and schema for every symbol/date/account-type probe.
- Preserve raw sample contract rows and response prefixes for auditability.
- Do not treat HTTP 200 or non-empty HTML as valid data; parse the actual CSV schema.

## Pre-registered feasibility gates

- At least 6 of 8 OI sample dates return contract-level rows with non-null OI.
- The available OI sample span is at least 3 years.
- Minimum exact ticker coverage across successful OI dates is at least 70% of the frozen 335-name universe.
- At least 80% of recent Volume Query probes (2025-01-03 and 2026-11-02) return non-empty parsed rows. The 2024 probe is diagnostic for the stated retention boundary and does not count against the recent-data gate.

These are source feasibility gates only. Passing does not prove PIT availability, historical F80 membership, trade direction, opening/closing activity, buyer identity, or alpha.

## PIT and economic limitations

- OCC Daily OI is contract inventory. A change in OI does not reveal whether informed buyers or sellers initiated a position.
- Volume by account type distinguishes Customer/Firm/Market Maker, but does not provide buy/sell aggressor side.
- OCC's public Daily OI documentation does not state the historical time at which each report became available. Record the response's Last-Modified header, but do not assume it is the original release timestamp.
- Do not use reportDate as KnowledgeDate. Keep the source conditional until release timing is evidenced; any eventual test must use a conservative next-session availability rule.
- The current frozen ticker list is not a point-in-time active/delisted universe. Historical security identity and option-root mapping must be reconstructed before backtesting.
- No IV/skew surface is included in this audit. A separate source is required for historical quotes/Greeks.

## Decision after audit

- If history or universe coverage fails, park the source.
- If OI passes but Volume Query fails, consider OI only as a weak contract-inventory feature; do not describe it as institutional flow.
- If both pass, continue with a full historical contract/OI coverage and PIT-publication audit before any return test.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
