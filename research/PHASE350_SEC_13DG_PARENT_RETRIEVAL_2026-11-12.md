# Phase 350 — SEC 13D/G explicit parent retrieval

**Original phase:** 2026-11-12 UTC  
**Live retrieval completed:** 2026-11-26 08:52 UTC  
**Run:** [45786611405](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405)  
**Artifact:** [15100039658](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45786611405/artifacts/15100039658)  
**Artifact SHA-256:** `d1ad6a7110256cfe057729782b6c90e37d0729ced17b7f3e7e6b95c9203ff87d`

## 1. Retrieval result

The immutable Phase 349 manifest contains 44 exact explicit parent accessions. The completed Phase 350 run attempted all 44 at 2 requests/second using the established shared project-contact fallback because the repository secret `SEC_USER_AGENT` was empty.

| Result | Count |
|---|---:|
| Target parent references | 44 |
| Requests attempted | 44 |
| HTTP 200 | 43 |
| HTTP 404 | 1 |
| Raw parent submissions saved | 43 |
| SEC-HEADER parsed | 43 |
| Valid explicit references | 43 |
| Quarantined / unresolved | 1 |

All 43 HTTP-200 documents passed exact accession, subject-company CIK, 13D/13G family and strictly-earlier acceptance checks. The artifact contains 43 raw submissions, the row-level validation CSV and a summary. Raw submissions were not committed to the repository.

The 15-test Phase 350 suite passed in the live run. The fallback source is recorded as `shared_project_contact_fallback`; the User-Agent value is never logged or persisted.

## 2. Single unresolved reference

The only unresolved target is:

- Child accession: `0000886982-25-001416`
- Child filing date: 2025-11-10
- Child subject issuer CIK: `0000723612`
- Child family: 13G
- Explicit parent accession: `0000769993-25-000432`
- Phase 350 attempted archive-path CIK: subject CIK `723612`
- Result: HTTP 404

The Phase 349 manifest records `769993` as the alternate archive-path candidate, equal to the accession prefix and distinct from the subject issuer CIK. This is a locator candidate only, not issuer or reporting-person identity. It must not be accepted unless the returned SEC-HEADER independently validates the exact parent accession, subject CIK `723612`, 13G family and parent acceptance strictly before the child.

The child is also listed on the issuer's SEC-filings page as a Schedule 13G/A filed 2025-11-10; this corroborates the child filing's existence, not the parent archive path. No inference is made that the explicit reference is the immediate predecessor.

## 3. Phase 351 targeted recovery

A separate Phase 351 workflow now attempts only the single unresolved HTTP-404 parent, using the manifest's alternate candidate `769993`. It reuses the immutable Phase 349 manifest and completed Phase 350 artifact, so it does not repeat the 43 successful SEC requests.

The Phase 350 workflow was also changed so pull-request updates run offline tests only. Repeating all 44 SEC requests now requires an explicit `workflow_dispatch` input `run_live_capture=true`.

Phase 351 will preserve the same controls:
- One targeted request only; no candidate fan-out.
- 2 requests/second ceiling (only one request in this recovery).
- Immediate stop on 403 or transient/rate-limit failure.
- Preserve raw bytes and SHA-256 only in the Actions artifact.
- Validate exact accession, subject issuer CIK, form family and strictly earlier acceptance.
- Keep unresolved/ambiguous results quarantined.
- No immediate-predecessor inference.

## 4. Research disposition

- 43/44 explicit parent references are validated.
- One parent remains quarantined pending Phase 351.
- Reporting-person overlap, CUSIP continuity and security identity remain separate checks.
- No historical first-publication timestamp is available; strict PIT admission remains false.
- No forward returns, alpha, chronological OOS, bootstrap, LOO or holdout test was run.
- No signal or production use is authorized.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No paid data, vendor contact, capital, exposure, universe, parameter or cost changes.
