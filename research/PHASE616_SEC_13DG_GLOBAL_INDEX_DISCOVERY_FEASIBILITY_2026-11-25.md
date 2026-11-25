# Phase 616 — SEC Schedule 13D/G global-index discovery feasibility and bounded identity sample

**Audit date:** 2026-11-25  
**Status:** offline implementation prepared and validated; bounded live sample not yet dispatched. The final offline CI passed 25/25 tests in [Run 45582424995](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45582424995); the live-sample job was correctly skipped.  
**Decision:** restore Schedule 13D subject-issuer discovery as the highest-priority free institutional-disclosure line; keep 13G separate as slower ownership-state context.

## 1. Why the source priority changes

Phase 596 and Phase 600 establish that the legacy 20,266-accession Schedule 13D/G panel is quarantined. The old discovery method queried submissions by the 335 F80 CIKs as filers. It can miss activist/reporting persons outside F80 whose filings name an F80 company as the subject issuer. It also constructed archive URLs from the filer CIK, which is unsafe for third-party filings.

The official SEC index-header example already in the repository demonstrates the distinction:
- Accession / FILED BY CIK: 0000895421 (Morgan Stanley).
- SUBJECT COMPANY CIK: 0001793855 (abrdn Global Infrastructure Income Fund).
- The archive path is under the subject CIK, not the accession-prefix filer CIK.

Therefore neither the accession prefix, the master-index CIK, nor an archive-path CIK may be substituted for the parsed SUBJECT COMPANY CIK.

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

The SEC master index provides filer CIK, filer name, form, filing date and archive filename. The archive path is retained as a separate candidate CIK. The index filename—not a guessed filer-CIK path—is used to locate each accession's index-headers.html file. The existing Phase 485 parser then verifies SUBJECT COMPANY and FILED BY independently and cross-checks FILED BY against both the accession prefix and master-index filer CIK.

## 3. Preregistered bounded sample

- 44 unique accessions selected deterministically from the global index.
- Round-robin stratification by quarter, 13D/13G family, original/amendment, legal deadline regime and XML/schema regime. The sample must contain at least one accession from each of the five preregistered quarters; missing-quarter input or sample coverage fails closed.
- Five quarterly index files only; no 20,266-row legacy-panel crawl.
- Retrieve index-header documents only; no primary filing body, ownership tables, holdings, prices or returns.
- Preserve each index file and header response with SHA-256 hashes and source URLs.
- Require all four exact forms and all five quarterly windows to appear in the 44-row sample, plus 44/44 verified subject/filer identities, 44/44 index-filer/accession matches and 44/44 header-filer/index matches for PASS_HEADER_IDENTITY_ONLY.
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

The 44-row selection now explicitly includes quarter as a stratification dimension. All five preregistered quarters must be represented in both the input index rows and the selected sample; otherwise the sample fails before any header request.

PASS only if: 44/44 header identities verify; master-index filer equals accession-prefix filer; header FILED BY equals master-index filer; zero unresolved header retrievals or identity conflicts.

Archive-path CIK mismatches are separately reported and quarantined for path/subject reconciliation; they are never used to infer subject identity.

Fail/park if: the SEC header cannot be retrieved, subject/filer blocks are missing or ambiguous, index and header filer identities disagree, or the 44-record sample cannot be selected from the fixed windows.

Even after a pass, the next gate is effective-dated subject CIK/CUSIP/security-class mapping against historical F80 membership and coverage/false-zero analysis. No returns are authorized until that gate passes.

**No strategy change:** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No signal, event study, forward-return, OOS, bootstrap, LOO, exposure, cost, universe or production change.
