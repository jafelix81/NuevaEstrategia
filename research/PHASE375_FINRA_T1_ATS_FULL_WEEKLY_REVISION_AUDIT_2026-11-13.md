# Phase 375 — FINRA T1 ATS full weekly revision-stability audit

**Status:** completed — 209/209 weekly partitions retrieved; revision-stable concentration feasibility passed; strict historical PIT remains unestablished.  
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


## Final hosted result — completed 2026-11-13

Run [43493465495](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495) completed successfully. The initial run [43493288658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493288658) was a preflight-only fixture failure; the corrected run performed the full retrieval.

- **209/209** consecutive weekly partitions retrieved, from 2021-11-15 through 2025-11-10.
- **10,917,933** rows across **2,292** pages; all partition Record-Total counts matched.
- **209/209** aggregate-to-firm symbol bridges passed; zero missing, ambiguous, invalid-numeric or mismatched symbol bridges.
- **438,798** aggregate symbol-week groups; **432,804** revision-stable and concentration-ready; **5,994** revised/excluded groups.
- Stable coverage: **98.633996%** of symbol-week groups and **96.943175%** of mapped aggregate share volume.
- Revisions occurred in **15/209** weeks. The most affected weeks were 2021-11-15 (1,205 symbols), 2023-11-13 (1,051), 2025-05-12 (915), 2025-05-05 (744), and 2022-06-27 (692). These weeks remain partially quarantined at symbol-week grain; no interpolation or backdating was applied.
- The panel contains **3,173** unique underlying symbols and **38** unique MPID/CRD-derived reporting-participant keys across the full sample. These are reporting identities, not beneficial owners or verified institutions.
- No stable symbol-week had missing participant identity, duplicate participant key, or a De Minimis bucket in the concentration-ready set.

### Descriptive concentration diagnostics (not alpha)

Across 432,804 eligible symbol-week observations, symbol-level broker-dealer reporting concentration averaged:
- HHI: **0.1659** (participant-weighted cross-sectional mean);
- top-one participant share: **27.37%**;
- top-three participant share: **56.97%**;
- reporting participants per symbol: **19.23**.

These are descriptive measures of the distribution of reported ATS activity among FINRA reporting participants. They do not reveal customer identity, beneficial ownership, trade direction, opening/closing intent, or whether any participant was informed. They are not predictive or economic results.

### Coverage sensitivity

- 15 weeks had at least one revised symbol-week.
- 10 weeks had stable share-volume coverage below 90%; 6 were below 50%.
- The weakest week was 2021-11-15: 38.99% symbol coverage and 5.66% share-volume coverage. It appears to be a heavily revised early archive week and must not be treated as representative.
- Outside those revision-heavy weeks, the stable panel generally retained full or near-full symbol and volume coverage; the full-week distribution is retained in the anonymized workflow artifact.

### Final disposition

**PASS — exhaustive retrieval, bridge integrity and revision-stable concentration feasibility. NOT PASS — strict historical PIT.**

The initialPublishedDate field is date-only and the API does not provide intermediate historical vintages or a certified first-receipt timestamp. The first full exchange session after that date is a conservative candidate availability rule, but it has not been certified as an actual contemporaneous receipt ledger. Therefore:
- no historical forward-return, alpha, chronological OOS, bootstrap, LOO or holdout test is authorized from this panel;
- no historical row is promoted to signal-eligible;
- the result is a source/grain/revision feasibility pass only.

The anonymized summary artifact is [14081855428](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43493465495/artifacts/14081855428). It contains weekly aggregate diagnostics only; raw rows, symbols, MPIDs, CRDs, firm names and participant hashes were not retained.

F80, production, universe, capital, exposure and parameters remain unchanged.


## Official publication-clock clarification — 2026-11-13 follow-up

A review of FINRA's own OTC Transparency Data Website User Guide (Version 4.0) narrows the PIT limitation:

- FINRA defines `initialPublishedDate` as the **initial publish date**: the first Monday or next business day after the tier-specific reporting delay (T1: two weeks; T2/OTCE: four weeks).
- FINRA states that weekly files and updates are available **no earlier than 6:00 a.m. ET on business days**.
- FINRA defines `lastUpdateDate` as the later of the last reported date or the initial publish date.

Official references: [FINRA OTC Transparency Data Website User Guide](https://www.finra.org/sites/default/files/OTC-transparency-data-user-guide-v5.pdf), especially the File Availability and Weekly Summaries sections; [FINRA Weekly Summary API documentation](https://developer.finra.org/docs#query_api-equity-weekly_summary).

**Revised interpretation:** for a symbol-week that passes the Phase 375 stability rule (`lastUpdateDate == initialPublishedDate`), the date-only `initialPublishedDate` is a documented first-publication date. Because the exact intraday release time is not supplied and FINRA only guarantees availability no earlier than 6:00 a.m. ET, the conservative daily research clock is the **first regular exchange session strictly after `initialPublishedDate`**. This avoids using same-day close/open data when publication may have occurred after the relevant market event. It is a conservative date-level availability bound, not an exact first-receipt timestamp.

This official documentation supports testing the date-level clock; it does not by itself certify every historical row or cure symbol identity, inactive-security coverage, or revised rows. A separate Phase 385 should re-fetch/verify the actual `initialPublishedDate` values for all 209 partitions, confirm the tier delay/calendar mapping, and calculate the next-session eligibility date. No return/alpha test is authorized until that gate and the effective-dated security/universe coverage gate pass.
