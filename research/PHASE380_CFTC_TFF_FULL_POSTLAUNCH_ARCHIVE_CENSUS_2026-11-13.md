# Phase 380 — CFTC TFF full post-launch archive Updated-date census

**Status:** implementation and deterministic tests added; hosted full census pending.  
**Parent:** Phase 379 archive Updated-date feasibility sample.  
**Scope:** reconstruct a conservative date-only availability panel for every post-launch TFF Futures Only report; no position data or returns.

## Correct first contemporaneous report date

CFTC announced the TFF report on 2010-07-22. The first static TFF Futures Only report is for positions as of 2010-07-20 and its archive page says Updated July 23, 2010. It contains no prior-week change values, consistent with the first report. Therefore:
- First contemporaneous TFF report date: 2010-07-20.
- First archived availability date observed: 2010-07-23.
- TFF dataset rows before 2010-07-20 are historical backcast, not contemporaneous TFF reports.
- This corrects the Phase 378 cutoff of 2010-07-22, which was the announcement date rather than the first report date. For Russell 23977A, the July 20, 2010 row (if present) should be treated as post-launch, not backcast. Russell 239742 contract-era conclusions are unchanged.

Official sources:
- TFF announcement, July 22, 2010: https://www.cftc.gov/PressRoom/PressReleases/5857-10
- First TFF report, positions as of July 20, Updated July 23: https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2010/futures/financial_lf072010.htm
- Explanatory notes on 2006 backcast: https://www.cftc.gov/sites/default/files/idc/groups/public/%40commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf

## Method

1. Retrieve every distinct report date from the CFTC TFF Futures Only dataset.
2. Separate report dates before 2010-07-20 (backcast) from the first contemporaneous report date onward.
3. Retrieve the corresponding static TFF Futures Only HTML archive page for every post-launch date.
4. Parse only the report heading date and final archive Updated date. Do not retain HTML or position values.
5. Verify page/report-date match, Updated date not earlier than report date, and exact/not-earlier consistency for the 23 official schedule crosschecks validated in Phase 379.
6. Reconcile CFTC dataset metadata before/after the census and report page coverage by year.

A date-only archive Updated field is treated as a conservative availability-bound candidate. If used later, the first eligible execution is the first regular market session after that date; never same-day close.

## Limitations

- CFTC does not formally define the archive Updated field as the first-publication timestamp.
- The official historical release-date list covers only the latest 13 months. Older archive-only pages do not have an independent release-date crosscheck.
- Archive Updated can be later than official publication (Phase 379 found one +2 day case), which is conservative but reduces timeliness.
- The CFTC TFF categories are broad business-purpose classifications, not verified informed-trader labels or beneficial-owner identities.
- Pre-2010-07-20 backcast categories remain excluded from primary feature research.
- No signal, alpha or backtest is authorized in this phase.

## Controls

Date-only metadata only; no raw HTML, positions or trader IDs retained. No forward returns, alpha, OOS, bootstrap, LOO or holdout use. No changes to F80, production, universe, capital, parameters or exposure.
