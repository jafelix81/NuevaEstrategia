# Smart Money Research — Phase 669 state addendum

**Cutoff:** 2026-11-27 after scheduled run 46057111964  
**Phase:** 669 — Form 4 live capture and Form 144/Form 4 crosswalk audit  
**Main:** `193a246959ac053c3c020fe9ca7b9b2ea66b3925`

## Update

- Phase 476 scheduled run [46057111964](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964) succeeded; 82 offline tests passed and both live feeds passed continuity gates.
- Form 4 emitted 94 new bounded accession metadata events and persisted 201 entity observations. Page-offset duplicates were explicitly audited; no issuer CIK mismatches or unkeyed/unknown-role entities were recorded.
- Scheduled backfills parsed 10 accessions for transaction details (21 detail rows, 30 footnote refs), 10 for footnote references (50 refs), and 10 for filing-level owner identity (10 single-owner records). Remaining queues: 3,468 transaction-detail accessions, 40 footnote accessions and 20 owner accessions.
- The Form 144/Form 4 crosswalk contains 16 proposed-sale matches across 15 Form 4 accessions and 11 issuers. Fourteen have Form 144 acceptance before Form 4 acceptance, but execution time is unknown; two Form 144 acceptance clocks are unresolved. All 16 remain signal-ineligible.
- PRs #255, #256 and #257 (Phases 666–668) were merged in order. Current main is `193a246959ac053c3c020fe9ca7b9b2ea66b3925`.

## Decision

`CAPTURE_SUCCESS_DESCRIPTIVE_ONLY_NO_SIGNAL_PROMOTION`.

No prices or post-event returns were inspected. No event study, OOS, bootstrap or LOO test was run. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Data spend USD 0.

## Next

1. Continue scheduled Form 4 polling and bounded enrichment.
2. Require transaction-line owner, exact execution-time evidence, economic-context adjudication and historical F80 membership before testing crosswalk matches.
3. Await the next scheduled FINRA Phase 469 capture; no post-Phase-661 natural live capture appeared in the reviewed latest 50 runs.
4. Continue SEC 13F amendment-vintage and unit-normalization work independently; keep the Canada Life amendment secondary-only until its primary filing documents are retrieved.
