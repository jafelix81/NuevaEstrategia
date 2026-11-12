# Phase 328 — SEC prior-filing XBRL identity pilot for Form 4 ticker collisions

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — source-coverage gate not met  
**Research class:** identity and historical-source feasibility; no return or alpha test.

## Executive decision

A 28-pair purposive panel was used to test whether the latest SEC periodic filing strictly before each collision date can supply an effective-dated issuer/listing/security/share-class crosswalk.

The pilot produced **56 issuer-date observations**. SEC Submissions responded for all 56, a supported periodic filing was found for 44, and 42 original filing documents were retrieved and hashed. Only 14/56 observations (25.0%; 14/42 retrieved documents, 33.3%) contained a usable TradingSymbol fact. Security-title facts appeared in 14/56, class-axis evidence in 7/56 and listing-axis evidence in 2/56.

This is far below the repository's existing 95% identity-coverage admission gate. **SEC periodic XBRL facts are useful positive evidence where present, but are not a complete historical identity source.** Missing facts are unknown, not proof that an issuer has no listed security.

## Reproducibility

- Final GitHub Actions run: [43217315822](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43217315822) — **SUCCESS**.
- Offline regressions: **14/14 passed**.
- Pinned sample: [phase328 collision manifest](phase328_collision_pair_manifest.csv), SHA-256 c9fb97c2572da04760188a47fac6d9d983f406f16f2797b656525bfeb10ecd2d.
- Source population: successful Phase 325 run 43196055022, artifact 13931894766, ZIP SHA-256 6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3.
- Result artifact: [13943024635](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43217315822/artifacts/13943024635), ZIP SHA-256 ed33844f2b9ec435a6ee7eaacbe86fc7001a167efdc2300b65fb6f18f1c24dd8.
- Artifact contains parsed metadata, source-document hashes and CSV summaries only; no raw SEC filing bytes.

The first implementation attempted a cross-run artifact download and received HTTP 401. The accepted workflow avoids that dependency: it pins the exact 28-pair manifest in the branch, verifies its SHA-256 and then retrieves SEC sources. The final run passed.

## 1. Population and retrieval

| Measure | Result |
|---|---:|
| Exact same-day collision pairs | 28 |
| Issuer-date observations | 56 |
| Shared filing dates represented in source panel | 42 |
| SEC Submissions responses | 56/56 |
| Prior supported periodic filing, strictly before event date | 44/56 |
| Original filing documents retrieved and hashed | 42/56 |
| Distinct document SHA-256 values | 39 |
| Median selected periodic-filing age | 67 calendar days |

Document outcomes were 17 parsed XBRL instances, 25 primary HTML documents without the target inline-XBRL facts, 12 observations with no eligible prior periodic filing, one oversized response and one filing without a usable primary document/instance.

The 42 retrieved documents reduce to 39 unique hashes because three issuer-CIK pairs resolve to the same accession and same primary document (see Phase 329). Those duplicate CIK observations are not independent source documents.

## 2. Structured fact coverage

| Fact or identity evidence | Observations |
|---|---:|
| TradingSymbol value | 14/56 (25.0%) |
| Security 12(b)/12(g) title | 14/56 (25.0%) |
| StatementClassOfStockAxis / share-class axis | 7/56 (12.5%) |
| Listing/exchange axis | 2/56 (3.6%) |

Among the 42 retrieved documents, only 14 contained a TradingSymbol value (33.3%). Of the full 56-observation panel, the comparison statuses were:

| Status | Count |
|---|---:|
| One symbol, exact candidate match | 5 |
| Candidate among multiple symbols | 6 |
| Candidate mismatch | 3 |
| No target TradingSymbol fact | 30 |
| Not tested because no prior periodic filing | 12 |

The six multiple-symbol cases matter: an issuer-level filing can report common stock, preferred series, warrants or other listed instruments. A symbol match alone does not identify the security class underlying a Form 4 transaction.

