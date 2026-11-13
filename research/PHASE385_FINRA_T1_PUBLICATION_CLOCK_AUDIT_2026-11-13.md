# Phase 385 — FINRA T1 ATS publication-clock census

**Status:** implementation prepared; hosted 209-week date-level audit pending.  
**Parent:** Phase 375 completed the exhaustive 209-week T1 ATS retrieval, aggregate-to-firm bridge and revision-stability audit.

## Objective

Validate the actual \`initialPublishedDate\` values for every T1 historical weekly partition and derive a conservative daily availability bound. Phase 375 established 209 complete partitions and 432,804 revision-stable/concentration-ready symbol-week groups, but its report correctly stopped short of authorizing historical return tests because the date-level publication clock had not yet been independently checked across every week.

## Method

- Reuse the 209 consecutive T1 partition anchors from 2021-11-15 through 2025-11-10.
- Retrieve only \`ATS_W_SMBL\` aggregate rows, with full pagination and FINRA Record-Total/Offset validation. No participant identifiers or raw rows are retained.
- Require every aggregate row in a partition to have a valid \`initialPublishedDate\` and \`lastUpdateDate\`, and require one common \`initialPublishedDate\` across all aggregate symbols in that partition.
- Check the T1 schedule: the nominal publication date is the first NYSE session on or after \`weekStartDate + 21 calendar days\` (two weeks after the Friday week-end). A Monday market holiday moves the publication date to the next session, ordinarily +22 calendar days.
- Independently map the actual publication date to the first NYSE regular session **strictly after** it. No same-day close/open is used; no intraday release time is inferred.
- Compare FINRA metadata before and after the census.

The NYSE calendar is provided by \`pandas_market_calendars==5.6.0\`, a versioned local calendar package; the run records its exact version.

## Acceptance gates

1. 209/209 consecutive partitions retrieved.
2. Every partition's filtered aggregate Record-Total exactly reconciles to retrieved rows.
3. Exactly one nonmissing publication date per partition.
4. Every actual publication date matches the documented T1/NYSE calendar rule and has a 21- or 22-day lag.
5. Every partition maps to a first NYSE session strictly after publication.
6. FINRA metadata remains stable during the snapshot.

## Interpretation and limitations

A pass would validate a **conservative date-level availability bound** for stable T1 ATS observations. It would not provide the exact first-receipt timestamp or intraday availability. The next-session rule intentionally sacrifices one or more sessions to avoid assuming the data were available before the publication date's market close/open.

Phase 375 already excludes an entire symbol-week from concentration when any aggregate or firm row has missing/invalid dates, a publication lag outside 21/22 days, or \`lastUpdateDate != initialPublishedDate\`. Phase 385 does not relax that quarantine.

Even if Phase 385 passes, a historical return test remains unauthorized until an effective-dated security-master/universe identity gate establishes symbol continuity, inactive/delisted security handling, and overlap with the frozen LTM/F80 comparison universe. T1 is a defined subset of NMS securities, not the entire equity market; it must not be treated as a complete broad universe.

## Controls

No forward returns, alpha, chronological OOS, bootstrap, LOO or holdout test. No use of the consumed legacy holdout. No changes to F80, production, universe, capital, exposure or parameters. No raw rows, symbols, MPIDs, CRDs or firm names are persisted.

## Official source documentation

- FINRA OTC Transparency Data User Guide v5: https://www.finra.org/sites/default/files/OTC-transparency-data-user-guide-v5.pdf
- FINRA Weekly Summary API documentation: https://developer.finra.org/docs#query_api-equity-weekly_summary

## Execution trail

- Phase 375 completed in run 43493465495: 209/209 partitions, 10,917,933 rows, 2,292 pages; 98.633996% revision-stable symbol-week coverage and 96.943175% stable share-volume coverage. Phase 375 disposition: exhaustive retrieval/bridge/revision-stability PASS; strict PIT not yet established.
- Phase 385 will be run once from the dedicated branch. No duplicate workflow will be launched while it is active.
