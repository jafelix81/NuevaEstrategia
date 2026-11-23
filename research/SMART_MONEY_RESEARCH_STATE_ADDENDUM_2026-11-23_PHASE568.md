# Smart Money Research state addendum — Phase 568

**Audit cutoff:** 2026-11-23 04:13 UTC  
**Main HEAD before this addendum:** `2e0ac07e26af37dd18de4393a564106f42d8fccd`  
**Disposition:** no new source admission or alpha result. The latest scheduled SEC Form 144 capture predates the Phase 565 post-capture artifact gate; repeated missing schedule slots remain a human-check operational blocker. FINRA short-interest one-settlement validation is prepared but credential/terms-gated.

## 1. Actions and repository preflight

- Repository-wide Actions API: **8,072 total runs**; latest 30 inspected; **zero in-progress and zero queued** runs at cutoff.
- Latest PR CI: [45096929863](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863), branch `phase565-form144-postcapture-10b5-audit`, offline regression success; live capture skipped by design. Its artifact [14783278471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45096929863/artifacts/14783278471) is the Phase 560 pre-capture descriptive refresh, not a post-capture result.
- Latest natural Form 144 schedule run: [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016), main, 2026-11-22 23:53:30 UTC, success. Jobs `offline-regression` and `live-capture` both succeeded. Artifacts: [14779385856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14779385856) (Phase 560 descriptive refresh) and [14778539572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14778539572) (poll/capture audit).
- The latest natural run predates Phase 565 merge [4eea1a95](https://github.com/jafelix81/NuevaEstrategia/commit/4eea1a95735a559083ae0ea12e80e83dcfa6e653). Therefore the first natural post-merge run and its `phase565-form144-10b5-post-capture` artifact remain unvalidated. The CI artifact does not substitute for this live test.
- Form 144 cron remains `47 * * * *`. Since the 23:53:30 UTC run, schedule slots 00:47, 01:47, 02:47 and 03:47 UTC are absent; 04:47 had not occurred at cutoff. This is a repeated delivery/visibility gap, not proof the workflow is disabled. The GitHub API connection does not expose the administrative enabled/allowed-schedule settings.
- Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) updated with this exact cutoff and human action: verify Phase 403 is enabled and scheduled workflows are permitted in repository Actions settings. No manual dispatch, rerun, cancellation, cron change or duplicate poll.
- Repository default branch is `main`, HEAD before this addendum `2e0ac07e26af37dd18de4393a564106f42d8fccd`; 373 branches were enumerated over four pages and 72 open PRs were returned.

## 2. Phase 565 post-merge artifact gate

PR [#206](https://github.com/jafelix81/NuevaEstrategia/pull/206) is merged. The main workflow now:
1. performs capture;
2. reconciles Phase 516 ledger counts;
3. runs the Phase 549 10b5-1 descriptive classifier and asserts accession/detail-row equality plus `signal_admitted=false`;
4. uploads a separate post-capture artifact;
5. persists a successful capture even if a downstream audit fails, then fails closed.

PR CI [45096929863] passed offline regression; the live job was skipped as designed. Its step summaries show the offline job and Phase 560 artifact upload succeeded. The latest natural live run [45085664016] predates the merge and has no Phase 565 post-capture step. Its live steps confirm capture, Phase 516 quality audit, ledger persistence and poll-artifact upload succeeded. The decoded job-log endpoint returned a transient GitHub artifact-storage `BlobNotFound`; step summaries and artifact metadata were available.

**Gate:** do not declare Phase 565 live-validated until a natural post-merge schedule run produces the named post-capture artifact and its counts/controls are inspected.

## 3. FINRA short-interest one-settlement readiness

The existing manual workflow is `.github/workflows/phase447_finra_single_live_validation.yml`. It accepts one required `settlement_date`, and the client uses asynchronous retrieval, requires exact completion metadata/row reconciliation, and stores raw output only in the runner's private temporary directory; only the non-raw manifest is uploaded.

The upcoming FINRA publication on 2026-11-24 concerns settlement date **2026-11-13**. If an authorized maintainer confirms project-appropriate FINRA credentials and terms before dispatch, the existing workflow can be invoked once with `settlement_date=2026-11-13`. Required secrets are either `FINRA_ACCESS_TOKEN` or both `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET`. The workflow's current default is 2026-09-30, so the date must be explicitly supplied. No credentials were inspected, no terms accepted and no request/dispatch was made. Do not start the 106-date historical batch.

PR [#159](https://github.com/jafelix81/NuevaEstrategia/pull/159) remains Draft and is 7 commits ahead / 142 behind main; PR [#204](https://github.com/jafelix81/NuevaEstrategia/pull/204) remains Draft and is 11 ahead / 19 behind main. Neither should be merged without deliberate reconciliation.

## 4. Research disposition

- Form 144: latest natural ledger remains 295 accessions / 2,196 detail rows, 268 accessions pending backfill; zero new accessions/events in that run, zero parse errors/hash mismatches, zero signal-eligible filings.
- FINRA Weekly Summary: Phase 567's final-value availability proxy remains conditional; no exact public revision timestamp, active-universe coverage or row-key re-audit has been certified.
- FINRA Short Interest: one-date async validation remains blocked by credentials/terms; old capped synchronous panel remains killed.
- FINRA Reg SHO: wait for a natural post-Phase 539 capture; keep fail-closed parsing.
- Options/OPRA, MIDAS, SEC FTD/13D-G and CFTC remain subject to their existing PIT, coverage, identity, licensing or credential gates; no new source was admitted in this checkpoint.
- New signals admitted: **0**. No return/event/alpha/OOS/bootstrap/LOO test. No universe, exposure, cost, holding-period, holdout or production change.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
