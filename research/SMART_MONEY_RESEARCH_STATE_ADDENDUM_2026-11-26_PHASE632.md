# Smart Money Research state addendum — Phase 632 (2026-11-26 05:40 UTC)

**Main HEAD:** `62dca69d2f7de95139dd07cd6e9c7be8f1c38d1c`

- Form 4 scheduled run [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) succeeded (offline + live). It added 90 canonical accession events and 192 entity observations; the feed gates passed, but exact public availability and signal eligibility remain false.
- The legacy `same_feed_duplicate_occurrences=100` field is repeated accession occurrences, not exact entity duplicates. PR #240 remains Draft/unmerged. Its strict exact-entity sidecar now validates numeric nonzero CIKs; after correcting an over-escaped regex, run [45762887631](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45762887631) passed 79/79 offline tests. Live capture was skipped; no production validation yet.
- The latest 37 transaction-detail rows (10 accessions) contain 11 P-coded acquisitions, but nine TEAM rows are explicitly under a Rule 10b5-1 plan and held indirectly through a trust. Two XBP P-coded rows lack matching owner-sidecar/footnote context and remain unresolved candidates. All 37 rows are signal-ineligible and public-availability-uncertified; 34 are filing-grain-only single-owner rows and three are multi-owner quarantined.
- Form 144/Form 4 crosswalk: 11 descriptive rows (10 proposed sales, one prior-sale history), zero eligible; two proposed-sale acceptance clocks unresolved, seven multi-owner accessions quarantined, and historical F80 membership unverified.
- SEC 13F run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) still fails closed because the scheduled job receives an empty `SEC_USER_AGENT`; no SEC request was made. The code fix is on main, but the Actions secret availability remains unresolved.
- SEC 13D/G runs [45733913256](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733913256) and [45733842155](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45733842155) were PR events; live sample was skipped. The 44-header sample has not run.
- FINRA Reg SHO run [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648): 8/8 HTTP-200 files rejected for BCPC/TPC overlapping facility rows; zero accepted/eligible. Keep fail-closed pending authorized security-grain reconciliation.
- CFTC TFF run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471): 3,043 rows through 2026-11-17, no new reports/revisions, zero eligible.
- Options/MIDAS remain feasibility-only; no vendor contact, quote or purchase. Options-data budget remains USD 0.
- Phase 20C same-day-close remains NO-GO under Phase 593. No new alpha, valid OOS, bootstrap or LOO result.

**Disposition:** no new signals. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no universe, exposure, costs, parameters, holding-period, holdout or production changes.

Full audit: [Phase 632](PHASE632_FORM4_TRANSACTION_QUALITY_AND_CROSS_SOURCE_GATE_RECHECK_2026-11-26.md).
