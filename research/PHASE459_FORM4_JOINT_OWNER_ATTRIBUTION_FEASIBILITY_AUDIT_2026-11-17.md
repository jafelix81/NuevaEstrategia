# Phase 459 — Form 4 joint-owner attribution and duplicate-event feasibility gate

**Audit date:** 2026-11-17  
**Disposition:** Kill the bulk-only multi-owner-count proxy for insider breadth. Quarantine transaction lines from joint/group accessions unless a line has explicit, unique owner linkage in the source document or an independently verified exhibit. Do not count separate accessions as independent trades when the filing text says they are split reports of the same event.

## 1. Why Phase 458's remaining gate matters

Phase 458 found that 15.794% of P-coded non-derivative rows in 2012Q1 and 13.390% in 2026Q3 sit inside accessions with multiple reporting owners. This is too large to treat as a negligible edge case. A naive owner-count feature can turn one shared beneficial-ownership report into several apparent insider purchases; assigning every row to every owner multiplies the same transaction. The opposite error is also possible: a joint filing may include securities owned separately by different filers.

## 2. Current SEC Form 4 instructions: joint filings can mix shared and separately owned securities

The SEC's current Form 4 (SEC 1474, 03-26) explicitly distinguishes an individual filing from a joint/group filing in Item 6. General Instruction 4(b)(v) states that:

- where multiple beneficial owners must report the same transaction, they may file individually or jointly;
- joint and group filings may be made by a designated beneficial owner;
- transactions in securities owned separately by any joint/group filer may also be included in the joint filing;
- the filing must include required information for each beneficial owner and be signed by each beneficial owner or an authorized person.

This means a multi-owner accession is not equivalent to multiple independent trades, and it is not necessarily one shared trade either. It can contain both shared beneficial ownership and separately owned securities. The number of reporting owners cannot be used as the number of buyers.

Official current form: https://www.sec.gov/files/form4.pdf (accessed 2026-11-17; Item 6 and General Instruction 4(b)(v), PDF pp. 1 and 8).

## 3. XML structure does not provide a general transaction-to-owner foreign key

The SEC's Ownership XML Technical Specification v3 (April 2010) documents the structure as separate sibling sections: repeated reportingOwner blocks (up to ten) followed by a nonDerivativeTable and derivativeTable. The transaction row schema contains transaction/security/amount/ownership fields but no reporting-owner CIK field. The same specification says there is no primary reporting owner, owner order is not important, signatures are not tied to reporting owners, signature order does not matter, and the number of signatures need not equal the number of reporting owners.

Official historical XML specification: https://www.sec.gov/files/info/edgar/ownershipxmltechspec-v3.pdf, especially §§3.5, 4.3.2 and 4.3.7 (accessed 2026-11-17).

The current SEC technical-specifications page lists Ownership Forms 3/4/5 version 5.5 dated 2026-03-18. Its published change note adds issuer foreign trading symbol and non-U.S. reporting-owner address elements. The v5.5 ZIP itself was not unpacked in this audit, so this report does not claim a fresh exhaustive inspection of every current schema element. The current Form 4 instructions and the bulk-table grain already establish that owner count is not transaction count. Before any future owner-line parser is promoted, inspect the exact v5.5 package and stratified current filings.

Current specifications index: https://www.sec.gov/submit-filings/technical-specifications.

## 4. Real SEC example: one economic event split across accessions

Two SEC ownership XML filings for issuer CIK 0001612720, period of report 2018-06-11, explicitly describe a two-form split for the same event because the filing involved more than ten reporting persons:

- First filing: accession 0001140361-18-028469. Its remarks say it is the first of two Forms 4 relating to the same event and that the filing was split because there were more than ten reporting persons.
  https://www.sec.gov/Archives/edgar/data/1612720/000114036118028469/form4.xml
- Companion filing: accession 0001140361-18-028465. Its remarks identify the corresponding second filing for the same event.
  https://www.sec.gov/Archives/edgar/data/1612720/000114036118028465/form4.xml

This is a concrete duplicate-event hazard: accession count is not necessarily economic-event count. Counting each filing as a separate independent insider signal can overstate breadth and flow. The filing's own remarks/exhibits are the evidence for grouping; do not infer a split merely from similar dates or transaction amounts.

## 5. Quantitative impact inherited from Phase 458

| Measure | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Form 4 / 4-A accessions | 63,678 | 34,148 |
| Accessions with multiple reporting owners | 1,134 (1.781%) | 854 (2.501%) |
| P-coded accessions | 4,136 | 3,211 |
| P-coded accessions with multiple owners | 380 (9.188%) | 238 (7.412%) |
| P-coded rows in multi-owner accessions | 1,134 / 7,180 (15.794%) | 694 / 5,183 (13.390%) |

These are two endpoint cohorts, not a full-history prevalence estimate.

## 6. Conservative machine policy

The accompanying helper is deliberately narrow:

1. A single-owner filing may be attributed to its sole reporting owner at filing grain, subject to the normal transaction-quality, footnote, amendment, 10b5-1, security-identity and PIT gates.
2. A multi-owner filing is quarantined unless a transaction line contains an explicit, unique owner reference that resolves to exactly one reporting-owner CIK.
3. Owner order, signature order, signature count, role/title, addresses, or proximity in the XML must never be used to assign a transaction to an owner.
4. Free-text footnotes and exhibits may be reviewed as separate evidence, but the helper does not guess from names or narrative text.
5. Repeated or split filings for the same event are candidate duplicate disclosures, not independent trades. Merge only with explicit same-event evidence; otherwise quarantine from breadth/cluster counts.
6. An unresolved line remains issuer-level descriptive context at most; it is not an owner-level purchase observation.

This policy is fail-closed. It is not a transaction classifier and does not authorize a signal.

## 7. Research disposition

- **Killed:** FORM4_MULTI_OWNER_OWNER_COUNT_CLUSTER when derived from bulk owner counts alone.
- **Quarantined:** multi-owner transaction lines without explicit unique line-to-owner evidence.
- **Still conditional:** single-owner Form 4 purchase candidates, after confirming P/A semantics, market-vs-private purchase, 10b5-1 status where available, amendment vintage, security class, historical universe membership, and first-public-availability clock.
- **Not admitted:** any new alpha, forward-return study, OOS test, bootstrap, LOO or production feature.

## 8. Next gates

1. Inspect the exact Ownership XML v5.5 ZIP and compare its owner/transaction/signature schema with v3.
2. Retrieve a stratified sample of multi-owner filings plus all referenced joint-filer exhibits; measure what fraction of transaction lines can be deterministically assigned without narrative guessing.
3. Add cross-accession same-event grouping only where filing remarks/exhibits explicitly establish the relation.
4. Continue the full 83-quarter SEC archive pilot only after the monitored-contact SEC_USER_AGENT is configured and first-seen/acceptance clocks are captured prospectively.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameter, capital, exposure, holding-period, holdout or production change was made.
