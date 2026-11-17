# Phase 452 — Post-Phase 451 operational and public-artifact audit

**Audit time:** 2026-11-17 11:10 UTC  
**Main HEAD at audit:** `f5f1bdb6be9d6cf48e20b76e1627b7ffbb61f6ba` (Phase 451 state update)  
**Disposition:** SEC Form 144 scheduled delivery remains unobserved after the :47 UTC re-arm; CFTC's next :22:25 UTC slot is still in the future. A legacy Cboe sample artifact remains publicly downloadable and unexpired; sample-specific redistribution permission is not established. No signal or strategy change.

## 1. Repository and Actions preflight

- Repository: `jafelix81/NuevaEstrategia`; default branch `main`.
- Main HEAD is `f5f1bdb6be9d6cf48e20b76e1627b7ffbb61f6ba`, a state-file-only update to Phase 451. No later commit was present at audit.
- Actions: 7,691 total runs. Latest 100: 62 success, 37 failure, 1 cancelled; zero in-progress and zero queued.
- Branches: 285 (100/100/85); open PRs: 56; workflow files: 69.
- Latest overall run: [44009082677](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44009082677), Phase 448 pull-request CI, created 2026-11-17 03:16:57 UTC. Job `offline-regression` passed 18/18 tests; `live-capture` was skipped. No artifact. Its log contains synthetic fixtures (`partial-run-1`, `new-144-hash`), not a live SEC poll.
- Latest main push CI: [44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167), Phase 447, 14/14 synthetic contract tests passed; no artifact.
- FINRA one-settlement validation: [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) failed at the credential guard. The log explicitly shows `FINRA_ACCESS_TOKEN`, `FINRA_CLIENT_ID`, and `FINRA_CLIENT_SECRET` empty; no FINRA request was made.

## 2. SEC Form 144 schedule delivery

- Schedule-filtered Actions inventory contains 17 historical scheduled runs; newest remains [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), created 2026-11-16 22:28:47 UTC.
- Its offline job passed 15/15 tests. Live capture failed after four retries on the Form 144/A read timeout. The append-only commit was skipped. The artifact-upload step itself completed, but the log says no files existed under `phase403_output/`; the run has no artifact.
- Main workflow YAML still contains `47 * * * *`, concurrency group `sec-form144-prospective-first-seen`, and schedule-mode append-only persistence.
- Phase 448 merged/re-armed at approximately 03:17 UTC on November 17. The eight expected hourly slots from 03:47 through 10:47 UTC are absent. No later schedule event appears by this 11:10 UTC audit.
- The read interface does not expose the workflow enabled/disabled setting. Do not infer that it is disabled, do not keep shifting cron minutes, and do not use manual mode to fabricate first-seen observations.
- Human check: in GitHub Actions, inspect **Phase 403 - SEC Form 144 prospective first-seen capture**. Enable it once only if the UI shows it disabled. If already enabled, leave the cron unchanged; scheduler delivery remains unresolved.

## 3. CFTC TFF timing

- Main workflow `.github/workflows/phase384_cftc_tff_prospective_capture.yml` specifies weekday cron `25 22 * * 1-5` UTC.
- At 11:10 UTC on November 17, the next 22:25 UTC slot had not occurred; this is not yet a missed run.
- Latest known run remains [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), a November 13 push/bootstrap, not a scheduled prospective capture. Its artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) is 1,068 bytes. Existing state records 3,035 historical warm-up rows and zero signal-eligible observations.
- Do not dispatch manual capture or backdate the first-receipt clock. Inspect the actual scheduled run after 22:25 UTC.

## 4. Public Cboe artifact rights check

- The public repository still exposes artifact [13291147097](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602/artifacts/13291147097) from run [41762583602](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41762583602).
- GitHub reports 3,963,598 bytes, not expired, with expiry 2027-02-02.
- Cboe's current Open-Close product page states that the dataset is proprietary, raw data is licensed for internal use only and may not be redistributed externally; derived-data distribution requires additional fees and approval. The page also offers a downloadable sample, but the sample-specific redistribution exception is not established by the material reviewed.
- Therefore, do not add further raw or raw-derived Cboe data to this public repository. Human action: verify the terms attached to the exact sample artifact and remove the artifact if public redistribution is not permitted. The available GitHub connector has no artifact-delete action; no deletion was attempted.

Official product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary

## 5. Research disposition

- Form 4: Phase 439 shows that 53/96 exact ticker matches are transaction-row-weighted and concentrated in ONTC; only 4/15 distinct issuers, 16/42 issuer-accessions and 16/41 issuer-filing-date units match. The legacy bridge is not admitted; the 95% identity gate remains.
- Options: Phase 430 demotes raw IV spread/skew to borrow-friction controls absent point-in-time borrow-fee data. Cboe EOD Open-Close remains a conditional participant-side open/close candidate, not beneficial-owner identity or aggressor flow. Phase 441 prioritizes EOD feasibility first, a Nasdaq 10-minute sample second, and Cboe 1-minute only if finer timing earns its cost.
- N-PORT: quarterly, delayed context only; no amendment-delta signal.
- FINRA Short Interest: asynchronous client is ready, but no live snapshot has been obtained because credentials are absent.
- SEC 13D/G still requires a monitored-contact `SEC_USER_AGENT`.
- No raw market data were acquired; no return/alpha/OOS/bootstrap/LOO/holdout test was run; no signal was admitted.

## 6. Frozen strategy control

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No changes to universe, parameters, capital, exposure, holdout, trading logic or production were made.
