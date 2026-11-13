# Phase 379 — CFTC archive Updated-date PIT feasibility audit

**Status:** deterministic tests and hosted sample retrieval pending.  
**Parent:** Phase 378 Russell contract-era / TFF classification-regime audit.  
**Scope:** timestamp provenance only; no features or returns.

## Hypothesis

Static CFTC TFF Futures Only archive pages end with an “Updated [date]” field. In recent samples, that date appears to match the actual COT publication date, including the 2025 government-shutdown catch-up schedule. If it is never earlier than actual publication, it may provide a conservative historical availability date when the official release-date list is unavailable.

This is not assumed to be true. CFTC says its historical report index dates are report dates, not release dates, and that a list of historical release dates is not available beyond the latest 13 months. The archive Updated field is not formally documented as the original first-publication timestamp.

## Pre-registered sample

- 13 CFTC 2025 catch-up reports with explicit report-date → new-publication-date pairs from Release 9147-25 / Historical Special Announcements.
- 10 2026 report dates with expected publication dates from the official CFTC 2026 release schedule.
- 6 older archive-only examples from 2017, 2020, 2022, 2023 and 2024, where the official release-date list is no longer available.

For every page, verify that the archive heading matches the requested report date and parse the final Updated date. For the 23 officially scheduled cases, require exact equality with the official publication date. Retain only dates, URLs, HTTP status and match results; never retain raw HTML or positions.

## Interpretation limits

Even if all 23 official-schedule cases match:
- The result validates the field only against this recent sample, not every historical year.
- “Updated” could reflect a later archive correction or migration rather than first publication.
- A date-only field does not supply the exact 3:30 p.m. ET release timestamp.
- Do not claim strict PIT or backtest with this field until a broader historical audit establishes it is never earlier than actual publication.
- A conservative candidate rule is to use the first regular market session after the archive Updated date, never the same-day close.

Official references:
- 2025 catch-up schedule: https://www.cftc.gov/PressRoom/PressReleases/9147-25
- Historical special announcements: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm
- 2026 release schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC COT FAQ / historical release-date limitation: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- Example archive page, report date 2025-11-10: https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2025/futures/financial_lf111025.htm
- Example archive page, report date 2026-10-27: https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2026/futures/financial_lf102726.htm

## Decision

No signal or alpha test is authorized. A successful sample audit only promotes archive Updated to a candidate conservative timestamp for a broader validation phase. TFF category backcast before 2010-07-22 remains excluded, and the Russell contract-era split from Phase 378 remains mandatory.

## Controls

No raw HTML, raw positions, trader identifiers, forward returns, alpha, OOS, bootstrap, LOO or holdout use. No F80, production, universe, capital, parameter or exposure changes.
