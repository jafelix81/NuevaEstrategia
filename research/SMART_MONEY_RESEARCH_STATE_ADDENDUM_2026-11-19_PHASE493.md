# Smart Money Research state addendum — Phase 493 (2026-11-19)

- **Phase 493 merged:** PR #149, merge commit `1adc01aeef5e8bf951e40b7e469af2b51aaf948e`.
- **SEC Form 4/4-A provenance:** the initial baseline contains 35 canonical unique accessions (10 Form 4, 25 Form 4/A) from 70 parsed feed accession occurrences. The page-only legacy observation ledger cannot reconstruct the exact same-feed/cross-feed duplicate split or every feed-path CIK variant.
- **New control:** the collector now appends `research/data/sec_form4_first_seen/accession_observations.csv`, preserving per-accession feed occurrences, watermark boundaries, duplicate classifications, unverified path CIKs, page hashes and suppressed incomplete-poll candidates. It does not store raw Atom payloads or filing XML/text. The first baseline is not backfilled.
- **Validation:** [Run 44439202893](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44439202893), 39/39 offline tests passed; live capture skipped.
- **Form 4 eligibility remains zero:** all 35 initial rows have no lower bound; no public availability, owner attribution, transaction semantics or historical F80 membership is certified.
- **Form 144:** 247 ledger rows; 55 bounded metadata observations, 50 possible-gap quarantines, 142 baseline rows; 0 signal-eligible.
- **CFTC:** 3,039 row hashes, latest report date 2026-11-10 across four contracts; 52-week prospective warm-up not met.
- **FINRA:** Phase 20B/20C not promoted; no prospective Reg SHO ledger.
- **Operational:** no scheduled run appears after the 2026-11-18 20:55 UTC Form 144 capture in the current inventory. Form 4/144/CFTC/FINRA cron declarations remain unchanged; administrative workflow-enabled state is not exposed by the read interface. No manual dispatch or schedule change.
- **Strategy:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No backtest, event study, OOS, bootstrap, LOO or holdout test; no new signals admitted.
