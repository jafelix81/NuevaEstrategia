# Phase 637 — CFTC TFF prospective-vintage versus archive eligibility audit

**Audit cutoff:** 2026-11-26 09:42 UTC  
**Base:** `main` after Phase 636 (`33ed1ac563e6fafcf44f1d3b8c49cf10875bf0ef`)  
**Disposition:** reconcile the 3,043-row headline into its historical archive and prospective-vintage components. No signal, return test or strategy change.

## 1. Actions preflight

- Reviewed the latest 100 Actions runs, the complete scheduled-run page (74 scheduled runs), relevant jobs/logs/artifacts, current branches, open PRs and research files.
- At the latest explicit queries there were **0 in-progress and 0 queued** runs.
- The latest Phase 352 PR check, [run 45788991215](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991215), passed and uploaded artifact [15101941929](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991215/artifacts/15101941929). Its Phase 350 companion [run 45788991208](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45788991208) was PR CI; the live retrieval was not repeated.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Reconciliation of the CFTC 3,043-row count

The latest natural prospective-capture run, [Phase 384 run 45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), completed successfully with `NO_NEW_REPORTS_OR_REVISIONS_NO_STATE_CHANGE`. Its log reports 3,043 combined rows. Inspection of the immutable main-branch files reconciles that count as:

| Component | Rows | PIT / eligibility disposition |
|---|---:|---|
| `historical_backfill.csv` | 3,035 | All `UNVERIFIED_ARCHIVE_PROXY`; all signal-ineligible |
| Two append-only prospective event batches | 8 | Research-observation eligible; signal-ineligible |
| **Combined inventory** | **3,043** | Not 3,043 historical PIT observations |

The historical CSV blob is `4711abbaeeb6107d1cb8f50a7c2e3627373b6d29`; its baseline manifest SHA is `9e58849093f2144ce8cfbf1d3e5efc626a1aa250`. The manifest explicitly records 3,035 rows and `signal_eligible=false`.

Historical archive composition:
- Contract codes 124603 (DJIA), 13874A (E-mini S&P 500), and 209742 (Nasdaq Mini): 851 report-date rows each from 2010-07-20 through 2026-11-03.
- Contract code 239742 (Russell E-mini): 482 rows from 2017-08-15 through 2026-11-03.
- 851 distinct report dates; median and 90th-percentile spacing 7 days (maximum 8).
- The CSV contains derived 4-report changes and 52-report z-scores, but these remain archive-derived proxies and must not be used to initialize prospective features or as PIT labels.

## 3. The eight prospective observations

The two immutable event files are:
- `events/20261118T034457Z_run44232546204.json` (blob `c9b8c21e0d7f4a14a367261f7212a816de70a79b`): four contracts, report date 2026-11-10, first seen 2026-11-18 03:44:57 UTC.
- `events/20261121T031736Z_run44860341977.json` (blob `f6a1a3cab8789e3921a5f93fd8ede1d6f390fd88`): four contracts, report date 2026-11-17, first seen 2026-11-21 03:17:36 UTC.

All eight rows have:
- `research_observation_eligible=true`;
- `signal_eligible=false`;
- `trade_signal_generated=false`;
- earliest research use defined as the first regular equity session after the first-seen upper bound.

These are **two time clusters**, not eight independent observations: all four correlated equity-index futures are captured in each report batch. Report date is the position snapshot date, not the knowledge/availability date. No exact public-release timestamp is certified.

The latest 2026-11-26 run added no new report or revision; the append-only prospective event inventory remains at two report dates / eight contract observations.

## 4. Research interpretation and preregistered next gate

CFTC TFF is a candidate **broad-market regime covariate**, not stock-level institutional flow. Trader categories (dealer, asset manager, leveraged money, other reportables and non-reportables) are hypotheses about positioning, not labels for informed or superior investors.

A future prospective-only study may examine:
- net positions scaled by open interest for leveraged money, asset managers and dealers;
- changes across four report dates and, only after sufficient prospective history, a 52-report rolling z-score;
- leveraged-money versus asset-manager divergence as a separate, preregistered regime feature.

No archive-derived feature may seed a prospective rolling statistic. Do not treat the four index contracts as independent samples. Align each report only after its first-seen upper bound and the next eligible XNYS session. Compare a pre-registered regime overlay against frozen F80 at identical exposure and costs, with chronological splits, time-block bootstrap and time-block LOO. The current two report dates are insufficient for any predictive or economic test.

## 5. SEC 13F post-merge schedule check

Phase 635 / PR #243 is merged to `main` at `11c2f1acb578784456bc30f82f131ed8fb858c32`; its 37/37 PR tests passed. The last scheduled Phase 614 run, [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501), predates that merge and failed before any SEC request because the secret was empty. The corrected collector now falls back to the already-declared Phase 401 project contact.

No post-merge natural Phase 614 run was visible in the scheduled-run inventory at the 09:41:40 UTC check. The connected read surface does not expose the workflow's administrative enabled/disabled state, so the absence of a run does not establish that it is disabled. Do not manually dispatch a duplicate poll; the next natural run must validate the fallback and all four feeds.

## 6. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No alpha, event study, OOS, bootstrap or LOO result was generated.
- No change to universe, exposure, costs, parameters, capital, holdout or holding-period policy.
- Options-data budget remains USD 0; no vendor contact, quote request or purchase.
- FINRA Reg SHO remains quarantined for BCPC/TPC row-grain conflicts.
- SEC 13D/G remains a lineage/identity feasibility result only: 43/44 parents retrieved, five CUSIP mismatches and six missing parent CUSIPs remain quarantined; no first-publication clock or event study is admitted.
