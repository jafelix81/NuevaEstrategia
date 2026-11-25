# Phase 616 — SEC Schedule 13D/G global-index discovery feasibility and bounded identity sample

**Audit date:** 2026-11-25  
**Status:** offline implementation and follow-up hardening validated. Final PR CI passed 27/27 tests on head `f4088647fa89f72f4ec7f72a4542e6cc7fd122d8` in [Run 45589384903](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45589384903). The live-sample job was skipped; no SEC request was made.  
**Decision:** restore Schedule 13D subject-issuer discovery as the highest-priority free institutional-disclosure line; keep 13G separate as slower ownership-state context.

## 1. Why the source priority changes

Phase 596 and Phase 600 establish that the legacy 20,266-accession Schedule 13D/G panel is quarantined. The old discovery method queried submissions by the 335 F80 CIKs as filers. It can miss activist/reporting persons outside F80 whose filings name an F80 company as the subject issuer. It also constructed archive URLs from the filer CIK, which is unsafe for third-party filings.

The SEC header identities must remain separate. One repository example has accession prefix / FILED BY CIK 0000895421 (Morgan Stanley) and SUBJECT COMPANY CIK 0001793855; those happen to coincide for the filer and accession prefix in that filing. A separate SEC Schedule 13G example for Wynn Resorts shows accession prefix 0001193125, SUBJECT COMPANY CIK 0001174922, and FILED BY CIK 0000096223 (Jefferies) — three distinct identities ([SEC header example](https://www.sec.gov/Archives/edgar/data/1174922/000119312523039159/0001193125-23-039159-index-headers.html)). The SEC states that the accession prefix can be a third-party filing agent's CIK ([SEC accession-number guidance](https://www.sec.gov/about/webmaster-frequently-asked-questions)).

Therefore the accession prefix is a submitter/login diagnostic, not a filer or subject identity. The master-index CIK/company-name pair is treated only as a subject-company candidate and must be verified against the SEC-HEADER SUBJECT COMPANY block. FILED BY remains a separate filing-entity identity. Archive-path CIK is a retrieval locator, not an identity substitute.

## 2. New discovery route

The new collector enumerates all filers from SEC quarterly master.idx files, then filters exact forms:
- SC 13D
- SC 13D/A
- SC 13G
- SC 13G/A

Quarterly index windows are fixed before retrieval:
- 2023 Q4 — pre-2024 13D/13G deadline regimes; straddles the 2023-12-18 voluntary structured-data start.
- 2024 Q1 — straddles the 2024-02-05 13D deadline change; remains pre-2024-09-30 for 13G.
- 2024 Q3 — post-2024-02-05 13D regime and pre-2024-09-30 13G regime.
- 2024 Q4 — straddles the 2024-09-30 13G change and 2024-12-18 mandatory structured-data transition.
- 2026 Q3 — recent complete-quarter post-transition coverage.

The SEC master index provides company CIK/name, form, filing date and archive filename. Its `Filename` field is a flat submission path (`edgar/data/{path_cik}/{accession}.txt`); the collector validates that source form, then derives the accession-number directory only for the index-headers URL. The index CIK/company-name pair is a candidate subject identity and is checked against the header SUBJECT COMPANY CIK. The archive-path CIK is retained as a locator diagnostic. The Phase 485 parser verifies SUBJECT COMPANY and FILED BY independently; the accession prefix is preserved as an EDGAR submitter/login CIK and is never required to equal FILED BY.

## 3. Preregistered bounded sample

- 44 unique accessions selected deterministically from the global index.
- Round-robin stratification by quarter, 13D/13G family, original/amendment, legal deadline regime and XML/schema regime. The sample must contain at least one accession from each of the five preregistered quarters; missing-quarter input or sample coverage fails closed.
- Five quarterly index files only; no 20,266-row legacy-panel crawl.
- Retrieve index-header documents only; no primary filing body, ownership tables, holdings, prices or returns.
- Preserve each index file and header response with SHA-256 hashes and source URLs.
- Require all four exact forms and all five quarterly windows to appear in the 44-row sample, plus 44/44 verified subject/filer header blocks and 44/44 header SUBJECT COMPANY-to-index-company CIK matches for PASS_HEADER_IDENTITY_ONLY. Accession-prefix/index-CIK and FILED BY/accession-prefix differences are diagnostics, not failures, because filing-agent CIKs can differ.
- Archive-path CIK versus parsed subject CIK is reported as an independent diagnostic. A mismatch is quarantined for path analysis but does not replace or invalidate an otherwise verified header identity.
- Any missing, malformed, conflicting or filer-mismatched record is quarantined. No ticker is inferred.

This is a parser/discovery feasibility sample, not a statistical coverage estimate and not an alpha test. A passing sample authorizes only a separate historical coverage audit, not the full rebuild.

## 4. Point-in-time and legal controls

- Keep SC 13D, SC 13D/A, SC 13G and SC 13G/A separate.
- 13D deadline regime changes effective 2024-02-05; 13G compliance regime changes from 2024-09-30 and depends on filer category.
- Structured-data transition: voluntary from 2023-12-18, mandatory from 2024-12-18.
- Preserve ACCEPTANCE-DATETIME for chronology only. It is not exact public availability.
- Filing date remains a coarse retrospective knowledge boundary; any later event study must use conservative next-full-session availability unless a stronger first-seen source exists.
- Model amendments as changes to reporting-group × subject issuer × covered class state, not automatically as independent new purchases.
- No 13G filer is assumed passive or uninformed; no 13D filer is assumed successful or informed.

## 5. Credential and execution safety

The manual-only workflow passes the repository secret SEC_USER_AGENT directly to the collector (without a literal escape prefix) and fails before the first request if it is missing or contains a placeholder. The secret value is never printed or stored. The connected GitHub interface cannot read or set secret values.

The user previously indicated that the SEC User-Agent may already have been configured. This code path now consumes the shared secret; PR #204's current scope only wires it into the separate FTD workflows, not this 13D/G workflow. If the secret already exists, no settings change is needed. After this PR is merged, the one-time workflow_dispatch input run_live_sample=true is required to run the 44-header sample. This environment cannot dispatch Actions workflows through the available GitHub GET interface, so that single dispatch must be initiated in GitHub by the repository maintainer.

The legacy Fase 49 workflow is not used by this phase: it still contains a placeholder User-Agent and the F80-filer-only discovery logic. Do not manually dispatch that legacy workflow.

No SEC request was made in this phase. PR validation is offline-only. No full historical crawl, paid data, vendor contact, quote request or strategy change is authorized.

## 6. Acceptance and kill criteria

The 44-row selection explicitly includes quarter as a stratification dimension. All five preregistered quarters must be represented in both the input index rows and the selected sample; otherwise the sample fails before any header request. This control passed its dedicated positive and negative regression tests.

PASS only if: 44/44 header SUBJECT COMPANY and FILED BY blocks contain valid, unambiguous CIKs; 44/44 header SUBJECT COMPANY CIKs match the master-index company CIK; zero unresolved header retrievals or identity conflicts. The accession prefix may identify a third-party filing agent and is not required to match FILED BY.

Archive-path CIK mismatches are separately reported and quarantined for path/subject reconciliation; they are never used to infer subject identity.

Fail/park if: the SEC header cannot be retrieved, subject/filer blocks are missing or ambiguous, the master-index company CIK disagrees with header SUBJECT COMPANY, or the 44-record sample cannot be selected from the fixed windows.

Even after a pass, the next gate is effective-dated subject CIK/CUSIP/security-class mapping against historical F80 membership and coverage/false-zero analysis. No returns are authorized until that gate passes.

**No strategy change:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No signal, event study, forward-return, OOS, bootstrap, LOO, exposure, cost, universe or production change.
