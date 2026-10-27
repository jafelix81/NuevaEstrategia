# Phase 39 — SEC Form 4 insider-transaction feasibility gate

Date: 2026-10-27 (actual-file gate added)

## Objective
Assess whether SEC insider transactions can provide a security-level, point-in-time Smart Money candidate for the frozen universe without look-ahead.

## Fresh official-source verification
The SEC Insider Transactions Data Sets currently cover **January 2006 through September 2026** and are published quarterly. The SEC page lists actual downloadable quarterly ZIP files, including 2026 Q3 and 2012 Q1. The data are extracted from the as-filed XML portions of Forms 3, 4 and 5. SEC also notes that documents filed after 5:30 PM ET on the last business day of a quarter roll into the subsequent quarterly posting.

Primary source: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
Documentation: https://www.sec.gov/files/insider_transactions_readme.pdf

## PIT rule
The quarterly dataset publication date is **not** the event-level knowledge date. For an investment-information test, use the individual EDGAR filing acceptance/publication timestamp where available. Form 4 instructions state that a Form 4 is due before the end of the second business day following the transaction and is deemed filed on the date received by the Commission. Therefore transaction date may define the economic event, but filing acceptance/publication time defines when the information becomes public.

The quarterly flat files may omit metadata needed for an exact filing-time PIT boundary. The actual-file audit therefore must determine which timestamp fields are present and whether they can be joined reproducibly to EDGAR filing metadata. If not, the candidate remains feasibility-only and no alpha test is authorized.

## Hypotheses — explicitly not assumed to be "smart money"
H1: discretionary open-market insider purchases contain incremental information beyond F80/LTM.
H2: clustered purchases across multiple insiders are more informative than isolated purchases.
H3: net insider buying after excluding grants, exercises, tax withholding, gifts and other non-discretionary codes is more informative than raw Form 4 activity.
H4: insider activity may predict returns only because it follows prior returns; residualized tests must distinguish information from return-chasing.

## Required feasibility gates before any return test
1. Security-level issuer/ticker mapping for the frozen universe.
2. Historical coverage sufficient for an apples-to-apples test; no reduced-universe alpha test if coverage is inadequate.
3. Reproducible filing acceptance/publication timestamp or another defensible PIT field.
4. Transaction-code filtering that separates discretionary open-market buys/sells from grants, awards, option exercises, tax withholding, gifts and other mechanical transactions.
5. No use of holdings reported after the transaction as if known at transaction time.
6. Chronological validation only; no full-sample feature selection.
7. If the gate passes, compare incremental information against frozen LTM/F80 using identical exposure, realistic costs, bootstrap/LOO, and a genuinely untouched OOS period.

## Actual-file audit
Added workflow `.github/workflows/phase39_sec_form4_actual_file_audit.yml` in commit `fab69329c96076c80a5c273fddb1024b7d3bdc3a`.

The workflow downloads and inspects representative **2026 Q3** and **2012 Q1** SEC ZIP files directly from the official SEC endpoints. It records ZIP members and CSV headers for submission, reporting-owner, non-derivative transaction and metadata files. This is a schema/coverage audit only; it does not perform a return test.

The purpose of the two-period sample is to detect historical schema drift and determine whether the fields needed for issuer mapping, transaction-code filtering, transaction date and filing/PIT reconstruction are actually present across the full history.

## Kill conditions
- Inadequate frozen-universe coverage.
- No reproducible filing-time PIT boundary.
- Signal vanishes after excluding non-discretionary transactions.
- Signal is explained by prior returns/volume/volatility.
- Apparent alpha exists only in-sample or fails chronological OOS/bootstrap discipline.

## Status
**ACTUAL_FILE_AUDIT_RUNNING_PENDING_SCHEMA_RESULT.** No return test or strategy change authorized yet.
