# Phase 641 — Smart Money post-merge capture and operational adjudication

**Audit cutoff:** 2026-11-26 11:54 UTC  
**Main HEAD at preflight:** `ca01835aac5f0fe0766582bb52d15a09f3b08d78`  
**Disposition:** the latest successful Form 4 capture is useful new prospective data, but it predates the Phase 626 merge. The latest Form 144 and 13F captures also predate their latest relevant fixes. No post-merge natural validation is visible for the three SEC collectors. This is an observed schedule-delivery gap, not proof that workflows are administratively disabled. No signal or strategy change.

## 1. Actions preflight

Queried the repository-wide Actions API before any write:

- Total runs: **8,347**.
- Latest 100: **71 success / 17 failure / 12 cancelled**.
- Active, queued, waiting or requested among the latest 100: **0**.
- Latest run in the inventory: [45806279188](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45806279188), a Phase 403 pull-request check at 10:58:38 UTC. It passed offline regressions; live capture was skipped.
- No workflow was dispatched, rerun, cancelled or duplicated.

Relevant latest scheduled runs (all jobs completed):

| Line | Latest scheduled run | Result | Post-merge status |
|---|---:|---|---|
| SEC Form 4 / Phase 476 | [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509), 05:08:18 UTC | Success | **Pre-merge** of PR #240 (merged 06:40:25 UTC) |
| SEC Form 144 / Phase 403 | [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670), 03:11:54 UTC | Success | **Pre-merge** of PRs #244 and #245 (10:53:27 / 10:59:43 UTC) |
| SEC 13F / Phase 614 | [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501), 03:46:56 UTC | Failure before SEC request | **Pre-merge** of PR #243 (08:49:05 UTC) |
| CFTC TFF / Phase 384 | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), 04:12:21 UTC | Success; no new report/revision | Prospective ledger unchanged |
| FINRA Reg SHO / Phase 469 | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648), 04:16:05 UTC | Workflow success; all eight files rejected | No accepted data |

The three SEC workflows remain present on `main` with their existing schedules: Form 4 at minute 17 on weekdays, Form 144 at minute 47 hourly, and 13F at minute 41 on weekdays. The connector does not expose the administrative enabled/disabled state or repository-level scheduled-workflow permission. Do not infer disabled status from missing events and do not change cron cadence without an authorized maintainer check.

## 2. SEC Form 4 — new natural capture, still non-signal

Run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) completed both jobs successfully and persisted an append-only update to `main` (run commit `2654f57`).

The live poll reported:

- 90 new Form 4 accessions and 90 canonical issuer events.
- 192 entity observations: 90 issuer rows and 102 reporting-person rows.
- Both Form 4 and Form 4/A feeds passed; both prior watermarks were found.
- Zero incomplete-poll candidates suppressed; zero path/entity-CIK mismatches.
- Exact public availability remains uncertified; signal eligibility remains zero.

Bounded enrichment in the same run:

- 10 accessions parsed into 37 structured transaction rows.
- 66 transaction-linked footnote references plus 26 additional references.
- 10 filing-level owner rows appended.
- Crosswalk: 11 descriptive rows, nine matched Form 4 accessions, 10 proposed-sale matches and one prior-sale match; **zero signal-eligible matches**.
- 3,414 bounded transaction-detail accessions remain.

### Phase 626 post-merge validation is still pending

PR [#240](https://github.com/jafelix81/NuevaEstrategia/pull/240) merged at 06:40:25 UTC as `b43c56297ec19fbde03cb38b11ae025ad5b21aeb`. The 05:08 run predates that merge, so it cannot validate the new `entity_duplicate_audit.csv` sidecar.

An independent offline reparse of the 192 entity rows from run 45759597509, using Phase 626's strict feed/accession/role/CIK/normalized-name key, finds **zero duplicate keys within that run**. This is a diagnostic reparse, not a production sidecar result. The persisted current-run rows contain 90 distinct issuer entities and 102 reporting entities; repeated observations at prior-poll watermarks are not treated as same-poll duplicate entities.

The next natural Form 4 capture after PR #240 must create the sidecar and reconcile its duplicate counts against the live Atom page observations.

## 3. SEC Form 144 — latest capture predates timestamp fixes

Run [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670) succeeded:

- 105 feed observations.
- 82 new accessions parsed.
- 534 structured detail rows appended.
- 188 bounded detail backfills remained.
- Zero parse errors and zero source-hash mismatches.
- Zero public-availability-certified filings and zero signal-eligible filings.

This run predates PR #244 (Phase 638) and PR #245 (Phase 639). Therefore, it does not validate the new distinction between expected initial-baseline intervals and malformed intervals, nor the rejection of timezone-naive Atom timestamps. The next natural capture must validate both fixes; no manual capture was launched.

Form 144 remains a proposed-sale notice, not proof of execution. The 10b5-1, sell-to-cover, trust and amendment controls remain descriptive/negative controls, not directional signals.

## 4. SEC 13F — fallback integrated; first natural validation pending

Run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) failed because `SEC_USER_AGENT` was empty. The failure occurred on commit `6143b535`, before the collector attempted an SEC request.

