# Phase 576 — FINRA short-interest release clock, license gate and SEC schedule recheck

**Audit cutoff:** 2026-11-23 14:41 UTC (07:41 America/Hermosillo)  
**Main HEAD before this checkpoint:** `7b8ba97b9bb30b8c4a653ff217055cd86cb18205`  
**Disposition:** FINRA single-settlement validation is technically prepared but must wait until the published availability time and use credentials/terms appropriate for non-commercial personal or professional research. SEC scheduled-delivery gaps remain an administrative issue. No signal or strategy change.

## 1. Preflight — Actions, jobs, artifacts, branches and PRs

- Repository-wide Actions API: 8,074 total runs. The latest 100 are all completed: 96 success / 4 failure; zero queued or in progress.
- Branch census: 373 (100 + 100 + 100 + 73). Open PRs: 72.
- Latest natural Form 144 run: [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123), started 2026-11-23 08:18:38 UTC. Both `offline-regression` and `live-capture` succeeded. Live steps include schema migration, SEC capture, Phase 516 ledger audit, Phase 549 post-capture 10b5-1 audit, artifact upload and append-only persistence. Log explicitly reports “Phase 565 post-capture 10b5-1 reconciliation passed.”
- Form 144 artifacts:
  - [14800551409 — Phase 560 descriptive refresh](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800551409), SHA-256 `97a317d501a908ae2340e6f900bc3fdf241c7a6e1755bfd50a45338802770047`.
  - [14800277734 — Phase 565 post-capture audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800277734), SHA-256 `7d8d62289b21ce28de22ebf408fd461534d1cea0b95034f00379b0e51e741c58`.
  - [14799993648 — Phase 403 capture audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14799993648), SHA-256 `3ec04baa014f21361478ea2110f2601278dd7122cdb9bfbb9a09c7eabde9f821`.
- Form 144 log/ledger reconciliation: 305 accessions, 2,244 detail rows, 10 existing accessions backfilled / 48 rows appended, 258 pending, zero new accessions in that capture, zero parse errors and zero hash mismatches. Phase 549 reports 118 formal plan dates across 70 dates (median 183 days; range 72–546), but no public-availability-certified or signal-eligible filings. A formal plan date is not the market-publication time.
- Latest natural Form 4 run: [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578), started 07:48:40 UTC. Both jobs succeeded. Live log reports 10 structured accessions backfilled / 39 detail rows, 10 filing-level owner rows, 20 owner accessions pending, no parse errors, no transaction-line owner attribution and zero signal-eligible rows. Public availability remains uncertified.
- Form 4 artifact [14798359037](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578/artifacts/14798359037), SHA-256 `55a7d8fa26c06b523318c5b7e829d396a7afbcfadcdf181904ad834c18297033`.
- No workflow was running or queued, and no duplicate/manual SEC collector was started.

## 2. SEC scheduled-delivery gap at the 14:41 UTC cutoff

The last natural runs remain Form 144 45137579123 (08:18:38 UTC) and Form 4 45133809578 (07:48:40 UTC). Current workflow files still specify:
- Form 144: `47 * * * *`.
- Form 4: `17 * * * 1-5`.

Elapsed slots absent from the repository-wide run inventory:
- Form 144: 08:47, 09:47, 10:47, 11:47, 12:47 and 13:47 UTC.
- Form 4: 08:17, 09:17, 10:17, 11:17, 12:17, 13:17 and 14:17 UTC.

This is an observed scheduled-delivery gap, not proof that the workflows are disabled. Repository-level Actions administration is not exposed by this read connection. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) remains the single tracking point. No cron change, dispatch, rerun or duplicate poll was made.

## 3. FINRA Short Interest — exact PIT release gate

Official FINRA's 2026 reporting calendar states that the settlement snapshot dated **2026-11-13** is due from firms on **2026-11-17 at 6:00 p.m. Eastern** and is published on **2026-11-24**:
- [FINRA Short Interest Reporting calendar](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest).

