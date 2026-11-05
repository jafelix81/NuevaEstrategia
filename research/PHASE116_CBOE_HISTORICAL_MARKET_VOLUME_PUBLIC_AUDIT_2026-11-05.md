# Phase 116 — Cboe U.S. Equities Historical Market Volume public archive audit

**Date:** 2026-11-05  
**Status:** PUBLIC SOURCE / MARKET-REGIME CONTEXT CANDIDATE ONLY  
**Scope:** verify annual daily and monthly public CSV availability from 2009–2026, validate arithmetic, keys and daily-to-monthly reconciliation. No symbol-level feature, forward return, alpha test, vendor contact or purchase.

## Why this source was added

The Cboe public historical market-volume page says its files cover **all U.S. equity exchanges and trade-reporting facilities (TRFs) from January 2009**. Daily and monthly CSV links are listed for every calendar year 2009–2026. Each market-center row is broken down by Tape A/B/C and includes shares, notional value and trade counts. The page says the source is based on UTDF and CTS consolidated data feeds and cautions that accuracy is not guaranteed.

Official page: https://www.cboe.com/markets/us/equities/market-statistics/historical-market-volume/

This is a useful independent, long-history **marketwide off-exchange activity context** source. It is not a substitute for FINRA ATS symbol-level data and cannot identify which individual stock experienced off-exchange activity.

## Data model and intended use

The daily/monthly files have 14 columns:
- Day/Month and Market Participant;
- Tape A/B/C Shares and Total Shares;
- Tape A/B/C Notional and Total Notional;
- Tape A/B/C Trade Count and Total Trade Count.

Rows are market-center aggregates. The public schema has no ticker, security identifier, MPID, buy/sell side, opening/closing status, customer classification, order identifier or beneficial-owner identity.

A potential derived market-regime descriptor is the aggregate TRF share/notional fraction:
- all FINRA TRF market-center shares divided by total shares across market centers;
- all FINRA TRF notional divided by total notional across market centers.

These are aggregate market structure measures. They should not be described as institutional or informed flow. If later used, they belong in a market-regime/control layer, not in a per-stock ranking feature. They may be correlated with volatility, market stress, venue mix and the broad market return itself.

## Audit protocol

The live audit attempts all 18 annual daily CSVs and all 18 annual monthly CSVs from 2009 through 2026. It checks:
1. Exact column schema and UTF-8 decoding.
2. Nonempty date/market-center keys, correct year and unique date/market-center or month/market-center keys.
3. Nonnegative finite numeric fields.
4. Tape A+B+C arithmetic against total shares, notional and trade counts.
5. For completed months, daily-to-monthly reconciliation by market participant and all 12 numeric fields.
6. First/last date, number of daily dates, market-center labels, long calendar gaps, raw-file byte counts and SHA-256 hashes.
7. A deterministic daily marketwide TRF share/notional context extract, without forward returns.

The current calendar month is excluded from daily/monthly reconciliation because the daily file may contain a partial month while the monthly file may not yet be final.

## Point-in-time and economic limitations

The public page documents historical coverage but does not expose first-publication timestamps, archived file vintages or a correction/revision history. A current historical CSV is not proof of what a trader knew on each historical date. Therefore strict PIT is **not established**. A conservative next-session lag can be evaluated only as a sensitivity after publication/update timing is independently documented; it cannot be mislabeled as strict PIT.

The data are aggregate across all symbols and all market centers. It cannot support a ticker-level off-exchange feature or identify informed participants. At most, it may later serve as a marketwide regime covariate, benchmark or control alongside stock-level features from other sources.

No return test is authorized by this audit. Do not merge it into F80 or change F80_TOP20_PARTIAL50_BASELINE_C20. No vendor purchase or contact is required or authorized.

## Decision rules

- If all years/files are accessible and monthly/daily totals reconcile, retain as a public long-history market-regime candidate.
- If historical years or reconciliation fail, document exact gaps and downgrade accordingly.
- Regardless of file-access success, keep strict PIT as pending because the public source does not supply historical publication/correction vintages.
- Do not run stock-level alpha tests with this marketwide series.
