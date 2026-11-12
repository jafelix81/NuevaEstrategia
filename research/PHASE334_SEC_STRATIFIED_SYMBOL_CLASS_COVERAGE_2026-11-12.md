# Phase 334 — stratified SEC symbol-to-class coverage with a fresh-anchor gate

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — STRATIFIED CLASS-BINDING AUDIT  
**Research class:** identity and source-feasibility audit; no return or alpha test.

## Executive decision

Phase 334 expands the Phase 333 nine-document pilot to every unique, hash-bearing TradingSymbol document found in the 28-pair / 56 issuer-side collision panel, subject to a predeclared freshness and completeness gate.

The audit re-ran the Phase 332 SEC event chronology, admitted only prior-periodic anchors no more than 365 calendar days before the collision event date, excluded truncated or shard-error windows, collapsed co-filer rows only after document-hash and schema agreement, and re-fetched each selected document.

**Result:** 38/56 observations had a complete fresh anchor; 26 unique symbol-bearing accessions were rechecked. All 26 document hashes and all 26 TradingSymbol sets matched the Phase 332 source. There were nine duplicate co-filer rows to collapse and zero accession conflicts.

The expanded sample shows useful direct XBRL identity evidence, including listing-exchange dimensions not observed in the Phase 333 nine-document pilot. It also reveals taxonomy-member naming drift that must be resolved before canonicalizing a security master.

## 1. Reproducibility

