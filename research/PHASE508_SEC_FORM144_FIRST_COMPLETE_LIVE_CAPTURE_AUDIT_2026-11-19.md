# Phase 508 — SEC Form 144 first complete live-capture audit (2026-11-19)

## Executive result

The scheduled SEC Form 144 capture **44614323236** is the first successful complete two-feed poll after the prior partial/diagnostic sequence. It completed both jobs, wrote the append-only ledgers, reconciled all 28 new Form 144 accessions to filing-detail acceptance metadata, and uploaded a compact audit artifact.

This is a source-capture milestone only. It is not evidence of executed sales, public first-receipt timestamps, historical F80 membership, or predictive alpha.

## Preflight and repository state

- Preflight main HEAD: `eabdd0ffabbb9bff87190851a69de2f44a0543fa`.
- Post-capture main HEAD: `c1f6f7f3f4959c539f188d53cc3ac0c0a669367e` (capture commit).
- Actions: 7,897 total runs; latest 100 inspected; none queued, in progress, waiting, pending, or requested at 2026-11-19 21:48 UTC.
- Latest runs: Form 144 scheduled run 44614323236; Form 4 scheduled run 44598981676; Form 4 PR regression 44608603027.
- Branch inventory: first two 100-branch pages reviewed; exact Phase 508 branch/PR name checked before creation.
- Open PRs at preflight: 57. PR #159 remains draft and conditional.
- No workflow was started, rerun, or duplicated.

## Run 44614323236

- Workflow: Phase 403 — SEC Form 144 prospective first-seen capture.
- Event: schedule; created 2026-11-19 21:00:09 UTC.
- Run status/conclusion: completed / success.
- Offline job 135878847277: success; 46 tests passed.
- Live job 135878935754: success; migration, both feed captures, append-only commit and artifact upload all succeeded.
- Artifact: `phase403-sec-form144-first-seen`, ID 14573957396, 1,949 bytes.
- Artifact SHA-256: `6f509e16b60015940d95465be64b9d4ed9ede52d6d93e6019e35202becd00d74`.
- Artifact contents: `schema_migration.json` (already-current schema; 350 rows) and `summary.json`.

## Exact feed results

### Form 144

- One Atom page; 100 raw entries, 50 unique accessions.
- Prior watermark `0001628280-26-074926` was found; pagination completed at that watermark.
- 28 new accessions/events appended.
- 52 total feed observations appended across both feeds.
- All 28 new events have a bounded interval from prior successful Form 144 poll start 2026-11-19 02:50:33 UTC to current response receipt 2026-11-19 21:00:26 UTC.
- All 28 XML metadata retrievals succeeded.
- 28 filing-detail acceptance reconciliations added; 0 unresolved.
- 3 issuers matched the static 290-CIK candidate manifest: Walmart Inc., Target Corp., and Snowflake Inc. This manifest is explicitly **not** the historical F80 security master.

### Form 144/A

- One Atom page; 4 raw entries and 2 unique accessions.
- No new accessions were found.
- The prior watermark was present, but the interval remains `PREVIOUS_POLL_GAP_INTERVAL_UNBOUNDED` because the preceding successful-poll history for this feed contains a gap.
- The current endpoint response succeeded. That does not retroactively create a valid lower bound for the prior interval, and no new 144/A event was admitted.

### Important status distinction

The overall poll status is complete because both endpoints responded. Form 144 has a valid bounded interval; Form 144/A has no new events and its prior interval remains unbounded. A successful current response does not erase an earlier feed-specific gap.

## Eligibility and temporal controls

- `research_observation_eligible_count=28`: this flag means scheduled capture plus a valid feed-specific interval. It does not mean historical universe coverage, public first-receipt certification, or a usable trading signal.
- `signal_eligible_count=0`.
- `public_availability_certified=false`.
- `historical_f80_membership_verified=false`.
- `same_day_intraday_use_authorized=false`.
- The recorded first-seen timestamp is a **poll-response receipt upper bound**, not an exact first public receipt.
- Acceptance datetime and Atom `updated` time are not treated as first public receipt.
- The poll was received around 16:00 ET on 2026-11-19, after the regular session. The first conservative regular-session execution opportunity is 2026-11-20 open.
- No forward returns were read or tested.

## What Form 144 could contain — and what this capture does not yet extract

The current SEC Form 144 instructions describe proposed-sale fields including security class, broker/market maker, units proposed to be sold, aggregate market value, shares outstanding, approximate sale date and exchange. The electronic filing guide also requires separate entries for each security and broker and describes reporting sales made during the preceding three months. Remarks can include Rule 10b5-1 plan information.

Official references:
- SEC, [File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically)
- SEC, [current Form 144 PDF](https://www.sec.gov/files/form144.pdf)
- SEC EDGAR Filer Manual, [Volume II archive](https://www.sec.gov/files/edgar/filermanual/archive/efmvol2-v68.pdf)

The present first-seen collector does **not** yet produce a normalized security-level proposed-sale table, prior-three-month sale table, broker mapping, or reliable 10b5-1 plan field. It records filing/issuer/filer metadata, selected remarks, retrieval status/source and content hash; it does not persist full filing XML. Those fields require a separate parser and semantic audit.

A Form 144 is a **notice of a proposed sale**, not proof that the proposed sale was executed. Any future hypothesis must distinguish proposed supply from completed insider sales and test whether notices are predictive, merely descriptive, or already reflected in price.

## Research disposition

**Retain as a prospective source-capture candidate; do not admit alpha.**

Next gate:
1. Build a schema inventory and stratified parser pilot for current electronic Form 144 submission XML, using synthetic fixtures first.
2. Extract security-level proposed quantities/value/date, recent completed-sale rows, broker, seller/relationship, remarks and 10b5-1 data where present; preserve missingness and multi-security rows.
3. Keep first-seen interval and actual receipt clocks separate from filing acceptance and filing date.
4. Require historical security identity and point-in-time F80 membership before universe coverage claims.
5. Accumulate prospective first-seen observations before forward-return/event-study work; use next executable session and identical costs/exposure versus frozen LTM/F80.
6. Do not infer actual execution from a notice or treat a 10b5-1 mention as a directional signal by itself.

## Other source gates

- SEC Form 4: scheduled run 44598981676 remains the latest reviewed Form 4 capture; 88 canonical new accessions, 0 research-observation-eligible and 0 signal-eligible rows.
- FINRA Reg SHO: still needs a real capture using the post-Phase-495 parser.
- FINRA Consolidated Short Interest: PR #159 remains draft; authorized credentials and one complete asynchronous settlement validation are required before historical batching.
- CFTC TFF: the next existing scheduled window was 22:25 UTC; FINRA's was 22:30 UTC. Neither was started or duplicated in this phase.

## Strategy protection

No backtest, event study, forward-return test, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen: universe, parameters, holding period, exposure, costs, holdout and production unchanged.
