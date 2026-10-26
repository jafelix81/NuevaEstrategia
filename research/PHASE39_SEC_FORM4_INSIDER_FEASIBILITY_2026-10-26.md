# Phase 39 — SEC Form 4 insider-transaction feasibility gate

Date: 2026-10-26

## Objective
Assess whether SEC insider transactions can provide a security-level, point-in-time Smart Money candidate for the frozen universe without look-ahead.

## Current evidence
The SEC Insider Transactions Data Sets cover January 2006 through September 2026 and are extracted from the as-filed XML portions of Forms 3, 4 and 5. SEC states the datasets are updated quarterly; filings after 5:30 PM ET on the last business day of a quarter roll into the subsequent quarterly posting. This dataset therefore has deep history but its quarterly posting date is not the transaction-level PIT boundary.

Form 4 is generally required within two business days after the transaction date. The individual EDGAR filing acceptance timestamp should therefore be treated as the primary ex-ante availability boundary when reconstructing historical information. Do not use the quarterly dataset publication date as a substitute if individual filing timestamps are available.

## Hypotheses — explicitly not assumed to be "smart money"
H1: discretionary open-market insider purchases contain incremental information beyond F80/LTM.
H2: clustered purchases across multiple insiders are more informative than isolated purchases.
H3: net insider buying after excluding grants, exercises, tax withholding, gifts and other non-discretionary codes is more informative than raw Form 4 activity.
H4: insider activity may predict returns only because it follows prior returns; residualized tests must distinguish information from return-chasing.

## Required feasibility gates before any return test
1. Security-level issuer/ticker mapping for the frozen universe.
2. Historical coverage sufficient for an apples-to-apples test; no reduced-universe alpha test if coverage is inadequate.
3. Individual filing acceptance/publication timestamp or another defensible PIT field.
4. Transaction-code filtering that separates discretionary open-market buys/sells from grants, awards, option exercises, tax withholding, gifts and other mechanical transactions.
5. No use of holdings reported after the transaction as if known at transaction time.
6. Chronological validation only; no full-sample feature selection.
7. If the gate passes, compare incremental information against frozen LTM/F80 using identical exposure, realistic costs, bootstrap/LOO, and a genuinely untouched OOS period.

## Kill conditions
- Inadequate frozen-universe coverage.
- No reproducible filing-time PIT boundary.
- Signal vanishes after excluding non-discretionary transactions.
- Signal is explained by prior returns/volume/volatility.
- Apparent alpha exists only in-sample or fails chronological OOS/bootstrap discipline.

## Status
FEASIBILITY GATE OPEN. No return test or strategy change authorized yet.

## Primary source
SEC Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
