# Smart Money Research — Phase 666 state addendum

**Cutoff:** 2026-11-27 16:36 UTC  
**Phase:** 666 — SEC 13F-HR/A amendment-burst and PIT audit  
**Repository base:** `main` `6919a03ca2da8da4b6a428c29e088531cba300f9`

## Current update

- Latest SEC 13F capture [run 46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554) succeeded on both jobs and all four feeds. Artifact [15212890251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554/artifacts/15212890251).
- The poll retained 44 accession observations and emitted 15 new canonical events, all 13F-HR/A dated 2026-11-27.
- Fourteen accessions share the unverified path-CIK candidate 0001778131; one has candidate 0001046192. All are bounded metadata-only; 0/15 are research-eligible or signal-eligible.
- A secondary EDGAR-derived index maps the 14-accession 0001778131 batch to BI Asset Management and 14 historical quarter-ends from 2023-03-31 through 2026-09-30. Its accepted timestamps match the feed's `updated` values 14/14, but this does not replace primary SEC acceptance verification.
- Two filings (#22 for Q2 2026 and #23 for Q3 2026) are individually identified by the secondary filing pages as restatements superseding original accessions #7 and #8. The other 12 amendment types remain unadjudicated. The 0001046192 accession's manager, period, amendment type and parent remain unverified.
- SEC FAQ 58b–58c confirms that restatements supersede originals while new-holdings amendments supplement them. Historical holdings must therefore be versioned by filing vintage; never backdate later corrections to quarter-end/original filing availability.

## Decision

`KEEP_METADATA_ONLY_NO_PROMOTION`. Preserve the 15 events as metadata. Do not treat the 14 filings as independent managers or as fresh trades. Do not use secondary manager mappings or feed-updated timestamps to satisfy identity/acceptance gates.

Next: retrieve primary SEC submission/header, cover-page amendment type/number, original accession, information table, and Accepted timestamp for each accession; then reconcile CUSIP/class to effective-dated ticker and historical F80 membership. Only afterward consider event-time testing against frozen LTM/F80.

## Other source status

- Form 144: latest live capture [46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465) succeeded; later Phase 665 PR checks skipped live capture.
- FINRA: no new natural capture after Phase 661 was present in the latest 30 runs; the next scheduled capture remains the first test of the symbol-volume panel.
- Form 4: latest reviewed structured capture remains [45976055356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45976055356); no newer live capture in the latest run window.
- SEC 13D/G Phase 616 live sample remains pending. The available GitHub connector supports reading runs and repository files but does not expose a new workflow-dispatch action in this run, so no manual dispatch was attempted.

No prices or post-event returns inspected; no OOS, bootstrap, or LOO run; holdout untouched; no data purchased; spend USD 0. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

Full audit: [Phase 666](PHASE666_SEC_13F_HR_A_AMENDMENT_BURST_PIT_AUDIT_2026-11-27.md).
