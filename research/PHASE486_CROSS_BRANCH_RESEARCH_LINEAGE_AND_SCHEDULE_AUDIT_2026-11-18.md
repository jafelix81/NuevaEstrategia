# Phase 486 — cross-branch research lineage and schedule-readiness audit

**Audit cutoff:** 2026-11-18 18:05 UTC  
**Preflight main HEAD:** `4afd223d80f697c472623caa589cab751940de70`  
**Disposition:** reuse existing research chains; do not repeat the 13D/G identity work or dispatch any live capture. The only new operational milestone in the current window is already recorded by Phase 471: the first prospective CFTC batch. No new alpha evidence.

## 1. Preflight: Actions, branches, PRs and artifacts

- Repository Actions history: **7,855** runs.
- Latest 100: 74 successful, 24 failed, 2 cancelled; **0 active/in-progress and 0 queued**.
- Complete schedule-triggered history: **22** runs.
- Branch inventory: **315** branches across four search pages.
- Open PRs: **56**.
- Latest runs: Phase 485 push/PR checks [44356862612](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356862612) and [44356946691](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356946691) passed the 8-test offline parser suite. Phase 484 [44356403599](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44356403599) passed its offline audit suite. These runs produced no artifacts and made no SEC requests.
- No workflow was dispatched, rerun, cancelled, or duplicated.

## 2. Important branch-reuse finding: SEC 13D/G work already exists

The Phase 484/485 mainline work re-confirms, but does not newly solve, a problem already documented in the unmerged historical research chain:

- **Phase 87** explicitly rejected the Phase 35 filer-side panel as a subject-issuer event panel and identified the same queried-CIK fallback / filer-versus-subject failure.
- **Phases 82–84** already built a global master-index candidate set and a 600-filing role-aware SEC-header validation design/sample. Phase 84 separates SUBJECT COMPANY from FILED BY and does not treat index, archive-path or accession-prefix CIK as issuer identity.
- **Phases 91–93** already address timing regimes, reporting-person identity limits, amendment lineage and event-mechanism classification.
- **Phases 347–350** already cover CUSIP integrity, explicit predecessor manifests and parent retrieval.
- **PR #37 / branch `phase350-sec-13dg-explicit-parent-retrieval`** is the existing 44-parent retrieval path. Its hosted run [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) passed offline tests but received HTTP 403 on its first SEC Archives request: 1 request attempted, 0 documents saved, 0/44 parents retrieved. It requires the repository Actions secret `SEC_USER_AGENT` to contain a project identifier and monitored contact email. No further SEC request should be attempted until that preflight is satisfied.

**Disposition:** keep the Phase 28D/35 20,266-row panel quarantined. Do not create another 13D/G parser, another 44-parent manifest, or a replacement SEC crawler. Phase 485's small pure parser is a useful offline component, but it is not a reprocessing of the 20,266 accessions and does not supersede the broader Phase 84/87 work. Do not merge PR #37 directly: it is stacked on Phase 347, not main.

## 3. Other existing lines: reuse rather than restart

- **Cboe:** PR #44 (Phase 357) remains draft and stacked on Phase 356. Phase 357 documents conflicting product-history dates and the lack of exact historical first-receipt/vintage evidence. Phase 472 on main classifies Complex Order Flow only as a possible confounder/control, not a directional or identity signal. Keep Open-Close EOD conditional; no vendor contact, trial, subscription or license acceptance. Do not repeat the OCC public aggregate OI endpoint test killed in Phase 354.
- **FINRA ATS:** Phase 392 already classifies ATS/MPID concentration as venue/firm structure, not beneficial-owner or investor concentration. PR #61 (Phase 385) is a draft stacked on Phase 375; its date-level publication-clock result is not an exact first-receipt clock and does not authorize returns.
- **FINRA Reg SHO:** Phase 469/470 is already on main, including the late-first-seen rule. The existing cron is `30 22,23 * * 1-5` UTC. At this cutoff, the first post-merge slots at 22:30 and 23:30 UTC on November 18 were still in the future; no live FINRA capture is claimed and no manual poll was started.
- **CFTC TFF:** Phase 471 already records the first prospective batch. Run [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204) appended four contract rows for the same 2026-11-10 report date, all first received at 2026-11-18 03:44:57 UTC. This is **one prospective weekly observation per contract**, not four weeks. Only ES/NQ belong to Phase 387's preregistered primary hypothesis. The 52-prior-prospective-observation warm-up remains unsatisfied; no percentile, signal or return test is available.
- **MOM120:** Phase 480 already adjudicated the old positive OOS result as overlapping the LTM/F80 momentum family, with no identical-exposure, cost-adjusted incremental comparison. Do not rerun or promote it as independent alpha.
- **Phase 20C prices:** Phases 473–475 already established that the seven missing symbols have corporate-action/delisting/ticker-change events and that current Yahoo responses are truncated. The source-selection audit identifies Massive Advanced / Sharadar as candidates, not acquired data. Do not substitute prices or drop symbols.

## 4. Scheduled capture status at cutoff

| Workflow | Latest relevant scheduled evidence | Status |
|---|---|---|
| SEC Form 144 / Phase 403 | [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069), 12:18 UTC | Offline regression failed on stale Phase 464 counts; live-capture job was skipped; no artifact. PR #140's 40-test correction passed, but no post-fix scheduled run is present through the 17:47 UTC slot. |
| SEC Form 4/4-A / Phase 476 | No schedule-triggered run in the 22-run schedule history | Workflow file is on main with `17 * * * 1-5`; the 16:17 and 17:17 UTC slots have no run. Administrative enabled/disabled state is not exposed by this read connection. |
| CFTC TFF / Phase 384 | [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), 03:44 UTC | Successful first prospective receipt; append-only state and artifact verified. Next existing weekday slot is 22:25 UTC. |
| FINRA Reg SHO / Phase 469 | No post-merge scheduled run yet | First existing slots are 22:30 and 23:30 UTC; they had not occurred at cutoff. |

Issues [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) and [#142](https://github.com/jafelix81/NuevaEstrategia/issues/142) remain the delivery-tracking records. Missing schedule events are evidence of a delivery gap, **not proof** that a workflow is disabled. Do not dispatch manually or create replacement workflows.

## 5. Next actions and research boundary

1. Wait for the already configured SEC Form 4/4-A and Form 144 schedule windows; inspect jobs, artifacts and append-only ledgers before any retry.
2. Inspect the first scheduled FINRA Reg SHO polls after 22:30/23:30 UTC, applying Phase 470's late-first-seen provenance rules.
3. Continue CFTC append-only collection. Preserve first receipt, revisions and cadence; do not use historical backfill to fill the Phase 387 prospective warm-up.
4. Resume the existing 13D/G parent retrieval only after `SEC_USER_AGENT` is correctly configured; use PR #37 rather than a duplicate crawler.
5. Keep Cboe conditional until sample-specific rights, historical coverage, version/vintage policy and exact receipt-time requirements are resolved.
6. Keep the seven delisted-price histories quarantined until a licensed provider sample passes date, OHLC, corporate-action and independent-source reconciliation.

No forward-return test, alpha, OOS, bootstrap, LOO or holdout test was run in this audit.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.** No universe, parameters, holding period, capital, exposure, costs, holdout or production changes were made.
