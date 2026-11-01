# Phase 39 — SEC Form 4 PIT verification V2 — 2026-11-01

## Status
**FEASIBILITY CONFIRMED; NO ALPHA AUTHORIZED.**

## Fresh official verification
The SEC's current Form 4 instructions state that Form 4 must be filed before the end of the second business day following execution for transactions subject to Section 16(a), and that the form is deemed filed on the date received by the Commission. This makes `filing_date` the conservative public-information timestamp and `transaction_date` the economic event date; the latter must never be substituted for the former in ex-ante signal construction.

SEC Form 4 structured XML examples also expose issuer ticker, reporting-person relationship, transaction date, transaction code, acquired/disposed amount, price, post-transaction beneficial ownership, and direct/indirect ownership. These fields are sufficient to construct economically interpretable insider-trading candidates without relying on prose-only parsing.

## Important contamination controls
- Code `P` is an open-market/private purchase; code `S` is a sale, but not every sale is discretionary. SEC filings can explicitly identify Rule 10b5-1 sales and sell-to-cover tax withholding. Those observations must be flagged/excluded or modeled separately rather than treated as informed discretionary selling.
- Automatic awards, vesting, option exercises, and other non-discretionary codes must not be pooled with open-market purchases/sales.
- Amendments must be treated as state corrections/updates and not as independent trades.
- Transaction date can precede filing date by up to the regulatory reporting window; using transaction date as if known contemporaneously would introduce look-ahead.

## Economic test to pre-specify
If the existing Phase 39 feasibility gate is passed, candidate signals should initially be limited to economically interpretable discretionary transactions: open-market purchases (`P`) and discretionary sales (`S`), stratified by reporting-person role and transaction size relative to prior ownership/turnover. 10b5-1, tax withholding, awards, exercises, and other mechanically generated transactions should be separately flagged.

The first comparison must be incremental versus frozen LTM/F80 using chronological OOS, identical exposure/cost assumptions, and return-chasing controls. No signal should be promoted from in-sample performance.

## Evidence
- SEC Form 4 instructions: filing deadline and deemed filing date.
- SEC Form 4 data instructions: transaction-code definitions.
- SEC archived Form 4 XML examples: transaction and ownership fields and explicit 10b5-1/tax-withholding explanations.

## Decision
Form 4 remains a credible historical/PIT source and is technically stronger than many 'smart money' proxies because the public availability timestamp is tightly bounded by regulation. This does **not** establish predictive power. The line remains gated until universe coverage, issuer mapping, amendment handling, and an executable historical dataset are confirmed.
