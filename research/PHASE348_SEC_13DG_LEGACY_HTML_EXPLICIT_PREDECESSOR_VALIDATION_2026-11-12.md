# Phase 348 — SEC 13D/G legacy-HTML explicit predecessor validation

**Date:** 2026-11-12 UTC  
**Status:** COMPLETE_2_OF_2_LEGACY_HTML_PARENTS_VALIDATED  
**Mode:** Offline only; immutable Phase 84 and Phase 93 artifacts. No new SEC requests.

## 1. Finding

Phase 93 classified two explicit previousAccessionNumber references as header-sample-consistent but XML-unavailable. Reinspection of the Phase 84 raw-submission artifact shows that both parent submissions are present as legacy HTML, not missing documents. The XML-only parser had treated a format boundary as unavailable lineage evidence.

Both references now pass exact checks for parent accession, SEC-HEADER subject CIK, 13D family, strictly earlier filing/acceptance time, immutable raw-file hash, and exact parent/child CUSIP equality.

## 2. Validated references

| Child amendment | Explicitly referenced parent | Subject CIK | Parent accepted UTC | Child accepted UTC | Matching CUSIP |
|---|---|---|---|---|---|
| 0001140361-25-028962 | 0001140361-24-021787 | 0001140411 | 2024-04-24 21:18:35 | 2025-08-06 00:57:32 | 72200N700 |
| 0000038777-25-000024 | 0000038777-24-000050 | 0001794041 | 2024-02-27 20:51:33 | 2025-02-11 15:54:50 | 35242N202 |

Both parent primary documents are HTML (ef20027478_sc13d.htm and frkbsp23in.htm). Their raw submission SHA-256 values match the Phase 84 manifest. The parent CUSIPs pass the standard check digit and exactly match the child filing's CUSIP.

These are validated explicit references, not inferred links. previousAccessionNumber is not assumed to identify the immediate predecessor; no event collapse or chain compression is performed.

## 3. Reproducibility

- Phase 84 run 41914491120 / artifact 13364856424; ZIP SHA-256 b807be9099e1a777c232f6d50b341e8e714585dc4da5fe993e833c2051494b16.
- Phase 93 run 41940675337 / artifact 13375652511; ZIP SHA-256 e9252a741d111319f7d93796658ebe4e1c439903444e905d557e8de0a023497a.
- Both immutable artifacts were downloaded and verified locally.
- Four offline regression tests passed.
- No live SEC requests were made.

## 4. Remaining gap and decision

The other 44 explicit predecessor accessions remain outside the 600-row Phase 84 header sample. They require a targeted retrieval and the same subject/family/time/CUSIP/person checks. The 51 amendments without an explicit predecessor remain unresolved; Phase 93 produced only two unconfirmed sample-limited candidate edges, neither of which is promoted here.

Decision: add a legacy-HTML parser path to the 13D/G lineage audit. Do not treat “no structured XML” as “no usable filing.” Preserve raw HTML, SEC-HEADER roles, acceptance time, CUSIP and parser regime separately.

This does not establish complete amendment history, effective-dated ticker/venue identity, historical F80 membership, or price coverage. No return, alpha, OOS, bootstrap/LOO or holdout test is authorized. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
