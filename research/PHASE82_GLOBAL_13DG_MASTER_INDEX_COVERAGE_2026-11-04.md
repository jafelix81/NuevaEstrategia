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

## Corrected Gate A result — 2026-11-04

Run [41892370262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41892370262) completed successfully after the pair-semantics correction. Job 126792849392 passed the Phase 74/82 offline tests, compiled the audit module, retrieved all 43 quarters and uploaded artifact [13353118959](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41892370262/artifacts/13353118959). Artifact ZIP SHA-256: `e925ad8fe9792f27e570b9e882dff772bb67d9edd67f1c93404a198faab80985`.

**Gate A: PASS.**

- 43/43 quarter indexes returned HTTP 200; zero retrieval errors.
- 324,964 distinct 13D/13G accessions; zero cross-quarter accession duplicates.
- Zero unexplained metadata conflicts and zero malformed index rows.
- 1,832 single-CIK accessions and 323,132 multi-CIK accessions with two archive paths. The latter are valid paired index records, not duplicate accessions.
- Form counts: 13D 13,340; 13D/A 45,729; 13G 78,953; 13G/A 186,942. Amendments are 71.60% of the observed accession population, so amendment lineage is a major part of the eventual event model.
- 34,400 accessions have at least one of the 319 current candidate CIKs in the unlabelled index/path identity set: 32,805 unique-CIK hits and 1,595 multi-CIK ambiguous hits; 290,564 are controls. These are candidate locators, **not** subject-issuer counts or historical F80 coverage.
- Raw quarterly snapshots total 1,064,707,960 bytes. An independent post-download check recomputed all 43 SHA-256 hashes with zero mismatches.

The initial v1 artifact from run 41891043331 remains preserved but its 323,132 false-positive metadata conflicts and 120-row single-CIK-only sample are invalid for inference. The corrected artifact is the sole accepted Gate A snapshot.

## Next gate — Phase 83 stratified identity pilot

A guarded 120-filing pilot is prepared. It will stratify by 13D/13G family, original/amendment, regulatory timing regime and candidate/control/ambiguous CIK class; try every archive-path CIK without inferring its role; validate SEC-HEADER SUBJECT COMPANY and FILED BY against primary XML where available; and preserve each retrieved complete submission, SHA-256 and UTC retrieval timestamp.

Passing Gate A establishes index history and reproducibility only. The 120-filing identity pilot must pass before a full global subject-side census is authorized. No forward returns, feature selection or economic test has been run.

The deterministic 120-row manifest in artifact 13353118959 is balanced across the six form-specific timing regimes: 60 13D / 60 13G, 62 originals / 58 amendments, and 44 unique-candidate / 32 ambiguous / 44 control accessions. The regression suite now also verifies that pilot mode saves the exact complete-submission bytes, SHA-256 and UTC retrieval timestamp; offline run [41893467636](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41893467636) passed. The live identity pilot [41893546069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41893546069) completed with a failed preregistered subject-role gate; see the final Phase 83 outcome below.


## Final Phase 83 outcome — 2026-11-04

Run [41893546069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41893546069) completed with a **failed preregistered data gate**, not a parser failure. Its 120/120 complete submissions parsed; header accession/form/date and subject/filer identity fields were 100% concordant; subject CIK appeared in the master-index/path set in 120/120; XML issuer and filer matched the SEC header in 40/40 XML rows; all 120 raw submissions, SHA-256 hashes and UTC retrieval timestamps were preserved.

The failed criterion was the assumption that a unique current-universe CIK hit in the unlabelled index/path pair must be the subject issuer. In 44 unique-candidate rows, only 11 (25%) were header SUBJECT COMPANY; 33 (75%) were FILED BY only. All 32 ambiguous rows contained a target subject CIK and a target filer CIK. Across 76 candidate rows, 43 had a target subject CIK and 33 were filer-only false positives. The index/path CIKs are therefore locators only; SEC header role is required. The original Phase 83 gate remains failed and is not relaxed retrospectively.

All 120 headers contained a 14-digit ACCEPTANCE-DATETIME. This is an Eastern acceptance timestamp; Phase 83 did not independently establish public dissemination latency. Future economic tests must convert it with America/New_York daylight-saving rules and use a conservative next-session availability rule unless exact dissemination time is verified.

## Phase 84 — next role-aware validation

Branch `phase84-13dg-role-aware-identity-validation` contains a new preregistered 600-filing disjoint pilot. It excludes the 120 Phase 83 accessions and tests: target-subject recall in the index/path set; subject/filer role resolution; mandatory XML presence and issuer/filer concordance; acceptance timestamp conversion; raw bytes, SHA-256 and UTC retrieval. Filer-only CIK hits are measured and excluded as issuer events, not treated as a gate failure. A Phase 84 pass would authorize only a full subject-side coverage/event-normalization design, not an alpha test.
