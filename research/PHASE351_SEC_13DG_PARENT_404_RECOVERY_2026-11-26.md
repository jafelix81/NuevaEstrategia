# Phase 351 — SEC 13D/G single-parent archive-path 404 recovery

**Date:** 2026-11-26 UTC  
**Parent phase:** Phase 350 run [45786611405](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405)  
**Prior artifact:** [15100039658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405/artifacts/15100039658)  
**Disposition:** one-row recovery only; no repeat of the 43 successful parent requests.

## 1. Target and evidence

Phase 350 retrieved and validated 43 of 44 exact explicit parent references. The only HTTP 404 is:

- Child: `0000886982-25-001416`, filed 2025-11-10.
- Child subject issuer: CIK `723612`.
- Child family: 13G.
- Explicit parent: `0000769993-25-000432`.
- Phase 350 path candidate: subject issuer CIK `723612`, HTTP 404.
- Phase 349 manifest alternate candidate: `769993`, equal to the accession prefix and distinct from the subject issuer CIK.

The alternate candidate is unverified until a retrieved SEC-HEADER independently confirms the exact accession, subject CIK, form family and acceptance chronology. The accession prefix is used only as a URL locator candidate.

## 2. Recovery design

The recovery script reads the immutable Phase 349 manifest and the completed Phase 350 artifact, requires exactly one unresolved HTTP-404 row, and attempts exactly one request using candidate CIK `769993`.

On HTTP 200, it preserves the raw submission and SHA-256 in the Actions artifact, then validates:
1. Parent accession exactly equals `0000769993-25-000432`.
2. SEC-HEADER subject-company CIK equals `0000723612`.
3. Parent form family equals 13G.
4. Parent acceptance UTC is strictly earlier than child acceptance UTC `2025-11-10T17:16:36Z`.

A 404 remains quarantined. A 403 or retryable transport/rate-limit response stops the workflow. The process never infers that the explicit reference is the immediate predecessor.

## 3. Duplicate-request protection

The Phase 350 workflow now runs offline tests on pull-request updates and only repeats the full 44-reference retrieval on an explicit manual dispatch with `run_live_capture=true`. Phase 351 downloads the existing Phase 350 artifact and makes only the one targeted recovery request.

## 4. Recovery result — 2026-11-26 09:00 UTC

- [Run 45787898552](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45787898552) passed all 11 offline recovery tests and completed exactly one SEC request.
- The request used the manifest candidate archive-path CIK `769993`; SEC returned HTTP 404.
- [Artifact 15101905659](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45787898552/artifacts/15101905659), SHA-256 `fb1d1b48759380bb64dfc37425afb42974d5aa1690223182c5d429eb42adb073`, records one target, one request, zero raw documents, zero validated references, and `NOT_FOUND`.
- The prior subject-CIK path `723612` also returned HTTP 404 in Phase 350.
- The child filing itself is independently visible as a 2025-11-10 Schedule 13G/A and its SEC primary document explicitly references `0000769993-25-000432` as `previousAccessionNumber`; the child identifies Avis Budget Group CIK `723612` and CUSIP `053774105`. This corroborates the child reference but does not establish that the parent accession is publicly retrievable.
- No third archive-path guess will be attempted. The parent remains unresolved and quarantined because the manifest/index did not verify an alternate path and both evidence-based candidates returned 404.

## 5. Validation limits

This recovery is identity/lineage work only. Even if the 44th parent validates:
- no first-publication timestamp is available;
- reporting-person overlap and CUSIP continuity still require independent validation;
- no historical F80 security-master or inactive-price coverage has been admitted;
- no alpha, return, OOS, bootstrap, LOO or holdout test is authorized;
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
