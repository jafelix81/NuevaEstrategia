# Phase 460 — Form 4 schema-gated owner attribution and split-event guard

**Audit date:** 2026-11-17  
**Disposition:** Remove the synthetic line-owner-reference path from Phase 459 until an exact element is validated against the applicable SEC Ownership XSD. Keep every multi-owner transaction line quarantined. Add a conservative detector for explicit same-event split remarks; it flags candidates but never merges accessions or deduplicates transaction rows.

## 1. Operational preflight

- Main HEAD: `a2d7e7f9c32c1d5e30b479173ba5e71e765f9cd6` (Phase 459).
- Latest Actions run: [44128628627](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44128628627), PR CI completed successfully. Its single `offline-regression` job passed 9/9 tests; it produced no artifact because the workflow is offline-only.
- Companion push run [44128606444](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44128606444) also completed successfully.
- Actions API: 7,699 total runs in the first-page repository snapshot; no queued/in-progress runs among the latest 50.
- Branches: 292 (100 + 100 + 92); open PRs: 56; workflow files in the main tree: 73.
- Latest scheduled SEC Form 144 run remains [44083941814](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44083941814). Its offline job passed, but live capture failed before Phase 454 was merged because the old CSV header shifted columns; the acceptance parser attempted to cast a timestamp to CIK. The Phase 454 PR regression [44086525354](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44086525354) passed 24/24 offline tests, but live capture was skipped on PR CI. No post-migration scheduled live capture appears in the latest run list through 2026-11-17 16:58 UTC, despite the configured `47 * * * *` cron. Workflow enabled state is not exposed by the available read interface; do not infer that it is disabled.
- FINRA one-settlement run [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) failed at the credential preflight before any API request. OAuth secrets remain a human configuration gate.

No workflow was dispatched, rerun or duplicated during this preflight.

## 2. Phase 459 code review: synthetic owner references were too permissive

Phase 459 correctly quarantined ordinary multi-owner lines, but its helper also accepted generic tags such as `reportingOwnerCik`, `ownerCik`, `ownerCikRef` and `reportingOwnerRef` when artificially placed inside a transaction node. The tests proved only that the helper recognized those invented fixture tags; they did not prove that any such element is valid in SEC Ownership XML v5.5.

The SEC's current technical-specifications page lists Ownership Forms 3/4/5 v5.5 dated 2026-03-18. Its published change note names `issuerForeignTradingSymbol`, `rptOwnerNonUSAddressFlag`, `rptOwnerNonUSStateTerritory` and `rptOwnerCountry`; it does not document a transaction-to-owner foreign key. The exact v5.5 ZIP could not be unpacked in this run: the web retrieval endpoint rejected the binary ZIP content type and the container had no DNS/network access. Therefore this phase does **not** claim exhaustive XSD inspection.

Official specification index: https://www.sec.gov/submit-filings/technical-specifications  
Direct v5.5 ZIP: https://www.sec.gov/files/edgar/filer-information/specifications/ownershipxmltechspec-v5-5.zip

A current 2026 Form 4 XML sample (schemaVersion X0609) shows repeated `reportingOwner` blocks followed by a separate `nonDerivativeTable`; the retrieved sample does not expose a transaction-level owner key. This is supporting sample evidence, not proof that every possible v5.5 element was inspected:
https://www.sec.gov/Archives/edgar/data/1889867/000089914026000592/form4.xml

**Code correction:** the helper now has an empty schema-approved line-owner reference allowlist. It never assigns a multi-owner transaction line from a guessed tag. It records unverified owner-like tokens for diagnostics only. A sole reporting owner can still be assigned at filing grain. The v5.5 XSD gate remains explicitly `NOT_VERIFIED_FAIL_CLOSED`.

## 3. New split-event finding: the 30-row limit creates same-owner multi-form disclosures

Phase 459 documented one split mechanism: more than ten reporting persons. A second, distinct mechanism appears in a current SEC example for Circle Internet Group (issuer CIK 0001876042; reporting-owner CIK 0001539940; Jeremy Allaire):

