# Smart Money Research state addendum — Phase 614

**Date:** 2026-11-25 UTC  
**Phase:** 614 — SEC 13F prospective first-seen metadata capture

- Added an independent, metadata-only SEC 13F Atom collector and an offline-only PR validation workflow.
- Captures exact 13F-HR, 13F-HR/A, 13F-NT and 13F-NT/A feed families; records accession-level first-seen poll intervals, hashes and conservative filing-date floors.
- Uses the existing throttled SEC fetch helper. No filing XML, INFOTABLE holdings, paid data or raw market data are downloaded or persisted.
- Bounded first-seen metadata remains ineligible for research features and signals until manager identity, security identity, historical F80 membership and public-availability gates pass.
- The scheduled workflow is hourly on weekdays and becomes active only after merge. Manual live diagnostics require explicit \`run_live_capture=true\` and do not persist.
- Initial offline validation [Run 45554185580](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45554185580) passed 23/23 tests. After adding a fail-closed regression for a full 100-entry page followed by an empty page without a boundary, final validation [Run 45554609362](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45554609362) passed 24/24 tests; the live-capture job was skipped as designed. No live SEC request was made in this phase.

Latest source status at preflight:
- FINRA Reg SHO: 7/7 latest HTTP-200 daily files rejected for overlapping duplicate BCPC/TPC rows; 14 duplicate occurrences / 14 extra rows; zero accepted files or signals.
- CFTC TFF: 3,043 rows, no new reports/revisions; zero signal-eligible historical rows.
- Form 4: 593 new canonical accessions, 24 transaction details and 10 owner rows appended; zero signal-eligible rows.
- Form 144: 135 new accessions, 912 detail rows appended; cumulative 659 accessions / 4,503 rows; 218 detail backfills pending; zero signals. Four sell-to-cover/tax-withholding notices remain negative controls, not executions.

Current priority: begin prospective 13F first-seen accumulation after merge, then reconcile acceptance timestamps, amendment state, manager roles and effective-dated CUSIP/FIGI-to-F80 identity before any economic test.

No alpha demonstrated. No OOS, bootstrap or LOO test run. No production or baseline change. \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
