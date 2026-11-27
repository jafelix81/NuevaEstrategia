# Smart Money Research — Phase 668 state addendum

**Cutoff:** 2026-11-27 18:40 UTC  
**Phase:** 668 — SEC 13F additive-amendment and post-2023 value-unit anomaly triage  
**Parent:** Phase 667, PR #256 (open draft); Phase 666 PR #255 (open draft)

## Update

- Reconciled the 15 Phase 666 13F-HR/A events into 14 BI Asset Management candidate accessions and one separate CIK 1046192 candidate.
- Secondary EDGAR-derived evidence classifies the 14 BI accessions as restatements. Four are primary SEC verified in Phase 667 as value-unit-only restatements; ten remain primary-unadjudicated.
- Secondary evidence identifies `0001046192-26-000018` as a Canada Life Assurance Co combination report / NEW HOLDINGS amendment for 2026-09-30, with 806 rows, supplementing base accession `0001046192-26-000015`. Its reported acceptance time is 2026-11-27 15:10:56 UTC and its value rows are interpreted by that secondary source as legacy thousands.
- The repository's `feed_updated_utc` matches the secondary acceptance time, but the field remains unverified. The primary SEC filing header/XML and acceptance record were not retrieved in this phase.
- This is not 806 trades. It is a purported add-only quarter-end holdings supplement; it must be timestamped at its own availability time.
- The SEC's 2023-01-03 nearest-dollar rule is the expected filing convention, but secondary evidence suggests some later filers may still submit legacy-thousands values. The pipeline needs a conservative implied-price anomaly detector and raw-value preservation.

## Decision

`SECONDARY_TRIAGE_ONLY_NO_SIGNAL_PROMOTION`.

No accession was promoted to research or signal eligibility. No historical F80 membership or public-availability certification was added. No prices/returns, event study, OOS, bootstrap, LOO or holdout data were used. Baseline unchanged; data spend USD 0.

## Next

1. Primary-verify Canada Life's amendment and base filing.
2. Primary-verify the remaining ten BI restatements.
3. Build and validate a conservative unit anomaly detector using CUSIP-specific implied prices and explicit exclusions.
4. Diff original/amended information tables and preserve each filing vintage.

