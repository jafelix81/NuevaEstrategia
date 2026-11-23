# Phase 570 — Narwhal FINRA short-data history, PIT/licensing gate and Actions recheck

**Audit cutoff:** 2026-11-23 07:27 UTC  
**Repository:** `jafelix81/NuevaEstrategia`  
**Main HEAD:** `5fc35b9e2e995c8da63a802b9fdbc381ffb52f24` (2026-11-23 05:44:04 UTC)

## Executive disposition

A newly documented third-party endpoint (Narwhal API, changelog 2026-11-20) advertises FINRA short-interest history back to December 2017, FINRA Reg SHO daily short volume from 2023-01-01, and SEC FTD from 2023-01-01. This is a potentially inexpensive way to audit historical availability and cross-check the existing direct-source pipeline, but it is **not an independent information source**: the underlying observations are FINRA/SEC data.

Do **not** ingest or backfill it yet. The endpoint documentation explicitly says FINRA's data terms limit the short-interest data to non-commercial use; Narwhal's general pricing page separately advertises commercial use with attribution, while its Terms make downstream use conditional on the underlying source licence. Obtain written clarification for the intended use before acquisition. No API key, request, purchase, or data download was used.

The endpoint also does not document per-row historical first-publication timestamps or full vintage history. Its `revised` flag is useful as a current revision indicator but does not reconstruct every historical vintage. The API's listing-name matching can suppress or mis-map renamed/reused symbols and does not replace an effective-dated CUSIP/security master. It therefore cannot by itself satisfy strict historical PIT or F80 universe coverage.

## 1. New source-feasibility finding: Narwhal short-data API

