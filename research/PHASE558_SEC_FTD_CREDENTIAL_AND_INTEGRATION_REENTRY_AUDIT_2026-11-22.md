# Phase 558 — SEC FTD credential and integration re-entry audit

**Audit cutoff:** 2026-11-22 16:42 UTC  
**Main HEAD at audit start:** `ee944e215ffc71a98b1762ac7ebcd3d27532e287`

## Executive decision

SEC FTD remains a **conditional, non-directional settlement-friction / fails-balance candidate**, not a Smart Money or short-selling signal. The representative-file coverage result is meaningful enough to preserve the source for a later date-appropriate identity audit, but it is not an active-universe coverage pass and does not authorize returns.

A fresh integration review found that the pending Phase 43/44 PR chain is not safe to merge unchanged: the canonical Phase 43 workflow on `main` still uses a generic User-Agent; PR #198 proposes the secret-backed correction, but Phase 44's separate workflow/script still hardcodes a placeholder contact; PR #4 adds a misspelled duplicate workflow path. These findings were posted to PRs #4, #5, and #198.

No data pull, manual dispatch, rerun, backfill, return test, OOS, bootstrap, LOO, or production change was performed.

## 1. Fresh repository and Actions preflight

- Actions API: 8,052 total runs; latest 100 = 98 completed successes, 2 completed failures; zero queued, in-progress, waiting, or requested.
- Branches: 370 across four pages; open PRs: 71.
- Latest natural Form 144 run: [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618), created 2026-11-22 10:22:19 UTC. No newer scheduled Form 144 event appears in the latest 100 runs at this 16:42 UTC cutoff. The 6h20m run-creation gap is an operational delivery/observability gap, not a certified missed cron timestamp; GitHub `created_at` is not the intended cron-fire time.
- Latest known weekday scheduled runs remain FINRA Reg SHO [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600), Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), and CFTC TFF [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977). No weekday capture was expected on Sunday.
- No workflow was dispatched, rerun, cancelled, or duplicated.

### Phase 550 natural validation rechecked

Run [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618):
- `offline-regression`: success.
- `live-capture`: success.
- Post-capture Phase 516 quality audit: success.
- Same-run reconciliation: 275 filing headers = 275 ledger accessions; 2,072 quality rows = 2,072 poll-ledger rows.
- Ten accessions were detail-backfilled, adding 166 rows; 288 remained in the bounded queue.
- 53 feed observations; no new accession/event; complete pagination and previous accession boundaries present; no possible feed-window gap.
- Zero parse errors, unresolved accessions, or source-hash mismatches.
- Zero public-availability-certified headers and zero signal-eligible headers.

Artifact [14750197356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618/artifacts/14750197356) is unexpired, 3,643 bytes, SHA-256 `2b7d749c4555754ff4d1ddad135ccf97c10bd0ad9e879597ad16968887bd88b6`. It contains the poll summary, schema migration result, and post-capture Phase 516 summary.

## 2. SEC FTD: representative coverage is real but denominator is not historical

The existing Phase 43/44 reports and PR artifacts were reconciled:

| Representative file | Economic rows | Fixed 335-name matches | Coverage |
|---|---:|---:|---:|
| 2018 first half | 43,567 | 253/335 | 75.522% |
| 2026 second half | 66,693 | 316/335 | 94.328% |
| Both files | — | 237/335 | 70.746% |
| Either file | — | 332/335 | 99.104% |

The parser audit reports no exact duplicate economic rows, empty CUSIPs, negative quantities, or trailer count/quantity reconciliation failures. One 2026 row has a missing ticker but a usable CUSIP.

**Important denominator limitation:** these percentages compare two representative historical files with a fixed 335-symbol snapshot recovered from a Phase 21C panel. They are not coverage rates for securities actually active/listed on those historical dates. The missing 2018 symbols cannot be treated as zero FTD or as data errors.

### Semantic and PIT disposition

The SEC FTD quantity is an aggregate balance outstanding at a settlement date, not a daily short-sale flow. FTD can arise from long or short sales and is not evidence by itself of naked short selling or informed directional activity.

For July 2009 onward, the existing audit uses conservative file-availability dates (first-half file at month-end; second-half file around the 15th of the following month), never settlement date. Any future feature must use that file knowledge date and the next executable session. Preserve the distinction among:
- not active/listed;
- active with zero observed FTD;
- active with observed FTD;
- identity/coverage unresolved.

**Decision:** retain only as a conditional, non-directional settlement-friction / fails-balance state candidate. Do not call it Smart Money, short pressure, or naked shorting. Next gate remains an effective-dated active-universe and CUSIP/ticker crosswalk by signal date. No return test is authorized.

