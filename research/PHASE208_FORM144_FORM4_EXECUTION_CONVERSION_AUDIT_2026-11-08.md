# Phase 208 — SEC Form 144 to Form 4 execution-conversion audit

**Date:** 2026-11-08  
**Disposition:** strong one-quarter filing-to-reported-disposition linkage; **strict PIT and alpha remain NOT ADMITTED**.  
**Scope:** immutable SEC-derived GitHub Actions artifacts only. No SEC requests, vendor contact, purchase, return test, holdout use, or production change.

## Executive result

A conservative one-to-one join of 2026 Q3 Form 144 original notices to original Form 4 non-derivative sale dispositions found:

- **1,451** Form 144 notices with a complete observable follow-up window, representing **1,460** sale tranches.
- **441** one-to-one notice/tranche-to-Form 4 accession/date matches within 0–2 calendar days of the Form 144 approximate sale date (**30.39%** of eligible notices).
- **394** of those matches have the **same reported transaction date and exactly the same share count as the proposed tranche** (**27.15%** of eligible notices).
- **359/394** exact date-and-share matches also agree under a conservative security-class-family crosswalk (**91.12%**). The other 35 remain class-conflicted or unresolved.
- The 394 exact date-and-share matches show **388/394 (98.48%)** agreement between the Form 144 structured plan-adoption-date presence and the Form 4 accession-level AFF10B5ONE flag.

This is meaningful evidence that a material subset of Form 144 proposed-sale notices can be linked to subsequently reported Form 4 dispositions. It validates a possible execution-conversion research path; it does **not** establish a predictive edge, institutional information advantage, or market-impact effect.

## 1. Immutable inputs and sample boundaries

| Input | Immutable source |
|---|---|
| Form 144 panel | Phase 69 run 41959603351, artifact 13385365595 |
| Form 144 expanded CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 source | Phase 39 run 40606706518, artifact 12781850078 |
| Form 4 2026Q3 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

The Form 144 panel contains 21,634 issuer-event rows over 2023 Q2–2026 Q3. This audit uses 1,487 original Form 144 notices in 2026 Q3; the eight Form 144/A amendments are excluded as independent sale events.

The Form 4 2026 Q3 bulk snapshot contains 38,152 submissions, including 33,521 original Form 4 and 627 Form 4/A submissions. Form 4/A, Form 5-type transaction rows, derivative Table II rows, and multi-owner accessions are excluded from the primary match.

To avoid right-censoring, the latest Form 144 approximate tranche date must be on or before **2026-09-24**. The Form 4 snapshot's maximum filing date is **2026-09-30**. This leaves 1,451 eligible notices and 1,460 tranches; 36 notices are excluded for an incomplete or unparseable follow-up window.

## 2. Conservative matching protocol

The match requires all of the following:

1. Exact normalized issuer CIK.
2. Exact normalized Form 144 seller name = the sole Form 4 reporting-owner name. Normalization is uppercase alphanumeric only; no fuzzy matching, token reordering, suffix deletion, or nickname expansion.
3. Original Form 4 only; Table I non-derivative transaction; TRANS_FORM_TYPE=4; TRANS_CODE=S; TRANS_ACQUIRED_DISP_CD=D.
4. Exactly one reporting owner in the Form 4 accession. Multi-owner accessions are excluded because the bulk tables do not provide a reliable transaction-line-to-owner foreign key.
5. TRANS_TIMELINESS is not L, and the calendar gap from transaction date to filing date is 0–4 days. This is a conservative sample-completeness envelope, not a legal timeliness determination.
6. A Form 4 accession/date block can match only one Form 144 tranche, and a tranche can match only one Form 4 block. Candidate collisions are rejected.

Form 144/A and Form 4/A are not treated as new independent executions. No Form 4 amendment lineage is inferred in this phase.

## 3. Primary match and negative control

| Measure | Post-notice window 0–2 days | Pre-notice placebo -2 to -1 days |
|---|---:|---:|
| Candidate pairs | 695 | 92 |
| Tranches with at least one candidate | 590 | 77 |
| One-to-one matches | **441** | **53** |
| One-to-one rate / eligible notices | **30.39%** | **3.65%** |
| Exact same date and shares | **394** | **0** |

The post-notice one-to-one match rate is 8.32 times the pre-notice placebo rate. This is a descriptive timing diagnostic only, not a significance test. The pre-notice window is not a randomized control and should not be interpreted causally.

Within the 441 post-notice one-to-one matches:

