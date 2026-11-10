# Phase 253 — SEC Form 144 registered-security XBRL identity gate

**Audit date:** 2026-11-10 UTC  
**Disposition:** conditional positive identity evidence only; no complete crosswalk, no PIT admission and no alpha.

## Executive result

The SEC's April 2026 EDGAR XBRL Guide provides a structured way to identify a registered security by its title, class context, listing context, exchange and trading symbol. But the Guide explicitly says that no instance type requires either registered-security title fact, Security12bTitle or Security12gTitle. Their absence is therefore unknown, not evidence that the issuer has no listed security.

This makes raw as-filed iXBRL a useful positive-evidence source, but not a complete crosswalk census. The SEC Company Facts API only aggregates facts applying to the filing entity as a whole; dimensioned class/listing facts require the original filing context. A visible cover-page table fallback may improve coverage, but it has not yet been validated across the Form 144 issuer panel.

## 1. SEC identity semantics

The April 21, 2026 SEC EDGAR XBRL Guide, §§3.2.4.1–3.2.4.4, establishes:

- Security12bTitle / Security12gTitle identify registered-security titles, but neither title fact is required for every instance type.
- StatementClassOfStockAxis and ClassesOfShareCapitalAxis distinguish registered share classes.
- EntityListingsExchangeAxis is separate: it distinguishes multiple exchange listings of the same security, not share classes.
- For a 12(b) security, SecurityExchangeName is paired with Security12bTitle in the same context, except for the ADR dimension exception.
- TradingSymbol and NoTradingSymbolFlag are mutually exclusive. If neither is present in a normalized context, the result remains unknown; it is not converted into an explicit no-symbol state.

Company Facts is not a complete class-level crosswalk because the SEC API aggregates only facts applying to the whole filing entity. The raw filing's iXBRL contexts are needed for dimensioned securities.

Sources:
- SEC EDGAR XBRL Guide, April 21, 2026: https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-04-21.pdf
- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Inline XBRL overview: https://www.sec.gov/data-research/structured-data/inline-xbrl

## 2. Primary-document examples

**Flowco, 2026 Form 10-Q/A:** its cover page lists Class A common stock as FLOC on both NYSE and NYSE Texas, while separately reporting Class A and Class B shares outstanding. This demonstrates why a class axis and a listing axis must not be collapsed. The filing says the amendment corrected only certifications and did not update later events.  
https://www.sec.gov/Archives/edgar/data/2035149/000119312526294682/floc-20260331.htm

**Noodles & Company, 2015 Form 10-Q/A:** the amendment corrected an original Class A share count that had accidentally included Class B shares, and states that the original filing continues to speak as of its original date. Amendments must be separate as-filed vintages; they cannot rewrite earlier knowledge.  
https://www.sec.gov/Archives/edgar/data/1275158/000127515815000046/q1201510qa.htm

**UWMC, 2023 8-K XBRL instance:** one issuer CIK contains distinct Class A common-stock and warrant security contexts, with separate symbols. CIK alone is not a security identifier.  
https://www.sec.gov/Archives/edgar/data/1783398/000178339823000040/xbrl-20231108_htm.xml

## 3. Actual Form 144 panel audit

Input was the immutable Phase 69 artifact from run 41959603351, artifact 13385365595. The ZIP and expanded CSV SHA-256 values were verified against the pinned hashes in the machine result.

| Measure | Result |
|---|---:|
| Issuer-event accessions | 21,634 |
| Original Form 144 notices | 21,438 |
| 144/A amendments | 196 |
| Issuer CIKs | 289 |
| Original sale tranches | 21,653 |
| Distinct raw security-class labels | 166 |
| Labels after case/whitespace normalization only | 135 |
| Issuers with 2+ raw labels | 233 / 289 |
| Issuers with 2+ normalized labels | 205 / 289 |
| Issuers with an explicit Class A/B/etc. label | 71 |

The exact generic label Common occurs in 12,562 tranches. Of those, 11,036 occur in issuers with multiple raw labels, and 3,297 occur in issuers that also have an explicit class-letter label.

These are text-heterogeneity diagnostics, not counts of distinct legal share classes. Labels may be variants, generic descriptions, ADR/ADS descriptions or other security descriptions. The results show why generic Common cannot safely be mapped to one ticker for an issuer with multiple security contexts.

## 4. Implemented fail-closed contract

The committed offline helper and 23 regression tests:
- preserve contextRef, class axes, listing axes and member QNames separately;
- reject conflicting title facts, duplicate values, multiple class/listing members in one context, and simultaneous TradingSymbol/NoTradingSymbolFlag;
- distinguish explicit no-symbol from unknown symbol;
- match Form 144 class text only by exact case/whitespace-normalized title—no fuzzy match, issuer-CIK fallback or current-ticker fallback;
- preserve multiple listings of the same class;
- select only a strictly earlier issuer-filing vintage for a Form 144 event; same-day ties without acceptance ordering remain unknown; later amendments are never backdated.

Local validation: **23/23 tests passed**. No Phase253-specific hosted workflow was added; the Phase253 tests have not yet run in GitHub Actions.

## 5. Admission gates and next step

| Gate | Status |
|---|---|
| Official XBRL identity semantics | PASS |
| Phase 69 panel hashes and class-label audit | PASS |
| Normalized context / class join / PIT selector | PASS, 23/23 local |
| Raw iXBRL parser validated against source bytes | NOT TESTED |
| Visible cover-page fallback across issuers | NOT TESTED |
| Registered-security fact coverage across 289 CIKs | NOT MEASURED |
| Exact Form 144 class-to-title match rate | NOT MEASURED |
| Effective-dated listing history, including inactive/delisted securities | NOT ESTABLISHED |
| PIT daily dollar-volume / ADV20 | NOT AVAILABLE |
| Returns, alpha, bootstrap/LOO, chronological OOS | NOT RUN |

Next gate is a stratified 20–30 issuer raw-iXBRL and visible-cover-page pilot spanning generic Common, explicit A/B/C, ADR/ADS, multiple registered securities, multiple exchange listings and amendments. For each event, use the latest filing strictly before the Form 144 filing date, preserve each accession/vintage and raw SHA-256, and measure exact-match coverage before scaling to all 289 issuers. If the tagged facts are absent, a visible-table fallback is admissible only after separate validation. Exact matches or manually adjudicated aliases are allowed; fuzzy matching is not.

Bulk SEC retrieval remains blocked because the authorized GitHub secret SEC_CONTACT_EMAIL is absent. No SEC bulk request was sent and no email was guessed. ADV20 remains separately blocked by the absence of an admitted survivorship-free, corporate-action-aware daily dollar-volume series. No paid data source was contacted or purchased.

## 6. Controls

No forward returns, event study, alpha, bootstrap/LOO, chronological OOS or holdout test was run. The consumed legacy holdout was not reused. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, capital or trading parameter changed. No vendor contact, trial, card authorization or data purchase occurred.

## Reproducibility

- Source panel: Phase 69 run 41959603351 / artifact 13385365595.
- Helper: https://github.com/jafelix81/NuevaEstrategia/blob/phase231-cboe-option-quotes-full-row-reparse/research/phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Tests: https://github.com/jafelix81/NuevaEstrategia/blob/phase231-cboe-option-quotes-full-row-reparse/research/test_phase253_form144_xbrl_registered_security_crosswalk_audit.py
