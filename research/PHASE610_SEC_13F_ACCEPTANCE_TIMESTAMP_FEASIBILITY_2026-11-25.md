# Phase 610 — SEC 13F filing acceptance timestamp feasibility audit

<badge>PASS · 6/6 timestamps found</badge>

**Workflow:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533660436  
**Artifact:** https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533660436/artifacts/14985559685  
**Offline tests:** 3/3 passed.  
**Samples:** three 2018 and three 2026 filings selected from source-XML exception and control cases.

## Result

All six SEC filing-detail pages exposed an exact Accepted timestamp. In all six cases, the calendar date of Accepted matched the Filing Date displayed by SEC. The Accepted field is displayed in Eastern Time.

| Filing | Accepted (ET) | Filing date | Period of report |
|---|---|---|---|
| Marshall Wace, 2018 | 2018-03-29 12:43:00 | 2018-03-29 | 2017-12-31 |
| 2018 clean control | 2018-02-06 12:07:51 | 2018-02-06 | 2017-12-31 |
| OppenheimerFunds, 2018 | 2018-02-12 15:13:44 | 2018-02-12 | 2017-12-31 |
| Dakota Wealth, 2026 | 2026-08-26 11:11:54 | 2026-08-26 | 2025-09-30 |
| XXEC, 2026 | 2026-08-17 08:57:42 | 2026-08-17 | 2026-06-30 |
| Allspring, 2026 | 2026-08-13 10:27:24 | 2026-08-13 | 2026-06-30 |

Each page's HTML byte count and SHA-256 are retained in the artifact. The SEC filing-detail page is the source for the Accepted timestamp.

## Point-in-time rule

The exact EDGAR acceptance time is a necessary availability input, but it is not automatically the strategy's usable time. A conservative backtest clock should be:

1. accepted_at_et from the SEC filing-detail page.
2. The later actual collector/ingestion availability, once that is captured prospectively.
3. The first complete daily decision bar after that effective availability, using a validated XNYS calendar and the strategy's end-of-day execution convention.

Until a validated calendar and collector-latency history exist, the conservative fallback is to withhold the filing until after its filing date. Do not use the period-of-report date as the information-availability date.

## Limitations

This is a six-filing feasibility sample, not proof of 100% timestamp coverage for all 18,422 filings in the two full-quarter data sets. The next gate is a larger stratified sample across filing types, amendments, filing agents, weekends/holidays and after-hours submissions, followed by a validated XNYS session mapper and prospective collector timestamp.

No alpha, OOS, bootstrap, LOO or production eligibility is inferred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No data purchase or vendor contact; options budget USD 0.
