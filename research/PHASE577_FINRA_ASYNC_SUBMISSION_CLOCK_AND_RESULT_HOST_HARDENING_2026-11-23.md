# Phase 577 — FINRA async submission-clock and result-host hardening

**Audit cutoff:** 2026-11-23 15:19 UTC  
**Base main:** `9e70cad10ae21e713a38d3e4429b58debe377126`  
**Branch:** `phase577-finra-async-timestamp-hardening`  
**Disposition:** Pre-publication client hardening only. The FINRA single-settlement request remains unexecuted and credential/license-gated. No raw data, source admission, alpha test or strategy change.

## 1. Mandatory preflight

- Repository Actions inventory: 8,074 total runs; latest 100 = 96 success / 4 failure; zero queued or in progress.
- Branch census: 373 (100 + 100 + 100 + 73); open PRs: 72.
- Current main at preflight: `9e70cad10ae21e713a38d3e4429b58debe377126`.
- Latest natural Form 144 run [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123): both jobs succeeded. Live steps completed capture, Phase 516 ledger audit, Phase 549 post-capture audit, append-only persistence and artifact uploads. The log explicitly reports Phase 565 post-capture reconciliation passed. Ledger: 305 accessions / 2,244 detail rows; 10 existing accessions backfilled / 48 rows appended; 258 pending; zero new accessions, parse errors or hash mismatches. Post-capture artifact [14800277734](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800277734), SHA-256 `7d8d62289b21ce28de22ebf408fd461534d1cea0b95034f00379b0e51e741c58`.
- Latest natural Form 4 run [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578): both jobs succeeded. Live steps backfilled 10 structured accessions / 39 detail rows, added 10 filing-level owner rows, left 20 bounded owner accessions pending, and generated 3 descriptive crosswalk rows / 0 signal-eligible rows. Artifact [14798359037](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578/artifacts/14798359037), SHA-256 `55a7d8fa26c06b523318c5b7e829d396a7afbcfadcdf181904ad834c18297033`.
- No workflow was running or queued; no collector was dispatched or duplicated.

## 2. SEC scheduled-delivery gap

At 15:19 UTC, the last natural Form 144 and Form 4 runs remain 45137579123 (08:18:38 UTC) and 45133809578 (07:48:40 UTC).

- Form 144 cron remains `47 * * * *`; slots 08:47 through 14:47 UTC are absent.
- Form 4 cron remains `17 * * * 1-5`; slots 08:17 through 14:17 UTC are absent. The 15:17 slot was only about two minutes old and was not classified as missed.
- This is an observed delivery gap, not proof of administrative disablement. Repository Actions settings are not exposed by the read interface. Existing Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) was updated in place; no new duplicate issue/comment, manual dispatch, rerun or cron change was made.

## 3. FINRA release gate

The intended one-date validation remains settlement **2026-11-13**, scheduled for publication **2026-11-24**. FINRA's documented availability-by time is 16:40 ET on publication date: **2026-11-24 21:40 UTC / 14:40 America/Hermosillo**.

The existing manual-only workflow remains the correct path:
`.github/workflows/phase447_finra_single_live_validation.yml`
- Explicitly pass `settlement_date=2026-11-13`; its default is still 2026-09-30.
- It requires `FINRA_ACCESS_TOKEN` or both `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET`.
- FINRA Equity Data terms for `otcMarket` restrict internal use to non-commercial personal/professional use. Do not assume the credentials or standard terms authorize commercial/client-facing use.
- No request, credential inspection, terms acceptance or dispatch was performed.

## 4. Static code-review findings and correction

A static review of `research/phase447_finra_async_snapshot_client.py` found that the manifest's `submitted_at_utc` was captured **before** the OAuth client-credentials exchange. With OAuth, it therefore preceded the actual dataset POST and was not a precise query-submission timestamp.

This branch changes the manifest clock to record:
1. `run_started_at_utc`;
2. `auth_ready_at_utc` after token acquisition or bearer-token selection;
3. `submitted_at_utc` immediately before the dataset POST;
4. `submission_accepted_at_utc` immediately after the POST response;
5. `status_checked_at_utc`;
6. `result_download_started_at_utc`;
7. `downloaded_at_utc` after the complete result body is parsed.

The pre-signed result-host check also used a raw string suffix test. A hostname such as `evilamazonaws.com` could pass `.endswith("amazonaws.com")`. Validation now checks the parsed hostname's dot-boundary suffix `.amazonaws.com`, HTTPS scheme, absence of user-info, and default/443 port only.

New synthetic tests cover strict timestamp ordering through the OAuth path and reject hostname-suffix confusion, user-info and nonstandard ports. The existing one-settlement filter, 100,000-row ceiling, FINRA completion-header reconciliation, raw-file private permissions, no-auth pre-signed GET, and manifest-only artifact policy remain unchanged.

## 5. Controls and disposition

- No FINRA network request, raw data retrieval, credentials or secret values accessed.
- No historical backfill, identity mapping, signal, return/event study, OOS, bootstrap or LOO.
- No changes to settlement date, universe, holding period, exposure, costs, holdout or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- This is timestamp/security hardening, not a Smart Money signal and not evidence of alpha.

## 6. Next gate

After publication and only with authorized credentials and permitted-use rights, run the existing Phase 447 workflow once for settlement 2026-11-13. Verify first-receipt timestamp, request/tracking IDs, completion headers, downloaded row count, hash and revision flags. Keep all rows descriptive until effective-dated security identity, historical F80 membership, coverage and false-zero gates pass.
