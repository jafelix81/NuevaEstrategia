# Phase 339 — SEC SecurityExchangeName and 12(b) security-context audit

**Status:** corrected protocol committed; awaiting a hash-verified rerun.  
**Source:** Phase 338 run 43236684291, artifact 13953101909.  
**Scope:** the 42 prior-periodic XBRL instance documents from the fixed, stratified 72-issuer sample.

## Method correction before interpretation

The first Phase 339 attempt passed a blank primary-document name to the Phase 328 retrieval helper. The helper correctly refused to guess an XBRL instance, so 42/42 attempts were quarantined with NO_PRIMARY_DOCUMENT_OR_INSTANCE. This was a retrieval-manifest omission, not evidence that SEC documents or exchange facts were missing. The diagnostic was retained; no data from that attempt are admitted.

The corrected workflow re-resolves each exact selected accession through the issuer's SEC Submissions JSON and, when needed, its date-covering historical shard. It verifies form, filing date, primary-document name and the original Phase 338 instance SHA-256 before parsing any fact.

## SEC taxonomy semantics

The SEC EDGAR XBRL Guide (2026-02-17), sections 3.2.4.2–3.2.4.3, says that SecurityExchangeName is paired with Security12bTitle in the same context, and only that context. It also distinguishes no national-exchange listing, one listing, and multiple listings. EntityListingsExchangeAxis is multi-listing evidence; its absence is not a negative test for a single listing. SecurityExchangeName uses EDGAR-defined national-exchange codes and does not cover every trading venue.

Official guide: https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-02-17.pdf

Accordingly, the corrected audit separates:
1. Security12bTitle + SecurityExchangeName in the same context (12(b) security-level exchange evidence).
2. TradingSymbol + Security12bTitle + SecurityExchangeName in the same context (a direct symbol-to-12(b)-security/exchange context).
3. EntityListingsExchangeAxis on the symbol context (additional multi-listing evidence).
4. Document-level co-occurrence, which is not a mapping.
5. Security12gTitle, which is not expected to carry the national-exchange pairing.

## Frozen source and reproducibility

- Phase 338 artifact ZIP SHA-256: 30b6a5b6753b24e8bd5d810d4193396249ed3f64de259e2fb8ef9513e29ecf92.
- Phase 338 audit JSON SHA-256: 0bcd8f355bd697d804296caeffd67fd69ff6aa593b8a5643535ad2f0224027a8.
- Phase 338 sample-manifest SHA-256: 9cca7f3eb027776dff89a4b44a0b234386ead708d758051a2b5e604f6d43736a.

## Results

No empirical findings are admitted until all 42 primary documents and instance hashes reproduce exactly. The failed initial retrieval is preserved as a diagnostic and is not pooled with the corrected run.

## Controls

F80 remains frozen. No security master, strict PIT source, effective-dated listing history, universe coverage, alpha/return/OOS, bootstrap/LOO, or holdout admission is authorized by this audit. No production, universe, capital, or parameter change; no vendor contact or purchase.