- 423 have the same approximate sale date and Form 4 transaction date.
- 394 have the same date **and** exactly equal proposed and reported shares.
- 418/441 (94.78%) have reported shares within ±20% of the proposed tranche.
- The median proposed-to-reported share ratio is 1.00.
- The median Form 4 filing lag is 2 calendar days; the 90th percentile and maximum are 4 days.

The exact quantity equality is strong cross-source evidence, but the remaining matches still require class-level and source-document adjudication.

## 4. Security-class cross-check

Issuer CIK alone does not uniquely identify a listed share class. A literal normalized class-string comparison is too strict: for example, Form 144 may say “Common” while Form 4 says “Common Stock”.

A deterministic coarse family parser was therefore applied only as a second-stage diagnostic: explicit Class A/B/C/D, Series A–Z, Preferred, Ordinary, Depositary, then generic Common. It does not rewrite the primary match and does not authorize a security-level feature.

- Literal normalized class-string equality: 30/394.
- Coarse class-family agreement: **359/394 (91.12%)**.
- Class conflicts or unresolved labels: **35/394**.

The 35 conflicts remain quarantined. The 359 family-agreeing matches are a higher-confidence linkage subset, not a complete effective-dated share-class crosswalk.

## 5. Independent 10b5-1 semantic cross-check

For the 394 exact date-and-share matches:

| Form 144 structured plan-adoption date | Form 4 AFF10B5ONE true/1 | Form 4 AFF10B5ONE false/0 |
|---|---:|---:|
| Present | 225 | 2 |
| Absent | 4 | 163 |

Thus 388/394 (98.48%) are concordant. AFF10B5ONE is an accession-level Form 4 indicator, not a per-line intent label. The cross-check supports the field semantics; it is not evidence that 10b5-1 status predicts returns or execution probability.

The overall execution-conversion rate is not higher in the plan-date-present group in this one-quarter sample (250/859 versus 191/592 under the primary one-to-one rule). These descriptive group rates are not causal and are not a signal test.

## 6. Interpretation and limitations

- Form 144 is a proposed-sale notice, not proof that the proposed sale completed. Form 4 is a subsequent reported disposition, not an exchange execution tape.
- Form 4 transaction code S covers an open-market **or private** sale under SEC semantics. This audit does not establish venue, aggressor side, beneficial-owner identity beyond the sole reporting-owner name, or market impact.
- The Form 144 approximate sale date is not an acceptance timestamp. The Form 144 panel has filing_date but not ACCEPTANCE-DATETIME or first-public-receipt time.
- The Form 4 quarterly bulk snapshot does not provide first-receipt vintages. FILING_DATE is date-only.
- Exact seller-name matching is conservative but can miss aliases, trusts, entities, name changes, and joint ownership. Multi-owner Form 4 accessions are excluded rather than expanded.
- The current 335-ticker panel is not a survivorship-free historical universe. The sample covers one quarter and cannot establish broad historical conversion rates.
- A match is not a predictive feature. We did not inspect forward returns, prior-return conditioning, liquidity, earnings events, or incremental value versus LTM/F80.

## 7. Decision and next gates

**Keep Form 144 as a conditional event-supply source and advance only to a broader execution-conversion/PIT audit.** The one-quarter match is strong enough to justify replicating the join across multiple quarters, but not to authorize alpha testing.

Before any return test:

1. Obtain a multi-quarter Form 144/Form 4 sample spanning the 2023-04-13 electronic-reporting boundary and later years.
2. Join every accession to EDGAR ACCEPTANCE-DATETIME and preserve original/amended vintages append-only.
3. Build a dated issuer/security-class crosswalk; adjudicate the 35 class conflicts and multi-owner accessions.
4. Reconcile Form 4/A line-level amendments and confirm seller/issuer/class identity from original filings.
5. Measure conversion rates by notice size, relationship, plan status, broker, and prior return only after definitions are frozen.
6. If all PIT and coverage gates pass, preregister a separate event-supply hypothesis and test incremental value versus frozen LTM/F80 with identical exposure/costs, chronological validation, label embargo, date-block bootstrap and leave-one-ticker-out. Use a new prospective final holdout; the legacy holdout remains CONSUMED_NOT_PRISTINE.

No forward-return, alpha, bootstrap/LOO, OOS, or final-holdout test was run. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production, universe, or portfolio changes were made.

## Reproducibility

- Audit code: research/phase208_form144_form4_execution_conversion_audit.py
- Regression tests: research/test_phase208_form144_form4_execution_conversion_audit.py
- Workflow: .github/workflows/phase208_form144_form4_execution_conversion_audit.yml
- Machine result: research/phase208_form144_form4_execution_conversion_audit_result.json
- Workflow downloads only the two immutable GitHub Actions artifacts listed above. It makes no SEC requests and requires no SEC contact secret.
