# Phase 398 — Form 144/A amendment lineage and tranche-level security resolution

**Audit date:** 2026-11-14 UTC  
**Disposition:** amendment versions must be treated as updates to an existing proposed-sale order, not as independent new sale events. The two audited ticker ambiguities are largely resolvable at tranche/issuer level, but the full historical F80 security-identity and delisting gates remain open. No economic test or signal admission is authorized.

## 1. Reproducible input

This is an offline extension of Phase 397 using the completed Phase 67 artifact:

- Phase 67 Actions run: [41828179718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41828179718).
- Artifact: [13334881835](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41828179718/artifacts/13334881835), phase67-form144-full-candidate-role-resolution.zip.
- ZIP SHA-256: 939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613.
- Input member: issuer_event_raw.csv, 21,634 rows.
- CSV SHA-256: fd20e338bd3624e7c1e85c39ab911f9fd5d1d78e8a20ed185e42db299a868b20.
- The 14-quarter census spans 2023Q2–2026Q3. No SEC crawl, price download, return calculation or vendor request was made.

The reproducible script is research/phase398_form144_amendment_lineage_audit.py; four synthetic regression tests are in research/test_phase398_form144_amendment_lineage_audit.py; the aggregate result is research/PHASE398_FORM144_AMENDMENT_LINEAGE_SUMMARY_2026-11-14.json.

## 2. Form 144/A is a version, not a second independent sale

The 21,634 issuer-event rows contain 21,438 original Form 144 filings and 196 Form 144/A amendments.

Of the 196 amendments:

| Parent resolution | Count |
|---|---:|
| Parent present in candidate issuer-event panel | 193 |
| Parent present in the broader 14-quarter accession census but absent from candidate panel | 2 |
| Parent outside the census or otherwise missing | 1 |

Among the 193 matched parents, 188 are original Form 144 filings and five are themselves Form 144/A amendments. There are no parent filing-date inversions, no issuer/filer CIK mismatches and no cycles in the matched amendment chains. Four chains reach a second amendment level in the candidate panel.

Only 106 of the 193 matched amendments preserve an exactly unchanged tranche payload. The remaining 87 change at least one tranche field. The overlapping change counts are:

| Changed field | Amendments |
|---|---:|
| Proposed units, aggregated by security class | 44 |
| Proposed value, aggregated by security class | 59 |
| Shares outstanding denominator | 19 |
| Approximate sale date | 18 |
| Broker / market maker | 20 |
| Exchange | 12 |
| Tranche count | 3 |
| Security-class set | 6 |

These counts overlap and must not be added. The result is material: treating each 144/A as a new seller-flow observation double-counts amended orders; replacing the original filing with the final amendment and backdating its contents would introduce lookahead.

**Required event-state model:** keep the original accession as the proposed-sale event root; preserve every 144/A as a separate version with its own filing date and first-public-availability boundary. A changed quantity, value, class, broker, exchange or date becomes known only with the amendment. Do not rewrite the original event at its earlier timestamp. For the two parents found in the broader accession census but absent from the candidate event panel, recover the parent metadata before using the amendment in a feature. The one parent outside/missing from the census remains unresolved.

## 3. Tranche-level class resolution

The 291 rows flagged by Phase 397 as multi-candidate ticker rows consist of 290 Zillow Group issuer rows with candidates Z/ZG and one AMT/ASTS filer-versus-issuer case.

### Zillow Group (CIK 0001617640)

The 2023 Form 10-K, filed 2023-02-15, states that Class A traded as ZG and Class C capital stock traded as Z from 2015-08-17. The 2025 Form 10-K, filed 2026-02-11, confirms the same Class A / ZG and Class C / Z mapping. These filings predate the relevant Form 144 observations.

Within the 290 ambiguous Zillow rows:

- 275 rows contain only Common Class C.
- Eight rows contain both Common Class C and Common Class A as separate tranches.
- Seven rows say only generic Common and remain unresolved.

Across the 298 tranches in these 290 rows, the audited rule maps 283 Class C tranches to Z and eight Class A tranches to ZG. The seven generic Common tranches remain unresolved. Do not assign a whole dual-class event to both tickers; map each tranche independently.

### AMT / ASTS

The single AMT;ASTS row has XML subject-issuer CIK 0001780312 (AST SpaceMobile) and filer/seller CIK 0001053507 (American Tower). The issuer-side CIK, not the seller's CIK, identifies the security issuer. AST SpaceMobile's 2023 Form 10-K, filed 2024-04-01, identifies its Class A common stock as ASTS. The row therefore resolves to the ASTS issuer side, subject to the effective-dated CIK/security crosswalk; it must not be assigned to AMT merely because American Tower is the filer/seller.

Official identity references:
- [Zillow Group 2023 Form 10-K](https://www.sec.gov/Archives/edgar/data/1617640/000161764023000010/z-20221231.htm)
- [Zillow Group 2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1617640/000161764026000015/z-20251231.htm)
- [AST SpaceMobile 2023 Form 10-K](https://www.sec.gov/Archives/edgar/data/1780312/000095017024039342/asts-20231231.htm)
- [SEC Form 144 electronic-filing guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically)

## 4. Regulatory clock recheck

The current eCFR text of 17 CFR 230.144(h)(3), up to date as of 2026-11-12, still requires Form 144 to be transmitted concurrently with placing the broker order or executing directly with a market maker. The SEC's 2023 Release 33-11159 extends EDGAR filing hours to 10:00 p.m.; it does not replace the concurrent-order requirement with a two-business-day filing window. The SEC filing guide says Form 144 submissions between 6:00 a.m. and 10:00 p.m. ET are deemed filed and publicly disseminated on the same business day.

This supports treating the filing as a selective order-placement / proposed-supply proxy, not a confirmed execution feed. The Phase 67 event CSV contains no accepted timestamp or first-public-receipt ledger. Keep the conservative daily rule: an event can first be used from the first regular NYSE session strictly after its SEC filing date. Do not use same-day close, intraday timing, notice_date, approximate sale date or an inferred 1–3 minute dissemination delay.

Official references:
- [Current eCFR, 17 CFR 230.144](https://www.ecfr.gov/current/title-17/section-230.144), especially paragraph (h)(3).
- [SEC Release 33-11159 — Extending Form 144 EDGAR Filing Hours](https://www.sec.gov/rules-regulations/2023/02/extending-form-144-edgar-filing-hours).
- [SEC Form 144 electronic-filing guide](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically).

## 5. Decision and remaining gates

1. Build the production research panel at tranche/version grain, keyed by original accession root, amendment accession, XML subject issuer CIK, seller/filer CIK, security class and filing date.
2. Never count 144/A as an independent new sale. Preserve the original version and each amendment at its own availability date.
3. Keep the seven generic Zillow Common tranches unresolved; do not infer class from seller, share count or current price.
4. Resolve the two broader-census parent accessions and the one missing/out-of-census parent before using those amendment chains.
5. Complete historical issuer/security identity, F80 membership, predecessor/delisted coverage and corporate-action mapping for the full frozen universe. The current 335-name map is not a historical security master.
6. Keep proposed units/value/outstanding validity masks from Phase 397; no zero or invalid denominator may be silently imputed.

**Disposition:** Form 144 remains a selective proposed insider-supply / order-placement hypothesis. This phase improves event integrity and resolves most of the 291 candidate-pair cases, but it does not establish predictive information, execution, or alpha.

## 6. Controls

- No forward returns, alpha, OOS, bootstrap, LOO or holdout test.
- No signal admitted.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No universe, capital, exposure, parameter or production changes.
- No SEC crawl, vendor contact, account, trial, license or data purchase.
