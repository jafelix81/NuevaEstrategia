# Phase 397 — SEC Form 144 PIT clock and event-payload integrity audit

**Audit date:** 2026-11-14 UTC  
**Disposition:** Form 144 is a credible *proposed insider-supply/order* source with a defensible next-session public-date clock, but it is not yet a security-level PIT panel. No return test or signal admission is authorized.

## 1. Inputs and reproducibility

This is an offline audit of the completed Phase 67 artifact; no SEC crawl or vendor request was made.

- Phase 67 Actions run: [41828179718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41828179718), job 126605281463.
- Artifact: 13334881835 (phase67-form144-full-candidate-role-resolution.zip), 14,656,596 bytes.
- ZIP SHA-256: 939d5564b14ce0f41df23a2c9ab681977cfde141cd0ea2b3c1213b1c5bfaf613.
- Audited member: issuer_event_raw.csv, 21,634 rows, SHA-256 fd20e338bd3624e7c1e85c39ab911f9fd5d1d78e8a20ed185e42db299a868b20.
- Phase 67 resolved 21,648 current-CIK candidate accessions into 21,634 issuer-event rows, excluded 14 filer-only false positives, had zero unresolved rows and zero XML fetch/processing errors, and reconciled 280/280 controls. The census covers 14 quarters, 2023Q2–2026Q3.
- Phase 68 later repaired the current ticker map to 335/335; Phase 69 found zero incremental accessions for the ten newly added fund-registrant CIKs in the same 14-quarter window. This does not create historical ticker/class membership.

The audit script is research/phase397_form144_pit_data_integrity_audit.py; its aggregate output is research/PHASE397_FORM144_PIT_DATA_INTEGRITY_SUMMARY_2026-11-14.json. It reads the downloaded artifact member and does not fetch data, calculate returns or generate signals.

## 2. What Form 144 actually measures

Form 144 is a **notice of proposed sale**, not proof that the disclosed quantity was executed. SEC Rule 144 guidance describes the notice as being filed concurrently with placement of the sell order with a broker or direct execution with a market maker. The SEC's current filing guidance says the Filer CIK belongs to the reporting person for whose account the securities are to be sold, not a filing agent. This gives us a useful seller-side identity, but it does not establish that the seller is informed or that the proposed sale completed.

Coverage is selective: the notice requirement applies to covered Rule 144 sales above the three-month threshold (more than 5,000 shares or aggregate proceeds above $50,000); non-affiliates generally no longer need to file Form 144. Therefore this is not a census of all insider sales.

Official sources:
- SEC Form 144 electronic filing guide: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically
- SEC filing-status guide: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/determine-status-my-filing
- SEC Rule 144 investor guidance: https://www.sec.gov/reports-and-publications/investor-publications/investorpubsrule144htm
- SEC Rule 144 interpretations: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/securities-act-rules

## 3. PIT clock decision

The SEC says EDGAR operates 6:00 a.m.–10:00 p.m. ET. Form 144 and 144/A submissions made after 5:30 p.m. and before 10:00 p.m. receive the same day's filing date and are disseminated that day. The SEC also says filings are often visible within 1–3 minutes of the EDGAR acceptance timestamp, but explicitly does not guarantee that delay.

**Baseline public-date rule:** use the SEC filing_date and make the event eligible only from the first regular NYSE session strictly after that date. Retain the Phase 65 no-same-day policy. This is a conservative daily-data clock even for Form 144 filings accepted after 5:30 p.m. because the SEC's Form 144-specific rule still gives them same-day filing/dissemination. Do not use notice_date, approximate sale date, or an inferred 30-minute buffer as the knowledge timestamp.

The Phase 67 event CSV contains no ACCEPTANCE-DATETIME/accepted-timestamp column. Therefore:
- next-session-only daily research has a defensible public-date rule;
- intraday/same-day-close research is **not** certified;
- if an intraday study is ever proposed, it needs accepted-time plus actual public-receipt evidence or a conservative next-session fallback. The SEC's typical 1–3 minute availability statement is not a guarantee.

## 4. Artifact-level findings

