# Phase 550 — Post-capture Form 144 ledger-quality artifact

**Audit cutoff:** 2026-11-22 04:05 UTC  
**Base main:** `4d7107c7b56926107f9049017947cdc7619483ce`  
**Disposition:** add a post-live-capture, local-only Phase 516 quality summary to the existing Phase 403 artifact. This closes a known timing/observability gap; it does not change SEC polling, event eligibility, signals or strategy behavior.

## 1. Preflight

- Inspected the latest 100 Actions runs, active/queued state, run-specific jobs/logs/artifacts, all four branch pages, all 71 open PRs, recent commits, and current Smart Money research files.
- Repository Actions inventory: 8,046 total runs; latest 100 contain 97 successes, 3 failures and 0 cancellations. No queued, waiting, requested or in-progress run was present.
- Branch count: 369 (100 + 100 + 100 + 69); open PRs: 71.
- Latest natural Form 144 run: [44977181082](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44977181082). Both jobs passed. The live artifact [14735949070](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44977181082/artifacts/14735949070) was downloaded and inspected.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Confirmed artifact timing gap

Phase 403 currently runs the Phase 516 ledger-quality audit in the separate `offline-regression` job. That job completes before the dependent `live-capture` job starts, and its runner does not share files with the live job.

In run 44977181082:
- The offline Phase 516 audit therefore described the pre-capture ledger: 255 filing headers / 1,828 detail rows.
- The live job subsequently backfilled 10 accessions / 78 detail rows.
- The post-capture ledger is 265 accessions / 1,906 rows, with 298 accessions remaining in the bounded backfill queue.
- The live artifact's own poll summary reports the post-capture counts and zero parse errors, unresolved accessions or source-hash mismatches, but it does not include the full Phase 516 semantic/PIT quality summary.

This is a reproducibility and artifact-synchronization issue, not a parser failure. The existing pre-capture regression remains useful and is retained.

## 3. Minimal correction

The existing Phase 403 `live-capture` job now:
1. Compiles the Phase 516 audit module along with the capture clients.
2. Runs the same deterministic, local-only Phase 516 audit immediately after the SEC capture/backfill step.
3. Writes `phase403_output/phase516_post_capture_summary.json`, which is included in the existing `phase403-sec-form144-first-seen` artifact.

No second collector, new schedule, new network request, manual dispatch, retry, or new artifact-upload workflow is introduced. The audit reads only the committed local CSV after the live step has updated it. Existing append-only commit and artifact upload behavior is unchanged.



## 5. Persistence and failure-semantics hardening (2026-11-22 05:00 UTC)

A review of the first PR validation [44983972414](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44983972414) found that the new post-capture audit was initially a hard-failing step placed before the append-only ledger commit. If Phase 516 failed after a successful SEC poll, GitHub Actions would skip the later commit step and the newly captured ledger/state could be lost with the ephemeral runner. The PR run passed 64 offline tests, but correctly skipped the live job; it did not exercise this ordering on a live capture.

The workflow was hardened before merge:
1. The SEC capture step now has the stable id `sec_capture`.
2. The post-capture Phase 516 step has id `post_capture_quality` and `continue-on-error: true`, so a quality-audit failure does not block persistence.
3. The append-only commit is explicitly gated on a successful SEC capture; a failed capture is never committed as a successful poll.
4. Artifact upload remains `if: always()`, so poll logs and any generated audit output are retained.
5. A final guard fails the job after commit and artifact-upload attempts if the post-capture quality audit failed. Thus data persistence is not silently traded for a green quality status.
6. The offline regression now smoke-tests the exact post-capture output path and summary schema against the committed ledger.

The new workflow revision has not yet passed its triggered PR check at this report cutoff. A natural scheduled capture is still required to prove that the artifact contains the post-capture summary and that its filing/row counts reconcile to the poll summary. No manual poll or merge was performed.

## 4. Validation and controls

- The PR will use the existing Phase 403 pull-request regression path; its `live-capture` job remains skipped for pull-request events.
- Existing Phase 516 tests remain in the offline regression suite.
- A future natural scheduled run is required to confirm that the artifact contains both the poll summary and the post-capture Phase 516 summary with matching ledger counts.
- No SEC poll was initiated during this phase.
- No raw or licensed data were added.
- No event study, forward-return test, backtest, OOS, bootstrap or LOO was run.
- No signal, universe, cost, exposure, holding-period, holdout or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
