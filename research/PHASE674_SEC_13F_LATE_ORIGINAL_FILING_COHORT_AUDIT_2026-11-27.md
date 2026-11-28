# Phase 674 — SEC 13F late-original filing cohort and period/PIT separation

**Research date:** 2026-11-27 local (UTC execution: 2026-11-28)  
**Source capture:** Phase 614, run [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349)  
**Poll interval:** 2026-11-27 15:36:28Z to 23:44:25Z  
**Disposition:** metadata audit only; no holdings or signal admitted

## 1. Four new 13F-HR metadata observations

The latest Phase 614 scheduled poll completed all four feeds successfully, reached a full-snapshot end-of-feed boundary, found no cross-feed or within-feed duplicates, and persisted four new 13F-HR accessions.

| Accession | Feed-updated UTC | Filing date | Period of report | Current adjudication |
|---|---|---|---|---|
| 0002037081-26-000009 | 17:37:43Z | 2026-11-27 | 2025-12-31 | IronOak Wealth LLC; late original Q4 2025 |
| 0002037081-26-000012 | 18:29:56Z | 2026-11-27 | 2026-03-31 | IronOak Wealth LLC; late original Q1 2026 |
| 0002037081-26-000013 | 18:35:54Z | 2026-11-27 | 2026-06-30 | IronOak Wealth LLC; late original Q2 2026 |
| 0001717977-26-000005 | 19:32:31Z | 2026-11-27 | 2026-09-30 | AMS Capital Ltda; original Q3 2026 |

The IronOak filing periods are confirmed by the primary SEC submission XMLs for accessions -009, -012 and -013. The manager identity is confirmed as IronOak Wealth LLC (CIK 2037081) in the primary submissions for -012/-013 and its adjacent SEC filing history. The fourth accession is identified from its primary SEC submission XML as AMS Capital Ltda (CIK 1717977), period 2026-09-30, original 13F-HR holdings report, 15 information-table entries and cover-page tableValueTotal 289276.

The feed-updated timestamps above are the SEC Atom feed's recorded update values in our ledger. They are not substituted for the system's page-received or certified public-availability clock.

### AMS Capital unit-review flag

The primary SEC cover-page XML for AMS Capital's Q3 2026 filing reports `tableEntryTotal=15` and `tableValueTotal=289276`. Secondary holdings sources describe the same portfolio at approximately USD 289.3 million and report that earlier AMS Capital information-table values were interpreted as thousands. This is a **unit-review flag only**: the Phase 614 pipeline did not download the information-table XML, and no row-level primary-price check has been performed for accession `0001717977-26-000005`. Do not multiply or otherwise normalize its values until the Phase 671 detector is run on at least four eligible ordinary-share CUSIPs with contemporaneous prices.

## 2. Material finding: filing date is not reporting period

IronOak submitted three original 13F-HR reports on 2026-11-27 for earlier quarter ends:

| Reporting period | Standard SEC deadline benchmark | Filing date | Calendar days after benchmark |
|---|---|---|---:|
| 2025-12-31 (Q4 2025) | 2026-02-17 | 2026-11-27 | 283 |
| 2026-03-31 (Q1 2026) | 2026-05-15 | 2026-11-27 | 196 |
| 2026-06-30 (Q2 2026) | 2026-08-14 | 2026-11-27 | 105 |
| 2026-09-30 (Q3 2026, AMS Capital) | 2026-11-16 | 2026-11-27 | 11 |

The SEC Form 13F FAQ (Question 25, updated 2026-03-06) specifies the 45-day reporting rule and explicitly moves the Q4 2025 deadline to 2026-02-17 because February 14 fell on Saturday and February 16 was a federal holiday. The same FAQ lists 2026-05-15 and 2026-08-14 as the Q1 and Q2 deadlines. Relative to the standard SEC deadline benchmarks, the filing dates are 283, 196 and 105 calendar days later for IronOak's Q4 2025, Q1 2026 and Q2 2026 reports, and 11 days later for AMS Capital's Q3 2026 report. This is a calendar-lateness classification, not a legal conclusion that either filer was obligated to file each report by those dates: Form 13F's threshold-triggered initial filing obligation depends on when the manager first met the $100 million threshold, and that trigger history has not been adjudicated here.

These are original 13F-HR reports, not 13F-HR/A amendments. The Q3 2026 original report for the same filer (accession 0002037081-26-000003, period 2026-09-30) had already been filed on 2026-11-06. Consequently, a filing-date sort would make the older Q4 2025, Q1 2026 and Q2 2026 reports appear newer than the Q3 2026 portfolio snapshot.

**Modeling implication:** preserve at least two independent clocks for every 13F filing:
- `period_of_report`: the portfolio measurement date;
- `first_seen/public_availability`: when the report became observable to the strategy.

A late original filing must be added to the historical record only at its actual first-seen/public-availability time and must not replace a more recent reporting-period snapshot merely because its filing date is later. It is disclosure of a historical quarter-end portfolio, not evidence of a new trade on the filing date.

## 3. Capture and eligibility controls

Phase 614 run 46084129349 reported:
- 4 feeds successful; all feed watermarks and continuity gates passed;
- 4 new accessions and 4 bounded metadata observations;
- 0 filing XML/text downloads;
- 0 holdings rows downloaded;
- 0 public-availability certifications;
- 0 research-observation eligible holdings;
- 0 signal-eligible observations;
- 0 duplicate occurrences.

The SEC's bulk Form 13F datasets are quarterly rather than a real-time replacement for the EDGAR feed. The SEC page currently lists coverage through August 2026 and says the datasets are updated quarterly. This reinforces the need to use first-seen EDGAR metadata for disclosure timing and the filing's own cover page for the report period.

A secondary rendering of one IronOak filing shows a legacy “(thousands)” label. This is retained only as a unit-review flag. No ×1,000 correction is applied; the Phase 671 detector must evaluate primary information-table rows against contemporaneous prices before any normalization is considered.

## 4. Next work

1. Download and hash the primary submission and information-table XMLs for AMS Capital accession 0001717977-26-000005; run the Phase 671 unit detector without modifying as-filed values.
2. Download and hash the three IronOak primary submissions and information tables, then reconcile report periods, filing types, entry counts, values and units.
3. Add an explicit late-original filing class to the 13F event ledger, separate from restatement and new-holdings amendments.
4. Add a regression proving that the latest filing timestamp does not necessarily identify the latest reporting-period portfolio.
5. Keep every late filing's original first-seen timestamp and report period; never backfill the holdings into an earlier strategy information set.

No holdings were downloaded in this phase, no CUSIP/ticker mapping was attempted, and no signal, event study, return test, OOS test, bootstrap, LOO or holdout analysis was run.