| Check | Result | Interpretation |
|---|---:|---|
| Original Form 144 | 21,438 | Proposed-sale notices |
| Form 144/A | 196 | Amendments/updates; not new events by default |
| Duplicate accessions | 0 | Accession-level uniqueness passes |
| Notice date differs from SEC filing date | 168 / 21,634 (0.78%) | Do not use notice date as the PIT clock |
| Notice date earlier than filing date | 141 | Up to four calendar days earlier |
| Notice date later than filing date | 27 | Up to three calendar days later |
| Multi-tranche events | 188 | Keep tranche-level payload before aggregation |
| Multi-candidate ticker rows | 291 | Issuer/security resolution still required |
| Zero/invalid proposed units | 2 | Exclude from unit-based pressure denominators |
| Zero/invalid proposed value | 3 | Exclude from value-based pressure denominators |
| Zero/invalid shares outstanding | 7 | Exclude from float/outstanding ratios |
| 144/A parent reference found in the 14-quarter census | 195 / 196 | One parent reference is outside/missing; reference is not necessarily immediate predecessor |

The *_all_numeric flags in the source CSV indicate parseability, not economic validity: the audit found numeric zero values/denominators that must not be treated as usable observations or silently imputed.

### Security-class/ticker ambiguity

Of 291 rows whose master-index CIK pair maps to multiple current ticker candidates:
- 290 are the Z;ZG pair for the same issuer. Within those 290 events, 275 contain only Common Class C, eight contain both Common Class A and Common Class C, and seven say only generic Common.
- One row is AMT;ASTS: XML identifies AST SpaceMobile as the subject issuer and American Tower as filer/seller. It must not be assigned to AMT merely because AMT appears in the CIK pair.

Thus XML issuer/filer roles solve issuer attribution, but ticker-level attribution still requires tranche-level security-class mapping and a historical security master. Do not explode a registrant-level event across every candidate ticker.

The 1,424 rows mentioning 10b5-1 are descriptive only. They do not establish whether a plan was active, whether the disclosed sale executed, or whether the event is predictive.

## 5. Gate status

| Gate | Status |
|---|---|
| Candidate accession completeness / XML issuer-filer resolution | **Passed for the Phase 67 current-CIK candidate set** |
| SEC public-date availability for next-session-only use | **Passed by SEC Form 144-specific filing/dissemination rule** |
| Accepted-time / first-public-receipt intraday clock | **Not tested / absent from artifact** |
| Notice-date as knowledge time | **Rejected** |
| Ticker/security-class resolution | **Not passed** |
| Historical F80 membership, predecessor/delisted issuer coverage | **Not passed** |
| Amendment/seller/security-class lineage | **Partial** |
| Numeric semantic validity | **Partial; 2 unit, 3 value and 7 outstanding exceptions** |
| Economic/OOS test | **Not authorized** |

## 6. Decision and next gates

Keep Form 144 as a **proposed insider-supply hypothesis**, not a Smart Money label and not a confirmed-sale feed. Do not repeat the same Phase 69 CIK extension; it produced no incremental accessions.

Before any event-return test:
1. Build a tranche-level panel keyed by XML subject issuer CIK and security class; resolve Z/ZG, the AMT/ASTS filer/issuer example, fund series/classes and all multi-tranche rows.
2. Reconstruct historical issuer/security identity, F80 membership (or define a separately frozen broad universe), predecessors, delistings and corporate actions. The current 335-name map is not historical membership.
3. Link 144/A by seller + subject issuer + security class + referenced accession; do not count amendments as new independent sale orders.
4. Preserve the next-regular-session-after-filing-date availability rule. No same-day or intraday use until first-public-receipt evidence exists.
5. Apply explicit validity masks for zero units/value/outstanding. Do not impute from future prices or future shares outstanding.
6. Only after these gates pass, retain the preregistered chronological development/validation/OOS structure and test proposed supply pressure incrementally against frozen LTM/F80 with identical exposure, costs, purging/embargo, block bootstrap and issuer LOO. Do not consume the legacy holdout.

No forward returns, alpha, OOS, bootstrap, LOO or holdout test was run. No data was purchased, no SEC crawl was launched, and F80_TOP20_PARTIAL50_BASELINE_C20, universe, capital, exposure, parameters and production were not changed.
