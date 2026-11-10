# Phase 254 — Form 144 issuer/accession-scoped XBRL class join and prior-vintage gate

**Audit date:** 2026-11-10 UTC  
**Disposition:** scoped normalized join contract PASS; raw iXBRL, panel coverage, strict PIT, ADV20 and alpha remain NOT ADMITTED.  
**Scope:** code-contract hardening only. No SEC bulk request, market-data acquisition, vendor contact, purchase, return test, holdout use or production change.

## Executive result

Phase 253 correctly separated the registered-security class axes from the listing axis, but its generic prior-vintage selector and class resolver relied on caller-side scoping: the selector did not take an issuer CIK, and the resolver did not require contexts to carry one issuer/accession/filing-date identity. Those functions were safe only if every caller prefiltered the inputs perfectly.

Phase 254 removes that implicit precondition:

1. The prior-filing selector requires the Form 144 issuer CIK and selects only that issuer's latest filing strictly before the event filing date.
2. Same-day filing-date ties require timezone-aware acceptance timestamps on that filing date; otherwise the vintage remains unknown.
3. The class resolver accepts only contexts whose issuer CIK, accession and filing date exactly match the selected prior vintage.
4. A class-specific join requires an explicit class-axis member. EntityListingsExchangeAxis alone is not class identity.
5. Multiple listings are reported as the same class only when every matching context has usable listing scope and all contexts agree on the class member and symbol. Incomplete listing scope remains UNKNOWN.
6. Amendments remain their own as-filed vintages; later amendments are never backdated. Exact title matching only; no fuzzy, current-ticker or issuer-only fallback.

This is a data-integrity correction, not evidence of predictive value.

## 1. Why the extra scope guard matters

The Phase 253 `select_prior_vintage(filings, event_date)` helper has no issuer-CIK argument. A caller that accidentally passes a mixed-issuer filing collection could select another issuer's most recent filing. Likewise, `resolve_form144_class(label, contexts)` assumes that the caller has already restricted contexts to one filing accession.

Phase 254 makes issuer and accession scope explicit and fail-closed. This does not claim that Phase 253 actually produced a cross-issuer join; it closes a caller-dependent safety condition before raw filing integration.

## 2. Listing and class semantics

The SEC's [April 21, 2026 EDGAR XBRL Guide](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-04-21.pdf) distinguishes class axes from the listing axis. The resolver therefore does not infer a share class from a listing member.

Two primary-document examples are consistent with this treatment:

- [Flowco 2026 Form 10-Q/A](https://www.sec.gov/Archives/edgar/data/2035149/000119312526294682/floc-20260331.htm) lists Class A common stock as FLOC on both NYSE and NYSE Texas (cover-page table). This is one class with multiple listings, not two share classes.
- [Noodles & Company 2015 Form 10-Q/A](https://www.sec.gov/Archives/edgar/data/1275158/000127515815000046/q1201510qa.htm) separately reports Class A and Class B shares and explains that the amendment corrected an earlier Class A count. The amendment must be a later vintage, not a rewrite of the original filing.

## 3. Implemented contract

New helper: `research/phase254_form144_xbrl_scoped_class_join.py`

New regression suite: `research/test_phase254_form144_xbrl_scoped_class_join.py`

The helper:
- normalizes issuer CIKs without using tickers as identity;
- filters candidate filings to the expected issuer before date selection;
- excludes same-day and future filings from a daily Form 144 event;
- resolves same-day prior-filing ties only with timezone-aware acceptance timestamps;
- preserves 10-K/A and 10-Q/A as independent later vintages;
- rejects missing/mismatched issuer CIK, accession or filing date in normalized contexts;
- requires an explicit class-axis member and a known trading symbol;
- distinguishes multiple listings of one proven class from incomplete/unknown listing scope;
- keeps exact title matching and fails closed on ambiguity.

## 4. Hosted validation

The first hosted run [42763927183](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763927183) passed its then-current 22 tests, but its metadata artifact used a hard-coded count of 21. The test log, not that stale artifact field, is the authoritative record for that first run.

The workflow was corrected to derive the test count dynamically, and two additional regressions were added for incomplete listing scope. Final hosted run:

- [Phase 254 run 42764068968](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968)
- Job: `129656300533`
- Result: **24/24 tests passed**
- [Metadata-only artifact 13738319528](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968/artifacts/13738319528), 381 bytes, SHA-256 `ae7b3269d9fa884e6fe4f0f716b427aacc9d701e9c416175038309c025a81768`

The workflow explicitly records `RAW_IXBRL_COVERAGE=NOT_MEASURED` and `STRICT_PIT_ALPHA=NOT_ADMITTED`.

## 5. Latest regression state

On the same PR branch code head, the existing Cboe workflows completed without being duplicated while active:

- Phase 231 [run 42763911397](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397): **9/9** tests; [artifact 13738991707](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397/artifacts/13738991707), 2,422 bytes. Reparse: 115,617 populated rows; 112,313 unambiguous rows passed; 3,304 ambiguous-expiration rows remain quarantined.
- Phase 249 [run 42763911410](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410): **11/11** tests; [artifact 13738418042](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410/artifacts/13738418042), 1,919 bytes. This remains one public C1 20% sample date, not a historical PIT panel or return test.
- Phase 246: 7/7; Phase 247: 11/11; Phase 248: 29/29; Phase 250: 17/17; Phase 251: 42/42 on the same validation set.

At the latest check, the last 30 workflow runs were successful and no workflow remained active.

## 6. Remaining blockers and next gate

| Gate | Status |
|---|---|
| Normalized context and issuer/accession scope | PASS, 24/24 hosted |
| Raw inline-XBRL parser against original SEC bytes | NOT TESTED |
| Visible cover-page fallback across issuers | NOT TESTED |
| Exact class mapping across 289 Form 144 issuer CIKs | NOT MEASURED |
| Effective-dated listed-security identity incl. inactive/delisted names | NOT ESTABLISHED |
| PIT daily dollar-volume / ADV20 | NOT AVAILABLE |
| Forward returns, alpha, bootstrap/LOO, chronological OOS | NOT RUN |

Bulk SEC retrieval remains blocked because the authorized GitHub secret `SEC_CONTACT_EMAIL` is absent. No SEC bulk request was sent and no email was guessed. ADV20 remains separately blocked by the lack of an admitted survivorship-free, corporate-action-aware daily dollar-volume history.

Next: once authorized SEC retrieval is available, run the preregistered stratified 20–30 issuer raw-iXBRL/cover-page pilot, retain original bytes and SHA-256 per accession, measure exact-match coverage, and only then scale to the 289 issuers. Obtain a separate PIT, survivorship-free market-data source before computing ADV20.

## 7. Controls

No forward returns, event study, alpha, bootstrap/LOO, chronological OOS or holdout test was run. The consumed legacy holdout was not reused. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production, universe, capital or trading parameter changed. No vendor was contacted, no trial/card authorization was made, and no data was purchased.
