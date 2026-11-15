# Phase 408 — SEC Form 144 schedule and SEC 13D/G access-gate recheck

**Audit time:** 2026-11-15 00:40 UTC  
**Disposition:** SEC prospective capture has no confirmed scheduled poll after bootstrap; SEC 13D/G parent retrieval remains blocked by an incomplete User-Agent contact route. No alpha, signal or strategy change.

## 1. Repository and Actions review

- Main HEAD at audit start: `9edbf49727242ec90f39f42e2da89ab599ecf2e4` (Phase 407).
- PR #84 (Phase 407) merged at 2026-11-14 23:15:06Z; PR #83 (Phase 406) at 22:57:35Z; PR #82 (Phase 405) at 22:56:33Z.
- Latest directly inspectable Phase 405 validation run: [43650633912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43650633912). Offline regression succeeded (15/15); `live-capture` was skipped because the event was a pull request. It uploaded no artifact.
- Last confirmed live SEC poll remains bootstrap run [43639405055](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43639405055), not a scheduled poll. Its live-capture job succeeded; artifact [14130779748](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43639405055/artifacts/14130779748).
- Mainline workflow `.github/workflows/phase403_sec_form144_first_seen_capture.yml` now has `schedule: 37 * * * *`, `workflow_dispatch`, and a serialized concurrency group. The :37 schedule change was merged in PR #82.
- The available GitHub connector exposes run-job/artifact retrieval but not a repository-wide workflow-run listing. Therefore this audit does not claim that no schedule run is currently queued or running. No manual or duplicate capture was triggered.

## 2. SEC Form 144 prospective-capture state

Mainline files were checked directly:

- `research/data/sec_form144_first_seen/state.json`: `poll_count=2`; last successful mode `bootstrap`; last successful poll `2026-11-14T20:48:22Z`; run ID `43639405055`.
- `events.csv`: 52 initial-baseline events; all remain research-ineligible, signal-ineligible, and uncertified for public availability.
- `feed_observations.csv`: header only; no per-feed poll observations have been persisted.
- `acceptance_reconciliation.csv`: 52 acceptance timestamps reconciled, but acceptance is not first-public-receipt.

A commit search for the scheduled-capture commit message finds only the two bootstrap commits (runs 43639113589 and 43639405055); no later scheduled-poll commit exists. This is consistent with the unchanged state and empty feed-observation ledger.

The Phase 403 client appends one feed-observation row per (poll run, feed, accession) on every non-manual poll and writes poll state. Therefore a successful scheduled poll should create a persistent state/ledger change even if no new accessions appear. No such successful scheduled poll is evidenced yet.

**Decision:** do not manufacture a first-seen interval, do not use bootstrap rows, and do not start another capture while a possible delayed/queued schedule run cannot be ruled out. Recheck run status and persistent state on the next audit. The current connector limitation prevents a definitive queue/in-progress check.

## 3. SEC 13D/G explicit-parent retrieval — human action required

PR [#37 — Phase 350](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains open and draft.

- The immutable Phase 349 target manifest contains 44 explicit parent accession references.
- Run [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) passed all 10 offline tests, then stopped on its first SEC Archives request.
- Job 131562053060 returned HTTP 403 on request 1/44; zero parent documents were saved; zero references were validated. The workflow correctly stopped rather than retrying or continuing to hit the SEC.
- The log shows the effective User-Agent was only `NuevaEstrategia research (https://github.com/jafelix81/NuevaEstrategia)`, with no monitored contact email.
- Artifact [13991999046](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770/artifacts/13991999046) preserves the blocked-run summary.

**Required human step:** in the repository, open **Settings → Secrets and variables → Actions** and set/update `SEC_USER_AGENT` to a project identifier plus a monitored contact email. Do not paste the email into chat. Once that secret is configured, the exact-parent retrieval can be resumed at the existing 2 requests/second throttle. No SEC request should be retried before then.

PR #36 remains the preceding draft identity/parent-manifest chain. Its 44 targets are explicit references, not assumed immediate predecessors; subject CIK, reporting-person identity and acceptance order must continue to be validated independently.

## 4. Options source access recheck

- Cboe Option Trades sample ZIP (`/download/sample/216`) still cannot be inspected through the available web reader because it rejects `application/x-zip-compressed`; a container download attempt also failed at DNS resolution.
- The official LiveVol condition workbook remains inaccessible as XLSX through the current reader.
- No sample rows, trade-condition map, historical coverage, correction/bust semantics or first-receipt timing are newly validated.
- The existing Phase 351 C1 TBT sample remains a one-day 3% sample, not population calibration: 17.86% blank OPEN_CLOSE, 0.45% incomplete option-series identity, 69 unmapped SIDE rows and unresolved TRADING_SEGMENT semantics.
- Cboe Option Trades remains conditional; no purchase, vendor contact, account, trial or economic test.

## 5. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No new Smart Money feature or signal admitted.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test in this phase.
- Holdout untouched; universe, parameters, capital, exposure and production unchanged.
- No vendor data acquired.

## Immediate next gates

1. Recheck GitHub Actions run status and SEC ledger before any manual or scheduled retry; do not duplicate a possible in-progress poll.
2. Obtain the monitored-contact `SEC_USER_AGENT` secret before resuming the 44 SEC 13D/G parent requests.
3. Keep Cboe sample/workbook inspection blocked until binary bytes are actually available; do not infer contents from the product specification or literature.
4. Continue only after the data-feasibility and PIT gates pass. No source is promoted based on a “smart money” label.
