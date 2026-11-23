# Phase 565 — Form 144 scheduled-capture recovery and post-capture 10b5-1 artifact gate

**Audit cutoff:** 2026-11-23 00:20 UTC  
**Main data commit:** [fcaa4d811ce03110d87637d507324af29c82984c](https://github.com/jafelix81/NuevaEstrategia/commit/fcaa4d811ce03110d87637d507324af29c82984c)  
**Disposition:** operational recovery observed; Form 144 detail backfill advanced; no new event, no signal and no alpha test.

## 1. Actions preflight and schedule recovery

The repository-wide Actions API returned 8,070 total workflow runs. The latest 100 contained 96 successes, 4 failures, 0 cancelled runs and 0 active/queued runs. The repository had 372 branches (four pages) and 72 open pull requests.

The latest natural Form 144 run is [45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016):

- Event: `schedule`; cron remains `47 * * * *`.
- Created/started: 2026-11-22 23:53:30 UTC; completed 23:53:52 UTC.
- This is 6 minutes 30 seconds after the 23:47 UTC scheduled minute, consistent with a delayed GitHub schedule delivery.
- Both `offline-regression` and `live-capture` succeeded.
- No active or queued run was present at the audit cutoff.
- The run performed one natural poll; no manual dispatch, rerun, cron change or duplicate workflow was used.

This is evidence that the scheduled workflow is enabled and delivered at least one later run. It does not prove every intervening hourly slot fired or guarantee future cadence. Continue monitoring; do not change the cron based on this single recovery.

## 2. Live capture and ledger reconciliation

Both Form 144 and Form 144/A feeds succeeded. Pagination and prior watermarks were present; no feed errors or possible feed-window gap were reported.

- Feed observations appended: 53.
- New accessions: 0.
- New events: 0.
- Existing-accession backfill: 10 accessions attempted and parsed; 82 detail rows appended.
- Remaining bounded backfill queue: 268 accessions.
- Current structured detail ledger: **295 accessions / 2,196 detail rows**.
- Forms: 293 Form 144 and 2 Form 144/A.
- Issuer CIKs represented: 193.
- Detail sections: 301 securities-information rows, 589 securities-to-be-sold rows, 1,011 prior-three-month sale rows and 589 acquisition-lot rows.
- Parse errors: 0; unresolved backfill accessions: 0; source-hash mismatches: 0.
- Research-observation-eligible headers: 295; public-availability-certified headers: 0; signal-eligible headers: 0.

The 82-row increase is backfill of already-known accessions, not 82 new filings or trades. The poll disposition was `POLL_COMPLETE_NO_NEW_ACCESSIONS`.

The capture commit [fcaa4d8](https://github.com/jafelix81/NuevaEstrategia/commit/fcaa4d811ce03110d87637d507324af29c82984c) persisted the feed-observation and structured-detail state. The live artifact [14778539572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14778539572) is unexpired (3,645 bytes; ZIP SHA-256 `d09d12afe2bf77a46e3cce4c2159e068db0a0dc1f70605138022bd69ee64d778`). The separate Phase 560 artifact [14779385856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14779385856) is also unexpired (1,306 bytes).

## 3. Important artifact-ordering defect found

The Phase 560 `phase560-form144-10b5-current-refresh` artifact is produced in `offline-regression`, which is a dependency of `live-capture`. Therefore it is computed **before** the live capture and its bounded backfill. In this run, the pre-capture artifact was based on the prior 285-accession / 2,114-row snapshot, while the post-capture ledger reconciled at 295 / 2,196.

The post-capture Phase 516 quality summary reports 108 formal-plan-date accessions, 14 Remarks mentions, 10 date/Remarks overlaps, 98 formal-date-only and 4 Remarks-only; plan dates after notice remain zero, with 72–546 day lags and a median of 185 days. This does not supply the Phase 549 positive/negative/ambiguous polarity breakdown. That breakdown must not be copied from the pre-capture artifact and labeled current.

A focused PR is prepared against the existing Phase 403 workflow (no second collector): run the existing Phase 549 classifier after successful post-capture Phase 516 reconciliation, assert its accession/detail counts match the quality summary, assert `signal_admitted=false`, and upload a separate `phase565-form144-10b5-post-capture` artifact. A static regression test protects the step order and reconciliation contract. The PR remains Draft until CI is reviewed.

## 4. Research disposition

Form 144 remains a proposed-sale notice, not execution confirmation. First-seen is a poll-receipt upper bound, not exact public availability. Historical F80 membership is still unverified. No signal is admitted.

- New signals: 0.
- Event/return/alpha/OOS/bootstrap/LOO tests: 0.
- No change to universe, parameters, holding-period policy, exposure, costs, holdout or production.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 5. Other source lines and blockers

- SEC FTD / 13D-G: PR #204 remains Draft and is now 11 commits ahead / 11 behind main. `SEC_USER_AGENT` remains a human prerequisite for the bounded two-file SEC validation; no live FTD request or historical backfill was attempted.
- FINRA / Phase 20C: Sunday; no weekday live capture was expected. The latest state remains 328/335 valid price histories with seven unresolved. No new FINRA result was inferred from the Form 144 run.
- Options: the existing ranking remains conditional—TradeFlow as primary signed-flow candidate only if first-receipt, method/version, coverage and license gates pass; Cboe OPRA raw trades/NBBO as independent reconstruction candidate. No purchase or sample-data rights were assumed.
- CFTC TFF and SEC MIDAS remain source-feasibility work only; their historical availability clocks and universe/identity gates are not promoted by this run.

## 6. Links

- Natural capture: [Run 45085664016](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016)
- Live artifact: [14778539572](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14778539572)
- Pre-capture Phase 560 artifact: [14779385856](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45085664016/artifacts/14779385856)
- Main capture commit: [fcaa4d8](https://github.com/jafelix81/NuevaEstrategia/commit/fcaa4d811ce03110d87637d507324af29c82984c)
