# Phase 53B — OCC Volume Query full-expiry universe audit
Date: 2026-11-04
Branch: phase53-occ-daily-open-interest-audit
Status: preregistered full-universe coverage audit; no alpha test.

## What the first OCC pilot actually established

The OCC Daily Open Interest endpoint returned a monthly report with market-wide totals by asset class (Equity, Index/Other, Debt, Futures and OCC Total), not contract-level OI by ticker. It is not a per-stock Smart Money source; it may be retained only as a broad market-regime control.

The OCC Volume Query endpoint is different: it returns rows with Quantity, Underlying Symbol, Options Symbol/root, Account Type (Customer/Firm/Market Maker), Call/Put, Exchange, Activity Date and Series/Contract Date. The initial pilot passed `contractDt=reportDate`, which restricted results to the same-day series (mostly 0DTE). The v2 audit intentionally omits contractDt to cover all series/contract dates.

The OCC Volume Query UI states a 24-month history limit. The 2024-01-03 probes returned the explicit message `Report date cannot be prior to 2 years`; 2025-01-03 and 2026-11-02 probes returned valid rows for all 18 ticker/date/account-type combinations in the initial three-ticker sample.

## Fixed universe audit

- Frozen 335-name universe.
- Dates: 2025-01-03 and 2026-11-02.
- One request per ticker/date using accountType=ALL.
- Options, underlying symbol, daily, equity options (OSTK), calls and puts.
- contractDt omitted to include all series/contract dates.
- Diagnostic boundary probes: AAPL, NVDA and TSLA on 2024-01-03.

## Required fields

Quantity, Underlying Symbol, Options Symbol/root, Account Type, Call/Put, Exchange, Activity Date, Series/Contract Date.

## Pre-registered gates

- At least 70% exact ticker coverage on each of the two recent dates.
- At least 95% valid schema among all ticker/date responses.
- Account types must be in C/F/M and call/put in C/P.
- Activity Date must match the requested report date for at least 95% of valid rows.

These are only short-window source-coverage gates. The 24-month retention is insufficient for a long multi-cycle OOS study by itself, and the OCC docs reviewed do not provide a reproducible historical publication timestamp.

## Economic limits

- Account type is not buy/sell side. Call/put volume is not directional order flow.
- No strike-level OI or open/close status is present in this query output.
- A firm or customer call/put imbalance is not proof of informed positioning.
- Do not treat the Daily Open Interest monthly aggregate report as per-ticker OI.
- No forward returns or alpha test.

## Decision after audit

If coverage passes, retain OCC Volume Query as a recent complementary feature only; do not use it as a standalone Smart Money signal. Prefer Cboe Open-Close EOD for longer history and explicit buy/sell/open/close classification, subject to licensing and Cboe-exchange coverage. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
