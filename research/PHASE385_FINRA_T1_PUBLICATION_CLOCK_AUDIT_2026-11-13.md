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


## First hosted attempt — systemic query failure and correction

Run [43524460681](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43524460681) passed compilation and all eight offline tests, but failed during the first data-retrieval step. The run completed **0/209** partitions and retained no publication-date observations. Its initial error collector recorded only the exception class (`RuntimeError`), so the precise HTTP response was not preserved; the failure must not be represented as a FINRA data-availability result.

Code review found that this phase added `summaryTypeCode` as a third API compare filter, whereas the proven Phase 371/375 retrieval filters on the dataset's partition keys (`historicalWeek` and `tierIdentifier`) and filters summary types after retrieval. The added filter was not necessary and was not independently validated. Phase 385 is corrected to use the proven partition-key query, paginate the complete T1 response, validate all known T1 summary types, and collect dates only from `ATS_W_SMBL` rows.

The correction also:
- distinguishes the number of target aggregate rows from the full paginated T1 response count;
- adds a regression test for mixed summary-type pagination;
- records a sanitized HTTP status/error detail without response bodies or credentials;
- stops after a first-partition preflight failure instead of repeating a systemic failure across all 209 weeks.

The corrected workflow is configured to run on changes to its script and tests as well as the workflow file. No second run is launched until this corrected commit triggers. No publication-clock conclusion, return test or alpha result is claimed from the failed attempt.


## Second hosted attempt — target-grain filter correction

Run [43536201647](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43536201647) passed compilation and all nine offline tests, and successfully retrieved the first partition's T1 response. It then stopped at the first row because the phase treated every returned T1 summary type as required to belong to the four-type allowlist. The Phase 371/375 implementation intentionally processes the response as a mixed-grain T1 partition and selects `ATS_W_SMBL` only for symbol-level aggregate work.

The second correction now counts observed summary-type labels (including a missing-label bucket), validates the week key on every returned row, ignores non-target summary grains, and calculates the publication clock only from `ATS_W_SMBL`. If the target grain is absent, the failure message reports only aggregate summary-type counts, not symbols or raw records. The full T1 pagination count remains reconciled separately from the target aggregate-row count.

This remains a retrieval/diagnostic correction only. No publication-clock conclusion or return test is claimed until the 209-week census completes.
