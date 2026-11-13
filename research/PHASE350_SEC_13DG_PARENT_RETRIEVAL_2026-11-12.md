# Phase 350 — SEC 13D/G explicit parent retrieval

**Date:** 2026-11-12 UTC  
**Scope:** Retrieve the 44 exact parent accessions manifested in Phase 349.  
**Mode:** Public SEC Archives; raw submissions and SHA-256 preserved.

## Retrieval protocol

- Use the exact parent accession and the first ten accession digits only as the SEC archive-path CIK. The SEC documents that those digits identify the submitting entity and may identify a third-party filing agent; they are not issuer identity.
- Archive URL: \`/Archives/edgar/data/{archive_path_cik_without_leading_zeros}/{accession_without_dashes}/{accession_with_dashes}.txt\`.
- Declare a project User-Agent and throttle to 2 requests/second, below the SEC's 10 requests/second fair-access ceiling.
- Stop on HTTP 403; do not continue sending requests after an access denial. Retry 429 and transient 5xx conservatively.
- Preserve every HTTP-200 raw submission, byte count and SHA-256.

Official SEC guidance:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/developer-resources
- https://www.sec.gov/about/webmaster-frequently-asked-questions

## Validation

For each parent submission, parse SEC-HEADER and compare:
1. Exact accession.
2. Subject-company CIK against the child issuer CIK.
3. 13D/13G family against the child family.
4. Parent acceptance UTC strictly earlier than child acceptance UTC.

The accession-prefix CIK is never used as subject issuer or reporting-person identity. A validated explicit reference is not automatically the immediate predecessor. Security CUSIP continuity and reporting-person overlap are separate Phase 351 checks.

## Timing and research controls

The SEC states that filings often appear on sec.gov within 1–3 minutes after EDGAR acceptance and does not provide a timestamp for first public availability. Therefore, even after header validation, no same-session execution is assumed: any later event study must use the next trading session after acceptance, with a conservative price-side execution rule.

No forward returns, alpha, OOS, bootstrap, LOO or holdout test is authorized. No source is admitted to production. F80 remains frozen.


## Material access block — 2026-11-12

- [Run 43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) passed all 10 offline tests and downloaded the immutable Phase 349 artifact, then received HTTP 403 on the first SEC Archives request.
- The request used a project-URL User-Agent but no monitored contact email. The SEC response contained no explanatory body. The script stopped immediately: 1 request attempted, 0 raw documents saved, 0 of 44 parents retrieved; no repeated requests were made.
- [Partial diagnostic artifact 13991999046](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770/artifacts/13991999046), SHA-256 `04c6568b01de176e55492d75f3224503c38cc8842a549b10f23a30c8d510d6c1`.
- The workflow now requires a GitHub Actions repository secret named `SEC_USER_AGENT`, containing a project identifier and a monitored contact email. The value is not written to logs or committed. No further SEC request will be attempted until that secret is configured.

## Safe preflight replay — 2026-11-12

The initial hosted run used the project-URL-only User-Agent and stopped after one HTTP 403. The current workflow revision adds a separate configuration preflight before the retrieval step:

- If repository secret `SEC_USER_AGENT` is absent or lacks an `@` contact address, the job exits before any SEC network request.
- If present, the secret is passed only through the Actions environment; it is not echoed or committed.
- The retrieval remains throttled at 2 requests/second and stops immediately on 403.

A documentation-only PR update is used to exercise this preflight against the current repository secret configuration. This does not authorize any request with an invalid/missing contact string. Parent retrieval remains blocked until the preflight passes.
