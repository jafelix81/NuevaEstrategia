# Phase 484 — SEC 13D/G subject-issuer identity failure and panel quarantine

**Audit cutoff:** 2026-11-18 17:08 UTC  
**Disposition:** **PHASE 28D/35 IDENTITY PANEL NOT VERIFIED. TWO ORIGINAL SEC FILINGS CONFIRM THAT THE STORED “ISSUER” CAN BE THE REPORTING FILER. QUARANTINE THE PANEL BEFORE ANY EVENT OR RETURN TEST.**

## 1. Preflight and repository state

- Main HEAD at preflight: 54dacb3a0d24f2ea3b4e2e8351c2303f25a9f42e (PR #144 / Phase 483 merged).
- Latest relevant Phase 483 runs: [44350669362](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44350669362) and [44350579835](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44350579835), both passed 9/9 offline tests; neither produced artifacts or made SEC requests.
- Latest failed Phase 403 scheduled run [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069) failed two stale Phase 464 assertions in offline regression; live capture was skipped. PR #140 regression run [44304878119](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44304878119) passed 40 tests but also skipped live capture.
- Phase 476 has no schedule-triggered Form 4/4-A poll in the inspected run history. The workflow is present on main; administrative enabled state is not exposed by the read interface. Issue [#142](https://github.com/jafelix81/NuevaEstrategia/issues/142) remains open.
- At cutoff, no workflow was active or queued. The next existing schedule slots were still ahead: Phase 476 at :17 UTC, Phase 403 at :47 UTC, CFTC at 22:25 UTC, and FINRA at 22:30/:23:30 UTC. No dispatch, rerun, cron change or replacement workflow was made.
- PR #144 is merged; its merge commit is the current base. The 311-branch / 56-open-PR repository census and research branches were reviewed; stale Phase 20C and Phase 24B branches remain unsuitable for direct merge.

## 2. The root cause is in the Phase 28D parser fallback

The historical Phase 28D source code on the parser-repair branch performs these steps:

1. Queries SEC submissions for each CIK mapped from the frozen ticker universe.
2. Stores that queried CIK as issuer_cik in the candidate row.
3. Parses the filing document for a CENTRAL INDEX KEY field.
4. If that field is absent, falls back to the queried CIK.
5. Maps ticker from the resulting issuer_cik.

The relevant fallback is effectively:

    issuer = parsed CENTRAL INDEX KEY or queried submissions CIK

For Schedule 13D/G, the queried CIK may be the reporting filer, while the subject issuer is a different company. The accession prefix identifies the filing CIK; it is not proof of the subject issuer. A successful HTTP fetch / zero resolver errors only proves that the document was retrieved, not that its subject issuer was identified correctly.

The artifact has no separate filing_cik, subject_issuer_cik, subject-name/CUSIP crosswalk, or identity-source provenance. The stored issuer_cik and ticker therefore cannot be accepted as a validated subject-security identity.

## 3. Aggregate artifact audit

Re-downloaded the existing Phase 35/28D artifact from [run 41346788365](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41346788365), [artifact 13107210885](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41346788365/artifacts/13107210885). The outer ZIP SHA-256 again matched the recorded value: ed92141e1474036291df07c9676129f46a0d304a7a8c21eca425d051f3184236.

| Audit measure | Result |
|---|---:|
| Rows / unique accessions | 20,266 / 20,266 |
| Accession filing CIK equals stored issuer_cik | 10,085 (49.76%) |
| Accession filing CIK differs from stored issuer_cik | 10,181 (50.24%) |
| Unique accession filing CIKs | 258 |
| Unique stored issuer CIKs | 303 |
| Rows in BLK/STT/MS/JPM/GS/BAC/BEN/TFC/WFC stored-ticker cohort | 12,478 (61.57%) |
| Cohort rows where accession CIK equals stored issuer_cik | 9,864 |
| Share of all CIK-collision rows represented by that cohort | 97.81% |
| Rows with reporting_person populated | 3,502 (17.28%) |
| Rows with reporting_person_type populated | 10,041 (49.55%) |

The CIK equality statistic is a review trigger, not an assertion that every such row is wrong. Conversely, a non-equal accession prefix does not prove that the stored CIK is the correct subject issuer. Because the artifact has no identity provenance, **zero rows can be certified as subject-issuer-verified from this artifact alone**.

## 4. Two original SEC documents confirm the misattribution

### Accession 0000895421-24-000126

The artifact stores ticker MS and issuer_cik 0000895421. The original SEC filing identifies the subject issuer as **FIRST TRUST SENIOR FLOATING RATE INCOME FUND II**, CUSIP 33733U108, while Morgan Stanley and Morgan Stanley Smith Barney LLC are the reporting persons. The SEC archive's subject-issuer path is CIK 0001282850.

- [Original SEC filing](https://www.sec.gov/Archives/edgar/data/1282850/000089542124000126/FirstTrustSeniorFCT.txt)

### Accession 0000895421-24-000178

The artifact again stores ticker MS and issuer_cik 0000895421. The SEC filing detail page explicitly separates **MORGAN STANLEY (Filed by), CIK 0000895421** from **abrdn Global Infrastructure Income Fund (Subject), CIK 0001793855**. The document identifies Morgan Stanley and Morgan Stanley Smith Barney LLC as reporting persons.

- [Original SEC filing](https://www.sec.gov/Archives/edgar/data/1793855/000089542124000178/abrdnGlobalASGI.txt)
- [SEC filing detail / filer-versus-subject CIK](https://www.sec.gov/Archives/edgar/data/1793855/000089542124000178/0000895421-24-000178-index.html)

These are not just ambiguous CIK-prefix collisions: the source documents identify different subject issuers. The stored MS ticker/CIK is the reporting filer context, not the subject security.

## 5. Reclassification of the two future event dates from Phase 483

The two 2024-12-31 event dates are present in the original SEC documents' labeled “Date of Event Which Requires Filing” field and in Item 4 ownership-date text. They are not shown to be unrelated dates accidentally extracted by the parser.

However, both original documents were filed in February 2024 while stating an event/ownership date of December 31, 2024. This is a **source-document date anomaly**, not a confirmed parser error and not a tradable future event. The reason for the date cannot be resolved from the filing alone.

Disposition:
- retain filing_date as the conservative knowledge date;
- preserve the as-filed event_date as source text;
- quarantine the event date from event timing;
- do not silently rewrite 2024-12-31 to 2023-12-31 or infer a corrected date;
- inspect any later amendment/correspondence before assigning semantics.

This supersedes the Phase 483 suggestion that the parser may simply have captured an unrelated nearby date.

## 6. Research disposition and required rebuild

**Quarantine the entire Phase 28D/35 13D/G event panel from event-study, cross-sectional and alpha use.** This is not a claim that every row is misattributed; it is a claim that the current artifact cannot establish the subject issuer for every row and contains confirmed misattributions.

The rebuild must preserve separate fields:
- filing_cik from the accession and SEC filing index;
- subject_issuer_cik from the SEC filing index / issuer identity evidence;
- reporting_person CIK(s) and names, including joint filers;
- subject issuer name;
- CUSIP / security class;
- ticker as an effective-dated security mapping, never as a substitute for CIK;
- filing acceptance and conservative knowledge date;
- event date as a distinct, non-availability field;
- original/amendment lineage and reporting-group identity;
- identity_source and identity_confidence.

If subject CIK cannot be established from an authoritative filing-index or equivalent source, the record remains quarantined. Do not use the reporting-filer CIK as a fallback. Do not infer subject identity from ticker alone. Resolve CUSIP and class effective dates before joining to the frozen 335-name historical universe.

The current SEC_USER_AGENT repository secret remains necessary for future automated SEC archive/API retrieval. No new SEC API request was made in this phase; the two source documents were inspected through their public SEC archive pages.

## 7. Tests, code and frozen controls

Added a deterministic, offline identity auditor and regression suite. It keeps accession filing CIK separate from the stored CIK, flags collisions for review, and deliberately leaves all rows signal-ineligible until subject-issuer provenance is supplied. It does not rewrite the historical artifact or commit raw SEC rows.

No forward returns, backtest, OOS, bootstrap, LOO or holdout test was run. No signal was admitted.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen**: no universe, parameter, capital, exposure, cost, holding-period, holdout or production changes.
