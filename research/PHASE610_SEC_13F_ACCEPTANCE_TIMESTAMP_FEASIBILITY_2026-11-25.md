# Phase 610 — SEC 13F filing acceptance timestamp feasibility audit

**Status at branch creation:** bounded six-accession audit pending.  
**Scope:** determine whether EDGAR filing-detail pages expose exact Accepted timestamps and whether the date matches the filing date. No full backfill.

## Why this gate matters

The SEC 13F data-set SUBMISSION table provides a filing date, but a point-in-time backtest needs a reproducible availability clock. The filing-detail page exposes an Accepted timestamp; Phase 610 samples the same six source-confirmed accessions used in Phase 607.

The parser records:
- Accepted timestamp as displayed by SEC (Eastern Time).
- Filing Date and Period of Report.
- Whether Accepted's calendar date matches Filing Date.
- A conservative fallback knowledge date one calendar day after Filing Date. Conversion to the first subsequent XNYS session requires a validated exchange calendar.

## Samples

- 2018 Marshall Wace.
- 2018 clean sequence control.
- 2018 OppenheimerFunds.
- 2026 Dakota Wealth Management.
- 2026 XXEC.
- 2026 Allspring.

## Interpretation

An Accepted timestamp is the EDGAR acceptance time, not proof that a strategy could parse the filing instantly. For conservative backtesting, the system must use the later of verified publication/acceptance and actual collector availability, then map that timestamp to the first tradable XNYS session. If exact timestamp coverage is incomplete, a date-only fallback must remain strictly after the filing date.

No alpha, OOS, bootstrap, LOO or production eligibility is inferred.
