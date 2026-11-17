# Phase 461 — SEC Ownership v5.5 schema owner-link audit

**Audit date:** 2026-11-17  
**Disposition:** The pinned v5.5 schema mirror contains no transaction-to-reporting-owner foreign key in either Form 4 or Form 4/A. The transaction tables are structurally separate from the repeated reporting-owner blocks. Keep the line-owner allowlist empty and quarantine every multi-owner transaction line. The official SEC ZIP could not be byte-for-byte verified in this runtime, so the mirror provenance caveat remains explicit.

## 1. GitHub preflight before changes

- Main HEAD: `f7c24f7203fd4fe07be93fe106fa62261d091b31` (Phase 460, merged PR #121).
- Actions API: 7,703 total runs. Explicit `status=in_progress` and `status=queued` queries each returned zero.
- Latest Phase 460 PR run [44133573427](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44133573427) and companion workflow run [44133573367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44133573367) both passed 16/16 offline tests; neither produced artifacts.
- Branch push run [44133517450](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44133517450) also passed 16/16. Earlier run [44133170761](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44133170761) failed one split-remarks fixture; the subsequent commit corrected the fixture/recognition and the later runs passed.
- Branches: 293 (100 + 100 + 93). Open PRs: 56. Workflow files in main tree: 74.
- Latest scheduled SEC Form 144 run remains [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814), failed before Phase 454 was merged. No post-Phase-454 scheduled live capture appears in the latest 30-run list. Workflow enabled state is not exposed by the available read interface.
- FINRA live preflight [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) stopped before any API request because OAuth credentials were absent at that time.
- No workflow was dispatched, rerun or duplicated during this preflight.

## 2. Schema source and provenance

The SEC's official [Technical Specifications index](https://www.sec.gov/submit-filings/technical-specifications) lists Ownership (Forms 3, 4, 5) version 5.5 dated 2026-03-18. Its published change note describes the 2026 foreign issuer/owner-address elements: `issuerForeignTradingSymbol`, `rptOwnerNonUSAddressFlag`, `rptOwnerNonUSStateTerritory` and `rptOwnerCountry`. The SEC page does not publish the XSD inline; the official ZIP endpoint returned an unsupported `application/zip` response in the web retrieval path, and direct binary download failed in the container.

To avoid treating a sample XML as an exhaustive schema, I inspected a pinned public mirror whose README states that its `ownership-xml-v5.5/schemas/` directory contains the reduced-content XSDs from the SEC v5.5 package and identifies the SEC technical-specifications page and ZIP as their source:

- Mirror repository: [alexkouzel/sec-api](https://github.com/alexkouzel/sec-api)
- Pinned commit: `50ac70b32e987c1dae2b747d499d86e964c1428e`
- README checked by that repository: 2026-10-23.
- `ownership4Document.xsd.xml`: Git blob `715807c0260af7b321afdc10933e718d68903a8a`, 8,604 bytes.
- `ownership4ADocument.xsd.xml`: Git blob `c0b1617bbe11b1b759a51cd2b1a332bf3d809912`, 8,733 bytes.
- `ownershipDocumentCommon.xsd.xml`: Git blob `c9f9da0b9cb4799894da50103ef7fb2290e76b7c`, 49,228 bytes.

**Provenance limitation:** these are pinned mirror blobs, not a byte-for-byte comparison against the SEC ZIP. The mirror README notes that the reduced-content XSD header comments still say X0306 while their contents include the 2026 v5.5 address elements. Therefore the schema-content finding is strong and reproducible against the pinned mirror, but official-archive hash identity remains unverified. No XSD files were copied into this repository.

## 3. Form 4 and Form 4/A structure

The inspected Form 4 and Form 4/A schemas define the same transaction structure.

**NONDERIVATIVE_TRANSACTION** direct sequence:

1. `securityTitle`
2. `transactionDate`
3. `deemedExecutionDate`
4. `transactionCoding`
5. `transactionTimeliness`
6. `transactionAmounts`
7. `postTransactionAmounts`
8. `ownershipNature`

**DERIVATIVE_TRANSACTION** direct sequence:

1. `securityTitle`
2. `conversionOrExercisePrice`
3. `transactionDate`
4. `deemedExecutionDate`
5. `transactionCoding`
6. `transactionTimeliness`
7. `transactionAmounts`
8. `exerciseDate`
9. `expirationDate`
10. `underlyingSecurity`
11. `postTransactionAmounts`
12. `ownershipNature`

Neither transaction type contains `rptOwnerCik`, `reportingOwnerCik`, `ownerCik`, `reportingOwnerRef`, `ownerRef` or another transaction-to-owner reference. The referenced nested transaction types also do not introduce such a field.

The common schema defines `REPORTING_OWNER` separately, with `reportingOwnerId`, address and relationship. `REPORTING_ID` contains `rptOwnerCik`, `rptOwnerCcc` and `rptOwnerName`; these fields identify the reporting-owner block, not a transaction row.

## 4. Root order, cardinality and identity constraints

The Form 4 root sequence is:

`schemaVersion → documentType → periodOfReport → notSubjectToSection16 → issuer → reportingOwner* → aff10b5One → nonDerivativeTable? → derivativeTable? → footnotes? → remarks? → ownerSignature*`.

- `reportingOwner`: `maxOccurs=10`.
- `ownerSignature`: `maxOccurs=10`.
- `nonDerivativeTable`: at most one table; its choice permits up to 30 transaction/holding rows.
- `derivativeTable`: at most one table; its choice independently permits up to 30 transaction/holding rows.
- The inspected Form 4, Form 4/A and common schemas contain zero `xs:any`, `xs:anyAttribute`, `xs:key`, `xs:keyref` or `xs:unique` constructs.

The 30-row maximum is **per table**, not a universal combined cap of 30 across both derivative and non-derivative tables. The Circle filing remarks remain valid evidence for that specific split, but the classifier must not infer that every Form 4 with more than 30 total rows across both tables necessarily requires two filings.

## 5. Research disposition

1. **Resolved for the pinned v5.5 mirror:** no schema-defined transaction-to-owner foreign key exists in Form 4 or Form 4/A.
2. **Killed:** any bulk/XML-only attempt to attribute individual transaction rows inside a multi-owner filing using owner order, signature order, proximity, roles, generic tags or inferred CIK references.
3. **Keep quarantined:** all multi-owner transaction rows for individual-insider breadth, clustering and buyer-count features. The schema provides no row-level mapping.
4. **Still admissible conditionally:** a single-owner filing may be attributed at filing grain only. This does not establish the beneficial execution account or prove an open-market purchase.
5. **Still conditional:** a separate exhibit or other independently verified document could support an external owner-to-line mapping for a specific filing; that evidence must be accession-specific and must not be generalized to the XML schema.
6. **Split events:** explicit same-event remarks can group accessions as one disclosure event after exact issuer/owner/date matching. Preserve every line and accession provenance; never deduplicate transaction rows without line-level proof.
7. **No alpha admitted:** no forward-return, incremental-value, OOS, bootstrap, LOO or holdout test was run.

Phase 458's two endpoint samples found 15.794% (2012Q1) and 13.390% (2026Q3) of P-coded transaction rows inside multi-owner accessions. Thus most P-coded rows in those two endpoint cohorts were not in multi-owner filings, but two endpoints are not a full-history prevalence estimate. The single-owner subset remains a feasible candidate for the next full-history coverage audit; it is not yet a predictive signal.

## 6. Version drift and next gates

The SEC technical-specifications page also lists draft Ownership v5.6 dated 2026-11-06, planned for EDGAR Release 26.4 on 2026-12-07. It is explicitly a draft and not yet effective. Re-run this structural audit after the release date before changing the allowlist or parser contract.

Next research steps:

1. Extend the single-owner filing census across all 83 quarterly archives (2006Q1–2026Q3), with hashes and no bulk-archive-date backdating.
2. Join every candidate to EDGAR acceptance and prospective first-seen clocks.
3. Reconstruct effective-dated issuer, ticker, share-class and historical-universe membership before measuring 335-name coverage.
4. Keep 4/A as amendment vintages, not new trades; preserve 10b5-1 absence as unknown in pre-field eras.
5. Revisit multi-owner lines only when an accession-specific exhibit provides explicit, independently verifiable attribution.

No raw SEC data, schema ZIP or vendor data were committed. No live SEC request or vendor request was made. `F80_TOP20_PARTIAL50_BASELINE_C20`, capital, exposure, universe, holdout and production remain frozen.
