# Phase 651 — OCC options account-type volume source feasibility audit

**Audit cutoff:** 2026-11-26 21:55 UTC  
**Base main HEAD:** `db332ddb2ee271abca7f3c38fd2d3475b297b767`  
**Disposition:** **NO-GO for automated strategy ingestion under the currently published OCC Website Terms.** OCC exposes potentially useful daily options volume by Customer / Firm / Market Maker account type, but its terms prohibit automated systems from accessing the Services/Data and restrict reproduction/exploitation. The public query pages also state only a rolling 24-month availability window. No data endpoint was queried, no sample was downloaded, no quote or license was requested, and no provider was contacted.

## 1. Required preflight: Actions, jobs, artifacts, branches and research state

Before this source audit, inspected the current Actions run inventory, schedule-event inventory, relevant jobs/logs/artifacts, current main research files, source-state sidecars, open PR state and the prior Phase 650 report.

- Actions total: **8,355**.
- Latest 100: **71 success / 18 failure / 11 cancelled**.
- Queued/requested/waiting/in-progress: **0**.
- Latest main HEAD before this report: `db332ddb2ee271abca7f3c38fd2d3475b297b767`.
- PR [#247](https://github.com/jafelix81/NuevaEstrategia/pull/247) is merged as `c7379f42ffffd631e8ce1bc3b9b3261871e3480d`. Its PR Actions run [45895296971](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45895296971) passed 62/62 offline tests. The live-capture job was skipped on the pull-request event. The first natural post-merge FINRA capture has not yet occurred.
- No workflow was dispatched, rerun, cancelled or duplicated.

### Latest natural captures inspected

| Source | Run / UTC | Job result | Artifact inspected | Key disposition |
|---|---|---|---|---|
| SEC Form 4 | [45848689364](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364), 15:23:55 | offline + live success | [15132214284](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45848689364/artifacts/15132214284) | 10-accession structured backfill appended 23 detail rows; footnote backfill appended 24 references; crosswalk 12 rows, 10 matched accessions, 11 proposed-sale rows, 1 prior-sale row, 7 multi-owner accessions quarantined, 2 unresolved Form 144 acceptance clocks, 0 signal-eligible matches. Duplicate audit contained two prior-watermark observations and zero exact duplicates. |
| SEC 13F | [45839454376](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376), 14:29:01 | offline + live success | [15125664876](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45839454376/artifacts/15125664876) | 29 accessions across four feeds; all four feed states were initial baselines with no lower bound. No holdings/XML downloaded; 0 research-eligible and 0 signal-eligible observations. |
| SEC Form 144 | [45827105431](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431), 13:13:48 | offline + live success | [15119964060](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45827105431/artifacts/15119964060) | 53 feed observations, 0 new accessions, 52 detail rows appended; 825 accessions / 5,495 detail rows; 178 detailed backfills remain; 807 bounded intervals and 18 initial baselines; 0 exact public-availability certifications and 0 signal-eligible rows. |
| CFTC TFF | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), 04:12:21 | capture success | [15086462804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471/artifacts/15086462804) | 3,043 rows total; Russell contract 239742 has 484 archive rows through 2026-11-17; no new reports/revisions; no forward outcomes or signal. |
| FINRA Reg SHO | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), 04:16:05 | offline + live success | [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251) | Pre-Phase-650 parser: 8 HTTP-200 files, 8 rejected, 16 duplicate symbol/date groups, BCPC/TPC quarantined, 0 first-seen/eligible events. This is not a post-merge parser validation. |

The 13F, Form 4 and Form 144 workflows have successful natural runs on 26 November, so they were active at those times. No later scheduled runs for these three sources were visible by 21:55 UTC. The run history therefore shows intermittent schedule delivery, not proof of administrative disablement. The connector cannot inspect the repository's administrative workflow-enabled setting. Existing operational tracking remains in Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194).

## 2. OCC source examined

Official OCC pages expose two potentially relevant report families:

1. **Volume by Account Type** — daily/weekly/monthly/yearly/last-12-month reports for options or futures, with Customer, Firm and Market Maker volume categories.
2. **Options Volume Query** — a contract/series-level daily query with quantity, underlying symbol, option symbol, account type, call/put, exchange, activity date and series/contract date.

The published record layouts do **not** provide buyer/seller aggressor side, opening/closing designation, trade price, bid/ask, implied volatility, delta or an open-interest field in the volume-query row. Customer/Firm/Market Maker are account-origin classifications, not named institutions or verified informed traders.

OCC's public Volume Query and Volume by Account Type pages state that data are available for the **past 24 months**. Batch-processing documentation lists daily, weekly, monthly, rolling-year and yearly report types, but does not establish a reproducible all-history daily archive beyond the stated public 24-month window. A yearly report parameter is not evidence of historical availability outside that window.

