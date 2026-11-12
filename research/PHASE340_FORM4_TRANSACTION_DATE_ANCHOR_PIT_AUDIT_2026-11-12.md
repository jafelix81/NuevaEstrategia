# Phase 340 — Form 4 transaction-date identity-anchor PIT audit

**Status:** protocol committed; awaiting GitHub Actions retrieval and reconciliation.  
**Source population:** the exact 72 issuer-quarter Form 4 / Form 4/A accessions selected in Phase 338.  
**Identity source:** the 42 byte-verified prior-periodic XBRL instances from Phase 339.

## Question

Phase 338 selected a prior periodic filing strictly before each Form 4 filing date. That does not prove the selected identity anchor predates the underlying insider transaction date. Form 4 can be filed after the transaction. This phase tests the correct transaction-level chronology before any event study.

## Method

1. Verify the immutable Phase 338 artifact, audit JSON and sample manifest, plus the Phase 339 artifact and audit JSON.
2. Retrieve the exact 72 original Form 4 / Form 4/A submission texts from SEC Archives, validate accession, form, filing date and XML issuer CIK, and hash every retrieved source.
3. Parse each non-derivative and derivative transaction row, including transactionDate, securityTitle, underlyingSecurityTitle, transactionCode, acquired/disposed, shares and price fields.
4. Compare each transaction date to the Phase 338 prior-periodic filing date:
   - anchor strictly before transaction date;
   - same date (not strictly prior);
   - anchor after transaction date (look-ahead);
   - missing/invalid transaction date.
5. Match Form 4 securityTitle to Phase 339 Security12bTitle only by conservative normalized exact text within the same issuer. No fuzzy match is admitted. Derivative underlyingSecurityTitle is evaluated separately.
6. Preserve every raw submission in the 90-day artifact with SHA-256.

## Interpretation limits

A prior filing date before a transaction date is a necessary conservative identity gate, not proof of an effective-dated listing or exact first-public time. EDGAR acceptance is not first public receipt. A strict title mismatch is not proof that two titles represent different securities; it means no automatic link is admitted. This is a data-feasibility audit, not an alpha/event-return test.

## Controls

F80 remains frozen. No transaction-level security mapping, event study, alpha/return/OOS, bootstrap/LOO or holdout admission. No production, universe, capital or parameter changes; no data purchase or vendor contact.
