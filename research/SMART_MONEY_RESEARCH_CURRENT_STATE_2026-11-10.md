# Smart Money Research — Current State

**Updated:** 2026-11-10 UTC  
**Active branch:** phase231-cboe-option-quotes-full-row-reparse (PR #14, stacked on PR #13)  
**Frozen baseline:** F80_TOP20_PARTIAL50_BASELINE_C20  
**Legacy holdout:** CONSUMED_NOT_PRISTINE; never reused

## Latest material result — Phase 253

SEC registered-security Inline XBRL is a conditional positive identity source, not a complete crosswalk census: the April 2026 SEC XBRL Guide says no instance type requires the registered-security title facts. Company Facts is entity-wide and cannot replace dimensioned filing contexts.

The Phase 69 Form 144 panel has 21,653 original sale tranches across 289 issuer CIKs: 166 raw security-class labels (135 after case/whitespace normalization); 205/289 issuers have multiple normalized labels; 71 have explicit class-letter labels. The generic label Common occurs in 12,562 tranches, including 11,036 in multi-label issuers and 3,297 in issuers with explicit class-letter labels. These are text-heterogeneity diagnostics, not counts of legal classes.

Normalized XBRL context, exact-title join and as-filed vintage prototype: **23/23 hosted tests passed** on isolated CI run [42755137270](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42755137270); metadata-only artifact [13734524132](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42755137270/artifacts/13734524132). Raw iXBRL parsing and issuer-panel coverage remain untested.

- Phase 253 report: PHASE253_FORM144_XBRL_REGISTERED_SECURITY_CROSSWALK_AUDIT_2026-11-10.md
- Helper: phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Tests: test_phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Result: phase253_form144_xbrl_registered_security_crosswalk_audit_result.json

## Next gates

1. Run a stratified 20–30 issuer raw-iXBRL and visible-cover-page pilot; preserve each filing accession, filing/acceptance time, context, axes/members, original bytes and SHA-256. Measure exact-match coverage before scaling.
2. Bulk SEC retrieval is blocked because the authorized GitHub secret SEC_CONTACT_EMAIL is absent. No request was sent and no email was guessed.
3. Obtain a survivorship-free, corporate-action-aware daily dollar-volume source before computing Form 144 ADV20. No paid source has been authorized or purchased.
4. For Cboe options, first prove multi-date coverage, immutable final/preliminary receipt vintages, effective-dated security identity and licensing. No trial/card authorization or purchase.
5. Keep CFTC BPR/TFF prospective capture and all Smart Money candidates out of production until PIT and incremental OOS evidence pass.

## Other source dispositions

- FINRA Phase 20C: not promoted; no demonstrated incremental stock-selection edge.
- CFTC BPR/TFF: prospective regime candidates only; no historical beneficial-owner identity.
- SEC FTD: context metadata only; external history contains backfills and no immutable first-receipt proof.
- N-PORT: Phase 247 fixed the UNIT/UNITS schema defect; raw PIT and security identity remain open.
- Cboe Open-Close: feature contract and one C1 20% sample validated; no PIT or alpha.
- Cboe option quotes: 115,617 rows; 112,313 unambiguous; 3,304 expiration-ambiguous rows quarantined; no PIT or alpha.
- Cboe All Access: conditional high-information candidate; no account, trial, token, API request or purchase.

## Controls

No alpha/OOS result from Phase 253. No returns, bootstrap/LOO, chronological OOS or holdout test. No production, universe, capital or parameter changes. No minimum/maximum holding period or CAGR target is imposed. Compare any future feature against frozen LTM/F80 with identical exposure and costs.


## Phase 254 — Form 144 issuer/accession-scoped XBRL class join and prior-vintage gate (2026-11-10 UTC)
- Hardened the Phase 253 normalized resolver so the selected prior filing is explicitly scoped to the Form 144 issuer CIK, accession and filing date. Phase 253's generic selector/resolver depended on caller-side prefiltering; Phase 254 makes that precondition explicit and fail-closed.
- Same-day/future filings remain excluded for a daily Form 144 event; same-date prior-filing ties require timezone-aware acceptance timestamps on the filing date. Later amendments remain separate vintages and cannot be backdated.
- A class join now requires an explicit class-axis member. EntityListingsExchangeAxis is not class identity. Multiple listings are only reported when all matching contexts have known listing scope and agree on class member/symbol; incomplete listing scope remains UNKNOWN.
- Added 24 hosted regressions covering issuer/accession/date scope, same-day/future exclusions, amendments, class-vs-listing axes, unknown listing scope, exact-title-only joins and ambiguous classes.
- Final hosted Phase 254 run [42764068968](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968) passed **24/24**; job 129656300533; metadata-only artifact [13738319528](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968/artifacts/13738319528), 381 bytes, SHA-256 `ae7b3269d9fa884e6fe4f0f716b427aacc9d701e9c416175038309c025a81768`. Initial run 42763927183 passed 22 tests but had a hard-coded artifact count of 21; the workflow was corrected to calculate the count dynamically before the final 24/24 run.
- Same-head Phase 231 run [42763911397](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397) passed 9/9; artifact [13738991707](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397/artifacts/13738991707). It parsed 115,617 rows: 112,313 unambiguous, 3,304 ambiguous expirations quarantined. Phase 249 run [42763911410](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410) passed 11/11; artifact [13738418042](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410/artifacts/13738418042); still one public C1 20% sample date.
- Last 30 workflow runs were successful and no workflows remain active. PR #13 and #14 remain open/unmerged; no merge was performed.
- Raw iXBRL parsing, visible cover-page fallback, 289-issuer class coverage, effective-dated inactive/delisted identity and PIT ADV20 remain unmeasured. Bulk SEC retrieval remains blocked by missing authorized `SEC_CONTACT_EMAIL`; no request was sent and no email was guessed.
- No returns, alpha, bootstrap/LOO, chronological OOS or holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe and capital are unchanged.
- [Phase 254 report](PHASE254_FORM144_ISSUER_ACCESSION_SCOPED_XBRL_CLASS_JOIN_GATE_2026-11-10.md) · [helper](phase254_form144_xbrl_scoped_class_join.py) · [tests](test_phase254_form144_xbrl_scoped_class_join.py) · [result](phase254_form144_xbrl_scoped_class_join_result.json)


## Phase 255 — ADV20 historical market-data feasibility and dollar-turnover contract (2026-11-10 UTC)
- Completed a source-feasibility audit for the Form 144 ADV20 denominator. CRSP is the preferred research-grade benchmark if authorized access exists (32k+ active/inactive securities, survivor-bias-free history, PERMNO/PERMCO). Massive is the strongest API candidate for the 2023–2026 panel, but its individual market-data terms prohibit non-display/derived investment-strategy use unless separately licensed; its date-based security master is effective-dated current vendor data, not an archived original vintage, and it has no permanent identifier. Sharadar has active/delisted EOD history to 1997 but its published license is personal-use only. Norgate's two-year trial cannot cover the earliest Form 144 events; Tiingo and Nasdaq Data Link lack sufficient documented delisted/PIT evidence in this audit.
- The best documented reported-turnover measure is daily `VWAP × volume` where both use the same share basis. Massive documents that VWAP covers the same trades as volume, including some odd-lot/average-price/contingent trades; this is reported turnover, not executable liquidity. Missing bars are UNKNOWN, never zero-filled.
- Added `phase255_adv20_source_feasibility.py` and 26 hosted regressions. The contract requires exactly 20 distinct supplied XNYS sessions strictly before the Form 144 filing date; raw/raw or split-adjusted/split-adjusted VWAP/volume; Decimal arithmetic; no missing-bar zero fill; no same-day/future bars.
- Initial run [42764563857](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764563857) failed one test-only Decimal string expectation (`19500` vs `19500.0`). Corrected the expectation and added fractional-volume and split-invariance tests. Final run [42764720861](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861) passed **26/26**; job 129658390045; artifact [13739416974](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861/artifacts/13739416974), 421 bytes, SHA-256 `be975ca3108944ba6a65acafa28cc446bf8f37a81eddadfaba218ed2212b4a90`.
- No vendor data, API key, account, license or purchase was obtained. No ADV20 was calculated for Form 144 records. Raw SEC iXBRL pilot remains blocked by missing authorized `SEC_CONTACT_EMAIL`.
- No returns/alpha/bootstrap/LOO/chronological OOS/holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe and capital unchanged.
- [Phase 255 report](PHASE255_ADV20_HISTORICAL_MARKET_DATA_FEASIBILITY_AND_TURNOVER_CONTRACT_2026-11-10.md) · [helper](phase255_adv20_source_feasibility.py) · [tests](test_phase255_adv20_source_feasibility.py) · [result](phase255_adv20_source_feasibility_result.json)
