# Smart Money Research — Phase 670 state addendum

**Cutoff:** 2026-11-27 20:59:00 UTC  
**Phase:** 670 — SEC 13F Canada Life primary-source and value-unit anomaly audit  
**Base:** `main` `833ffe6057336de47a73dcc29628d44a191ef5a6`

## Update

- Rechecked the latest 100 Actions runs, jobs, logs, artifacts, branches, open PRs and research files. The latest 100 runs comprise 78 success, 18 failure and 4 cancelled; zero active/queued runs. Main remains at the Phase 669 merge commit `833ffe6057336de47a73dcc29628d44a191ef5a6`.
- Phase 476 Form 4 scheduled run [46057111964](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964) succeeded. Its live log confirms 94 new bounded metadata accessions, 201 keyed entity observations, 21 transaction-detail rows, 30 transaction-linked footnote references, 50 additional footnote references, 10 single-owner accessions and zero research/signal-eligible rows. The 5,979-byte artifact contains a compact poll summary, not raw filing XML.
- Phase 614 SEC 13F scheduled run [46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554) succeeded. Its log confirms 15 new accession metadata observations, all four feeds complete, zero research/signal-eligible observations. The 873-byte artifact contains only `poll_summary.json`, not filing XML or holdings rows.
- The SEC archive's primary information-table XML for Canada Life amendment `0001046192-26-000018` is now identified and indexed: [13F_Filing_Sep26.xml](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000018/13F_Filing_Sep26.xml). Four ordinary common-stock rows (B, BBWI, BLK, MRVL) are exposed in the indexed XML. Multiplying their filed values by 1,000 produces implied prices within 0.11% of 2026-09-30 closes. This independently corroborates the base filing's AAPL/AMZN unit anomaly.
- Important limitation: the complete XML bytes could not be downloaded/read by the current interface, so no raw SHA-256 exists and the 806 rows have not been fully parsed or normalized. The four-row sample is not a full-table audit; automatic rescaling remains prohibited.
- A secondary filing-chain index reports acceptance at 2026-11-27 15:10:56 UTC and ingestion at 15:11:30 UTC; its acceptance timestamp matches the SEC Atom `feed_updated_utc`. The secondary source also links base accession `0001046192-26-000015`. The official SEC filing index, primary parent link and first-public-availability timestamp remain unverified.
- PRs #255–#258 are merged in order. PR #259 (Phase 670) remains an open documentation-only draft pending the updated evidence record. Older 13F sequence/knowledge-clock PRs #221–#230 remain untouched.
- Phase 616's 13D/G live sample and Phase 469's FINRA live capture were skipped on PR-triggered runs; neither was manually dispatched. No scheduled workflow was duplicated.

## Decision

`PRIMARY_BASE_AND_AMENDMENT_SAMPLE_UNIT_ANOMALY_STRONGLY_CORROBORATED_ADDITIVE_AMENDMENT_PRIMARY_CLASSIFIED_NO_SIGNAL_PROMOTION`.

The base report has two primary row-level checks; the amendment has four additional indexed-primary row samples. This is strong evidence of a factor-1,000 anomaly in both filing vintages, but it is not a full 806-row normalization or a validated trading signal. Preserve all as-filed values and filing vintages.

No post-event returns, event study, OOS, bootstrap or LOO test was run. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No data purchase; spend USD 0.

## Next

1. Retrieve and hash the complete amendment information table through the established SEC User-Agent path.
2. Parse and reconcile all 806 rows against the base filing; test for mixed units and non-common-stock exceptions.
3. Verify the official acceptance index and exact parent accession, and keep first public availability as a separate bound.
4. Build and test a fail-closed unit detector on known positive and negative controls before any normalization.
5. Continue scheduled FINRA, Form 4, Form 144, 13F and CFTC captures without duplicate manual dispatch.
