# Phase 326 — SEC Form 4 same-day collision security-title adjudication

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED WITH ONE SOURCE QUARANTINE — 282/283 original submissions retrieved; 27/28 collision pairs have source-level title diagnostics.  
**Research class:** primary-source identity/schema audit; no return or alpha test.

## Executive decision

Phase 325 identified 28 issuer-CIK pairs whose conservative SEC as-filed ticker candidates collide on at least one exact filing date (42 shared dates). Phase 326 selected all accessions attached to those collision pairs: **283 accessions across 56 issuer CIKs** (280 Form 4 and 3 Form 4/A).

The final full retrieval attempt obtained **282/283 original SEC submission texts**. Every retrieved submission passed header identity and XML identity checks: accession/form/filed date/header CIK; XML issuer CIK; reporting-owner CIK set; and issuer symbol. The remaining accession was not retrieved after all six unpadded archive URL layouts returned HTTP 404.

The audit does **not** infer that equal transaction-security-title strings mean the same security, or that different title strings mean different share classes. Security titles are free-text labels, not permanent identifiers.

## 1. Immutable source and execution

- Phase 321 source artifact: [13925636412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43177940904/artifacts/13925636412), SHA-256 e45cab68d1ebe15248cc76bad70b015c8f0bd2052689c0690478bbca4526965c.
- Phase 325 collision artifact: [13931894766](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43196055022/artifacts/13931894766), SHA-256 6d7930230a60036931857520df07b28087720d54ae9d3bee8f4b1cfe2fbcefa3.
- Final Phase 326 full-retrieval attempt: [GitHub Actions run 43209373482](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43209373482).
- Parsed metadata artifact: [13939999128](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43209373482/artifacts/13939999128), SHA-256 eea7eaf97b91acfdbdac866f8d98660ec98be03adc8c4038b800f74cf86d81d5.
- The final Phase 326 run passed **14/14 offline regression tests**, verified both immutable source artifacts, completed all 283 planned attempts, and uploaded the parsed artifact. The workflow job is marked failure only because its strict retrieval gate requires 283/283, while 282/283 were retrieved. The explicit quarantine is retained; it is not silently counted as success.

## 2. Retrieval and identity results

| Measure | Result |
|---|---:|
| Planned accessions | 283 |
| Form 4 / Form 4/A | 280 / 3 |
| Distinct issuer CIKs | 56 |
| Original submissions retrieved | **282/283** |
| Header identity matches | 282/282 retrieved |
| XML parsed | 282/282 retrieved |
| XML issuer CIK matches | 282/282 retrieved |
| XML reporting-owner CIK matches | 282/282 retrieved |
| XML issuer-symbol matches bulk label | 282/282 retrieved |
| Unresolved original submission | 1 |

The 282 validated submissions contain 268 non-derivative transaction rows, 186 derivative transaction rows and 45 distinct security-title labels. These are rows/labels in this purposive collision sample, not market events or population estimates.

The transaction-code summary is **filing presence**, not transaction-row count: A 156, D 14, F 35, G 4, J 39, M 20, P 6, S 20 and X 3. In particular, SEC code P can mean an open-market **or private** purchase; it is not by itself proof of a public-market execution. Code S also requires transaction/footnote context. The sample is not representative of insider activity.

## 3. Title-label comparison

| Pair diagnostic | Pairs |
|---|---:|
| Overlapping labels — explicitly not security identity | 20 |
| Disjoint labels — explicitly not proof of different share classes | 7 |
| Incomplete because one original submission is unavailable | 1 |
| **Total** | **28** |

The equal-title and different-title regression tests were added to make the conservative interpretation executable. They passed. The title comparison is descriptive only; it does not adjudicate corporate relationships, listed classes, ADRs, units, or the security actually traded.

## 4. Sole unresolved accession

- Accession: 0000939057-26-000239
- Form/date: Form 4, 2026-09-25
- Bulk issuer: CIK 1041368, RIVERVIEW BANCORP INC
- As-filed ticker candidate: TSBK
- Reporting-owner CIK: 1972440
- Quarter: 2026Q3
- Phase 321 daily-index file SHA-256: f7962a73b80234608c45f53cc5aac19b2374d5085e3fa73aa262448dce6d10a5

The Phase 326 retrieval attempted the flat-submission and accession-directory layouts for the accession-prefix, issuer and reporting-owner CIK paths. All six unpadded layouts returned HTTP 404. Phase 327 then tested all six corresponding zero-padded layouts; those also returned HTTP 404. The original SEC submission is therefore **unavailable through the 12 tested archive path/layout combinations**. It remains quarantined; no secondary-source substitute was promoted to primary evidence.

The ticker/issuer pair is not adjudicated. The bulk ticker candidate must not be treated as a permanent security identifier or used to infer the listed security.

## 5. Decision and next gate

- Keep all 28 collision pairs as issuer-label diagnostics, not security mappings.
- Keep the one unavailable accession and its pair incomplete.
- Preserve CIK as issuer identity; do not join transactions to returns on ticker or security-title text alone.
- Before any Form 4 event study, build an effective-dated issuer → listing → security → share-class crosswalk, including ticker reuse, multiple classes, ADRs, units, mergers, spin-offs, delistings and relistings.
- Then parse transaction-level dates, codes, shares, prices, ownership roles, 10b5-1 indicators and footnotes. Separate grants, exercises, tax withholding, gifts, private transactions and public-market executions.
- Apply conservative ex-ante availability and broad survivorship-aware universe coverage before testing incremental information versus frozen LTM/F80.

No alpha/return, bootstrap/LOO, chronological OOS or holdout test was run. F80, production, universe, capital and parameters remain unchanged. No vendor was contacted, no data were purchased, no email was sent and no raw SEC bytes were uploaded.
