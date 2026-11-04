# Phase 76 — Global 13D/13G archive-path CIK correction
Date: 2026-11-04

## Finding

The global SEC master-index parser preserves both:
- CIK in the master-index CIK column (submitting filer association); and
- CIK embedded in the Filename archive directory path.

These are separate fields and must not be collapsed. For agent-filed 13D/13G submissions, the accession prefix is the submitting account CIK and may differ from the archive path CIK. Phase 74's current `complete_submission_url(accession)` used the accession prefix, which would reproduce the Phase 73 HTTP 404 defect on agent-filed documents even though the index already contains the correct archive directory CIK.

Concrete SEC example:
- Accession: 0000950157-25-000788
- Accession-prefix / submitting account: 0000950157
- Subject company: Fox Corp, CIK 0001754301
- Filed by: MFT SH Family Trust, CIK 0002080603
- SEC complete-submission text is accessible under the subject/archive directory CIK 1754301:
  https://www.sec.gov/Archives/edgar/data/1754301/000095015725000788/0000950157-25-000788.txt
- SEC filing index page also exposes the filed-by identity separately:
  https://www.sec.gov/Archives/edgar/data/2080603/000095015725000788/0000950157-25-000788-index.htm

## Correction

Branch: `phase76-global-13dg-archive-path-correction`

- `complete_submission_url(accession, archive_path_cik)` now requires the archive-path CIK from the quarterly master index.
- It refuses to guess from the accession prefix when the path CIK is absent.
- Pilot mode quarantines rows with non-unique/missing archive path CIK rather than issuing an ungrounded URL.
- Regression tests cover a conventional two-CIK index row and the agent-filed FOXA example.

Commits:
- 213adbb84169398d0629db7cd953ed1c2be5f1cd — path-aware URL resolver.
- 3be7e66ac3143c37d68c015f7085ed6ceb4b6173 — regression test.
- b81e2ff4a627ed48ea4f8d38836cffdb79acce10 — workflow branch filter for hosted offline tests.

## Validation status

Hosted offline tests are queued as run 41872762613. No SEC data crawl has been launched from this branch. Do not trigger a global 120-filing pilot until:
1. Phase 76 offline tests pass;
2. the separate Phase 73 corrected 80-filing pilot (run 41872288761) completes and its artifact is inspected;
3. no other SEC public-data crawl is active.

## PIT / research guardrails

- Archive path CIK is a retrieval locator, not proof of subject identity.
- The SEC-HEADER SUBJECT COMPANY and FILED BY blocks remain the identity ground truth.
- XML issuer and filer identifiers are independent cross-checks.
- Master-index CIK and archive-path CIK are candidate associations only.
- The global 13D/13G pilot remains an identity/discovery test, not an ownership-alpha test.
- No forward returns or economic tests are authorized.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
