# Phase 612 — XNYS session and SEC 13F conservative knowledge-clock audit

**Date:** 2026-11-25  
**Status:** bounded calendar audit and point-in-time clock implementation  
**Branch:** \`phase612-xnys-session-knowledge-clock-audit\`  
**Baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` unchanged

## Objective

Phase 611 established that EDGAR Accepted timestamps can be reconciled with the SEC legal Filing Date, but did not map them to actual XNYS sessions. Phase 612 adds a reproducible exchange-session layer and separates event availability from daily-bar completion and execution.

## Calendar feasibility result

The audit uses the pinned \`exchange_calendars==4.13.1\` XNYS calendar. It is a third-party maintained calendar, not an official NYSE data feed. The historical schedule from 2013-01-01 through 2026-11-24 contains 3,496 sessions, with 29 early closes at 13:00 ET. All scheduled opens in this interval are 09:30 ET; scheduled closes are 13:00 or 16:00 ET; no weekend sessions are present.

Selected checks are reconciled to the official NYSE calendar:
- 2026-07-03 and 2026-11-26 are closed.
- 2026-11-27 and 2026-12-24 close at 13:00 ET.
- Regular NYSE core trading is 09:30–16:00 ET.
- DST conversion moves the regular open from 14:30 UTC in winter to 13:30 UTC in summer.

Historical special closures spot-checked include 2018-12-05, 2025-01-09, the 2012 Hurricane Sandy closure, and the 2001 September 11–14 closure. This is not an exhaustive reconciliation of every historical exchange notice.

Official NYSE reference: https://www.nyse.com/trade/hours-calendars  
Calendar package documentation: https://pypi.org/project/exchange_calendars/4.13.1/

## Conservative point-in-time rule

The implementation preserves three distinct clocks:

1. **Event-only earliest open:** first XNYS open strictly after effective knowledge time. This is only a theoretical event-driven lower bound; it is not a recommended fill.
2. **First completed daily bar:** first XNYS session whose scheduled close is strictly later than effective knowledge time.
3. **Daily-bar signal execution:** next XNYS session after that completed bar, with both next-open and next-EOD timestamps returned.

Effective knowledge time is:
- \`max(EDGAR Accepted, collector first-seen)\` when a prospective first-seen timestamp exists.
- Otherwise, the end of the legal Filing Date (23:59:59 ET), never the report period and never an assumed intraday time.

Strict inequality matters: an event timestamp exactly at the scheduled close cannot use that session's completed bar. Early closes use the actual scheduled close, not a hard-coded 16:00 ET. The next-open and next-EOD execution alternatives are both retained so later strategy tests can use the actual execution convention rather than silently choosing one.

## Limitations

- The calendar package is third-party maintained; only selected 2026 dates and selected historical special closures were independently spot-checked.
- A scheduled session close is not proof of the exact time a vendor publishes its daily bar.
- No auction cutoff, order type, halt, symbol-specific restriction, or fill/slippage model is included.
- Historical collector first-seen timestamps remain unavailable; the end-of-filing-date fallback is intentionally conservative.
- No effective-dated CUSIP/FIGI-to-F80 crosswalk is completed.
- No 13F signal, alpha, OOS, bootstrap, LOO, return, or risk test was run.

## Decision

**PASS for calendar/clock feasibility only.** Do not mark any 13F observation signal-eligible. The next gate is to join prospective first-seen records, validate the actual daily-price provider's bar-publication timing, and complete the historical F80 security master before any incremental ownership-feature test.

No SEC requests, vendor contacts, paid data, production changes, portfolio changes, capital changes, or exposure changes. Options/data budget remains USD 0.
