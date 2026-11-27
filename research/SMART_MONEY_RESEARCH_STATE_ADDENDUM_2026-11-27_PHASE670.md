# Smart Money Research — Phase 670 state addendum

**Cutoff:** 2026-11-27 20:49:57 UTC  
**Phase:** 670 — SEC 13F Canada Life primary-source and value-unit anomaly audit  
**Base:** `main` `833ffe6057336de47a73dcc29628d44a191ef5a6`

## Update

- Reconciled latest Actions runs/jobs/artifacts; no active or queued run was present.
- Phase 476 Form 4 scheduled capture (run 46057111964) succeeded: 94 new bounded metadata accessions, but no research-eligible or signal-eligible rows.
- Phase 614 SEC 13F scheduled capture (run 46026323554) succeeded: 15 new 13F-HR/A metadata accessions, but no filing XML/holdings rows in the 873-byte poll-summary artifact and zero research/signal-eligible observations.
- Primary SEC evidence now verifies Canada Life Q3 2026 base filing `0001046192-26-000015` has a strong legacy-thousands value-unit anomaly: AAPL and AMZN row-level implied prices become accurate within 0.14% of 2026-09-30 closes after multiplying filed values by 1,000.
- Primary SEC `primary_doc.xml` verifies Canada Life amendment `0001046192-26-000018` is a 13F-HR/A, amendment type NEW HOLDINGS, combination report, 806 entries, filed summary value 8,531,520. The amendment information table and official acceptance index are still unavailable in the current evidence set.
- SEC Atom `updated` is 2026-11-27T15:10:56Z and page receipt is 15:36:23Z; this remains bounded metadata only, not certified public availability.
- PRs #255–#258 are merged in order. Open 13F knowledge-clock/sequence PRs #221–#230 remain untouched.
- Phase 616's 13D/G live sample and Phase 469's FINRA live capture were skipped on PR-triggered runs; neither was dispatched manually.

## Decision

`PRIMARY_BASE_REPORT_UNIT_ANOMALY_STRONGLY_CONFIRMED_ADDITIVE_AMENDMENT_PRIMARY_CLASSIFIED_NO_SIGNAL_PROMOTION`.

The Canada Life base 13F must not be ingested with a universal nearest-dollar assumption without a quality-control check. Do not auto-scale any filing from date alone. Keep raw values and filing vintages intact. The 806-row amendment is an additive quarter-end disclosure, not a trade tape.

No post-event returns, event study, OOS, bootstrap or LOO test was run. Contemporaneous prices were used only for unit validation. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Data spend USD 0.

## Next

1. Retrieve/hash the amendment information table and official index.
2. Build a fail-closed unit detector and test it on known correct and known legacy-thousands filings.
3. Verify the remaining ten BI amendments.
4. Preserve filing-specific PIT clocks and historical CUSIP/ticker identity before any signal test.
5. Continue FINRA and 13D/G natural/authorized capture gates without duplicating workflows.