The FINRA Developer Center's Consolidated Short Interest dataset documentation adds an exact availability statement: the dataset is available by **4:40 p.m. Eastern on the publication date**. The dataset is identified as group `otcMarket`, name `consolidatedShortInterest`:
- [FINRA Developer Center — Consolidated Short Interest](https://developer.finra.org/docs).

For a conservative no-lookahead gate, do not use the 2026-11-13 settlement snapshot before **2026-11-24 16:40 America/New_York**, equivalent to **2026-11-24 21:40 UTC** and **2026-11-24 14:40 America/Hermosillo**. This is FINRA's documented “available by” time, not an independently observed first-receipt timestamp. The live capture must still persist its actual UTC receipt time, request/tracking metadata, provider completion metadata, exact row reconciliation, result hash and revision flags.

The existing workflow is the correct one:
`.github/workflows/phase447_finra_single_live_validation.yml`
- It is manual-only and accepts one `settlement_date`.
- Its default remains `2026-09-30`; the intended date must be explicitly entered as `2026-11-13`.
- It requires `FINRA_ACCESS_TOKEN` or both `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET`, and has a credential guard before any FINRA request.
- It submits one asynchronous settlement-date-filtered query, verifies FINRA completion headers against downloaded row count, and writes raw data only to a private runner directory; only the non-raw manifest is uploaded.
- No request or workflow dispatch was made before the publication date/time.

## 4. FINRA license/use gate — clarified from the current official terms

The Developer Center identifies Consolidated Short Interest as an `otcMarket` dataset. FINRA's [Specific Terms for Equity Data](https://developer.finra.org/specific-terms-equity-data) expressly cover all datasets in that group and state:
- Internal use is limited to the developer's **non-commercial personal or professional use**.
- Redistribution of Equity Data and derivative/resultant data is limited to end users' non-commercial personal or professional use, with FINRA attribution, no fee for the data, and no further redistribution.
- Derivative/Resultant Data may be created within those stated restrictions.

The broader [FINRA API Terms of Service](https://developer.finra.org/finra-api-terms-service) were updated 2026-03-19 and require acceptance by an individual with authority to bind the developer. FINRA's [Developer Center documentation](https://developer.finra.org/docs) says Individual accounts are intended for individual investors/researchers using public data for their own non-commercial purpose and are not intended for commercial purposes.

This does not automatically block private, non-commercial personal research. It does block assuming that a public credential grants commercial strategy, client-service or redistribution rights. If the intended use becomes commercial or client-facing, do not use this dataset until FINRA grants the necessary written permission/rights. Credentials must be provisioned and accepted by the authorized account holder; this audit did not inspect secrets or accept terms on anyone's behalf.

## 5. PR and broader-source disposition

- PR [#159 — Phase 505 FINRA Consolidated Short Interest PIT feasibility](https://github.com/jafelix81/NuevaEstrategia/pull/159) remains Draft/open. Its branch is 7 commits ahead and 164 behind main (diverged); do not merge without refreshing and reconciling.
- Phase 447 remains the only intended single-date live validation path. Do not batch historical dates until the first live response, exact completeness and revisions reconcile.
- SEC MIDAS remains a public exchange-market-structure/liquidity candidate, not investor identity or off-exchange accumulation; quarterly first-public timestamps, file integrity and point-in-time identity/universe coverage remain open.
- Cboe OPRA/Open-Close remains the strongest conditional independent options-flow candidate, subject to historical first-receipt/correction vintages and written model-development rights.
- OCC Stock Loan remains parked pending written authorization. CFTC TFF remains a market-regime source with limited prospective observations, not a stock-specific institutional flow signal. Form 4/Form 144 remain descriptive, with zero eligible observations.

## 6. Quantitative disposition

- New Smart Money signals admitted: 0.
- Incremental alpha demonstrated: none.
- New independent OOS, event-study, bootstrap or LOO evidence: none.
- Model, universe, exposure, costs, holdout and production: unchanged.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

**Next gate:** on 2026-11-24, after 14:40 Hermosillo / 21:40 UTC, use the existing Phase 447 workflow for exactly `settlement_date=2026-11-13` only if authorized credentials and the intended non-commercial use rights are in place. Validate completeness and revisions before any historical backfill or return test.
