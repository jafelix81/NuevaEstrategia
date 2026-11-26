# Phase 630 — SEC 13F access-guard merge and Form 144 post-capture refresh

**Audit cutoff:** 2026-11-26 03:33 UTC  
**Main HEAD:** `d81c2c65de8853c46c3987570720bbe8d274b626`  
**Disposition:** Phase 629 transport guard merged; Form 144 prospective capture and descriptive 10b5-1 refresh completed. No new alpha, return test, OOS result or strategy change.

## 1. Actions preflight and merge verification

- Repository Actions API: 8,308 total runs; latest 100 = 70 success / 19 failure / 11 cancelled; zero queued or in progress at cutoff.
- Latest natural capture: Form 144 run [45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670), created 2026-11-26 03:11:54 UTC; both `offline-regression` and `live-capture` succeeded.
- Artifacts [15083886905](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670/artifacts/15083886905) and [15083916912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670/artifacts/15083916912) are unexpired. The post-capture Phase 549 artifact 15083916912 was downloaded and inspected.
- PR [#242](https://github.com/jafelix81/NuevaEstrategia/pull/242) was independently reviewed and merged at 2026-11-26 03:31:23 UTC as [commit d81c2c6](https://github.com/jafelix81/NuevaEstrategia/commit/d81c2c65de8853c46c3987570720bbe8d274b626). Its final offline suite passed **36/36**; the PR live-capture job was skipped as designed.
- Phase 629 now injects `secrets.SEC_USER_AGENT` into the Phase 614 live-capture step and validates it before any SEC request. Missing or placeholder values fail closed. The secret value was not read, printed or persisted.
- Phase 614 retains its weekday hourly cron `41 * * * 1-5`. No scheduled 13F run had appeared by 03:33 UTC after the merge; the next nominal slot is 03:41 UTC. The available read interface does not expose workflow administrative enabled-state. Do not infer disabled state from the missing run alone. No manual dispatch, rerun or duplicate workflow was started.

## 2. SEC Form 144 natural capture — run 45747356670

Both exact-form feeds (144 and 144/A) completed with pagination and no reported feed-window gap.

- **82 new canonical events** from 84 feed-entry observations; two cross-feed overlaps.
- 82 XML resolutions; 14 candidate-manifest issuer matches. The manifest is not an effective-dated historical F80 security master.
- The 82 new events have bounded successive-poll observation intervals and are marked research-observation-eligible by the collector. This means only that the collector's observation interval is bounded; it does **not** certify the SEC's exact first-public timestamp.
- Public-availability-certified: **0**. Signal-eligible: **0**. Same-day intraday use remains unauthorized.
- Structured ledger after capture: **815 accessions / 5,443 detail rows** (807 Form 144 and 8 Form 144/A), representing 441 issuer CIKs.
- 82 new accessions parsed with 534 detail rows appended; bounded backfill separately attempted 10 accessions, appended 35 detail rows, had zero parse/hash errors and left 188 accessions in the backfill queue.
- Phase 516 quality audit: 5,443/5,443 source-hash matches, zero mismatches and zero parse-error rows. The ledger remains descriptive, not a trade/execution ledger.

The run's successful conclusion is a capture/integrity result, not evidence that proposed sales occurred or were publicly knowable at the exact poll time.

## 3. Form 144 Rule 10b5-1 descriptive refresh

The downloaded Phase 549 post-capture artifact reports 815 accessions and 5,443 detail rows:

| Accession-grain classification | Count |
|---|---:|
| Positive explicit 10b5-1 Remarks polarity | 23 |
| Negative explicit | 4 |
| Ambiguous mention | 3 |
| No mention | 785 |
| **Total** | **815** |

Additional descriptive fields:
- 295 accessions (36.2%) have a structured formal plan-adoption date; 126 distinct dates.
- Plan-date-to-notice lag: n=295; min 0, p25 97, median 183, p75 273, max 1,687 days. 294 dates precede notice, one is the same date, none is after notice.
- 18 accessions contain both sell-to-cover and tax-withholding context.
- Four explicit-negative Fermi Inc. notices dated 2026-11-19 total 2,253,270 **proposed** units. They describe mechanical sell-to-cover/tax withholding and are a negative control, not verified executions or discretionary bearish sales.

The classifier is a text/structured-field diagnostic, not a legal determination of plan status or seller intent. A Form 144 is a proposed-sale notice, not proof of execution. A plan-adoption date is not a market-knowledge timestamp. First-seen poll receipt is an upper bound, not exact first public availability.

**Disposition:** retain as descriptive context / conditional future event-study candidate only. No forward-return study, alpha, OOS, bootstrap or LOO test was run.

## 4. Other source status and priority

- **SEC Form 4:** latest natural run [45714679017](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45714679017) succeeded with 415 new accession events and 912 entity observations; 27 transaction-detail rows and 33 footnote references were appended in bounded enrichment. Zero signal-eligible rows. PR #240's exact-entity duplicate sidecar remains Draft/unmerged; natural post-merge validation has not occurred.
- **SEC 13D/G:** PR #241 remains Draft. Latest offline validation [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) passed 30/30; its live 44-header identity sample was skipped. The 13D subject-issuer rebuild remains a higher research priority than treating delayed 13F holdings as a directional signal. A one-time `workflow_dispatch` with `run_live_sample=true` is still required for the bounded sample; it has not been run.
- **SEC 13F:** the Phase 629 guard is now on main, but the prospective collector remains metadata-only. Historical accession joins do not solve the incomplete effective-dated F80 security coverage, amendment lineage or 42-day median filing lag previously observed. No holdings feature is admitted.
- **FINRA Reg SHO:** latest natural run [45550366574](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550366574) returned seven HTTP-200 daily files, but all seven were rejected by the duplicate-symbol/facility-overlap gate (BCPC/TPC). Zero accepted files and zero eligible rows; raw volumes were not persisted. Phase 20C same-day-close remains NO-GO for look-ahead; no stale branch was replayed.
- **CFTC TFF:** run [45550124780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45550124780) found no new reports/revisions; 3,043 rows remain through report date 2026-11-17, with zero historical signal-eligible rows. Treat it as a possible broad positioning/regime covariate, not security-level institutional flow.
- **SEC MIDAS:** retain as a conditional public market-quality/liquidity candidate (59 quarterly archives, 2012 Q1–2026 Q3). Actual ZIP payload integrity, F80 coverage and per-quarter first-public timestamps remain unverified. `HiddenVol` is on-exchange execution against hidden resting orders, not dark-pool/off-exchange volume or beneficial-owner flow. See [Phase 534](PHASE534_SEC_MIDAS_SECURITY_METRICS_SEMANTICS_AND_PIT_AUDIT_2026-11-20.md) and [Phase 563](PHASE563_SEC_MIDAS_2012Q1_ARCHIVE_LINK_INTEGRITY_AND_OPERATIONAL_RECHECK_2026-11-22.md).
- **Options:** Databento OPRA remains a conditional market-wide reconstruction candidate; license/non-display rights and historical sample remain unresolved. IvyDB TradeFlow remains a conditional signed-flow hypothesis. No vendor contacted, quote requested, data purchased or credential added; options-data budget remains USD 0.

## 5. Research disposition and next gates

1. Observe the first natural Phase 614 scheduled run after the Phase 629 merge. Require all four exact-form feeds to pass complete-snapshot, watermark and receipt-interval gates before treating the metadata baseline as established. If no scheduled run appears after an eligible slot, a maintainer must verify workflow enablement; the read connection cannot inspect that setting.
2. Run the bounded 44-header Phase 616 13D/G sample once, after review, then adjudicate subject/filer identity and historical coverage before any crawl or return test.
3. Keep Form 4 / Form 144 as descriptive prospective ledgers until public-availability, security/owner identity, transaction semantics and historical F80 membership are independently certified.
4. Keep FINRA short flow quarantined and CFTC/MIDAS in source-feasibility mode. Do not reinterpret any source as institutional behavior without testing it as a hypothesis.

- New signals admitted: **0**.
- New incremental alpha / valid OOS / bootstrap / LOO results: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No changes to universe, exposure, costs, parameters, holding-period policy, holdout or production.
