# Phase 293 — second-filer N-PORT public short positive controls

**Audit date:** 2026-11-11  
**Status:** NPORT_HARDENED_CLASSIFIER_TWO_PUBLIC_FILERS_26_SELECTED_ROWS_PASS_NO_RAW_BYTES_NO_ALPHA

## Executive result

The hardened Phase 292 N-PORT direct-short row classifier now passes **26 manually selected public-filing rows across two distinct registrants and two report periods**:

- Cromwell Long Short Fund (CIK 0001872253), accession 0001145549-24-071567, report date 2024-09-30: 3 positive controls.
- ACAP Strategic Fund (CIK 0001467631), accession 0001145549-25-033457, report date 2025-03-31: 23 selected positive controls.

The second filing was already examined in Phase 217. Phase 293 replays its 23 line-referenced selected U.S. common-equity short rows through the stricter Phase 292 classifier using exact CUSIP, U.S. country, NS share units, EC common equity, CORP issuer type, explicit Short payoff, and negative share balance/USD value/NAV percentage.

This is useful evidence that the corrected row predicate is not tailored only to the Cromwell filing. It is still a selected fixture sample, not a raw parser validation, complete-filing census, prevalence estimate or economic test.

## Independent second filing

SEC filing detail:
\`https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/0001145549-25-033457-index.html\`

- CIK: 0001467631.
- Fund: ACAP Strategic Fund.
- Period of report: 2025-03-31.
- Filing/acceptance: 2025-05-28, 16:04:35 ET.
- Conservative next full XNYS session candidate: 2025-05-29.
- Phase 217 selected 23 U.S. common-equity direct-short rows with unique CUSIPs and source-line ranges.
- The filing's rendered Part A shows no EDGAR series identifier; Phase 293 therefore does not claim that longitudinal fund-series identity has been established.

The rendered primary document was spot-checked for Public Storage, Kilroy Realty, Thermo Fisher Scientific, Campbell Soup, Tesla and ServiceNow. The public filing also contains foreign short common-equity rows and derivative-option rows; these are not part of the 23 selected U.S. physical common-equity short controls. The classifier's country, asset-category, unit and payoff gates keep those distinct.

## What this does and does not establish

Established:
- The Phase 292 predicate accepts the three Phase 291 Cromwell rows after exact identifier, U.S.-country and sign-concordance checks.
- It also accepts the 23 selected ACAP rows from a different registrant and a different report date.
- The Phase 292 five negative controls remain in force.
- The old descriptive-title dependency is unnecessary; structured classification and exact identifiers carry the row decision.

Not established:
- Raw XML/submission bytes or SHA-256 provenance.
- Exhaustive Part-C holdings parsing or random/representative sample selection.
- Amendment/vintage lineage and first-public receipt time.
- Longitudinal series identity (the ACAP fixture has no series ID).
- Effective-dated CUSIP/ISIN-to-primary-listing crosswalk.
- Coverage of the frozen 335-name universe or historical active/delisted securities.
- Direct-short position changes, predictive value, incremental information versus LTM/F80, costs, bootstrap/LOO or OOS performance.

## Validation

The dedicated workflow compiles and runs Phase 221, 291, 292 and 293 regression modules, then emits a metadata-only artifact. Expected positive controls: 26 across two registrants; Phase 292 negative controls: 5. The workflow enforces that raw bytes/hashes, PIT admission, alpha, return tests, bootstrap/LOO, holdout and production changes remain false.

## Decision

Keep N-PORT direct-short unadmitted. This is a stronger cross-filer row-classification control, not evidence that institutional short positions predict future returns. Next substantive gate remains raw, hash-verified accession retrieval, complete per-filing Part-C parsing, amendment state reconstruction, public-availability clocks, effective-dated security identity and historical universe coverage. No further synthetic source-audit expansion is warranted until those data gates are met.

## Controls

No SEC automated request was sent; no contact secret was read or changed; no raw filing bytes were downloaded or hashed; no vendor was contacted; no data was purchased; no return/alpha test, bootstrap/LOO or holdout use occurred. F80 remains frozen, and production, universe, capital and parameters remain unchanged.


## GitHub Actions validation — completed 2026-11-11 18:10 UTC

Dedicated run [43075250170](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43075250170) completed successfully on workflow-trigger commit \`02d658aa82126a035aac32eadfe58bb5ee72f9a8\`. Job \`second-filer-audit\` passed compilation, all four regression modules and the final cross-filer/no-alpha gate.

- **29/29 tests passed**.
- Second-filer ACAP selected positive controls: 23/23.
- Combined selected positive controls: 26 across two distinct registrants.
- Existing negative controls: 5/5.
- Artifact: [13879983178](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43075250170/artifacts/13879983178), SHA-256 \`fdedf37b1d62674e114ae848e835f830feb39d700f3ca950b091955161b838f1\`.

The artifact confirms the sample is non-exhaustive; raw XML/submission bytes and hashes, first-public receipt, longitudinal series identity, PIT admission, prevalence, alpha, return tests, bootstrap/LOO, holdout and production changes remain false. F80 remains frozen.
