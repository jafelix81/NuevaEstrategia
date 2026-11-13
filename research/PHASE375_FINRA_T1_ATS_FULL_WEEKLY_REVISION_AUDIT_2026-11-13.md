# Phase 375 — FINRA T1 ATS full weekly revision-stability audit

**Status:** design and offline tests passed; full 209-week retrieval is running.  
**Parent evidence:** Phase 374 completed successfully in run 43481384832 / artifact 14067403379.

## Objective

Replace Phase 371's one-week-per-month sample with a census of every T1 partition in the four-year historic inventory. The inventory must contain 209 consecutive weekly anchors from 2021-11-15 through 2025-11-10.

For each complete week, reuse the Phase 374 symbol-level rules:
- require exact Record-Total pagination;
- reconcile aggregate symbol/product rows to firm rows at symbol grain;
- combine CTS/UTP aggregate rows only when product codes are distinct and combined shares/trades exactly match firm rows;
- exclude an entire symbol-week from concentration if any aggregate or firm row has missing/invalid dates, a publication lag outside 21/22 calendar days, or lastUpdateDate different from initialPublishedDate;
- calculate broker-dealer reporting concentration only for stable, reconciled symbol-weeks with complete unique MPID/CRD-derived identities and no De Minimis bucket.

## Phase 374 result now available

The 47-month sample completed successfully:
- 47/47 partitions retrieved; 2,469,987 rows / 517 pages.
- 47/47 symbol bridges passed.
- 96,919 revision-stable symbol-week groups; 1,968 revised groups; 98,887 total groups.
- 96,919 groups were concentration-ready.
- Revision events were concentrated in 2023-11-13 (1,051 symbol groups) and 2025-05-12 (915), with one each in 2024-02-12 and 2025-06-16.
- Exact intraday PIT remains unestablished; no return test is authorized.

**Correction:** Phase 374's field unique_participant_keys_union_count is incorrectly computed as the number of distinct pairs of (per-week participant count, week) (47), not the union of participant identities. Do not use that field. Phase 375 independently recomputes the unique participant-key union in memory using SHA-256 digests and persists only the count; raw keys and digests are not written.

## Expected output

Only summary.json is retained. It contains weekly aggregate counts, bridge/revision/concentration gates, aggregate coverage ratios, and union counts. No raw rows, symbols, MPIDs, CRDs, or firm names are retained.

## PIT limitation

initialPublishedDate is date-only; lastUpdateDate is not an intermediate-vintage ledger. Even a revision-stable historical row does not prove the exact first-receipt timestamp. The candidate daily availability rule remains the first exchange session strictly after the actual initialPublishedDate, never the same-day close and never a backdated date. Phase 375 is feasibility only and does not authorize alpha or return testing.

## Controls

No forward returns, alpha, OOS, bootstrap, LOO, or holdout use. No changes to F80, parameters, universe, capital, exposure, or production.

## Execution trail

- First preflight run [43493288658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493288658) failed before data retrieval because the synthetic aggregation test fixture omitted the rows/pages fields expected by the summary function. No FINRA requests or data conclusions resulted.
- Fixed the fixture in commit f2f7ea1d9e9444876c6a2d870aff31c3f900fb16. The corrected run [43493465495](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495) passed compilation and all five offline tests, then began the 209-week retrieval. It remains in progress; no duplicate run has been started.

Final retrieval metrics and artifact link will be added after completion.