### Historical depth

| Collision event year | Observations | Documents retrieved | TradingSymbol facts |
|---|---:|---:|---:|
| 2006 | 14 | 7 | 0 |
| 2012 | 18 | 16 | 0 |
| 2023 | 12 | 10 | 8 |
| 2025 | 6 | 5 | 2 |
| 2026 | 6 | 6 | 4 |

No retrieved 2006 or 2012 document in this panel exposed a target structured TradingSymbol fact. This is a serious historical-depth limitation for an XBRL-fact-only crosswalk. It does **not** establish that the visible cover pages lack ticker tables: the Phase 328 HTML fallback searched inline-XBRL facts, not legacy visible HTML tables. A separate legacy-cover-page parser is the next feasibility test.

## 3. Three apparent mismatches require event chronology

The periodic filing is only a snapshot. Two of the three mismatches are explained by corporate actions between the selected periodic filing and the Form 4 event date; the third remains quarantined. Phase 329 records the source-level reconciliation.

- **LFCR / CIK 1005286:** the selected 10-Q (filed 2022-10-07) still reports LNDC; a subsequent SEC 8-K dated/filed 2023-01-09 shows LFCR, before the 2023-01-11 collision date. This is a ticker-transition timing issue, not evidence that the Form 4 candidate is wrong.
- **SAFE / CIK 1095651:** the selected 10-K/A (filed 2023-03-30) reports STAR; the merger closed 2023-03-31 and the surviving company began trading as SAFE. The official company release is dated 2023-03-31, before the 2023-04-04 Form 4 filing. The related SEC 8-K was filed on April 4 and is not used as a pre-Form-4 timestamp. This is a merger/name/ticker transition.
- **TSBK / CIK 1041368:** the selected 10-Q (filed 2026-08-14) reports RVSB; a later 8-K/A filed 2026-09-08 also reports RVSB. The other side of the pair, CIK 1046050, reports TSBK in its 2026-08-07 10-Q. The bulk candidate TSBK for Riverview is therefore a likely metadata misattribution, but the original Form 4 accession 0000939057-26-000239 remains unavailable. It stays quarantined; the missing XML prevents definitive source-level adjudication.

## 4. Co-filer duplication and identity

Three pairs share the same accession and identical primary-document hash across two CIKs:

- DLR: CIKs 1297996 and 1494877; accession 0001104659-26-054255.
- LQI: CIKs 313749 and 314661; accession 0000950134-05-019932.
- PCG: CIKs 1004980 and 75488; accession 0001004980-22-000133.

The DLR and PCG co-filings both report the candidate symbol for both CIKs. This is not evidence of two independent listed securities. The issuer-CIK-to-security graph must preserve co-filer/parent/subsidiary relationships and must not count repeated filing payloads as independent identity confirmations.

## 5. Decision and next gates

1. **Do not admit periodic XBRL facts as a complete security master.** Structured TradingSymbol coverage is only 25% of the collision panel and absent in the 2006/2012 cohorts.
2. Extend the source audit to visible legacy HTML cover-page tables, while keeping XBRL facts and visible-text extraction as distinct evidence types.
3. Add intervening 8-K/8-K/A, merger, spin-off, name-change, exchange-listing and delisting events between periodic reports. Periodic snapshots alone are stale across corporate actions.
4. Model issuer CIK, co-filer, parent/subsidiary, plan/fund, listing, security and share class as separate nodes/relations. CIK is an issuer/filer key, not a security identifier.
5. Retain the 95% admission gate for broad universe mapping. This purposive collision panel is not a universe-coverage estimate and cannot establish survivorship-aware coverage.

## Controls

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No strict PIT admission, security-master admission, universe-coverage admission, alpha/return test, bootstrap/LOO, chronological OOS or holdout use.
- No production, universe, capital or parameter change.
- No vendor contact, data purchase or email.
- No raw SEC bytes uploaded.
