# Phase 45 — SEC Form 4 PIT Timestamp Gate v1
Date: 2026-11-01
Status: FEASIBILITY / DESIGN ONLY — no alpha test authorized

## Objective
Establish the legally and technically defensible point-in-time availability timestamp for insider Form 4 signals before any historical return test.

## Findings
- SEC EDGAR ownership filings are disseminated through the EDGAR system on business days. The SEC states that ownership forms (Forms 3, 4 and 5) submitted after 10:00 p.m. ET are disseminated on the next business day. Therefore a calendar-date-only `filing_date` is conservative but can still be insufficient for intraday timing studies; the exact submission/acceptance timestamp should be retained where available.
- EDGAR historical coverage begins in 1994/1995, so the source has materially longer history than the current 335-name research universe requires.
- Form 4 XML exposes issuer/ticker, reporting-person relationship, transaction date, transaction code, acquired/disposed quantity, price, post-transaction ownership and the Rule 10b5-1(c) indicator. SEC examples also show that footnotes can identify tax-withholding sales and transactions executed under 10b5-1 plans.

## PIT rule
1. `transaction_date` is the economic event date, never the information-availability date.
2. The earliest defensible signal timestamp is the SEC dissemination/filing availability timestamp, not the transaction date.
3. If only a filing date is available, signals enter at the next tradable session after that filing date; do not assume same-day availability.
4. For filings submitted after the SEC's ownership-form dissemination cutoff, shift availability to the next business day.
5. Amendments must update the prior state but must not create a new independent insider event unless the amendment changes an economically relevant field and that change was genuinely newly disclosed.

## Signal exclusions before alpha testing
- Exclude or separately classify Rule 10b5-1 transactions.
- Exclude/flag tax-withholding and vesting-related dispositions.
- Do not interpret all sales as bearish or all purchases as bullish.
- Aggregate by reporting person and issuer before cross-sectional testing to avoid prolific-insider/issuer concentration.

## Pre-specified test families
A. discretionary open-market purchases/sales, separately by side;
B. net insider buying intensity scaled by shares outstanding and/or normal insider ownership;
C. clustering: number of distinct insiders buying within a fixed post-filing window;
D. persistence: repeated discretionary buying by the same insider/issuer pair;
E. interaction with baseline momentum/quality controls to test incremental information.

## Validation gate
Any candidate must beat the frozen F80/LTM baseline on identical universe/exposure/cost assumptions under chronological train/validation/OOS splits. Use issuer-clustered bootstrap/LOO and explicitly test whether the effect survives removal of the largest issuers and prolific filers. A positive result that disappears after excluding 10b5-1/tax/vesting transactions is not considered evidence of informed trading.

## Current decision
KEEP as a high-priority data source, but do not run alpha until the PIT timestamp field and historical issuer/ticker mapping are materialized reproducibly. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Sources
- SEC, Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC Form 4 XML examples / filing schema in EDGAR archives.