## 3. Phase 43/44 PR integration defect

### Canonical Phase 43 workflow on main

Current `main` contains `.github/workflows/phase43_sec_ftd_actual_file_audit.yml`. Its SEC download step still sends the generic header `User-Agent: NuevaEstrategia research contact`; it does not pass a monitored contact.

### PR #198 — secret-backed correction

[PR #198](https://github.com/jafelix81/NuevaEstrategia/pull/198) changes the canonical Phase 43 workflow to require `secrets.SEC_USER_AGENT`, fail closed if absent, and avoid printing the secret. Its two checks are offline-regression successes only; there has been no live SEC access validation. It remains Draft and is based on an older main snapshot.

### PR #5 — Phase 44 still has a placeholder

[PR #5](https://github.com/jafelix81/NuevaEstrategia/pull/5) adds `phase44_sec_ftd_universe_coverage_audit.py` and its workflow. The script still hardcodes `User-Agent: NuevaEstrategia research audit contact research@example.com`; the workflow does not inject `SEC_USER_AGENT`. Fixing Phase 43 alone therefore does not make Phase 44's live downloads safe/reliable. Both the script and workflow must consume the same secret and fail closed when absent.

PR #5 is Draft and based on the 2026-10-29 main snapshot. Its 75.522% / 94.328% results remain a fixed-snapshot diagnostic, not historical active-universe coverage.

### PR #4 — duplicate/misspelled workflow

[PR #4](https://github.com/jafelix81/NuevaEstrategia/pull/4) adds `.github/workflows/fase43_sec_ftd_actual_file_audit.yml` (misspelled `fase43`) and a second copy of the Phase 43 parser, while the canonical `phase43` workflow already exists on main. Merging it unchanged would add a duplicate Phase 43 workflow and preserve the generic User-Agent.

Integration comments were added:
- [PR #198 comment 7082324455](https://github.com/jafelix81/NuevaEstrategia/pull/198#issuecomment-7082324455)
- [PR #5 comment 7082324862](https://github.com/jafelix81/NuevaEstrategia/pull/5#issuecomment-7082324862)
- [PR #4 comment 7082325237](https://github.com/jafelix81/NuevaEstrategia/pull/4#issuecomment-7082325237)

### Human prerequisite

Configure repository Actions secret `SEC_USER_AGENT` with a project identifier and monitored contact email. The connected GitHub interface cannot inspect or set secret values. Do not put the value in source, PR text, or chat. After configuration, run only the existing bounded two-file sample; do not start a historical FTD or 13D/G backfill before the sample and identity/coverage gates pass.

## 4. Relative source priority

- **SEC 13D/G:** remains a high-priority ownership-disclosure hypothesis, but the 20,266-row legacy panel is quarantined pending subject/filer identity, legal/schema regime, and public-availability reconstruction. It shares the SEC User-Agent prerequisite.
- **SEC FTD:** conditional secondary state variable only; active-universe/CUSIP mapping and PIT remain incomplete.
- **FINRA ATS:** Phase 535's archive route returned HTTP 530. The Query API recent-history sample (968,139 rows across ten partitions) had non-null `initialPublishedDate` for sampled symbol rows, but 1,882 rows were revised after initial publication; strict vintage/PIT integrity did not pass. ATS activity is venue activity, not beneficial-owner direction.
- **Options:** PR #200 remains Draft; OPRA Option Trades/Quotes are independent broad-market candidates, Open-Close is a Cboe-venue capacity complement, and IvyDB TradeFlow remains the conditional all-venue signed-flow candidate. Exact universe/date coverage, historical receipt/correction vintages, and license rights remain unverified.
- **FINRA Reg SHO:** latest natural run [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) predates Phase 539; eight files were rejected for duplicate symbols, zero valid/eligible. Wait for the next natural weekday validation; do not aggregate/deduplicate.
- **Phase 20C:** Phase 487 rejected Phase 20B and 20C for promotion; seven of 335 price histories remain unresolved. No re-test is justified on the same incomplete panel.

## 5. Research decision

- New signals admitted: **0**.
- New return/event/OOS tests: **0**.
- FTD directional/short-pressure interpretation: **not admitted**.
- SEC 13D/G historical panel: quarantined.
- FINRA ATS and options: conditional, not PIT/license admitted.
- No universe, cost, exposure, holding-period, holdout, or production change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

The next useful work is not another backtest. It is (1) resolve the SEC User-Agent prerequisite and reconcile the Phase 43/44 workflow chain, then (2) build a date-appropriate FTD active-universe/CUSIP panel or, if that cannot be made reproducible, park FTD and preserve effort for the higher-value 13D/G and options candidates.
