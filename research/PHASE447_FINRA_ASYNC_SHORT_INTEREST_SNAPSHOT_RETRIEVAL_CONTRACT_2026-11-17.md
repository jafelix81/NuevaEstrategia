# Phase 447 — FINRA consolidated short-interest asynchronous retrieval contract

**Audit date:** 2026-11-17 UTC  
**Disposition:** **READY FOR A CONTROLLED, SINGLE-SETTLEMENT LIVE VALIDATION; NO HISTORICAL REINGESTION OR ALPHA TEST AUTHORIZED YET.**  
**Scope:** repository preflight, official API-contract audit, private retrieval-client implementation, synthetic offline regression only.

## 1. Repository preflight performed first

- Repository: \`jafelix81/NuevaEstrategia\` (public).
- Main HEAD at preflight: \`c397e3edef9e8babd947f062b87fd7063963739c\` (Phase 446).
- Actions API: 7,678 total workflow runs; latest 30 inspected. No run was in progress or queued in the returned latest-run set.
- Latest run [43990197952](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43990197952) was a Phase 444 pull-request run, not a production capture: \`offline-regression\` passed; \`live-capture\` was skipped; no artifact expected. Its log includes a synthetic accession fixture, not a live SEC observation.
- Latest main-branch SEC scheduled capture [43970444015](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43970444015): offline regression passed; live capture failed on the Form 144/A feed after four 60-second read attempts; state commit was skipped; artifact list empty. Phase 444's independent-feed persistence correction has CI coverage but no post-merge live validation was present at this preflight.
- Prior successful SEC scheduled run [43862500790](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43862500790): both jobs passed; artifact \`14223876987\`, 1,181 bytes, SHA-256 \`a1a806b330723ab6d8487727518b80fe70ea3ed93a9a30a93720a09f904d74aa\`; 55 feed observations, zero new accessions/events.
- SEC 13D/G run [43918910577](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43918910577): 11/11 offline tests passed; the explicit configuration step failed because \`SEC_USER_AGENT\` was empty; archive retrieval was skipped and no artifact was produced.
- CFTC TFF run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) remains a successful branch-push/bootstrap, not a scheduled first-receipt observation. Its artifact \`14084802705\` is 1,068 bytes, SHA-256 \`c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef\`. The mainline warm-up remains 3,035 historical rows with zero prospective signal-eligible observations. The next scheduled capture is not due at this preflight.
- Branch enumeration: 281 branches across three pages. Open PRs: 56. Workflow files: 67.
- Relevant stacked PRs remain open and draft: #61 (FINRA T1 publication clock) and #44 (Cboe DataShop metadata/PIT). Neither was changed or merged.
- No workflow was dispatched, rerun, or duplicated.

## 2. Phase 446 finding carried forward

The old Phase 31 short-interest panel remains **killed as retrieved**. The inspected artifact \`12588045711\` had 102 successful synchronous requests, all exactly 5,000 rows (the FINRA synchronous cap), plus four failed settlement requests. Its 9,420 filtered rows contained only 98 observed symbols, all A–D. Those 98 are not complete positive-position incidence, not effective universe coverage, and not evidence that E–Z had zero positions. None of the old snapshots is proven complete; no absent symbol may be zero-filled.

Phase 447 does not revive that panel. It prepares a new retrieval contract.

## 3. Official FINRA contract confirmed

The official FINRA Developer Center documents the production dataset as:

- Group: \`otcMarket\`
- Dataset: \`consolidatedShortInterest\`
- Endpoint: \`/data/group/otcMarket/name/consolidatedShortInterest\`
- Data availability: by 4:40 p.m. ET on the publication date.

The Query API supports asynchronous requests. For a POST request, \`async: true\` returns HTTP 202 with a \`Location\` status URL and no result body. The client polls the status URL; FINRA recommends no more than one poll per minute. HTTP 202 means pending; HTTP 200 means complete and includes a pre-signed \`resultLink\` and expiry. The pre-signed result URL must be fetched before expiry **without an Authorization header**, because the embedded token makes an Authorization header return HTTP 400. The completed async status response carries the record metadata headers needed for reconciliation.

Limits documented by FINRA:
- Synchronous maximum: 5,000 records per request.
- Asynchronous maximum: 100,000 records per request.
- Offset maximum: 500,000.
- For larger datasets, use narrow filters/partitions and reconcile all partitions; never infer completeness from a successful HTTP status alone.

Official references:
- https://developer.finra.org/docs
- https://developer.finra.org/products/query-api
- https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest

FINRA's documentation also states that Individual API accounts are for personal/non-commercial use and are not intended for commercial purposes. No credential, account, trial, purchase, or vendor contact was created in this phase. The client does not redistribute data; raw output defaults to a private local temporary directory.

## 4. Phase 447 implementation

Added a reusable, read-only async client for one settlement date at a time:

1. Submit a narrow POST with \`settlementDate = YYYY-MM-DD\`, selected raw fields, \`async=true\`, \`limit=100000\`, and \`offset=0\`.
2. Require HTTP 202 and a valid HTTPS \`api.finra.org\` async status URL.
3. Poll at intervals of at least 60 seconds; validate request ID and pending/complete status.
4. On completion, capture \`Record-Total\`, \`Record-Offset\`, \`Record-Limit\`, \`Total-Records-On-Page\`, provider tracking IDs, and result expiry from the completed status response.
5. Reject a result over the 100,000-row ceiling or any nonzero offset; partitioning is deliberately not guessed until the provider metadata confirms a disjoint field and values.
6. Download the pre-signed result URL without an Authorization header.
7. Require JSON row objects, exact row-count equality to \`Record-Total\`, optional page-count equality, exact settlement-date equality on every row, and a nonblank \`symbolCode\`.
8. Save raw JSON and a SHA-256 manifest only to the supplied private output directory. No raw file is uploaded as a GitHub artifact.
9. Set \`snapshot_complete=true\` only after exact reconciliation. \`zero_inference_allowed\` and \`signal_eligible\` remain false because effective-dated identity/scope and the separate research admission gates have not passed.

Files:
- \`research/phase447_finra_async_snapshot_client.py\`
- \`research/test_phase447_finra_async_snapshot_client.py\`

## 5. Offline validation

Local synthetic regression: **11/11 tests passed**, plus Python compilation. The client also restricts result links to HTTPS AWS S3 hosts, rejects an invalid polling interval before submitting any request, and writes private output with restrictive file permissions.

Tests cover:
- narrow async payload and settlement filter;
- HTTP 202 / Location validation;
- pending versus complete state;
- request-ID matching and result expiry;
- required record metadata headers;
- row-count and settlement-date reconciliation;
- over-limit partition rejection;
- minimum one-minute polling interval;
- no Authorization header on the pre-signed result download;
- private output and manifest generation.

No live FINRA request was made. The fixtures are synthetic and do not establish the actual response shape for a production consolidated-short-interest query. The next phase must perform one controlled live validation before any historical batch.

## 6. Exact next gates

1. Verify that a valid \`FINRA_ACCESS_TOKEN\` is available to the authorized research runtime. No secret values were inspected or changed.
2. Execute one historical settlement-date query only, using the async path. Record the submission time, status polls, completed headers, result expiry, row count, raw hash and private manifest.
3. Confirm that the result file format and all response headers match the official contract. If the dataset returns a format other than JSON despite \`Accept: application/json\`, stop and adapt only after inspecting the actual response.
4. If \`Record-Total <= Record-Limit <= 100,000\` and the downloaded count matches exactly, repeat the same protocol for the 106 Phase 31 settlement dates under FINRA's 20 async requests/minute/dataset/account throttle. If any date exceeds 100,000, stop and design metadata-verified disjoint partitions; do not offset blindly.
5. Reconstruct positive rows / structural zeros / unknowns only after each entire settlement snapshot is complete and the effective-dated security identity and market-scope gates pass.
6. Only after the 335-name panel is valid may a new chronological diagnostic be designed against frozen LTM/F80. Phase 31 return diagnostics remain exploratory and are not reused as alpha evidence.

## 7. Research disposition

- Phase 31 short-interest panel: **KILL / incomplete as retrieved**.
- FINRA consolidated short interest: **conditional source candidate; async re-ingestion readiness improved, live contract still unverified**.
- No signal, alpha, return, OOS, bootstrap, LOO, or holdout test was run.
- No raw market data, credential, or secret was committed.
- No production workflow or capture schedule was changed.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\`, universe, parameters, holdout, capital and exposure remain frozen.


## 8. OAuth extension and final credential check (2026-11-17)

The client was extended to support FINRA's documented OAuth 2.0 client-credentials flow. If no bearer token is provided, it POSTs to the FIP token endpoint using Basic Auth over FINRA_CLIENT_ID:FINRA_CLIENT_SECRET, validates access_token and expires_in, then uses the short-lived bearer only for FINRA API and status calls. The token itself is never logged or written to the manifest. FINRA documents this exact flow and recommends regenerating before expiry or caching no longer than 30 minutes.

The final local suite is **14/14 synthetic tests**, including token exchange, client-credential retrieval, and fail-closed behavior when all credentials are absent. Python compilation also passes.

The one-settlement live-validation workflow was corrected to accept either FINRA_ACCESS_TOKEN or both OAuth client secrets. Run [44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531) failed at the credential guard: all three environment variables were empty. The capture step was skipped; **no FIP or FINRA API request was made**. The live workflow is retained as manual workflow_dispatch only, with no schedule or automatic polling.

**Human action required before live validation:** configure FINRA_CLIENT_ID and FINRA_CLIENT_SECRET as GitHub Actions secrets (preferred), or provide a valid FINRA_ACCESS_TOKEN. Do not put credentials in repository files or workflow YAML. After configuration, dispatch exactly one settlement-date validation, inspect the non-raw manifest, and only then consider the 106-date historical batch.

The offline CI after the original merge, [Run 44007179732](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007179732), passed compilation and all 11 then-current tests. The OAuth extension was subsequently validated by the PR workflow and the post-merge main-branch workflow (14/14 tests).


## 9. Final merge and CI (2026-11-17)

The OAuth extension was merged in [PR #111](https://github.com/jafelix81/NuevaEstrategia/pull/111), commit 13b028593213108077dc100f0a81fed688ad9a70. Post-merge push CI [Run 44007937167](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007937167) passed: Python compilation and **14/14 synthetic contract tests**. No live credential was present, so this run performed no FINRA request. The manual-only live workflow is now available on main for use after the required Actions secrets are configured.
