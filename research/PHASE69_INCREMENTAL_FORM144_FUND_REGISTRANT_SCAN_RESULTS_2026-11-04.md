# Phase 69 — Incremental Form 144 fund registrant scan results

Date: 2026-11-04  
Branch: `phase71-original-universe-rule-trace`  
Run: [41862496090](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41862496090)  
Job: `126687859505`  
Artifact: [13340097937](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41862496090/artifacts/13340097937)

## Result

<badge color="success">DATA GATE PASS</badge> The incremental scan incorporated the ten new fund registrant CIKs from the corrected 335-ticker map. It found **zero candidate accessions** across the 14-quarter Form 144 index window.

| Metric | Result |
|---|---:|
| Current tickers mapped | 335 / 335 |
| Expanded registrant CIKs | 319 |
| New fund registrant CIKs | 10 |
| Incremental candidate accessions | 0 |
| New accessions / overlaps | 0 / 0 |
| New issuer events | 0 |
| XML / mapping errors | 0 / 0 |
| Controls reconciled | 280 / 280 |
| Expanded candidate rows | 21,648 |
| Expanded issuer-event rows | 21,634 |

## Exact reconciliation

The expanded output is not merely count-equivalent to Phase 67:
- `expanded_candidate_role_resolution.csv` is byte-for-byte identical to the pinned Phase 67 baseline; SHA-256 `a2f4f73130da13dcbe63e1963298eae1102580a418a41a932b3e43bc8548ca87`.
- `expanded_issuer_event_raw.csv` is byte-for-byte identical to the Phase 67 `issuer_event_raw.csv`; 67,014,714 bytes, SHA-256 `fd20e338bd3624e7e1c85c39ab911f9fd5d1d78e8a20ed185e42db299a868b20`.

The expanded role distribution remains 21,633 issuer matches, 14 filer-only false positives excluded, and one ambiguous-pair issuer match. The 280/280 controls reconcile.

## New fund CIK crosswalk

The 10 new registrants cover 27 current ETF tickers:
- `0001579982`: ARKF, ARKG, ARKK, ARKQ, ARKW.
- `0001064641`: XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY.
- `0001100663`: IEFA, IWM, SOXX.
- `0001064642`: KRE, XBI.
- `0001137360`: OIH, SMH.
- `0000734383`: VNQ.
- `0000857489`: VWO.
- `0000923202`: VEA.
- `0001174610`: BITO.
- `0001540305`: JETS.

SEC seriesId/classId values are preserved in `ticker_mapping.csv`. They are not yet mapped to Form 144 security-class descriptions; do not fan out a registrant-level filing to every ticker in that registrant.

## Execution integrity note

The first job log reaches the complete summary and artifact upload at 2026-11-04 15:56:19 UTC. A documentation-only update inadvertently queued a second run (41863703923) because the specification file was included in the workflow's push path filter. That second job also completed and uploaded artifact 13340957307 at 16:04:44 UTC. Its expanded candidate-role and issuer-event CSVs are byte-for-byte identical to the first artifact; its control-validation rows are set-equivalent, with row ordering differing. Both REST run objects still report `queued` despite complete logs and artifacts. The workflow path filter has since been narrowed to the script file only, and the concurrency group is shared with other SEC data scans. No further scan is intended. The separate Phase 69 unit-test job log reports 8/8 tests passed.

## Decision

Phase 69 is complete as a negative incremental result: the ten newly mapped fund registrants contributed no Form 144 candidates/events in the tested 14-quarter window. The expanded panel is exactly the same as Phase 67. Stop this incremental CIK scan; retain the 335/335 ticker map, and redirect effort to historical PIT security identity, fund series/class-to-security reconciliation, filing accepted-time availability and exact amendment lineage.

No forward returns or alpha tests were run. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## Duplicate-run reconciliation

- Second run: [41863703923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41863703923), job `126692245930`, artifact `13340957307` (7,334,163 bytes; SHA-256 `b0afe0b9d77f685cfb88a6961671cf4beb000d33fd94f4e789bc98cf32892119`). The job log shows the same zero-candidate result for all quarters and successful artifact upload.
- The second artifact's `summary.json`, `expanded_candidate_role_resolution.csv`, `expanded_issuer_event_raw.csv` and `ticker_mapping.csv` are byte-for-byte identical to the first run. The candidate and issuer-event hashes remain `a2f4f73130da13dcbe63e1963298eae1102580a418a41a932b3e43bc8548ca87` and `fd20e338bd3624e7c1e85c39ab911f9fd5d1d78e8a20ed185e42db299a868b20`. The 280-row control-validation file contains the same rows, though serialized order differs.
- Cause: the documentation path was mistakenly included in the push trigger. It has been removed; the workflow now triggers only when the scan script changes. The Phase 69 concurrency group was also unified under `sec-public-data-research` for future SEC scans.
- This duplicate adds no research information and should not be repeated. No manual dispatch was issued.
