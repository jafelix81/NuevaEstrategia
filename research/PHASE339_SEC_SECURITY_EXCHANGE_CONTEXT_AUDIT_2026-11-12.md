# Phase 339 — SEC SecurityExchangeName and same-context symbol audit

**Status:** protocol committed; awaiting reproducible GitHub Actions result.  
**Source:** Phase 338 run 43236684291, artifact 13953101909.  
**Scope:** the 42 prior-periodic XBRL instance documents from the fixed, stratified 72-issuer sample.

## Question

Does the SEC's SecurityExchangeName fact occur in the same XBRL context as TradingSymbol, and does the symbol fact itself carry EntityListingsExchangeAxis? These are separate questions. A document-level exchange fact is not a symbol-to-listing mapping, and a same-context exchange-name fact is contextual evidence rather than proof of an effective-dated listed security.

## Frozen source and reproducibility

- Phase 338 artifact ZIP SHA-256: 30b6a5b6753b24e8bd5d810d4193396249ed3f64de259e2fb8ef9513e29ecf92.
- Phase 338 audit JSON SHA-256: 0bcd8f355bd697d804296caeffd67fd69ff6aa593b8a5643535ad2f0224027a8.
- Phase 338 sample-manifest SHA-256: 9cca7f3eb027776dff89a4b44a0b234386ead708d758051a2b5e604f6d43736a.
- The workflow re-fetches only the 42 XBRL instance documents, verifies each byte hash against Phase 338, and retains document-level and fact-level context evidence.

## Classification rules

1. Direct listing-axis evidence requires EntityListingsExchangeAxis on the TradingSymbol fact's own context.
2. Same-context SecurityExchangeName is recorded as contextual evidence, not admitted as a security-master mapping.
3. An exchange fact elsewhere in the document is document-level co-occurrence only.
4. Blank or different context references never create a symbol/exchange association.
5. Preserve class-axis members, listing-axis members, titles, raw exchange strings, source accession, and hashes. Never merge securities or infer a listing from issuer-level facts.

## Results

Results will be appended only after the pinned source has been re-fetched and the Phase 339 workflow has completed. No result is inferred from the Phase 338 aggregate because Phase 338 did not retain SecurityExchangeName fact rows.

## Controls

F80 remains frozen. No security master, strict PIT source, effective-dated listing history, universe coverage, alpha/return/OOS, bootstrap/LOO, or holdout admission is authorized by this audit. No production, universe, capital, or parameter change; no vendor contact or purchase.