- GitHub Actions [run 43226260351](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43226260351) — **SUCCESS**.
- Offline regressions: **13/13 passed**.
- Live Phase 332 chronology rerun: 56/56 submissions available; 178 event documents retrieved from 182 candidates.
- Phase 334 document recheck: 26/26 SHA-256 matches and 26/26 TradingSymbol-set matches.
- Artifact [13947767592](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43226260351/artifacts/13947767592), 73,242 bytes, SHA-256 f107cdeab68b9905a0fb8adfd10c97564bc03f2315148f986f58e91d5ed706a4.
- Rechecked audit JSON SHA-256: c360eac0358ca4181664ecf18ea6699bccedd0e3d2251ea936c296a19588bc46.
- Draft review: [PR #23](https://github.com/jafelix81/NuevaEstrategia/pull/23), based on Phase 333; no merge.

The workflow re-ran Phase 332 from the SHA-pinned 28-pair Phase 328 manifest. Phase 334 then re-fetched each selected document and required the original document hash and symbol set to match before admitting its fact-level binding result.

## 2. Fresh-anchor and document coverage

| Gate / result | Count |
|---|---:|
| Collision pairs | 28 |
| Issuer-side observations | 56 |
| Complete fresh anchors (0 < age <= 365 days) | **38** |
| Pairs with at least one fresh complete side | 25 |
| Stale anchors | 6 |
| No valid prior periodic anchor | 12 |
| Incomplete / truncated / shard-error observations | 0 |
| Unique symbol-bearing accessions rechecked | **26** |
| Duplicate co-filer rows collapsed | 9 |
| Accession hash/schema conflicts | 0 |
| Document SHA-256 matches | 26/26 |
| TradingSymbol-set matches | 26/26 |

The 26 accessions span 2022 (11), 2023 (4), 2025 (2) and 2026 (9), but they occur in only nine of the 28 purposive collision pairs. This is not a representative universe sample.

The audit rejected 45 event rows outside a fresh complete anchor and 98 event rows without a TradingSymbol fact. These exclusions remain explicit; they are not silently treated as negative identity evidence.

## 3. Direct class-axis evidence

Across the 26 unique documents:

| Measure | Result |
|---|---:|
| TradingSymbol facts rechecked | **98** |
| Facts with a class axis on their own context | **86 / 98 (87.8%)** |
| Facts without a direct class axis | 12 |
| Documents with direct class binding on every symbol fact | 14 / 26 |
| Documents with no direct class binding | 12 / 26 |
| Unique symbols with at least one direct class-axis fact | 20 / 26 |
| Unique symbols without direct class-axis evidence | 6 |

The six symbols without direct class-axis evidence in this sample are RVSB, LNDC, LFCR, SAFE, NWLI and NWN. A single issuer-level TradingSymbol fact without a class axis is not promoted to a share-class mapping.

Direct class evidence is concentrated in four issuer groups:

- **DLR:** DLR, DLRPRJ, DLRPRK and DLRPRL have stable class members across five 2026 filings.
- **FTAI:** FTAI, FTAIN, FTAIO and FTAIP have direct class members in one 2022 filing only; this is not longitudinal validation.
- **PCG:** ten symbols have direct class members across six 2022–2023 filings.
- **STR:** STR and STRWS have direct class members in two 2022 filings.

These are direct XBRL context relationships, not inferences from a ticker appearing somewhere in the same document.

## 4. Taxonomy-member drift: do not canonicalize by raw QName

Six symbols have more than one exact class-axis QName across the sampled filings:

- PCG-PB
- PCG-PE
- PCG-PG
- PCG-PH
- PCG-PI
- STR

For all six, the corresponding same-context Security12bTitle text is identical across the observed QName variants. Examples include 5.50 versus 550 in the PCG-PB member name, omission of A in one PCG-PE member name, and CommonClassA versus CommonStock for STR.

This is evidence of a likely taxonomy/member naming variation, **not permission to merge the QNames**. The original QNames, accession, context and title must remain preserved. Phase 335 should inspect taxonomy/linkbase labels and effective dates before proposing any alias relation. Until then these are classified as candidate taxonomy aliases, not merged.

Fourteen unique symbols have one exact class QName within this sample; six have multiple QNames; six have no direct class-axis fact. “One QName in this sample” is not proof of permanent class stability.

## 5. New listing-exchange evidence

Phase 334 found **18 TradingSymbol facts with a direct dei:EntityListingsExchangeAxis**, covering ten unique PCG symbols in two 2022 filings:

- PCG and PCGU carry pcg:XnysMember (NYSE).
- PCG-PA, PCG-PB, PCG-PC, PCG-PD, PCG-PE, PCG-PG, PCG-PH and PCG-PI carry pcg:NYSEAMERICANLLCMember (NYSE American).

This is a useful positive result: the SEC XBRL context can directly bind a TradingSymbol to both a class axis and a listing-exchange axis. However, all 18 listing-axis facts come from only two filings for one issuer group. They do not establish broad exchange-coverage prevalence or an effective-dated security master.

## 6. TSBK/RVSB remains quarantined

Four pre-event filings in the TSBK collision pair contain the actual TradingSymbol RVSB, not TSBK. They have no direct class-axis facts. This strengthens the conclusion that the bulk-index TSBK label is suspect for the Riverview issuer, but it does not replace the missing original Form 4 XML or independently establish the exact security reported in accession 0000939057-26-000239.

Do not resolve that accession or promote RVSB to a security master from these event filings alone.

## 7. Interpretation and next gates

Phase 334 establishes that fresh, complete pre-event SEC XBRL event documents can contain direct symbol-to-class and, occasionally, symbol-to-listing relationships. It also shows why a raw QName is not yet a canonical class key.

Next:

1. Audit class-axis QName labels and taxonomy versions for the six multi-QName symbols; preserve raw members and propose aliases only with explicit label/linkbase evidence.
2. Check listing-axis stability and its relationship to class-axis facts across the same issuer's filings.
3. Expand beyond the purposive 28-pair collision panel to a survivorship-aware sample from the actual historical Form 4 universe; report issuer, listing, security and share-class coverage separately.
4. Only after effective-dated identity and broad coverage pass, build transaction-level Form 4 features and test incremental information versus frozen LTM/F80 under identical exposure/costs, chronological OOS, bootstrap and LOO.

**Controls:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No security master, strict-PIT source admission, universe coverage, alpha/return test, bootstrap/LOO, chronological OOS or holdout use. No production, universe, capital or parameter changes. No vendor contact or data purchase.
