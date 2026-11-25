# Phase 603 — SEC 13D/G global-index subject-discovery pilot

**Audit date:** 2026-11-24  
**Workflow run:** [45493730680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45493730680)  
**Artifact:** [14966963205](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45493730680/artifacts/14966963205)  
**Branch:** `phase603-sec-13dg-global-index-discovery-pilot`  
**Commit audited:** `7422ee7d69453ba3a1e88fb35265837c8c660c90`

## Decision

**PASS for a bounded current-quarter subject/filer discovery pilot; NOT admitted for historical F80 coverage, point-in-time availability, signal construction, or return testing.**

The pilot demonstrates why Schedule 13D/G discovery must be based on the filing header's **SUBJECT COMPANY** role rather than the accession submitter or **FILED BY** reporting person. It does not establish a predictive or economic edge.

## 1. Workflow and reproducibility

- Latest Phase 603 run completed successfully; job `bounded-global-index-pilot` completed with success.
- Offline regression suite: **22/22 tests passed** (Phase 603 plus Phase 485 header parser).
- The latest 20 repository Actions runs were completed; no active or queued run was present at this audit.
- The Phase 603 workflow uses push-only branch/path filters and a concurrency group. Several earlier pushes were superseded/cancelled; the final run above is the successful final-head result. No additional dispatch or duplicate workflow was started.
- Artifact ZIP SHA-256: `e7f7cfdee99744258f61079c9f9f720114f07a715345a99531392b56b81918e6`.

## 2. Global-index coverage — 2026/QTR3

Source: SEC EDGAR quarterly master index  
URL: https://www.sec.gov/Archives/edgar/full-index/2026/QTR3/master.idx  
SHA-256: `c0125fa6123fd9f47072a00a6b676bbed493e99ce30721614de081a5cd18e75f`

| Form | Candidate accessions |
|---|---:|
| SC 13D | 270 |
| SC 13D/A | 980 |
| SC 13G | 2,561 |
| SC 13G/A | 4,037 |
| **Total** | **7,848** |

- 15,692 index rows were retained and grouped into 7,848 unique accessions.
- 7,844 accessions have two distinct index rows; four have one. No exact duplicate rows were removed.
- No index-CIK/archive-path-CIK mismatches were found.
- 11,546 index rows have an index CIK different from the accession-prefix CIK. The accession prefix is therefore not a safe substitute for either filing-header role.
- Candidate discovery found 1,340 accessions with at least one currently mapped F80 CIK among the index rows versus 1,130 with an F80 CIK matching the accession prefix. These are discovery counts only; the index CIK is not assigned to a subject/filer role until the header is parsed.

## 3. Header-identity sample

A deterministic, bounded sample of **147 unique accessions** was selected across form and current-F80-index-presence strata: 27 SC 13D, 40 SC 13D/A, 40 SC 13G and 40 SC 13G/A.

- 147/147 submissions returned HTTP 200.
- 147/147 header identities were parsed as verified subject and filed-by CIKs.
- 147/147 header accession numbers matched the expected accession.
- 147/147 had both header roles represented in the grouped index CIKs.
- 147/147 archive-path CIKs matched the header subject-company CIK.
- Accession submitter CIK matched FILED BY in 63/147; it differed in 84/147.

### Current-F80 role comparison in this stratified sample

| Role match | Accessions |
|---|---:|
| SUBJECT COMPANY maps to current F80 | 24 |
| FILED BY maps to current F80 | 45 |
| Both roles map to current F80 | 2 |
| Subject-only F80 match | 22 |
| Filed-by-only F80 match | 43 |

This is the key diagnostic: a filer-only screen would miss 22 of the 24 sampled current-F80 subject matches, while 43 of the 45 filer matches are not subject-company matches. Those filer-only records may be legitimate reports by holders of non-F80 issuers; they are not issuer matches for an F80 subject-company study.

**Sampling limitation:** the sample is deliberately stratified on form and the presence of any current-F80 CIK in the index. These counts are not population prevalence estimates, have no inferential confidence interval, and must not be extrapolated to the full quarter. In addition, the 35 unmapped current-F80 tickers can cause genuine F80 subjects to fall into the apparent no-current-F80-index stratum.

## 4. Current-F80 identity coverage limitation

The frozen snapshot contains 335 tickers. Current SEC ticker-file mapping resolved **300/335 tickers (89.55%) to 299 unique CIKs**, with no conflicting ticker-to-CIK mappings. **35 tickers remain unmapped**:

`ARKF, ARKG, ARKK, ARKQ, ARKW, AVB, BITO, EA, EQR, IEFA, IWM, JETS, KRE, LPRO, OIH, QQQ, ROKU, SMH, SOXX, VEA, VNQ, VWO, WBD, WBS, XBI, XLB, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY`.

The current SEC mutual-fund ticker endpoint returned HTTP 200 but contributed no parsed ticker/CIK rows. This is a mapping/parser follow-up, not evidence that the unmapped names are inactive. The current ticker files are discovery aids only; they do not establish historical CIK/security identity, share-class continuity, delisted coverage, or historical F80 membership.

## 5. SEC User-Agent access observation

The final workflow log shows the `SEC_USER_AGENT` environment value was empty. The artifact records:

- `sec_user_agent_secret_present = false`
- `sec_user_agent_secret_accepted = false`
- `sec_user_agent_source = shared_phase401_contact_fallback`

The 147 submissions nevertheless returned HTTP 200 using the shared Phase 401 fallback contact. This does **not** verify that the repository Actions secret exists or is available to workflows. Do not expose any contact value in logs or artifacts. The bounded pilot completed, but the separate Phase 350 parent-retrieval path remains gated on a valid repository secret.

## 6. Point-in-time and research limits

- The 2026/QTR3 master index is a retrospective/corrected quarterly snapshot, not a prospective first-seen ledger or exact public-dissemination timestamp.
- SEC acceptance datetime is retained as metadata only; it is not certified as public availability.
- Filing date is used only as a coarse historical boundary.
- Current SEC ticker files do not prove historical F80 membership. No effective-dated CIK-to-security crosswalk was built.
- The pilot did not test returns, event alpha, OOS, bootstrap, LOO, or holdout.
- Signal-eligible rows: **0**.
- No raw SEC submission payloads were persisted; the artifact contains parsed public metadata, sample rows, and hashes.

## 7. Next gates

1. Verify/configure the repository Actions secret `SEC_USER_AGENT` with a project identifier and monitored contact email; never place the value in source, PR text, artifacts, or chat.
2. Repair the current ticker/CIK parser and resolve the 35 unmapped names, including fund/ETF and historical/delisted cases.
3. Run a bounded multi-quarter index census spanning pre- and post-structured-filing regimes (for example 2016Q1, 2020Q1, 2024Q1 and 2026Q3), preserving the same subject/filer/submitter separation and immutable source hashes.
4. Build an effective-dated security/CIK/ticker/class crosswalk and reconstruct the original 335-name universe by date before measuring historical issuer coverage.
5. Establish conservative knowledge times from actual first-seen evidence or a documented next-session bound. Do not backdate acceptance or filing dates as exact public release.
6. Only after those gates pass, preregister a subject-company event hypothesis and compare it incrementally with frozen LTM/F80 under chronological OOS, identical exposure and costs, block bootstrap/LOO. Do not treat 13G ownership or 13D activism as a directional signal by definition.

## Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged. No signal was admitted, no production workflow was modified, no capital/exposure/holding-period rule changed, and no paid data or vendor quote was requested. Options-data budget remains USD 0.
