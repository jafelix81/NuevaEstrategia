# Phase 645 — CFTC Russell prospective-vintage and release-clock reconciliation

**Audit cutoff:** 2026-11-26 17:45 UTC  
**Main HEAD at audit start:** `e377c25e35f37d180ad860f889f4283127eb7ae6`  
**Disposition:** reconcile the two prospective CFTC report vintages with the narrow Russell E-mini archive candidate; retain both as research observations only. No signal, return test or F80 change.

## 1. Why this audit was needed

Phase 644 retained the post-2017 Russell E-mini TFF code `239742` as a conditional macro-positioning candidate, while keeping the broad CFTC archive outside strict PIT training. The Phase 383 archive panel ended at report date 2026-11-03. The mainline Phase 384 prospective stream has since recorded two later report dates, 2026-11-10 and 2026-11-17.

This audit reconciles the historical panel, the immutable prospective event files, the official CFTC release calendar and the latest Actions capture. It does not promote archive dates into first-publication timestamps.

## 2. Prospective first-receipt reconciliation

The two immutable event files are:

- [2026-11-10 vintage — run 44232546204](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/data/cftc_tff_prospective/events/20261118T034457Z_run44232546204.json)
- [2026-11-17 vintage — run 44860341977](https://github.com/jafelix81/NuevaEstrategia/blob/main/research/data/cftc_tff_prospective/events/20261121T031736Z_run44860341977.json)

Each event file contains one observation for each of four index-futures contracts. The Russell E-mini row is code `239742`.

| Position report date | CFTC scheduled release | Pipeline first receipt (UTC) | Receipt after scheduled release | First eligible XNYS session |
|---|---|---|---:|---|
| 2026-11-10 | 2026-11-16 15:30 ET | 2026-11-18 03:44:57Z | 31h 14m 57s | 2026-11-18 |
| 2026-11-17 | 2026-11-20 15:30 ET | 2026-11-21 03:17:36Z | 6h 47m 36s | 2026-11-23 |

The scheduled dates are consistent with the CFTC's official 2026 release calendar: November 16 is the Veterans Day-delayed release and November 20 is the next release. The current CFTC TFF Futures Only dataset reports a last data update of November 20 and the current Futures Only report is dated November 17. See the official [COT release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm), [TFF Futures Only dataset](https://publicreporting.cftc.gov/Commitments-of-Traders/TFF-Futures-Only/gpe5-46if) and [current Futures Only report](https://www.cftc.gov/dea/futures/financial_lf.htm).

**Clock interpretation:** `first_seen_utc` is the first receipt by this project's scheduled collector, not the exact instant the information first became public. Both observations were received after the scheduled release; the first was substantially delayed relative to the scheduled release. Use the pipeline receipt as the conservative knowledge upper bound and the next regular XNYS session as the earliest daily-equity research session. Never backdate to the Tuesday position date or scheduled release time.

## 3. Russell E-mini positioning: two-vintage arithmetic check

The event payloads were independently recomputed as `(category long - category short) / open_interest_all`. Spreading positions are excluded from directional net.

| Russell E-mini | 2026-11-10 | 2026-11-17 | Change |
|---|---:|---:|---:|
| Asset Manager net / OI | +4.4630% | +6.6715% | +2.2085 pp |
| Dealer net / OI | +5.0532% | +2.7114% | -2.3418 pp |
| Leveraged Money net / OI | -10.0843% | -9.2126% | +0.8717 pp |
| Open interest | 440,576 | 459,730 | +4.3475% |

This is a two-observation arithmetic check, not a time-series result. The category changes do not form a single unambiguous directional or risk-on/risk-off pattern. The labels are regulatory business-purpose classifications, not verified informed-investor identities or evidence of superior skill.

## 4. Historical archive and prospective stream remain separate

Phase 383's immutable artifact [14074056247](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43500752903/artifacts/14074056247) contains the date-only audit for 482 post-2017 Russell E-mini report-date/code rows:

- 480/482 archive pages valid (99.5851%).
- 2018-09-25 remains excluded because the archive page heading is 2018-09-18.
- 2019-12-24 remains excluded because the expected archive page returned 404.
- Valid-page archive `Updated` lag: median 3 days, p90 6 days, maximum 50 days.
- 23/23 official-schedule cross-checks were not earlier than the official publication date.

The Phase 383 panel ends at 2026-11-03. The two later prospective report dates are separate first-receipt observations; they do not retroactively validate the archive pages or remove the two historical exclusions.

Current repository reconciliation:

| Component | Rows | Disposition |
|---|---:|---|
| Historical CFTC archive | 3,035 | `UNVERIFIED_ARCHIVE_PROXY`; excluded from PIT features and returns |
| Prospective first-seen observations | 8 | Four contracts × two report-date clusters; research-observation eligible only |
| Total persisted CFTC rows | 3,043 | No signal-eligible rows |

For Russell code `239742`, the historical archive has 482 report-date rows through 2026-11-03 and the two later prospective events extend the API history to 484 rows through 2026-11-17. The two known archive exceptions remain missing from any admissible historical feature panel. No zero-fill, forward-fill or report-date interpolation is allowed.

## 5. Latest operational check

- Latest Phase 384 scheduled capture: [run 45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), 2026-11-26 04:12:21 UTC; successful, `NO_NEW_REPORTS_OR_REVISIONS_NO_STATE_CHANGE`, 3,043 rows, zero signal-eligible historical rows.
- Latest SEC Form 4: [run 45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), successful at 15:23 UTC; zero new accessions, 10 bounded detail/owner backfill accessions processed, zero signal-eligible rows.
- Latest SEC 13F: [run 45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), successful at 14:29 UTC; 29 initial-baseline accessions, all without a lower first-seen bound, zero holdings downloaded and zero eligible observations.
- Latest SEC Form 144: [run 45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431), successful at 13:13 UTC; 825 accessions / 5,495 detail rows, 807 bounded intervals, 18 initial-baseline intervals, zero public-availability-certified or signal-eligible filings.
- Latest FINRA Reg SHO: [run 45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648); eight HTTP-200 files, all eight rejected by the BCPC/TPC consolidated-symbol row-grain gate; zero market rows admitted.
- Actions API at cutoff: 8,350 total runs; latest 100 = 71 success / 17 failure / 12 cancelled; zero queued or in-progress runs. No manual dispatch or rerun was performed.

The next CFTC release on the official calendar is Monday 2026-11-30 at 3:30 p.m. ET, following the Thanksgiving delay. Phase 384 already polls weekdays after the scheduled release; retain actual first receipt and do not launch a manual poll.

## 6. Research disposition

1. Keep the 480-page post-2017 Russell archive subpanel as a **conditional archive-derived macro-positioning candidate**, not certified strict PIT.
2. Keep the two newer Russell observations as prospective research observations with actual collector first-receipt clocks.
3. Do not run a Russell return or alpha test yet. Two prospective report vintages cannot support persistence, percentile, dose-response, OOS, bootstrap or LOO inference.
4. Do not insert Russell into Phase 387's preregistered ES/NQ hypothesis. Any Russell-specific downside-risk or small-cap regime study requires its own preregistration before outcomes are inspected.
5. Continue prospective capture. For Phase 387, the fixed 52-prior-report warm-up and 150-observation evaluation requirements remain unchanged; the current two report-date clusters are far below those gates.
6. Treat CFTC categories as hypotheses about aggregate positioning, not "smart money" ground truth.

## Frozen controls

- Signals admitted: **0**.
- Incremental alpha vs LTM/F80: **none demonstrated**.
- New OOS / bootstrap / LOO: **0**.
- Holdout remains sealed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, parameter, capital, exposure, cost or holding-period change.
- Options-data budget remains **USD 0**.