- First Form 4: accession 0001876042-26-000217, period of report 2026-07-06. Its remarks say it is the first of two Forms 4 for the same reporting person's transactions on that date; the split was required because more than 30 rows could not be entered on one Form 4.
  https://www.sec.gov/Archives/edgar/data/1876042/000187604226000217/wk-form4_1783544406.xml
- Second Form 4: accession 0001876042-26-000218, same issuer, reporting person and transaction date. Its remarks say it is the second of two Forms 4 and that both should be read together as one consolidated filing.
  https://www.sec.gov/Archives/edgar/data/1876042/000187604226000218/wk-form4_1783544456.xml

This is one disclosure event split across two accessions, not two independent insiders. The forms contain multiple direct/indirect and trust-related lines. Do not discard those lines or assume identical price/quantity rows are duplicates: aggregate the explicit split at the owner-event level, retain line provenance, and deduplicate only with line-level evidence.

A second current XML example shows the separate ten-reporting-person cap: a Coursera Form 4 with two reporting-owner blocks says it is the first of two Forms 4 for the same event because more than ten reporting persons were involved. The retrieved XML uses schemaVersion X0609 and keeps owner blocks separate from the transaction table:
https://www.sec.gov/Archives/edgar/data/1889867/000089914026000592/form4.xml

This second example is a candidate split disclosure. Without the companion accession and exact identity reconciliation, it is not automatically linked to another filing.

## 4. Conservative event and owner policy

1. **Single-owner filing:** transaction lines may be associated with the sole reporting owner at filing grain, not with an inferred execution account.
2. **Multi-owner filing:** quarantine every transaction line from owner-level breadth/cluster features until an exact XSD-approved transaction-owner link or independently verified exhibit is demonstrated.
3. **Split due to >10 reporting persons:** mark as an explicit same-event split candidate; never treat accession count as independent-buyer count. Do not automatically join without exact issuer/event/owner-set or designated-filer identity evidence.
4. **Split due to >30 rows:** when both filings explicitly say first/second of two and identify the same issuer, reporting owner and transaction date, group the accessions as one disclosure event. Retain all transaction lines and provenance; do not deduplicate rows merely because price/quantity patterns repeat across trusts.
5. **Amendments:** remain vintage updates, not new trades. Apply a correction only from its own EDGAR acceptance/first-seen time.
6. **No backdating:** transaction date and period of report are event descriptors, not the market-knowledge timestamp.

The new split-remarks helper only classifies explicit text. It does not fetch filings, infer a companion accession, merge events, assign owners or alter signal data.

## 5. Research disposition

- **Killed:** bulk-only multi-owner owner-count clustering (Phase 459).
- **Disabled pending XSD proof:** generic/synthetic transaction-owner reference tags.
- **Quarantined:** all multi-owner lines without a schema-validated foreign key or independently verified exhibit.
- **Conditional:** single-owner filing-grain Form 4 candidates, subject to transaction-code/amount/footnote/10b5-1/amendment/security-class/PIT gates.
- **New candidate grouping rule:** explicit first/second-of-two same-event split remarks, with separate reason codes for the ten-owner and 30-row caps.
- **Not admitted:** new alpha, forward-return test, OOS, bootstrap, LOO or production feature.

No raw SEC filing, vendor data or binary schema package was committed. No live SEC request or return test was performed. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 6. Next gates

1. Obtain and unpack the exact v5.5 ZIP; compare the XSD elements for Form 4/4-A transactions, reporting owners and signatures. Only then may a non-empty line-owner allowlist be considered.
2. Retrieve the complete XML and companion accession for the Coursera >10-owner split; measure whether any exhibits create deterministic owner-to-line links.
3. Extend split detection across historical archives, but group only with explicit remarks plus effective-dated issuer/owner/event keys.
4. Confirm a post-Phase-454 scheduled SEC Form 144 capture and configure FINRA OAuth credentials before any live retrieval.

`F80_TOP20_PARTIAL50_BASELINE_C20` and all production controls remain unchanged.
