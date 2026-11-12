# Phase 335 — SEC taxonomy-member drift and listing-axis stability

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — ARTIFACT-REPRODUCIBLE IDENTITY AUDIT  
**Research class:** XBRL identity semantics and source-feasibility; no return or alpha test.

## Executive decision

Phase 335 consumes the immutable Phase 334 artifact and audits the stability of raw class-axis QNames, same-context Security12bTitle evidence, and listing-exchange dimensions. It makes no new SEC requests and does not merge any raw QName.

**Result:** across 98 TradingSymbol fact contexts and 26 unique symbols, 20 symbols have at least one direct class-axis fact and six do not. Fourteen symbols have one exact class QName in this sample; six have multiple QNames. For all six multi-QName symbols, the same-context security-title text is identical across the observed variants. These are candidate taxonomy aliases only, not merged identities.

A second positive result is that 18 TradingSymbol facts in two PCG filings carry both a direct class axis and a direct listing-exchange axis. Ten symbols map to two distinct exchange members.

## 1. Reproducibility

- Source: Phase 334 run 43226260351, artifact 13947767592.
- Phase 334 artifact SHA-256: f107cdeab68b9905a0fb8adfd10c97564bc03f2315148f986f58e91d5ed706a4.
- Pinned Phase 334 audit JSON SHA-256: c360eac0358ca4181664ecf18ea6699bccedd0e3d2251ea936c296a19588bc46.
- GitHub Actions [run 43227805268](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43227805268) — **SUCCESS**.
- Offline regressions: **8/8 passed**.
- Phase 335 artifact [13949055980](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43227805268/artifacts/13949055980), 11,061 bytes, SHA-256 7ad27816c0c43ba3fe08e9a3f9a417077ba3e94f7523385bb0788f04b9104060.
- Draft review: [PR #24](https://github.com/jafelix81/NuevaEstrategia/pull/24), based on Phase 334; no merge.

The workflow downloaded the pinned Phase 334 artifact, verified the audit JSON hash and source counts, then analyzed its 98 context associations. No SEC re-fetch, vendor data or external file was used.

## 2. Class-axis stability

| Symbol-level classification | Count |
|---|---:|
| Unique symbols in sample | 26 |
| Symbols with at least one direct class-axis fact | 20 |
| Symbols without a direct class-axis fact | 6 |
| One exact class QName in this sample | 14 |
| Multiple exact class QNames | 6 |
| Multiple QNames with identical same-context title evidence | **6** |
| Multiple QNames with conflicting/missing title evidence | 0 |
| QNames merged | **0** |

The six multi-QName symbols are PCG-PB, PCG-PE, PCG-PG, PCG-PH, PCG-PI and STR. Their observed title text is identical across the respective raw QName variants:

| Symbol | Same-context title evidence |
|---|---|
| PCG-PB | First preferred stock, cumulative, par value $25 per share, 5.50% nonredeemable |
| PCG-PE | First preferred stock, cumulative, par value $25 per share, 5% series A redeemable |
| PCG-PG | First preferred stock, cumulative, par value $25 per share, 4.80% redeemable |
| PCG-PH | First preferred stock, cumulative, par value $25 per share, 4.50% redeemable |
| PCG-PI | First preferred stock, cumulative, par value $25 per share, 4.36% series A redeemable |
| STR | Class A common stock, par value $0.0001 per share |

The PCG variants are split between filing cohorts dated 2022-11-21/2022-11-30/2023-01-06 and 2022-12-02/2022-12-15. The STR variants occur in filings dated 2022-11-14 and 2022-12-29.

Identical same-context titles support a candidate alias hypothesis, but they do not prove that two taxonomy QNames are interchangeable in every filing or reporting context. Preserve the original QName, accession, context, title, issuer CIK and filing date. No alias table is admitted until the relevant taxonomy schema and label linkbase are inspected.

The 14 single-QName symbols are DLR, DLRPRJ, DLRPRK, DLRPRL, FTAI, FTAIN, FTAIO, FTAIP, PCG, PCG-PA, PCG-PC, PCG-PD, PCGU and STRWS. DLR's four symbols recur in five 2026 filings with the same raw class members. FTAI's four symbols occur in only one filing, so their apparent stability is not longitudinally tested.

The six symbols without a direct class-axis fact are RVSB, LNDC, LFCR, SAFE, NWLI and NWN.

## 3. Listing-exchange axis

Phase 335 confirms the Phase 334 result:

| Listing axis member | Symbols | Filings |
|---|---|---:|
| pcg:XnysMember (NYSE) | PCG, PCGU | 1 |
| pcg:NYSEAMERICANLLCMember (NYSE American) | PCG-PA, PCG-PB, PCG-PC, PCG-PD, PCG-PE, PCG-PG, PCG-PH, PCG-PI | 2 |

There are 18 fact rows, ten unique symbols, two listing-axis members and two documents. All 18 listing-axis facts also carry a class-axis member on the same TradingSymbol fact context. No symbol has multiple listing members in this sample.

This is a direct filed XBRL relationship and a useful mapping source. It is still only one issuer group and two filings; the context's reporting date and first-public availability have not been independently converted into an effective-dated listing history.

## 4. Research decision

- Preserve the 6 candidate QName alias groups without merging.
- Retrieve the actual custom taxonomy schema and label linkbase for the PCG variants; compare member QNames, labels, definitions and taxonomy versions.
- Inspect the standard taxonomy label differences for STR's CommonClassA/CommonStock members.
- Preserve listing-exchange and class axes as separate dimensions.
- Expand beyond the purposive collision panel before estimating issuer, listing, security or share-class coverage.

Phase 335 is an identity-semantics audit, not a signal test. The direct XBRL mappings may help prevent false ticker-to-security joins, but no predictive or economic value has been established.

## 5. Controls

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No security master, strict-PIT admission, broad universe coverage, alpha/return test, bootstrap/LOO, chronological OOS or holdout use. No production, universe, capital or parameter changes. No QName alias merge, vendor contact or data purchase.
