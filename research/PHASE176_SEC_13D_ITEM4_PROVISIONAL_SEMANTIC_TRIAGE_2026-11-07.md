# Phase 176 — SEC Schedule 13D Item 4 provisional semantic triage and PIT exception audit

**Date:** 2026-11-07  
**Status:** COMPLETED — descriptive first-pass coding only; no feature, return or alpha test

## Scope and immutable inputs

This phase examines only the 55 legacy HTML Schedule 13D rows that satisfy all of the following in the Phase 159 artifact:

- index form is SC 13D (not SC 13D/A);
- cover-page Amendment No. is blank/N/A, missing or unresolved (not a positive number);
- Phase 158 Item 4 extraction is present.

**These are not confirmed initial filings.** Phase 159 explicitly left their parent accessions unresolved. All 55 have `parent_accession_resolved=false` and no `previous_accession` value in this sample. They are therefore an unconfirmed non-/A cohort, not a validated initial-disclosure cohort.

Immutable source artifacts:
- Phase 124 global stratified sample: run [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379), artifact 13436764625. All 600 raw submission SHA-256 values were independently rechecked against the manifest: **600/600 matched**. Phase 124 CSV SHA-256: `be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5`.
- Phase 157 legacy HTML field audit: run [42342166554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42342166554), artifact 13561827396. CSV SHA-256: `154b628436d6c438e54bb953f7d77b0a82f89b5c19373e9f1b642a5140f20072`.
- Phase 158 Item 4 extraction: run [42342166582](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42342166582), artifact 13561732564. CSV SHA-256: `038fbab2c3f4ebafac55078c16c68f89af3037b021c50462b8070cdab8909b60`.
- Phase 159 amendment-role correction: run [42342166506](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42342166506), artifact 13561009769. CSV SHA-256: `bb6411e78fc3eca1ca8c7aae6c76a1b26e6ef03138bb5eb622d8747cf330cfa4`.

The 55 Item 4 sections were re-extracted from the Phase 124 raw submissions using the Phase 158 primary-document/section-boundary rules. The source artifact's 600 raw hashes and the Phase 157/158/159 CSV hashes were verified before analysis. No new SEC requests were made.

## 1. Provisional content triage

A single-reviewer, model-assisted first pass assigned one dominant descriptive category to each of the 55 full Item 4 sections. This is **not** a gold-label set: there was no independent second reviewer, adjudication protocol, inter-rater statistic or classifier validation. The labels are not approved features and must not be used to train a model.

| Provisional category | Rows | Share |
|---|---:|---:|
| Specific transaction / corporate event | 20 | 36.36% |
| Governance / strategic engagement | 12 | 21.82% |
| Routine investment / no specific plan | 12 | 21.82% |
| Mixed / unclear | 9 | 16.36% |
| Administrative / incorporated reference only | 2 | 3.64% |
| **Total** | **55** | **100%** |

Examples show why a single “institutional buying” interpretation is invalid:
- The transaction/event group includes merger and tender-offer disclosures, recapitalization, privatization, purchase/convertible-note documents, lock-ups, founder/compensation awards and other corporate events. Those are not all investor purchases or informed-flow observations.
- The governance/strategy group includes explicit opposition to a transaction, board/management engagement, strategic alternatives, shareholder-value language and a letter to a board. This is not automatically activism, successful influence or predictive information.
- The routine group contains ordinary-course/investment-purpose language and broad reserved rights to buy or sell, often without a specific current plan.
- Mixed/unclear rows combine multiple mechanisms or rely on cross-references; they should not be forced into a single economic category.
- Two sections are only administrative pointers to exhibits/other documents and have no substantive standalone Item 4 text.

The first-pass distribution is useful only as a parser/taxonomy feasibility result. It does not estimate the population prevalence of activism or any other mechanism: the 55 rows are a hash-stratified sample subset selected by parser and cover-field conditions, not a random sample of verified initial 13D events.

## 2. Event-date and identity coverage

Within the 55 rows:
- Subject CIKs: 55 distinct; filer CIKs: 54 distinct.
- Checksum-valid CUSIPs: 47/55; a valid checksum does not establish the correct historical share class or ticker.
- Event date present: 52/55; missing: 3.
- Among the 52 parsed event dates, four equal the filing date, none are later than the filing date, median event-to-filing lag is 10 calendar days, and the maximum is 283 days.
- Event date remains a reported trigger-date field, not a trade date or public-knowledge timestamp. The 283-day lag is a manual-review candidate, not evidence of a stale trade.

## 3. Acceptance-time exception discovered

The raw SEC-HEADER `ACCEPTANCE-DATETIME` clock is at or after 16:00 in **36/55** rows. This reinforces that filing-date-only joins can mis-time disclosures. However, this pilot also found **13/55** rows where the calendar date in the raw acceptance field differs from the Phase 124 filing-date field:
- 11 have an acceptance-header date before the filing date (eight by one calendar day and three by three calendar days); these may reflect after-hours/weekend filing-date rules and must be interpreted from the exact accepted timestamp, not backdated to the filing date.
- Two have an acceptance-header date one calendar day *after* the filing date and are quarantined pending direct SEC filing-index corroboration:
  - `0001213900-19-010653`: filing date 2019-06-13; raw acceptance header 2019-06-14 09:00:12.
  - `0000898822-19-000061`: filing date 2019-08-29; raw acceptance header 2019-08-30 09:38:59.

The raw header strings are preserved as source evidence. The two forward-date discrepancies are not silently corrected, shifted by a guessed timezone, or assigned a synthetic timestamp. Until their SEC filing-index “Accepted” values are reconciled, those rows are **PIT-quarantined**. More generally, the exact public dissemination time is not proven by this pilot; use the verified acceptance timestamp and the next tradable session as the conservative daily decision boundary.

## 4. Decision

1. **Do not call the 55 rows initial filings.** Positive Amendment No. candidates were removed by Phase 159, but blank/missing cover fields do not prove initial status.
2. Keep Item 4 text categories descriptive and unvalidated. Do not use them as “smart money” labels, train a classifier, or run returns tests.
3. Continue parent-lineage work across quarters and resolve issuer + effective-dated security/class identity before any event-state reconstruction.
4. Reconcile the two acceptance-date anomalies against the SEC filing-index accepted timestamps; quarantine them until then.
5. Keep 13D separate from 13G. Do not pool 13G quarter-end reporting dates with 13D purpose text.
6. Only after parent, identity, PIT and historical active-universe gates pass should a preregistered mechanism (for example, *newly disclosed* governance/strategic intent) be tested against frozen LTM/F80 and price-momentum controls with identical exposure/costs, chronological OOS, bootstrap and LOO.

**No forward returns, feature panel, bootstrap/LOO, chronological OOS, final-holdout use or production change occurred.** No vendor was contacted or purchased. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Reproducibility

- Source reports: [Phase 157](PHASE157_SEC_13DG_LEGACY_HTML_PIT_FEASIBILITY_AUDIT_2026-11-06.md), [Phase 158](PHASE158_SEC_13D_ITEM4_SEGMENTATION_AND_AMENDMENT_AUDIT_2026-11-06.md), [Phase 159](PHASE159_SEC_13D_COVER_PAGE_AMENDMENT_NUMBER_AND_ITEM4_COHORT_AUDIT_2026-11-06.md).
- This is a deterministic source re-extraction plus a provisional qualitative review. The extraction is reproducible from the pinned Phase 124/157/158/159 artifacts; the semantic labels require independent human adjudication before any predictive use.
