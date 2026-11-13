# Phase 380 — CFTC TFF full post-launch archive Updated-date census

**Status:** deterministic tests passed. First hosted retrieval stopped at the final metadata comparison because the HTTP Response object was not decoded as JSON; fixed in the current revision, hosted rerun pending.  
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

## Hosted full-census result — completed as a diagnostic, acceptance gate not passed

Run [43499455469](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469), date-only artifact [14074090576](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469/artifacts/14074090576).

- CFTC dataset contained 1,065 distinct report dates; 214 pre-first-report/backcast dates (2006-06-13–2010-07-13) and 851 post-launch report dates (2010-07-20–2026-11-03).
- Retrieved 846/851 static archive pages (99.4125%).
- Five pages failed retrieval/parsing: 2011-06-14, 2013-12-31, 2014-11-25, 2014-12-02 and 2019-12-24.
- One page-heading mismatch: requested report date 2018-09-25, but file financial_lf092518.htm says positions as of 2018-09-18.
- Two archive Updated fields predate their report dates: 2011-05-10 page says Updated 2010-05-13 (362 days earlier); 2012-10-16 page says Updated 2007-06-29 (1,936 days earlier). The 2011 page's stale footer is visible in the official HTML archive.
- Among the 23 recent official-schedule crosschecks, all 23 archive Updated dates were on/after official publication; 22 exact and one +2 days. This does not cure older archive anomalies.
- For successfully parsed pages, median archive lag was 3 days, p90 4 days, maximum 70 days (delayed 2025 catch-up reports).
- First TFF report check passed: positions as of 2010-07-20, archive Updated 2010-07-23.

**Decision:** do not promote archive Updated to a global historical PIT timestamp. A 99.4% page retrieval rate is useful, but missing pages, a misaligned heading and stale Updated fields require per-date exclusions/repair. For any future TFF study, only page-level records with exact report-heading match and a non-stale Updated date may be considered; strict PIT remains unauthorized until the affected dates and the archive field's semantics are resolved. The 2018-09-25 and 2019-12-24 Russell weeks require targeted review.

A separate implementation issue was also found: the Phase 380 workflow checked a non-existent summary key for the first-report gate (it should be first_report_page_gate). The source audit result above is unaffected; the key should be corrected before any rerun.

