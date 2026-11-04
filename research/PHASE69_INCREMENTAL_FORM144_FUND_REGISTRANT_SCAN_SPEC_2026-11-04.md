# Phase 69 — Incremental Form 144 scan for newly mapped fund registrants

**Date:** 2026-11-04  
**Branch:** \`phase71-original-universe-rule-trace\`  
**Status:** Code and 8 hosted regression tests passed; latest Phase 67 rerun reconciled SUCCESS; incremental SEC scan is now authorized.

## 1. Completed Phase 67 baseline

The latest successful Phase 67 run 41828179718 produced artifact 13334881835 (artifact digest SHA-256 \`939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613\`). The earlier successful run 41828139052 / artifact 13327123059 produced the same core counts; the later run is the pinned baseline for Phase 69. Its full 14-quarter census (2023Q2–2026Q3) passed the predeclared XML identity gate:

- 21,648 current-CIK candidate accessions processed.
- 21,634 issuer-event rows: 21,438 Form 144 originals and 196 Form 144/A amendments.
- 14 filer-only false positives excluded from the issuer-event file.
- 0 unresolved candidates, 0 XML fetch/processing errors, 0 duplicate accessions.
- XML pair concordance, distinct issuer/filer CIKs and form concordance: 100%.
- 280 zero-candidate controls: 100% master-pair concordance.
- Candidate mapping at the time: 308/335 tickers, 309 CIKs; 27 current tickers were unresolved.

This is a current-CIK issuer-role identity pass, not historical F80 membership, PIT security identity, accepted-time availability, fund-series attribution or economic evidence. No returns were calculated.

The later Phase 67 run 41828179718 has now completed successfully (job 126605281463); all tests, the 14-quarter XML resolution step and artifact upload completed. Its artifact 13334881835 is available and is the pinned Phase 69 baseline. No Phase 67 or Phase 69 data scan is currently active.

## 2. Phase 68 mapping expansion

Phase 68 run 41828426133 passed and artifact 13321546076 confirms:

- 335/335 current universe tickers mapped.
- 319 candidate registrant CIKs.
- 0 mapping-source errors.
- 10 additional CIKs relative to Phase 67's 309-CIK set.

The ten new registrant CIKs are:

| CIK | Current mapped ticker(s) |
|---|---|
| 0001579982 | ARKF, ARKG, ARKK, ARKQ, ARKW |
| 0001174610 | BITO |
| 0001100663 | IEFA, IWM, SOXX |
| 0001540305 | JETS |
| 0001064642 | KRE, XBI |
| 0001137360 | OIH, SMH |
| 0000923202 | VEA |
| 0000734383 | VNQ |
| 0000857489 | VWO |
| 0001064641 | XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY |

The CIK map is registrant-level. The SEC fund map also supplies seriesId/classId; those values are retained. A trust-level Form 144 must not be assigned to every ticker sharing a registrant.

## 3. Implemented incremental method

Script: \`research/phase69_form144_incremental_fund_registrant_scan.py\`  
Tests: \`research/test_phase69_form144_incremental_fund_registrant_scan.py\`

The script:

1. Requires the exact Phase 67 completed baseline output from run 41828179718 / artifact 13334881835 and validates its summary and row counts before using it.
2. Rebuilds the live Phase 68 current mapping and fails closed unless all 335 tickers map, there are exactly 319 CIKs, all ten new CIKs are present, and the remaining old set is exactly 309 CIKs.
3. Reads the same 14 quarterly master indexes (2023Q2–2026Q3).
4. Fetches XML only for accessions whose master-index pair contains at least one of the ten new CIKs. The candidate set for each selected pair includes **all 319** current CIKs, so any old/new overlap is reclassified as unique or ambiguous using the expanded set.
5. Reuses Phase 67's XML issuerCik/filer CIK and proposed-sale/acquisition/prior-sale parser. No role is inferred from archive path or filer identity.
6. Compares every overlapping accession's XML issuer, filer, master-index pair, form and filing date with the Phase 67 baseline. Any difference fails the gate.
7. Replaces overlap classifications in the expanded baseline, adds genuinely new accessions, and rebuilds the issuer-event panel. A previous filer-only event is removed if expanded identity resolves it differently.
8. Preserves ticker mapping, fund series/class candidates, incremental rows, overlap reclassification, expanded rows/events, controls, errors and summary as separate artifacts.

The scan is deliberately incremental; it does not redownload or reprocess all 21,648 baseline XMLs.

## 4. Predeclared acceptance gates

- Exact baseline artifact validation.
- 335/335 current tickers, 319 CIKs and the ten preregistered new CIKs.
- XML fetch success >=99.5%.
- Explicit issuer/filer role resolution >=99.9%.
- XML/master-index pair concordance, distinct CIKs and form match >=99.9%.
- 100% XML identity consistency for accessions overlapping Phase 67.
- 100% concordance for deterministic zero-candidate controls.
- Zero duplicate expanded accessions.
- Zero filer-only rows in the expanded issuer-event panel.
- No silently unclassified rows or XML processing errors.

Any gate failure is preserved in the artifact; do not relax thresholds or drop difficult records.

## 5. Workflow coordination

The latest Phase 67 run 41828179718 is complete; the former concurrency hold is removed. A dedicated Actions workflow now downloads artifact 13334881835 by run ID, runs the incremental scan once, and uploads the expanded panel. The workflow uses a non-cancelling concurrency group so duplicate Phase 69 scans cannot overlap.

The Phase 69 code has seven regression tests covering exact CIK-set expansion, incomplete-map rejection, rejection of a wrong legacy set with matching counts, overlap reclassification, identity mismatch detection, event removal/addition and strict baseline validation. The script also reconstructs the old mapper without the SEC symbol field to verify the exact 309-CIK baseline before any SEC index scan. Hosted Actions run 41847627672 (job 126635192916) passed all eight tests after adding an exact 27-name legacy-unresolved snapshot check; earlier run 41847339213 passed the initial seven-test suite. The full SEC scan is launched by the dedicated Phase 69 data workflow; results remain pending until its artifact is inspected.

## 6. Remaining limitations

Passing Phase 69 will establish only a larger current-CIK Form 144 candidate census. It will not establish:

- Historical ticker/CIK effective dates or historical F80 membership.
- Security-level identity for funds sharing one registrant CIK.
- Historical delisted/predecessor issuer coverage.
- Accepted/publication timestamps or first-known availability.
- Complete seller/security-class amendment lineage.
- Actual execution of proposed sales.

Form 144 remains a selective proposed Rule 144 sale-order notice, not proof of execution and not a complete insider-selling feed. Form 144/A is an update record, not a new sale event by default.

No forward returns, feature selection or alpha tests are authorized in Phase 69. The historical security-master/universe PIT gate from Phase 70 remains a hard blocker before broad alpha promotion.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.


## 7. Latest execution reconciliation (2026-11-04)

- GitHub Actions run 41828179718 completed SUCCESS at 2026-11-04T14:46:06Z; job 126605281463 completed the full 14-quarter resolution and uploaded artifact 13334881835 (14,656,596 bytes; SHA-256 digest `939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613`).
- The artifact was downloaded and independently inspected. `summary.json` reports 21,648 candidate rows, 21,634 issuer-event rows, 14 filer-only false positives, zero unresolved rows/errors/duplicates, 280/280 controls, and 100% XML/index/form concordance. It still uses the pre-Phase-68 309-CIK / 308-of-335 ticker map; 27 tickers are unresolved in that baseline.
- The newer Phase 67 artifact is the pinned baseline for this scan. The Phase 69 script constants now identify run 41828179718 and artifact 13334881835. The data workflow is separate from the unit-test workflow; the latter's run 41847627672 passed all 8 tests but performed no SEC requests.
- Phase 67 is no longer active. No forward returns or alpha tests are authorized by this scan.
