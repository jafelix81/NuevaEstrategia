# Phase 444 — SEC Form 144 independent-feed persistence and partial-outage audit

**Audit time:** 2026-11-17 00:41 UTC  
**Main HEAD at preflight:** `283c4056e7f56d4d6cabfa9d3aec3ae5f5ca709c` (Phase 443)  
**Disposition:** implement independent per-feed capture and persistence after the 2026-11-16 scheduled poll lost all output when the 144/A endpoint timed out, despite the 144 feed having already completed earlier in the configured feed order.

## 1. Operational preflight

- Latest 100 Actions runs: 61 success / 38 failure / 1 cancelled; total historical runs 7,677; zero in-progress or queued.
- Audited 278 branches across three pages (100/100/78), 56 open PRs, and the 67-workflow inventory previously recorded. The Phase 403 scheduled capture and Phase 384 CFTC workflow files were inspected.
- Latest run: [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015), Phase 403 SEC Form 144 scheduled capture. Offline regression passed. Live capture failed on the second configured feed, 144/A, with a read timeout after four 60-second attempts. The first configured 144 feed had already returned and parsed before the 144/A request failed.
- Job log confirms the failure at `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=144%2FA...`. The commit step was skipped. Upload step succeeded but had no files; run artifacts list is empty. No event ledger, feed-observation ledger, or poll-state update was persisted.
- Latest successful SEC Form 144 capture remains [43862500790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790): 55 feed observations, zero new accessions/events, metadata artifact [14223876987](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790/artifacts/14223876987).
- CFTC TFF remains at bootstrap [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), event `push`, not a prospective scheduled capture. Phase 384 state still records 2026-11-13 23:03:38 UTC as last capture and report date 2026-11-03 for all four contracts; no Nov 10 report is persisted. No Nov 16 scheduled capture appears in the latest 100 runs. Next expected scheduled poll: 2026-11-17 22:15 UTC.
- No workflow was dispatched, rerun, or duplicated.

## 2. Root cause

Phase 403's prior `fetch_all_feeds()` loop was fail-fast. It fetched 144 and then 144/A sequentially, but any exception escaped the function. The caller only wrote events, feed observations, state and `summary.json` after both requests returned.

Consequently, one feed outage discarded the successful response from the other feed for that poll. It also prevented the upload step from preserving a useful poll summary. This is an avoidable loss of prospective first-seen evidence.

## 3. Change implemented

- Fetch and parse each feed independently; capture typed error metadata for each failed feed and continue with any successful feed.
- A partial poll appends events and feed observations from successful feeds only.
- Only successful feeds advance their own first-seen clock, latest accession, hash and poll counter. A failed feed's prior state is preserved unchanged.
- The global `last_successful_poll_utc`, mode and run ID advance only when both feeds succeed.
- Add `last_poll_attempt_utc/run_id/status`, successful/failed feed lists, bounded error details, and complete/partial poll counters.
- Events created during a partial poll explicitly set `cross_feed_provenance_complete=false` and `capture_poll_status=partial`. The feed-name list is only what was observed from successful feeds.
- Cross-feed overlap count is null during a partial poll because the failed feed could contain additional overlaps.
- If every feed fails, the client writes a `POLL_FAILED_ALL_FEEDS` summary artifact and then exits non-zero; it does not advance state or write events.

The existing 60-second timeout/four-retry policy, SEC endpoints, polling schedule, append-only keys, acceptance reconciliation, candidate manifest, no-intraday policy and signal-ineligible guard are unchanged.

## 4. Regression coverage

Three offline tests were added:

1. A 144 success plus 144/A timeout returns one usable snapshot and one typed error.
2. A partial scheduled poll persists the successful feed, advances only its per-feed clock, leaves the failed feed/global success clock unchanged, marks event cross-feed provenance incomplete, and records partial counters.
3. An all-feed failure writes an audit summary, raises, and preserves the prior state and event ledger.

The PR's Phase 403 workflow is expected to run only the offline-regression job on pull_request; live capture is excluded from PR events.

## 5. Research and production controls

- No source data were downloaded or committed.
- No public-availability claim is made from acceptance timestamps.
- Partial observations remain upper-bound first-seen evidence, not exact receipt times.
- `research_observation_eligible` remains feed-specific and requires a bounded interval; `signal_eligible` remains false.
- No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.

## 6. Decision

Retain the two-feed SEC capture as one workflow, but make each feed an independent persistence unit. This reduces evidence loss during a single-endpoint outage without inventing missing feed data or overstating cross-feed completeness.
