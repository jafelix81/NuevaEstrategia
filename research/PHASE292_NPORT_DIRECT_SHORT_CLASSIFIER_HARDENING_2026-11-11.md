# Phase 292 — N-PORT direct-short classifier hardening

**Audit date:** 2026-11-11  
**Status:** CLASSIFIER_HARDENED_PUBLIC_RENDERED_XML_FIXTURE_PASS_NO_RAW_BYTES_NO_ALPHA

## Executive result

A review of the Phase 291 correction found that its title-substring fix was directionally correct but the replacement predicate was too permissive relative to the preregistered Phase 219 direct-short hypothesis. The Phase 291 classifier checked negative share balance and structured common-equity/corporate fields, but it did not require U.S. investment country, sign concordance of USD value and NAV percentage, or row-level exact CUSIP/ISIN agreement. Its three positive-control tests also did not pass currency value, percentage, CUSIP or ISIN into the classifier. The Phase 291 commit message included \`[skip ci]\`; GitHub reports zero check-runs on that commit, so its newly added test file had not been executed by Actions.

Phase 292 closes those gaps and runs an offline workflow against the existing manually transcribed public SEC filing fixture. It does **not** download or parse raw XML bytes, admit a PIT panel, or test alpha.

## Public source reconciliation

The official SEC-rendered primary document for accession \`0001145549-24-071567\` shows:

- DAY / CUSIP 15677J108 / ISIN US15677J1088: balance -4,447 shares, USD value -272,378.75, NAV percentage -0.2848831381, payoff Short, Equity-common, Corporate, United States.
- CLX / CUSIP 189054109 / ISIN US1890541097: balance -1,920 shares, USD value -312,787.20, NAV percentage -0.3271466629, same structured classification.
- CDW / CUSIP 12514G108 / ISIN US12514G1085: balance -1,115 shares, USD value -252,324.50, NAV percentage -0.2639082358, same structured classification.

The SEC N-PORT data dictionary identifies the flattened fields \`ISSUER_CUSIP\`, \`BALANCE\`, \`UNIT\`, \`CURRENCY_VALUE\`, \`PERCENTAGE\`, \`PAYOFF_PROFILE\`, \`ASSET_CAT\`, and \`ISSUER_TYPE\`. The rendered primary filing also displays the investment country. The issuer/title string remains descriptive and is not required to contain the words "Common Stock".

Source line references from the SEC-rendered primary document:
- DAY: lines 464–493.
- CLX: lines 737–766.
- CDW: lines 282–311.

SEC data dictionary: \`https://www.sec.gov/files/nport_readme.pdf\`, especially the FUND_REPORTED_HOLDING field definitions around lines 521–551 of the PDF text.

## Corrected fail-closed predicate

A row can be classified as a direct short only when all of the following hold:

1. The caller supplies an exact expected CUSIP and/or ISIN, and each row matches at least one supplied identifier without conflict.
2. \`UNIT=NS\`, \`ASSET_CAT=EC\`, \`ISSUER_TYPE=CORP\`, and \`INVESTMENT_COUNTRY=US\`.
3. \`PAYOFF_PROFILE=Short\`.
4. \`BALANCE<0\`, \`CURRENCY_VALUE<0\`, and \`PERCENTAGE<0\`, all finite.
5. The existing series, filing-completeness, as-filed vintage, prior-public-Part-C and corporate-action gates still pass.

Long rows used in an exact-security Part-C absence search must have positive balance, value and percentage. Missing identifiers, wrong CUSIP/ISIN, non-U.S. country, non-common equity, sign conflicts, missing/non-finite values and unknown payoff profiles fail closed. Ticker alone is never accepted as an identity key.

## Validation scope

- Existing Phase 221 semantic cases: 13, updated to include exact identifiers and the complete sign/country fields.
- Phase 291 public filing positive controls: 3 rows, now pass all classifier fields rather than only the share balance.
- New Phase 292 negative controls: non-U.S. country, positive USD value, positive NAV percentage, wrong CUSIP, and missing identifiers; all must remain UNKNOWN.
- The dedicated GitHub Actions workflow compiles the relevant modules, runs all three test modules, emits a metadata-only JSON result, and checks that no alpha/PIT/holdout/production gate was opened.

The positive controls are manually transcribed from the SEC's rendered primary filing page. This is not a raw XML parser validation: no raw XML bytes were downloaded or hashed. No bulk archive was retrieved, no series/security longitudinal panel was built, and no return, bootstrap, LOO or OOS test was run.

## Decision

Keep N-PORT direct short unadmitted. The classifier is now stricter and the public-filing fixture is a better positive control, but raw-byte provenance, as-filed amendment lineage, first-public timing, fiscal-month public coverage, effective-dated CUSIP/ISIN-to-listing identity and broad-universe coverage remain open. Do not infer that reported short positions represent trade flow, beneficial-owner conviction, or profitable bearish information.

## Controls

- \`SEC_CONTACT_EMAIL\` was not read, changed or supplied.
- No SEC automated request was sent.
- No vendor was contacted and no data was purchased.
- No alpha or return test, bootstrap/LOO, or holdout use occurred.
- F80 remains frozen; production, universe, capital and parameters remain unchanged.
- The consumed legacy holdout remains unavailable for reuse.


## GitHub Actions validation — completed 2026-11-11 18:05 UTC

Dedicated run [43074329311](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43074329311) completed successfully on commit \`d20874ca28734d1d6ec05099eb51f877965b2e39\`. Job \`offline-classifier-audit\` passed compilation, all three test modules and the final no-alpha/data-control gate.

- **26/26 tests passed**: 14 Phase 221 semantic tests, 3 Phase 291 public-filing controls and 9 Phase 292 hardening tests.
- Public rendered-document positive controls: 3/3.
- Negative controls: 5/5.
- Artifact: [13880167054](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43074329311/artifacts/13880167054), SHA-256 \`321ef631c94d4a5a3b5909a07b7ddc1e497be2c2527ffc7a52a3aef9d5e6f3a2\`.
- The artifact records raw XML bytes/hash, automated SEC requests, strict PIT admission, alpha, return tests, bootstrap/LOO, holdout use and all production changes as false; F80 remains frozen.

The validation is offline and fixture-based. It does not establish raw XML parsing, bulk-history coverage, first-public timing, longitudinal fund/security identity or economic predictability.