### Official source documentation

- OCC Volume Query: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-query
- OCC Volume by Account Type: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-by-account-type
- OCC Volume Query batch parameters: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-query-batch-processing
- OCC Volume by Account Type batch parameters: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-by-account-type-download-batch-processing
- OCC Options Volume Query record layout: https://www.theocc.com/getcontentasset/50cf357d-6ec6-436e-a96b-c4710313a472/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/options-volume-query-record-layout.pdf
- OCC account-type volume record layout: https://www.theocc.com/getcontentasset/f7517699-a966-4c84-bcf6-acd9fba381dd/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/onn-volume-vol-only-no-totals-record-layout.pdf
- OCC Website Terms and Conditions (updated 2025-02-05): https://www.theocc.com/specialpages/legal/terms-and-conditions

## 3. Rights and automation gate — decisive failure

The OCC Website Terms apply to its Services and Data. They state that the Services/Data may not be reproduced, duplicated, copied, sold, resold or otherwise exploited for commercial purposes. More decisively for this GitHub Actions project, the user obligations prohibit use of an automated system, including robots, spiders or offline readers, to access the Website/Services.

The proposed collector would be an automated system. Therefore, the public web/batch endpoints are **not admitted** to this automated research workflow under the currently published terms. This is not cured by the fact that the pages are publicly viewable or that the batch URLs are documented.

No attempt was made to call OCC endpoints or test historical downloads. No account, key, sample, trial, quote, license request or vendor contact was initiated. The existing options-data authorization remains **USD 0** and does not authorize purchases or vendor outreach.

## 4. Research value if rights were ever cleared

OCC's data could support hypotheses such as:
- Customer versus Firm/Market-Maker volume share by underlying.
- Customer call/put composition by series and exchange.
- Abnormal changes in account-type mix relative to the same underlying's own history.

However, these would be **account-origin/volume-composition hypotheses**, not institutional accumulation or directional smart-money flow. The published record layout lacks buyer/seller side and open/close flags. A 24-month public history is also weak for robust regime coverage and independent long-horizon OOS validation. The public documentation does not establish the exact first-publication timestamp or correction/revision history needed for a strict historical PIT panel.

Even with future written rights, this source would require a separate feasibility review for:
- lawful automated access and retention;
- actual daily-history depth and historical revision behavior;
- exact publication/first-receipt timestamps;
- complete underlying and series coverage against an effective-dated universe;
- corporate-action and option-series identity continuity;
- a defensible signal definition that does not equate Customer or Firm with informed institutional activity.

No feature or backtest was created.

## 5. Source disposition

| Source | Potential information | Main blocker | Decision |
|---|---|---|---|
| OCC Volume Query | Series-level volume by account type, call/put, exchange | Automated access prohibited by current terms; 24-month public window; no side/open-close; no proven PIT clock | **NO-GO / RIGHTS_BLOCKED** |
| OCC Volume by Account Type | Underlying-level Customer/Firm/Market Maker mix | Same rights and history limitations; no directional trade side | **NO-GO / RIGHTS_BLOCKED** |
| Cboe historical options volume | Aggregate exchange volume by symbol/product | Existing Phase 649 rights gate; not account-origin or full quote/IV/OI panel | Not admitted |
| Cboe DataShop options quotes/EOD | Potential IV/Greeks/OI and quote/trade history | Paid/licensed; no quote or purchase authorized | Parked |

OCC is archived as a potentially interesting but currently infeasible source. Do not create an OCC collector unless explicit written rights permit automated research use and the user separately authorizes any quote/purchase or vendor contact.

## 6. Strategy and validation controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen.
- Incremental alpha: none demonstrated.
- New valid OOS / bootstrap / LOO: none.
- Final holdout: untouched.
- No universe, feature, parameter, cost, exposure, capital or holding-period change.
- No option data acquired; budget USD 0.

## 7. Next actions

1. Await the next **natural** FINRA Reg SHO scheduled capture to validate Phase 650's partial-symbol quarantine parser. Do not manually backfill or promote the eight old invalid files.
2. Continue prospective SEC 13F capture. The 29 initial-baseline accessions remain unbounded and ineligible; only new accessions first seen between two complete successful snapshots can receive a bounded interval.
3. Continue Form 4/144 descriptive enrichment and preserve multi-owner, 10b5-1, tax/withholding, proposed-sale, identity and acceptance-clock quarantines.
4. Keep CFTC Russell feature construction outcome-blind until a lawful, reproducible price/control source is established.
5. Keep OCC, Cboe and other options data parked under the current rights/budget constraints.

**No alpha claim and no strategy promotion resulted from Phase 651.**
