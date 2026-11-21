# Phase 512 — CFTC TFF archive Updated-date publication-conflict audit

**Audit date:** 2026-11-20 UTC  
**Disposition:** Phase 380's archive `Updated` field is not a conservative historical publication bound. At least six report dates that pass Phase 380's weak page checks have archive Updated dates earlier than the CFTC's normal/known publication date. Historical CFTC TFF remains ineligible for strict PIT backtests unless each report is reconciled to an official publication date or a separately proven conservative receipt bound.

## 1. Why this follow-up was necessary

Phase 380's full post-launch census (run [43499455469](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469), artifact [14074090576](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469/artifacts/14074090576)) retrieved 846 of 851 static archive pages. It rejected five retrieval failures, one heading mismatch, and two pages whose archive Updated date predated the report date.

However, its page-level test only required:

- successful retrieval;
- exact report-heading match; and
- `archive_updated_date >= report_date`.

That rule is insufficient. The CFTC's own documentation says TFF/COT reports are generally published Friday at 3:30 p.m. ET for positions from the preceding Tuesday, subject to holiday changes. A static archive Updated date can therefore be later than the report date but still precede publication.

## 2. Reproducible artifact census

The Phase 380 artifact ZIP was downloaded and hashed during this audit:

- Run: `43499455469`
- Artifact: `14074090576`
- ZIP SHA-256: `f74850aed35d7ed885f33de892895d6bbc755edbd7d4546340427d28468ceb9b`
- Nested `summary.json` SHA-256: `36c75bb5fd5ea4d47fe6ec4f5add84fb81dd8e9c6b3a884691fd20ba666f94f0`
- Report-date population: 1,065 total; 214 pre-first-contemporaneous-report/backcast; 851 post-launch.
- Static archive pages: 846/851 retrieved.
- Among retrieved pages: one report-heading mismatch and two Updated dates earlier than the report date.
- **843 pages pass Phase 380's weak page-level rule.**

A separate full-dataset coverage audit completed on 2026-11-20 (run [44648241623](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44648241623), artifact [14589078987](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44648241623/artifacts/14589078987)) reports 47,420 rows, 90 fields, and 1,066 distinct report dates through 2026-11-10. This does not contradict the Phase 380 archive census: that earlier census ended at 2026-11-03 and contained 1,065 report dates, so the one-date difference is the newer weekly report, not a missing historical week. The newer dataset coverage result does not repair the archive Updated-date PIT failure.

A second test compared those 843 dates against the CFTC's stated normal Friday release convention and its official historical announcements. Six pages have Updated dates earlier than the normal/known publication date:

| TFF report date | Archive Updated | Expected/known publication date | Conflict |
|---|---|---|---|
| 2012-07-03 | 2012-07-03 | 2012-07-06 | Updated is 3 calendar days early |
| 2012-09-04 | 2012-09-04 | 2012-09-07 | Updated is 3 calendar days early |
| 2015-06-16 | 2015-06-16 | 2015-06-19 | Updated is 3 calendar days early |
| 2018-12-18 | 2018-12-20 | 2018-12-21 | Updated is 1 calendar day early |
| 2021-03-23 | 2021-03-25 | 2021-03-26 | Updated is 1 calendar day early |
| 2021-05-04 | 2021-05-06 | 2021-05-07 | Updated is 1 calendar day early |

The 2015 case is particularly clear: CFTC's historical special-announcements page says the report for June 16, 2015 had already been published with formatting problems and that a revised report would be released June 23. Its archive page says Updated June 16, which cannot be used as the public-availability bound. The 2018 case is also inconsistent with the CFTC's notice that the publication date remained Friday as usual. The other four conflict with the CFTC's standard Friday schedule and have no relevant Friday-holiday exception.

A seventh page, report date 2014-12-30 / Updated 2015-01-03, is left **unresolved and excluded from the six-count** because the holiday-adjusted publication date for that exact report was not independently established in this audit.

## 3. Consequence for point-in-time eligibility

The Phase 380 rule "first regular market session after archive Updated" can place a historical TFF observation before it was published. For example, the 2012-07-03 row would become eligible after the July 4 market holiday, while the normal CFTC publication was Friday July 6. This is direct look-ahead if the feature is joined to earlier sessions.

Therefore:

- Do not use archive Updated as a global PIT timestamp.
- Do not use the 843 weakly valid pages as a historical feature panel merely because their headings match and Updated is not earlier than report date.
- Do not forward-fill missing or delayed reports.
- Keep the five retrieval failures, heading mismatch, two stale-date pages, six publication conflicts, and the unresolved 2014-12-30 page excluded until independently repaired.
- Use official CFTC publication dates where explicitly documented; for other historical weeks, require a reliable archived release schedule or an actual first-receipt ledger.
- The prospective CFTC first-receipt collector remains the only unambiguous route for strict PIT until a historical release-date panel is reconstructed.

## 4. Source semantics remain limited

TFF categories (Dealer, Asset Manager, Leveraged Money, Other Reportables, Nonreportables) are broad business-purpose classifications, not verified informed-trader identities. CFTC says the classification is based on predominant business purpose and that it does not know the specific reason for a trader's positions. Treat any crowding or risk-regime relationship as a hypothesis, not "smart money."

CFTC also documents delayed and corrected releases, including the 2023 ION incident and the 2025 federal-appropriations lapse. A report date is a position snapshot, not an availability date; later revisions must not overwrite what was knowable at the original release.

## 5. Research decision

**Historical TFF Updated-date PIT gate: FAIL.**  
**Historical TFF alpha/backtest authorization: NO.**  
**Prospective first-receipt collection: CONTINUE.**

The source may still be useful as a broad-market positioning or crowding-risk overlay, not a stock-specific flow signal. Any future test must compare it incrementally against frozen LTM/F80, use the actual first eligible session after verified publication, and keep the F80 holdout untouched.

No position rows, trader IDs, raw HTML, or vendor data were added to this repository. No returns, event study, backtest, OOS, bootstrap, LOO, or holdout test was run. No workflow was dispatched or duplicated. `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.

## Official references

- [CFTC About the COT Reports — normal Friday 3:30 p.m. ET publication and Tuesday position date](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm)
- [CFTC Historical Special Announcements — 2015, 2018, 2021 publication delays and corrections](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm)
- [CFTC 2015 special-announcement detail](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm)
- [Phase 380 full post-launch archive census](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469)
- [Phase 380 artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43499455469/artifacts/14074090576)
