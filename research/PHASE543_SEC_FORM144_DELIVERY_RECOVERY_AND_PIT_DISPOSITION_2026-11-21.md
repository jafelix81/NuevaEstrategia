# Phase 543 — SEC Form 144 delivery recovery and PIT disposition

**Audit cutoff:** 2026-11-21 08:54 UTC  
**Main HEAD before this report:** `c30b2d3263a974de737900035f3d0fe9a1da4c71` (SEC Form 144 scheduled-capture commit)  
**Disposition:** Form 144 scheduled ingestion resumed for one natural poll after an approximately 7h52m interval and recovered three new filing events without a detected feed-window gap. This is a partial operational recovery, not proof of stable schedule delivery or a predictive signal.

## 1. Actions preflight

- Inspected the latest 100 of 8,011 Actions runs, relevant jobs/logs/artifacts, open PRs/issues, research files and branch search.
- Latest 100 run outcomes: 87 success, 12 failure, 1 cancelled; no queued, waiting or in-progress run.
- Branch search returned 363 branches; 67 open PRs were visible.
- No workflow was dispatched, rerun, cancelled or duplicated.
- Main advanced automatically through scheduled capture commit `c30b2d3`.

## 2. Form 144 / 144-A: successful natural capture

Run [44886726541](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541), created 2026-11-21 08:50:10 UTC, completed successfully. Both jobs passed: offline regression (64/64 tests) and live capture. Artifact: [14700173280](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541/artifacts/14700173280).

The live poll started at 08:50:22 UTC and completed at 08:50:23 UTC. The previous successful poll started at 00:58:15 UTC, so the observed interval was **7h52m07s**.

| Capture measure | Result |
|---|---:|
| Form 144 feed entries | 51 |
| Form 144-A feed entries | 2 |
| Feed observations | 53 |
| New accession events | 3 |
| XML-resolved events | 3 |
| Acceptance reconciliations added | 3 |
| Unresolved acceptance reconciliations | 0 |
| New candidate-issuer matches | 0 |
| New cross-feed overlaps | 0 |
| Signal-eligible events | 0 |

New accessions: `0001213900-26-122846`, `0001213900-26-122848`, `0001213900-26-122849`.

The previous latest accession was present in the feed page, pagination stopped at that accession, and `possible_feed_window_gap=false`. This means the collector found its prior boundary and did not detect a missing feed window in this poll. It does **not** mean the hourly schedule ran continuously: expected hourly slots 01:47–07:47 UTC were absent from the observed run list.

The first-seen timestamp remains the poll-receipt upper bound. The output explicitly leaves public availability uncertified and same-day intraday use unauthorized. Three rows were metadata-level research observations, but none is signal eligible.

## 3. Structured detail backfill

The same live job parsed the newest ten bounded accessions:
- 55 detail rows appended;
- zero parse errors, zero unresolved accessions and zero source-hash mismatches;
- cumulative ledger: 235 accessions and 1,712 rows;
- 328 accessions remain in the bounded backfill queue.

The preceding successful poll reported 338 remaining accessions, so the queue advanced by ten. This is ledger enrichment only; it does not establish security identity, historical F80 membership, exact public availability or signal eligibility.

## 4. Cross-source schedule and data disposition

### SEC Form 4

The latest scheduled Form 4 run remains [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), created 2026-11-21 00:50:30 UTC. No newer scheduled Form 4 run appears in the latest 100 Actions records at this audit cutoff. Its last run produced 474 new feed accession observations, parsed ten structured filings (24 detail rows), enriched ten owner filings (15 owner rows), and generated three descriptive Form 144/Form 4 matches with zero signal-eligible matches. No exact public-release time or transaction-line owner attribution is certified.

### FINRA Reg SHO

The latest scheduled run is [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600). Its head SHA `2f3839b` is 13 commits behind the Phase 539 merge commit `c7666f0`; therefore this run predates the new duplicate-symbol diagnostics. Eight files were rejected, zero were valid and zero observations were eligible. The first natural post-merge capture is still required. No aggregation or deduplication rule was changed.

### CFTC TFF

The latest prospective run remains [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977). Its 17 offline tests passed and four new contract-report events were captured. The historical archive remains 3,043 rows, but historical first-publication timestamps are insufficient for full-history PIT eligibility; historical rows remain excluded from features and returns tests.

### SEC FTD / 13D-G

[PR #198](https://github.com/jafelix81/NuevaEstrategia/pull/198) remains Draft. Its workflow wiring uses the repository secret `SEC_USER_AGENT`, but the secret must be configured by a repository administrator and cannot be inspected or set through this connection. No bounded FTD sample was run; no historical backfill is authorized. SEC 13D/G remains quarantined pending authorized retrieval and identity repair.

### Phase 20C and other sources

The latest recorded Phase 20C census remains 328/335 price histories; the seven terminal/successor and corporate-action cases have not been revalidated in this phase. Options remain conditional on licensing, historical PIT/vintage and universe coverage. No vendor data were purchased.

## 5. Decision

- Form 144 ingestion: **partial recovery confirmed**, one successful natural poll after a long interval; continue observing cadence.
- SEC Form 4: no newer scheduled capture observed at cutoff.
- FINRA: no post-Phase-539 live diagnostic yet.
- CFTC: prospective collection remains healthy but too short for predictive inference.
- New signals admitted: **0**.
- No new backtest, event study, OOS, bootstrap or LOO.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no changes to universe, costs, exposure, holding period or production.

## 6. Next gates

1. Observe another natural Form 144 poll before treating schedule delivery as stable.
2. Observe the next natural FINRA capture to validate Phase 539 diagnostics; do not dispatch manually.
3. Continue weekday CFTC first-receipt capture without backdating historical rows.
4. Human prerequisite: configure `SEC_USER_AGENT`; only then run the bounded two-file FTD sample.
5. Preserve Form 4/144 eligibility gates and keep all unverified events descriptive only.
