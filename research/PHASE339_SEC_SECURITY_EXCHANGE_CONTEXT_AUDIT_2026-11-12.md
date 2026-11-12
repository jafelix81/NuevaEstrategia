# Phase 339 — SEC registered-security, symbol and exchange-context audit

**Final status:** COMPLETED_HASH_VERIFIED_IDENTITY_DIAGNOSTIC  
**Final run:** [43249238927](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43249238927) — success, 10/10 offline regressions.  
**Artifact:** [13959007527](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43249238927/artifacts/13959007527).  
**Scope:** the 42 prior-periodic XBRL instance documents from the fixed, stratified 72-issuer Phase 338 sample.

## Retrieval correction and reproducibility

The first retrieval attempt omitted the SEC Submissions primary-document name and therefore could not select the XBRL instance. It quarantined all 42 attempts as NO_PRIMARY_DOCUMENT_OR_INSTANCE. This was a retrieval-manifest omission, not evidence of absent filings or facts. The corrected run re-resolved each exact accession from the issuer's SEC Submissions JSON, verified form and filing date, supplied the recovered primaryDocument to the Phase 328 instance selector, and compared the resulting instance bytes with the Phase 338 SHA-256. All 42/42 documents reproduced exactly. All 42 primary-document lookups were found in the recent Submissions arrays; no historical shard was needed.

- Phase 338 artifact ZIP SHA-256: 30b6a5b6753b24e8bd5d810d4193396249ed3f64de259e2fb8ef9513e29ecf92.
- Phase 338 audit JSON SHA-256: 0bcd8f355bd697d804296caeffd67fd69ff6aa593b8a5643535ad2f0224027a8.
- Phase 338 sample-manifest SHA-256: 9cca7f3eb027776dff89a4b44a0b234386ead708d758051a2b5e604f6d43736a.
- Phase 339 artifact ZIP SHA-256: 186bd582c8cd0ffff73cda16c7331e5a2bd34e413b6aba3715b5fac430a0a66f.
- Phase 339 result JSON SHA-256: 4560b26f6cb37db8a3cf499207643026aab7e4e309ef8c7cf496b9e02d2d9e15.

## Correct SEC XBRL semantics

The SEC EDGAR XBRL Guide dated 2026-02-17, sections 3.2.4.1–3.2.4.4, governs this audit:

- SecurityExchangeName is paired with Security12bTitle in the same context, and only that context.
- SecurityExchangeName is relevant to 12(b) securities; Security12gTitle is not expected to carry a national-exchange name.
- EntityListingsExchangeAxis is used for multiple listings; its absence is not evidence of no listing and is consistent with one listing.
- SecurityExchangeName values are EDGAR-defined national-exchange codes; venues outside that scope are not tagged. NONE is an explicit value, not a missing fact.
- TradingSymbol is a separate concept. A symbol-to-security association is admitted here only when TradingSymbol, Security12bTitle and SecurityExchangeName share the exact contextRef.

Official source: https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-02-17.pdf

## Findings

| Measure | Result |
|---|---:|
| XBRL instance documents re-fetched and byte-hash verified | 42/42 |
| Documents with TradingSymbol facts | 35/42 |
| Documents with Security12bTitle facts | 35/42 |
| Documents with SecurityExchangeName facts | 35/42 |
| TradingSymbol fact rows | 61 |
| Security12bTitle fact rows | 61 |
| SecurityExchangeName fact rows | 61 |
| Symbol/title/exchange exact same-context triples | 61/61 |
| Symbol-bearing documents with triple linkage | 35/35 |
| XBRL documents with 12(b)-title/exchange pairing | 35/42 |
| Security12gTitle facts | 1 |
| EntityListingsExchangeAxis on symbol contexts | 0 |

The exact same-context triple was present for every one of the 61 TradingSymbol facts. This is strong evidence that SEC XBRL can bind a symbol to a specific 12(b) security title and national-exchange status when the facts are present. It is not a permanent security identifier and does not establish effective-dated listing history.

Design-weighted descriptive coverage was 86.3121% among the 42 verified XBRL documents for a 12(b)-title/exchange pair, and 100% among the 35 symbol-bearing XBRL documents. Across the entire Phase 338 sample, only 35/72 issuer-quarter units had symbol facts (48.61% unweighted; 48.06% design-weighted). The 86.31% figure is conditional on the XBRL subset; it must not be presented as universe-wide coverage.

Exchange fact values: NYSE 41, NASDAQ 19, NONE 1. Thus 60 facts carry an EDGAR national-exchange code and one (CMBMF) explicitly reports NONE. The NONE observation is not a national listing.

No symbol context in this sample carried EntityListingsExchangeAxis. The SEC guide explains why that is not a failure: a single listing does not require the axis. The sample showed one exchange code per security context; it does not prove that issuers never have multiple listings.

## Instrument-type contamination check

A transparent title-text classification of the 61 security titles (not an official security master) produced:

| Provisional title class | Rows |
|---|---:|
| Common equity / ordinary shares | 37 |
| Debt / senior notes | 13 |
| Preferred (non-depositary) | 3 |
| Depositary shares / ADS | 5 |
| Warrants | 2 |
| Corporate units | 1 |
| **Total** | **61** |

This matters: 24/61 symbol rows are not plain common equity under this conservative text classification. In particular, the AMT filing contributed 13 debt symbols plus one common-stock symbol. A ticker-only mapping would have contaminated a common-equity universe with debt, preferred/depositary securities, warrants and corporate units. All original titles and class-axis members remain preserved in the artifact; the text classification is a diagnostic, not a final instrument master.

## Limits and next gate

Phase 338 chose a prior periodic filing strictly before the Form 4 filing date. It did **not** establish that the anchor predates each underlying Form 4 transaction date. A Form 4 may report transactions occurring before its own filing date, so this identity result cannot yet be used for a transaction-date event study. The next gate is to retrieve the 72 sampled Form 4 documents, parse each transaction date and securityTitle, and verify that the identity anchor predates every transaction being evaluated. If not, the affected transaction must be quarantined or mapped to an earlier filing. The first-public timestamp of the periodic filing is also not established beyond SEC filing-date granularity.

No permanent security master, effective-dated listing history, strict PIT event panel, full universe coverage, alpha/return/OOS, bootstrap/LOO or holdout admission. No production, universe, capital or parameter changes; no data purchase or vendor contact. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
