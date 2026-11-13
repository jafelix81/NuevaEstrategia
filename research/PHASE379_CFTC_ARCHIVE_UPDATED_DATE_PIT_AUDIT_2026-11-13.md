# Phase 379 — CFTC archive Updated-date PIT feasibility audit

**Status:** first hosted run found 22/23 exact date matches; the remaining archive Updated date was two days later than the official release date. The acceptance criterion has been corrected to test the conservative condition (Updated date is never earlier than official release). Corrected hosted run pending.  
**Parent:** Phase 378 Russell contract-era / TFF classification-regime audit.  
**Scope:** timestamp provenance only; no features or returns.

## Hypothesis

Static CFTC TFF Futures Only archive pages end with an “Updated [date]” field. In recent samples, that date appears to match the actual COT publication date, including the 2025 government-shutdown catch-up schedule. If it is never earlier than actual publication, it may provide a conservative historical availability date when the official release-date list is unavailable.

This is not assumed to be true. CFTC says its historical report index dates are report dates, not release dates, and that a list of historical release dates is not available beyond the latest 13 months. The archive Updated field is not formally documented as the original first-publication timestamp.

## Pre-registered sample

- 13 CFTC 2025 catch-up reports with explicit report-date → new-publication-date pairs from Release 9147-25 / Historical Special Announcements.
- 10 2026 report dates with expected publication dates from the official CFTC 2026 release schedule.
- 6 older archive-only examples from 2017, 2020, 2022, 2023 and 2024, where the official release-date list is no longer available.

For every page, verify that the archive heading matches the requested report date and parse the final Updated date. For the 23 officially scheduled cases, require the archive Updated date to be on or after the official publication date. Exact matches and later archive updates are reported separately. Retain only dates, URLs, HTTP status and match results; never retain raw HTML or positions.

## Interpretation limits

The first hosted run retrieved all 23 official-schedule pages: 22 Updated dates matched the official publication date exactly; the 2025-12-23 report page was marked Updated 2025-12-31, two days after the official 2025-12-29 publication date. This is consistent with a later archive modification and should be treated as a conservative delay, not an exact release timestamp. The corrected audit therefore tests that Updated is never earlier than the official release date, rather than requiring exact equality.
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

## Hosted result — completed 2026-11-13

Corrected run [43499068179](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499068179) passed; date-only artifact [14072598314](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499068179/artifacts/14072598314).

- All 23 official-schedule archive pages were retrieved and their report headings matched the requested report dates.
- Archive Updated date was **not earlier than the official publication date in 23/23 cases**.
- 22/23 were exact matches. One case was later: report date 2025-12-23, official publication 2025-12-29, archive Updated 2025-12-31 (+2 days). This is a conservative delay, not a reason to backdate the signal.
- Six older archive-only examples (2017, 2020, 2022, 2023 and 2024) were all retrieved; each had an archive Updated date three days after its Tuesday report date. These six are descriptive only because an independent historical release-date list is unavailable.
- The first run [43498878730](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43498878730) failed because the initial test incorrectly required exact equality. The corrected rule tests the safe direction (archive Updated >= official release), and the second run passed.

**Disposition:** archive Updated is promoted to a candidate conservative availability bound for a wider audit, not a certified first-publication timestamp. If used, first eligible execution is the first regular market session after the archive Updated date; never same-day close. Strict historical PIT and alpha testing remain unauthorized pending a full post-launch archive census and review of any later corrections/migrations.