Official vendor documentation:
- [Short-interest API reference](https://narwhalapi.com/docs/api/stocks/short-interest)
- [20-Nov-2026 changelog](https://narwhalapi.com/changelog/short-data-api)
- [Narwhal Terms](https://narwhalapi.com/terms)
- [Narwhal pricing](https://narwhalapi.com/pricing)

Documented coverage:
- FINRA short interest: every settlement date held from **December 2017**; bi-monthly.
- FINRA Reg SHO short-sale volume: trading days held from **2023-01-01**.
- SEC fails-to-deliver: settlement days held from **2023-01-01**.
- History endpoint: up to **500 dates per page**; default 24.
- Responses identify the underlying source. FINRA short interest is not float-adjusted short interest; the vendor says it does not hold a float field.
- FINRA daily short volume covers only trades reported to FINRA TRFs/ORF; exchange-printed trades are excluded. Its `total_volume` is therefore not consolidated market volume.
- FTD is the SEC's net outstanding balance by CUSIP. The vendor maps to a listing only when its issue-name matching rule passes; unmatched listings return `not_covered`.

PIT and integrity assessment:
- Settlement/trade date is not the knowledge date.
- The reference exposes a `revised` boolean, but does not document an immutable per-row publication/vintage history with the exact first-public timestamp and every correction timestamp.
- A top-level history-page update time, if returned, is not a substitute for per-observation first-public availability.
- A prospective poll could record our own first-seen UTC timestamp, response hash, request parameters, listing ID, and vendor/source revision flag. That would provide a conservative *our-observation* clock going forward, not historical public-availability reconstruction.
- The vendor's name-based mapping is not sufficient for historical ticker reuse, corporate actions, share classes, or effective-dated CUSIP identity. Keep CUSIP-level FTD raw until a separate security-master join is validated.

Coverage/licensing gate:
- Vendor documentation says the endpoint serves only US listings it holds and may return `not_covered` for warrants, units, preferreds, renamed/reused tickers, or failed name matches. No complete coverage census against the frozen 335-symbol universe or historical F80 membership is available from the public documentation.
- FINRA's official [Short Interest Reporting page](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest) states that FINRA DATA provides non-commercial use. Narwhal's short-interest endpoint also states that FINRA's source terms limit the data to non-commercial use. Narwhal's general commercial-use statement is not sufficient to override the underlying source licence; its Terms say downstream use is permitted where the source licence allows it.
- Decision: **conditional feasibility candidate only**. No account creation, API call, download, caching, backfill, or model use until source-use rights are clarified in writing and a frozen-universe coverage audit is designed.

Potential role if cleared:
1. Reconcile a bounded sample of FINRA settlement rows against the direct FINRA pipeline.
2. Measure historical date coverage and symbol-level missingness, not infer smart-money identity.
3. Keep FINRA short interest, FINRA off-exchange short volume, and SEC FTD as distinct datasets with distinct clocks and denominators.
4. Do not call the vendor a second independent confirmation; it republishes the same underlying regulatory sources.

## 2. Official FINRA next publication

FINRA's current [2026 Short Interest Reporting Dates](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest) confirm:
- Settlement date: **2026-11-13**.
- Reporting deadline: **2026-11-17, 6:00 p.m. ET**.
- Publication date: **2026-11-24**.

The existing Phase 447 single-date workflow is the only intended validation path. Its default settlement date is stale (`2026-09-30`); if an authorized run is later approved, it must explicitly pass `2026-11-13`. No credentials were inspected, no live request was made, and no workflow was dispatched. The direct FINRA route remains preferred over adding a vendor dependency, subject to the existing credential and terms gates.

## 3. GitHub Actions, jobs, logs and artifacts

Repository-wide API snapshot:
- **8,072** total workflow runs.
- Latest 100: **96 success / 4 failure**.
- **0** in-progress; **0** queued.
- **373** branches (100 + 100 + 100 + 73 across four pages).
- **72** open pull requests.

Relevant runs:
- Latest overall PR check: [45096929863](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863). `offline-regression` succeeded; log confirms **80 tests passed**. `live-capture` was correctly skipped for the pull-request event. Artifact [14783278471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863/artifacts/14783278471) is the pre-capture Phase 560 descriptive refresh, **not** the Phase 565 post-capture artifact.
- Latest natural Form 144 schedule run: [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), 2026-11-22 23:53:30 UTC. Both jobs succeeded. The live job's steps predate the Phase 565 merge and do not include the new post-capture Rule 10b5-1 artifact step. Artifacts: [14779385856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14779385856) and [14778539572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14778539572). The live log reconciles **295 accessions / 2,196 detail rows**, with zero parse errors and zero signal-eligible rows.
- Form 4: [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), both jobs succeeded. Live log: 474 new event/metadata rows, 988 accession-observation rows; 10 structured accessions parsed and 24 detail rows appended; 10 owner accessions processed and 15 owner rows appended; 20 owner accessions remain in the bounded queue; three descriptive crosswalk rows and **zero signal-eligible matches**. Artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646).
- CFTC TFF: [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977), capture/commit/artifact steps succeeded; 17/17 tests passed; **3,043 rows**, zero historical signal-eligible rows. Artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870).
- FINRA Reg SHO: [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600), both jobs succeeded, but the live log reports **8 invalid files / 0 valid / 0 eligible**. Artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921). This run predates the Phase 539 parser correction and does not validate it.

### Scheduled-delivery gap

- Form 144 main workflow cron remains `47 * * * *`. Since the latest natural run at 23:53:30 UTC, the 2026-11-23 slots **00:47, 01:47, 02:47, 03:47, 04:47, 05:47 and 06:47 UTC** are absent from the latest schedule-event inventory at the 07:27 UTC cutoff.
- Form 4 main workflow cron remains `17 * * * 1-5`. Latest schedule event visible remains [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), created 2026-11-21 00:50:30 UTC; no later Form 4 schedule event appears in the latest schedule inventory. Monday 2026-11-23 00:17–06:17 UTC expected slots are absent at this cutoff.
- This is an observed delivery gap, **not proof** that either workflow is administratively disabled. The connected GitHub API does not expose the workflow enabled-state or repository-level scheduled-workflow permission. No manual dispatch, rerun, cancellation, cron change, or duplicate poll was performed.

## 4. Open research PRs — no unsafe merge

Current comparisons against main:
- PR #204 SEC FTD credential integration: Draft, **11 ahead / 25 behind**, diverged.
- PR #159 FINRA short interest PIT: Draft, **7 ahead / 148 behind**, diverged.
- PR #200 Cboe OPRA: Draft, **5 ahead / 45 behind**, diverged.
- PR #201 SEC MIDAS: Draft, **2 ahead / 45 behind**, diverged.
- PR #202 Form 144 10b5-1 audit: Draft, **17 ahead / 44 behind**, diverged.

No PR was merged or rebased. In particular, do not merge PR #204 or #159 as-is; reconcile against current main and retain offline-only/live-access gates.

## 5. Research disposition

- Narwhal is a potential historical *transport/backfill convenience* for existing FINRA/SEC observations, not a new independent source or a smart-money identity signal.
- No data were acquired and no source was admitted.
- No new signal, event study, return test, backtest, OOS, bootstrap, LOO, or holdout result.
- No changes to universe, costs, exposure, holding rules, production, or frozen baseline.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Next gates

1. Human confirmation of Phase 403/476 enabled-state and repository scheduled-workflow permission in GitHub Settings → Actions.
2. For FINRA short interest, use the existing Phase 447 one-date workflow only after authorized credentials and terms are confirmed; explicitly use settlement date `2026-11-13` for the 2026-11-24 publication.
3. For Narwhal, obtain written clarification of FINRA source-use rights for the project's intended use before even a bounded sample; then audit coverage and response/vintage semantics against the exact historical F80 universe.
4. Validate a natural post-Phase-565 Form 144 run and a natural post-Phase-539 FINRA Reg SHO run before treating either pipeline as current.