PR [#243](https://github.com/jafelix81/NuevaEstrategia/pull/243) merged at 08:49:05 UTC as `11c2f1ac`. Current code prefers the repository secret and falls back to the established Phase 401 project contact; it still fails closed if both are invalid. The next natural scheduled poll is required to validate this fallback. No secret value was read or changed, and no SEC request was made by the failed run.

The 13F holdings/manager/security graph and historical availability gates remain separate from the prospective feed baseline. No holdings feature is admitted.

## 5. Other source dispositions

- **FINRA Reg SHO:** latest run received eight HTTP-200 files, but all eight were rejected by the fail-closed duplicate-symbol gate. BCPC and TPC each recur; 16 extra rows were diagnosed. No raw volume values or first-seen events were persisted. Keep issue [#214](https://github.com/jafelix81/NuevaEstrategia/issues/214) open; do not sum or drop rows.
- **FINRA Phase 20C:** same-day-close implementation remains NO-GO for look-ahead. The next-session-open hypothesis remains untested because actual first-receipt labels, a complete effective-dated 335-name price panel and terminal corporate-action returns are still missing. Keep the final six holdout signals sealed.
- **CFTC TFF:** 3,043 total rows remain 3,035 unverified historical archive proxies plus eight prospectively observed rows across only two report-date clusters. The latest capture found no new report or revision. Continue collection only; no 52-report warm-up or signal test is available.
- **SEC MIDAS:** retain as a public market-structure/risk-context candidate, not institutional identity or dark-pool flow. The official SEC catalog lists 59 quarterly files from 2012 Q1 through 2026 Q3, but per-quarter first-publication timestamps, ZIP payload integrity and effective-dated F80 identity coverage remain unverified. See [Phase 534](PHASE534_SEC_MIDAS_SECURITY_METRICS_SEMANTICS_AND_PIT_AUDIT_2026-11-20.md) and [Phase 532](PHASE532_SEC_MIDAS_OFFICIAL_QUARTERLY_CATALOG_RECONCILIATION_2026-11-20.md).
- **Options:** Cboe Open-Close remains a conditional prospective opening-position-side candidate; ThetaData/OPRA is a separate aggressor-estimation companion. IV/skew remains demoted to a borrow-fee/friction control. No license, sample, vendor contact or purchase was initiated; authorized budget remains USD 0.
- **SEC 13D/G:** 43/44 parent documents remain recovered; five CUSIP mismatches and six missing parent CUSIPs remain quarantined. PR #37 is Draft and heavily diverged from main; no wholesale merge.

## 6. Repository/branch disposition

Main HEAD before this checkpoint: `ca01835aac5f0fe0766582bb52d15a09f3b08d78`.

Validated merges:
- PR #240 / Phase 626 — Form 4 entity duplicate audit.
- PR #243 / Phase 635 — SEC 13F User-Agent fallback.
- PR #244 / Phase 638 — Form 144 baseline interval classification.
- PR #245 / Phase 639 — reject timezone-naive Form 144 Atom timestamps.

Do not merge stale research branches wholesale. Current comparisons against main include:
- `phase99-broad-pit-universe-charter`: 580 ahead / 558 behind.
- `phase231-cboe-option-quotes-full-row-reparse`: 906 ahead / 558 behind.
- `phase350-sec-13dg-explicit-parent-retrieval`: 292 ahead / 572 behind.
- `phase613-sec-13f-legal-dissemination-floor`: 137 ahead / 594 behind.

Port or rebuild only narrowly scoped, independently reviewed changes on current main.

## 7. Research and strategy disposition

- New signals admitted: **0**.
- Incremental alpha versus frozen LTM/F80 demonstrated: **none**.
- New valid OOS, bootstrap or LOO evidence: **0**.
- No return test or final-holdout access.
- No changes to universe, parameters, exposure, costs, holding-period policy, capital or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next gates:** obtain an authorized maintainer check of scheduled-workflow enablement; wait for natural post-merge Form 4, Form 144 and 13F captures; keep FINRA data quarantined until the row-grain/security identity is authoritatively reconciled; continue CFTC prospective accumulation. No manual dispatch, duplicate poll, paid data or vendor request was made.
