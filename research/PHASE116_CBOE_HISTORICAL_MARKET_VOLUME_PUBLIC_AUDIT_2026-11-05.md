# Phase 116 — Cboe U.S. Equities Historical Market Volume public archive audit

**Date:** 2026-11-05  
**Status:** <PASS> public archive coverage and daily/monthly reconciliation; <CONDITIONAL> marketwide regime-context candidate; <NOT PIT> historical availability  
**Live run:** [42033472218](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42033472218)  
**Artifact:** [phase116-cboe-historical-market-volume-audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42033472218/artifacts/13416659256) (5,940,729 bytes)

## Result

The audit successfully downloaded all 18 annual daily files and all 18 annual monthly files listed by Cboe for 2009–2026.

| Metric | Result |
|---|---:|
| Annual file pairs | 18/18 |
| Daily rows | 72,103 |
| Monthly rows | 3,395 |
| First daily date | 2009-01-02 |
| Last daily date | 2026-11-04 |
| Daily trading dates | 4,488 |
| Completed participant-month comparisons | 55,865 |
| Offline parser/regression tests | 14/14 |
| Live workflow | PASS |

For every completed month available in both daily and monthly files, all participant-month comparisons passed across all 12 numeric measures (shares, notional and trade counts for Tapes A/B/C and totals) within explicit output-precision tolerances. Duplicate date/market-center and month/market-center keys, invalid numeric values, wrong-year dates and tape-total discrepancies beyond tolerance fail the audit.

The live run confirms a usable public time series from January 2009 through November 4, 2026. This is materially longer than the FINRA ATS symbol-level API window, but its unit of observation is the market center, not the individual issuer.

## Important legacy conventions discovered

1. The 2009 monthly URL uses a first-column header of `Day`, while its values are monthly keys in `YYYY-MM` format. The auditor normalizes that legacy header to `Month` without changing the source bytes or recorded SHA-256.
2. Older daily/monthly files round some notional fields at different precisions; current monthly aggregates can also differ from sums of daily tape shares by a very small relative amount. The parser therefore uses conservative scale-aware tolerances rather than falsely demanding bitwise arithmetic equality:
   - daily notional: max($0.20, 1e-10 × absolute total);
   - monthly notional: max($2.00, 1e-9 × absolute total);
   - monthly shares: max(1 share, 1e-7 × absolute total);
   - trade counts remain exact.
3. The official Cboe market-volume summary labels the TRFs as **DQ, DN and DB**. Historical files may label these rows `NASDAQ (DQ)`, `NYSE (DN)` or `NASDAQ (DB)`, while current files spell out FINRA/TRF names. The final auditor maps both naming conventions; it does not rely solely on the literal string `TRF`.

Official sources:
- Cboe historical archive and field definitions: https://www.cboe.com/markets/us/equities/market-statistics/historical-market-volume/
- Cboe current market summary showing `TRFs (DQ,DN,DB)`: https://www.cboe.com/us/equities/market_share/market/

Cboe states that the files cover all U.S. equity exchanges and TRFs from January 2009, report daily shares/notional/trade counts by market center and Tape A/B/C, and are based on UTDF/CTS consolidated feeds. Cboe also says the data are believed reliable but not guaranteed.

## Derived context extract

The artifact includes `marketwide_daily_trf_context.csv` with 4,488 daily observations:
- total consolidated shares and notional across all listed market centers;
- shares and notional attributed to TRF centers DQ/DN/DB;
- TRF share and notional fractions.

This is a marketwide venue-mix descriptor. It cannot identify the stock traded, the side of the trade, an MPID, account type, opening/closing status or beneficial owner. It is not a ticker-level off-exchange feature and does not establish informed/institutional activity.

## PIT decision

**Strict historical point-in-time availability is not established.** The public page and current files do not provide historical first-publication timestamps, immutable historical file vintages, or a correction/revision history. The current copy of a 2009 or 2016 file is not proof that the same values were available on the corresponding historical trading date.

A conservative next-session lag may be studied as a future sensitivity only after publication timing and revision behavior are documented. It must not be represented as strict PIT. Prospective capture of daily file snapshots can establish a clean forward archive but cannot repair the historical vintage gap.

## Research decision

- Retain as a **long-history marketwide off-exchange/venue-regime context candidate**.
- Do not call it Smart Money or institutional flow.
- Do not use it for stock ranking or issuer-level event studies.
- Do not run historical alpha/return tests until the availability/vintage gate is resolved.
- Do not modify or unfreeze `F80_TOP20_PARTIAL50_BASELINE_C20`.
- No vendor purchase, account creation, contact or data acquisition was performed or requested.

The highest-information options candidate remains Cboe C1 Open-Close EOD (Phase 114/115), still conditional on paid historical archive access, PIT underlying mapping and final-file availability. Phase 116 is a separate public market-regime control, not a replacement for that options dataset.


## 2026-11-05 execution-log correction

The final successful run 42033472218 executed **14** offline regression tests (not 13); all 14 passed. The earlier failed attempt 42033447324 had one failing legacy TRF-code assertion and did not produce an audit artifact. The final run produced artifact 13416659256. The report's test count is corrected to match the successful job log.
