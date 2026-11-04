# Phase 82 — Global SEC 13D/13G master-index coverage audit

**Date:** 2026-11-04  
**Branch:** phase82-13dg-global-index-coverage-audit  
**Scope:** global index-only feasibility; no complete-submission crawl and no economic test.

## Why this phase is necessary

Phase 35's original 20,265-row artifact is filer-side retrieval from CIKs associated with the current 335-name ticker map. It is not a subject-issuer census: investors and filing agents outside the current ticker universe can submit 13D/13G filings about a target issuer. Phase 77 corrected the 80-filing complete-submission pilot's role/timestamp interpretation (80/80 XML issuer/header SUBJECT COMPANY and XML filer/header FILED BY concordance), but that pilot remains a small filer-side sample.

Phase 74 already contains a global master-index parser. Phase 82 expands its index-only feasibility window to every completed quarter from **2016Q1 through 2026Q3** (43 quarters). The incomplete current quarter, 2026Q4, is excluded.

## Frozen current-universe candidate CIK input

The Phase 68 hosted artifact 13321546076 contains the current 335-row ticker mapping (ticker_mapping.csv): 335/335 tickers mapped, 319 distinct candidate CIKs, six registrant CIKs shared by multiple tickers, and two tickers with multiple CIK candidates. Phase 82 freezes the 319 distinct values extracted from that CSV's ciks column in:

- research/phase82_current_candidate_ciks.csv

This is a candidate-locator crosswalk only. It is not historical PIT identity, does not resolve fund series/class security identity, and must not be used as a tradable-security master. The current 335-name universe's original eligibility rule/membership history remains unresolved (Phase 71).

## Bounded retrieval plan

- Exactly 43 quarterly SEC master-index files: /Archives/edgar/full-index/{year}/QTR{q}/master.idx.
- No filing-level .txt, XML, HTML or exhibit downloads.
- Parse only SC 13D, SC 13D/A, SC 13G and SC 13G/A.
- Group duplicate master-index rows by accession while preserving all master-index CIKs/names, archive-path CIKs, forms, filing dates and filenames separately.
- Preserve each raw quarterly index in the artifact under raw_master_indexes/.
- Record URL, HTTP status, content type, byte count, retrieval timestamp (UTC) and SHA-256 for every quarter.
- Emit quarterly and form-family counts, unique CIK counts, duplicate accessions, malformed/metadata-conflict records, candidate CIK overlap and a deterministic pilot manifest.

The SEC request throttle is 0.8 seconds with the existing bounded retry policy. The job is guarded by an explicit commit-message trigger so code/documentation pushes run tests only.

## Gate A — index feasibility

A clean index gate requires:
1. all 43 quarter files retrieved successfully;
2. zero duplicate accessions across quarters;
3. zero unexplained form/date/archive-path conflicts (quarantine and report any conflicts);
4. separate counts for 13D, 13D/A, 13G and 13G/A;
5. immutable raw bytes and hashes for all retrieved quarter files.

A failure is archived with exact quarters and errors; no automatic retries or horizon changes are used to manufacture a pass.

## What a pass would and would not establish

A pass establishes the size and basic reproducibility of the global 13D/13G accession population for 2016Q1–2026Q3. Candidate overlap against the 319 current CIKs is only a locator diagnostic. It does **not** establish that the master-index CIK or archive-path CIK is the subject issuer. The following remain separate identities:

- master-index CIK / company name;
- archive-path CIK;
- accession-prefix submitting-account CIK;
- SEC-HEADER SUBJECT COMPANY CIK;
- SEC-HEADER FILED BY CIK;
- structured XML issuer CIK;
- structured XML filer CIK;
- each reporting person's CIK or explicit no-CIK status.

No CIK role may be inferred from another.

## Next gate, only if Gate A passes

1. Use the 319 current CIKs to stratify candidate/control/ambiguous index rows, but do not treat a CIK hit as subject identity.
2. Select a deterministic sample across 13D/13D-A/13G/13G-A, original/amendment, timing regime, candidate/control/ambiguous identity and legacy HTML/structured XML.
3. Download only the sample's complete-submission text and verify SEC header subject/filer, accession, form/date, and XML issuer/filer roles.
4. Measure candidate-index recall and filer-only false positives. Do not run the full global document corpus until these gates pass.
5. Reconstruct historical F80 security identity/membership separately; Phase 71 found that the original 335-name eligibility rule and dated membership ledger are not documented in the repository.

## Economic boundary

No return data, forward returns, signal construction, alpha tests, feature tuning, production changes, or changes to F80_TOP20_PARTIAL50_BASELINE_C20 are authorized. Even a successful global index and identity audit is a data-feasibility result, not evidence of informed trading or predictive value.

## 2026-11-04 — first hosted execution and parser correction

Run [41891043331](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41891043331) retrieved all 43 quarterly indexes (2016Q1–2026Q3) with HTTP 200, 43/43 requests, no retrieval errors and zero accession duplicates across quarters. It found 324,964 unique 13D/13G accessions and 34,400 accessions with at least one of the 319 current candidate CIKs in the master-index/archive-path identity set. Those candidate hits are locators only, not subject-issuer coverage.

The first parser version incorrectly treated any accession with more than one archive-path CIK as a metadata conflict. The raw index shows that two rows and two distinct archive paths are a normal paired-CIK representation: 323,132 accessions had two master-index rows/two archive paths, while 1,832 had one row/one path. The 323,132 were therefore false-positive conflicts, not SEC data corruption. The initial 120-row pilot manifest was consequently biased toward single-row filings and is **not valid for sampling**.

The parser has been corrected to:
- accept multiple master-index CIK rows and one or more corresponding archive-path CIKs without assigning roles;
- flag only unexplained row/form/date/path inconsistencies;
- distinguish single-CIK, multi-CIK/single-path and multi-CIK/multiple-path accessions;
- try all archive-path CIK candidates in deterministic order for a later sample;
- preserve complete-submission raw bytes, SHA-256 and UTC retrieval time in pilot mode.

Offline regression runs 41892207563 and 41892228391 are checking this correction. The original run/artifact remains preserved for auditability, but its metadata-conflict and clean-sample counts must not be used. A corrected 43-quarter run is required before the subject-identity pilot. No filing-level crawl, forward returns or economic test has been run.
