# Phase 327 — single-accession SEC Form 4 archive recovery

**Date:** 2026-11-12 UTC  
**Status:** COMPLETED WITH ONE QUARANTINED ACCESSION  
**Research class:** targeted source-recovery audit; no return or alpha test.

## Executive decision

Phase 326 retrieved and reconciled 282 of 283 original Form 4/4-A submissions selected from the 28 exact same-day ticker-collision pairs. One accession remained unavailable after six unpadded SEC archive layouts returned HTTP 404.

Phase 327 avoided another full 283-document download. It reused a SHA-256-pinned, checked-in Phase 326 metadata manifest and retried **only the one unresolved accession**, using zero-padded CIK archive paths. All six padded layouts also returned HTTP 404. The record remains quarantined. The 282 previously validated submissions were not re-fetched.

This closes the recovery attempt without inventing a document or replacing primary SEC evidence with a secondary source.

## 1. Reproducibility

- Final GitHub Actions run: [43211633876](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43211633876) — **SUCCESS**.
- Offline regressions: **5/5 passed**.
- Recovery artifact: [13941202444](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43211633876/artifacts/13941202444), SHA-256 a2b0f342958448a33f0337383c2f8b21d82efac19bf1be098a6ea7d3e6ad3b77.
- Phase 326 source artifact: run 43209373482, artifact 13939999128, SHA-256 eea7eaf97b91acfdbdac866f8d98660ec98be03adc8c4038b800f74cf86d81d5.
- The compact prior manifest is committed at [phase326_prior_recovery_manifest_2026-11-12.json](phase326_prior_recovery_manifest_2026-11-12.json); its SHA-256 is pinned in the recovery code.
- The workflow reads the immutable Phase 321/325 source hashes from that manifest and does not download or refetch the prior 282 successful submissions.

Two earlier Phase 327 setup attempts were not accepted: one attempted a cross-run artifact download that returned HTTP 401; another used an incorrect manifest digest. The final workflow removed the cross-run artifact download, pinned the manifest's actual digest and passed all offline controls before making the six targeted SEC requests.

## 2. Recovery result

| Measure | Result |
|---|---:|
| Previously validated submissions reused | 282 |
| Accessions retried | 1 |
| Zero-padded CIK/layout attempts | 6 |
| HTTP 404 responses | **6/6** |
| Bytes downloaded in recovery | 0 |
| Final retrieved submissions | 282/283 |
| Remaining quarantined accessions | 1 |

The six paths were the flat-submission and accession-directory layouts for normalized CIKs 939057, 1041368 and 1972440, with each CIK zero-padded to ten digits. No candidate returned a submission body. Combined with the six unpadded 404s from Phase 326, twelve tested archive path/layout variants failed.

The failed accession remains 0000939057-26-000239 (Form 4, 2026-09-25; issuer CIK 1041368; reporting-owner CIK 1972440; bulk ticker label TSBK). The Phase 321 daily-index row and its file hash are preserved in the prior manifest. The index row is not a substitute for the missing original submission XML/header.

## 3. Interpretation

- This is a **source-availability quarantine**, not evidence that the index row is false or that the filing never existed.
- No third-party aggregator was used to fill the gap.
- The TSBK collision pair remains incomplete. No inference about the actual listed security, share class or issuer-symbol correctness is made.
- The other 27 pairs have source-level title diagnostics: 20 overlapping title-label sets and 7 disjoint sets. Neither category proves security identity or distinct share classes.
- Phase 326's 282/282 retrieved submissions remain the validated evidence set; Phase 327 adds no new filing document.

## 4. Research controls and next step

- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No strict PIT admission, alpha/return test, bootstrap/LOO, chronological OOS or holdout use.
- No production, universe, capital or parameter change.
- No raw SEC bytes uploaded, vendor contacted, data purchased or email sent.
- Do not repeat the same 12 archive-path attempts. Keep the accession quarantined unless a new, independently documented SEC primary-source route becomes available.

The next material research gate is not another retry of this one filing. It is the effective-dated issuer → listing → security → share-class crosswalk and broad survivorship-aware universe coverage, followed by transaction-level Form 4 semantics and only then an incremental event study against frozen LTM/F80.
