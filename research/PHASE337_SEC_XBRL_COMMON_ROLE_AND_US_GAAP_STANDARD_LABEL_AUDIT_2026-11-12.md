# Phase 337 — common-role XBRL labels and official US-GAAP member evidence

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED — COMMON-ROLE AND STANDARD-TAXONOMY AUDIT  
**Research class:** identity metadata and source feasibility; no return or alpha test.

## Executive decision

Phase 337 corrected a comparison weakness in Phase 336 and retrieved the official US-GAAP standard label and documentation linkbases for the two STR members. It compares exact common \`(role, language)\` pairs, records one-sided roles separately, and keeps cross-role text overlap distinct from same-role agreement.

**Result:** 4/6 alias groups have exact matching labels on at least one common role/language pair; 2/6 have a common-role label conflict. Five groups have exact text overlap across roles, and all six have identical same-context Security12bTitle text. Documentation matches: 0/6. **No QName was merged.**

## 1. Reproducibility and source integrity

- Pinned Phase 336 run: [43228785778](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43228785778).
- Pinned Phase 336 artifact: [13949661332](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43228785778/artifacts/13949661332).
- Phase 336 artifact ZIP SHA-256: \`da010b603e408260d3191b9af9d70de3f03537db97e1dfd0a98ed8c3b8739dac\`.
- Phase 336 audit JSON SHA-256: \`17f088d14cdc1f271afc54ab0fd968237b615902ac06a763b2f45a4a37e9aa5e\`.
- Final GitHub Actions [run 43231603567](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43231603567) — **SUCCESS**.
- Offline regressions: **7/7 passed**.
- Phase 337 artifact [13950567282](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43231603567/artifacts/13950567282), ZIP SHA-256 \`55b08b42da9be212d52efbb3d8b64e34f86e00b8253a7769652d37035d534982\`.
- Draft review: [PR #26](https://github.com/jafelix81/NuevaEstrategia/pull/26), based on Phase 336; no merge.

The workflow verified the pinned Phase 336 audit JSON before any comparison. All eight original filing instances remain hash-matched through Phase 336. Phase 337 did not re-fetch or alter those SEC documents.

## 2. Official US-GAAP resources retrieved

The FASB technical guides describe the standard-label and documentation linkbases as separate taxonomy resources; the documentation linkbase is not referenced from the base schema. Phase 337 therefore retrieved both resources explicitly for each namespace version observed in STR's filings.

| Version | Resource | HTTP | Bytes | SHA-256 |
|---|---|---:|---:|---|
| 2021 | [us-gaap-lab-2021-01-31.xml](https://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-lab-2021-01-31.xml) | 200 | 14,134,277 | \`f48353943afdf09121e3b7113797db9551c5d067348ced22e11cf2be7897252b\` |
| 2021 | [us-gaap-doc-2021-01-31.xml](https://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-doc-2021-01-31.xml) | 200 | 13,646,645 | \`b6c606d758b73a7f4b4588879abc47c8f06e44af06c85289017e16ae48823f72\` |
| 2022 | [us-gaap-lab-2022.xml](https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-lab-2022.xml) | 200 | 13,886,233 | \`b05abba64f933de9a2084e7aede54af77a7f67f048c636e6ae4f2a85c912a536\` |
| 2022 | [us-gaap-doc-2022.xml](https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-doc-2022.xml) | 200 | 13,510,945 | \`a9d515b582ddab7961cfc5283c4d5799db03b6c4fbc6875bdb0fd31de482f0d2\` |

All four resources parsed successfully. The audit extracted only the two target member QNames from each version and retained URL, version, HTTP status, byte count and SHA-256. FASB's [2021 taxonomy technical guide](https://storage.fasb.org/2021%20US%20GAAP%20Financial%20Reporting%20Taxonomy%20and%20Data%20Quality%20Committe%20Rules%20Taxonomy%20Technical%20Guide.pdf) and [2022 taxonomy technical guide](https://storage.fasb.org/2022%20GAAP%20Financial%20Reporting%20Taxonomy%20Technical%20Guide.pdf) document the separate label/documentation resources.

## 3. Common-role results

| Symbol group | Common-role result | Cross-role exact text overlap | Same-context title |
|---|---|---|---|
| PCG-PB | \`terseLabel\` matches | Yes | Match |
| PCG-PE | \`terseLabel\` matches | Yes | Match |
| PCG-PG | \`terseLabel\` matches | Yes | Match |
| PCG-PH | \`label\` conflicts; text overlaps across roles | Yes | Match |
| PCG-PI | \`terseLabel\` matches | Yes | Match |
| STR | \`label\` conflicts | No | Match |

The four PCG groups with exact common-role matches are candidate taxonomy aliases only. Their custom schema elements contain no inline documentation, so the definition comparison remains incomplete. PCG-PH has an exact text overlap, but it occurs across different label roles; that is not equivalent to a same-role match. Preserve the conflict.

## 4. STR is not an alias under the retrieved standard taxonomy evidence

The two filings report the same same-context title, \`Class A common stock, par value $0.0001 per share\`, but their standard taxonomy resources differ:

| QName | Standard label | Documentation |
|---|---|---|
| \`us-gaap:CommonClassAMember\` (2021) | Common Class A [Member] | Classification of common stock representing ownership interest in a corporation. |
| \`us-gaap:CommonStockMember\` (2022) | Common Stock [Member] | Stock that is subordinate to all other stock of the issuer. |

The standard label and documentation roles conflict. The shared filing title does not override that evidence. Keep the QNames distinct; do not infer that the 2022 \`CommonStockMember\` means Class A solely because the filing's separate Security12bTitle says so.

## 5. Interpretation and next decision

- Four PCG groups: retain as **candidate alias relationships**, with exact common \`terseLabel\` and same-context title agreement, but no custom schema documentation and no effective-date/security-level proof.
- PCG-PH: retain as unresolved because the common default-label role conflicts; cross-role text overlap is recorded but not promoted.
- STR: **do not merge**; the official standard labels and documentation differ materially.
- Keep raw QNames, namespace versions, accessions, contexts and source hashes immutable.
- Stop extending this six-symbol label comparison. The next useful step is a survivorship-aware, stratified sample beyond the purposive 28 collision pairs, measuring issuer, listing, security and share-class coverage separately. Do not construct a canonical security master until broad coverage, corporate-action chronology and PIT availability pass.

Taxonomy labels and documentation are identity metadata, not a smart-money signal. No transaction-level feature or return hypothesis was tested.

## 6. Controls

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No alias/QName merge, security-master admission, strict-PIT admission, broad-universe coverage, alpha/return test, bootstrap/LOO, chronological OOS or holdout use. No production, universe, capital or parameter changes. No data purchase or vendor contact.
