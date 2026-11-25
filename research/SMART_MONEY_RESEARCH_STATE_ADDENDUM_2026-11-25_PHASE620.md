# Smart Money Research — state addendum, Phase 620

**Cutoff:** 2026-11-25 15:21 UTC  
**Main reviewed:** `074e3596b6982308889ed33e614ec4e169005ee5`  
**Implementation branch:** `phase620-sec-form4-entity-aware-feed-dedup`

## Latest source evidence

- Form 4 run [45620008946](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45620008946) passed both jobs and persisted 36 unique accessions.
- The 74 candidate feed occurrences comprise 36 accessions: 35 groups with two entity rows and one group with four. All repeated rows are within a page; no cross-page duplicate group was found.
- The repeats represent issuer/reporting-owner entity rows for the same accession, not 38 extra filings. The four-row OrbiMed/Avenzo example is independently corroborated by public filing metadata.
- The prior collector selected the first occurrence as the event locator, which could be a reporting owner. Phase 620 now selects the issuer row, preserves all entity occurrences in a separate append-only sidecar, omits the locator when issuer identity is missing, and quarantines path/title or multiple-issuer conflicts.
- Six focused regression tests were added. The initial PR run failed one test-fixture assertion; after correcting the initial-baseline fixture, [runs 45644057878](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45644057878) and [45644162986](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45644162986) passed `py_compile` and all 69 offline tests. The live-capture job was skipped.

## Limits

- Historical run 45620008946 did not persist Atom titles. Its 74 entity occurrences therefore remain role-unresolved except for the independently checked sample; no retrospective bulk relabeling is claimed.
- Capture cadence remains inadequate for intraday research: 14 successful windows / 13 gaps, median 8.676h, p90 12.490h, maximum 54.964h.
- SEC first-seen receipt remains an upper bound, not exact public availability. No signal is eligible.
- FINRA Reg SHO remains quarantined (7/7 files rejected for duplicate/overlap checks). CFTC TFF remains unchanged at 3,043 records with no new report/revision.
- Form 144/Form 4 crosswalk remains descriptive only: 11 matches, zero signal-eligible; F80 historical membership and execution clocks unresolved.

## Next steps

1. Review Phase 620 PR CI and keep it in draft until tests pass.
2. After an approved integration, let the next natural scheduled capture populate `entity_observations.csv`; do not dispatch an extra live SEC poll.
3. Reconcile the new entity CIK/role rows against Form 4 XML issuer/reporting-owner blocks before owner attribution or transaction-level research.
4. Continue the independent Form 4 cadence audit; do not infer intraday availability from Atom `updated` or first-seen receipt.
5. Continue the SEC 13D/G global-index feasibility line separately; the 44-document live sample remains unexecuted pending its existing approval path.

## Strategy control

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No signal promotion, OOS test, bootstrap, LOO, capital/exposure/universe/cost/parameter change or production change. No options data purchase, quote request or vendor contact; authorized budget remains USD 0.
