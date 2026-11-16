# Phase 431 — SEC Form 4 AFF10B5ONE schema and semantics audit

**Date:** 2026-11-16 UTC  
**Status:** completed — schema and semantics audit passed; no signal admission  
**Scope:** actual SEC quarterly Form 345 files, no new network request, no return test.

## Executive decision

The SEC Form 4 Rule 10b5-1 checkbox is now available in the SEC quarterly Insider Transactions Data Sets as the submission-level field **AFF10B5ONE**. This is a useful new *classification/exclusion control* for the insider-trading hypothesis, but it is not a standalone Smart Money signal and it does not identify discretionary transactions when unchecked.

The audit confirms four rules:

1. A checked value is evidence that the filing reports a transaction intended to satisfy the amended Rule 10b5-1(c) affirmative-defense conditions.
2. An unchecked, blank, or absent value is **not** proof that a transaction was discretionary or not plan-based. The checkbox does not apply to plans adopted before the amendments' effective date.
3. AFF10B5ONE is stored in SUBMISSION at accession/filing level, not on each transaction row. Do not blindly propagate it to every transaction in a multi-row filing.
4. Transaction code P means **open-market or private purchase**, not necessarily an open-market buy. Footnotes must be inspected before treating P as a discretionary open-market purchase.

The Form 4 source remains **not admitted for alpha testing** because the issuer/security identity bridge remains far below the required full-universe coverage gate.

## 1. Reproducible source artifact

Reused the immutable Phase 39 actual-file feasibility artifact; no new SEC request was made.

- GitHub Actions run: [40606706518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518)
- Artifact: [12781850078](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078)
- Outer ZIP size: 22,886,008 bytes
- Outer ZIP SHA-256: 203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66
- 2012Q1 inner ZIP: 14,219,288 bytes; SHA-256 0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357
- 2026Q3 inner ZIP: 8,660,776 bytes; SHA-256 a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3

The audit reads SUBMISSION.tsv and NONDERIV_TRANS.tsv directly from both nested quarterly ZIPs, hashes the inputs, checks schema metadata/readme, joins transaction rows by ACCESSION_NUMBER, and keeps Form 4/4A transactions separate from Form 5 transactions.

## 2. Historical schema comparison

| Cohort | Form 4 + 4/A filings | AFF10B5ONE in SUBMISSION.tsv | Interpretation |
|---|---:|---|---|
| 2012Q1 | 63,678 | absent | unknown; not an unchecked population |
| 2026Q3 | 34,148 | present | checked/unchecked field available |

For 2026Q3, AFF10B5ONE is present in SUBMISSION.tsv, the quarterly archive's FORM_345_metadata.json and FORM_345_readme.htm. It is absent from NONDERIV_TRANS.tsv. The SEC-hosted PDF readme's current SUBMISSION field table does not list AFF10B5ONE, while the actual 2026Q3 archive metadata and HTML readme do. Prefer the actual vintage's archive metadata and observed TSV header over the stale/incomplete PDF table.

The SEC data page says coverage runs from January 2006 through September 2026, data are published quarterly, and filings received after 5:30 p.m. Eastern on the last business day of a quarter roll into the next quarterly posting. It also notes that 2023–2025 datasets were updated in July 2025 to add AFF10B5ONE to SUBMISSION and future datasets will be processed similarly. The 2026Q3 actual file confirms the field in a current vintage.

## 3. 2026Q3 filing-level counts

The 34,148 Form 4/4A filings contain:

| Normalized flag | Filings | Share |
|---|---:|---:|
| Checked (raw 1 / true) | 5,035 | 14.74% |
| Unchecked (raw 0 / false) | 29,113 | 85.26% |
| Blank / unknown | 0 | 0.00% |

Raw values are mixed (1, true, 0, false); normalization must preserve unknown and unrecognized values rather than coercing them to false.

By document type:
- Form 4: 4,991 checked / 28,530 unchecked (33,521 filings).
- Form 4/A: 44 checked / 583 unchecked (627 filings).

## 4. Filing-level flag is not a transaction-row label

The SEC form presents one Rule 10b5-1 checkbox on the filing, and the bulk dataset stores AFF10B5ONE only in SUBMISSION. It does not add a transaction-level field to NONDERIV_TRANS.

In the 2026Q3 Form 4/4A sample:
- 4,989 checked filings have at least one non-derivative transaction row.
- 1,608 of those filings contain more than one distinct transaction code.
- 1,573 checked filings contain code S plus at least one other transaction code.
- Two checked filings contain code P plus another transaction code.

Therefore the checkbox cannot be blindly copied onto each transaction row as if every row were individually identified. The conservative policy is to treat a checked accession as **plan-associated / contaminated for discretionary-flow classification** and exclude the entire filing from a discretionary feature unless the underlying filing and footnotes permit a defensible row-level adjudication.

## 5. Transaction-code cross-check

Only Form 4/4A accessions are included below; Form 5 rows are excluded from this Form 4-specific comparison.

| Code | Meaning in SEC data dictionary | Rows | Distinct Form 4/4A accessions | Checked accessions |
|---|---|---:|---:|---:|
| P | Open-market **or private** purchase | 5,183 | 3,211 | 82 (2.55%) |
| S | Open-market or private sale | 25,430 | 9,837 | 4,777 (48.55%) |

For P-coded rows, 136 transaction rows belong to checked accessions and 5,047 to unchecked accessions. For S-coded rows, 15,516 rows belong to checked accessions and 9,914 to unchecked accessions.

These are filing-level associations, not transaction-level plan labels. The large difference between P and S flag rates is descriptive only; it is not evidence that unflagged P transactions are discretionary or predictive. Code P expressly includes private purchases. Footnote review is required to distinguish private purchases, plan references, and other special circumstances.

## 6. Regulatory timing and interpretation

Official SEC sources establish:

- The amendments became effective February 27, 2023; Section 16 filers had to comply with the amended Forms 4/5 for filings on or after April 1, 2023.
- The checkbox indicates that a reported transaction was intended to satisfy amended Rule 10b5-1(c) conditions. It is not an SEC validation that the affirmative defense is legally available.
- SEC C&DI 135.04 states that the checkbox does **not** apply to plans adopted before the amendments' effective date. Thus an unchecked value can still include transactions under a grandfathered pre-amendment plan.
- Form 4 is due before the end of the second business day following execution. For point-in-time research, the transaction date is the economic event date; EDGAR acceptance/receipt time is the earliest reproducible public-availability boundary. Do not use the quarterly flat-file posting date or the transaction date as the signal-availability timestamp.

The Phase 39 accession-level acceptance-time join remains the required PIT implementation. The quarterly SEC flat file is a historical extraction aid, not a live event feed or a replacement for the original EDGAR filing. SEC warns that the bulk data may omit filing metadata and may contain extraction errors.

## 7. Revised Form 4 hypothesis and admission gate

A candidate discretionary-purchase feature may eventually use:
- non-derivative transaction code P with acquired indicator A;
- direct/indirect ownership and reporting-owner relationship;
- transaction size relative to issuer liquidity and the insider's prior holdings;
- clustering across distinct insiders;
- filing timeliness and exact EDGAR acceptance time;
- exclusion of checked AFF10B5ONE accessions;
- footnote adjudication to remove private purchases, grants, exercises, tax withholding, gifts, and other mechanical or plan-based transactions.

However:
- AFF10B5ONE checked is an exclusion/context marker, not a bearish/bullish signal.
- AFF10B5ONE unchecked, blank or absent is unknown, not a discretionary label.
- Pre-April 1, 2023 data must not be labelled unplanned because the field is absent and the amended checkbox does not cover pre-effective-date plans.
- The 2026Q3 sample's form-level flag must not be propagated blindly to individual transaction rows.
- Code P cannot be equated with an open-market execution without footnote evidence.

The existing identity bridge is only 53/96 (55.21%) in its audited PIT-eligible legacy-HTML sample, far below the 95% gate. PR #35 (Phase 346 legacy HTML identity bridge) and PR #34 (Phase 345 multi-cohort identity replication) remain open and are not treated as merged mainline evidence. No return study is authorized until security identity and frozen-universe coverage pass.

## 8. Decision

**PASS:** actual-file AFF10B5ONE schema, value normalization, filing-level grain and conservative interpretation.

**NOT PASSED:** universal security identity, complete historical checkbox-vintage audit across 2023Q2 onward, footnote-level transaction attribution, full-universe coverage, and all return/alpha/OOS gates.

Next work:
1. Audit actual 2023Q2 and 2023Q3 archives plus intervening vintages for AFF10B5ONE field continuity and value encoding.
2. Build a conservative filing-level exclusion and footnote review path; consider Item 408 plan adoption/termination disclosures as supplementary context.
3. Continue effective-dated issuer/security identity reconstruction; retain the 95% coverage requirement.
4. Only after these gates, pre-register a post-April-2023 study and compare incremental information with frozen LTM/F80 using identical exposure, costs, chronological OOS, block bootstrap and LOO.

No alpha, forward-return, OOS, bootstrap, LOO or holdout test was run in this phase. No vendor was contacted or purchased. No production workflow, universe, parameter, capital or exposure change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## 9. Sources

- SEC Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- SEC Insider Transactions Data Sets readme PDF: https://www.sec.gov/files/insider_transactions_readme.pdf
- SEC Form 4: https://www.sec.gov/divisions/corpfin/topic-topics/forms/form4.pdf
- SEC Final Rule 33-11138: https://www.sec.gov/files/rules/final/2022/33-11138.pdf
- SEC Exchange Act Section 16 C&DI, Question 135.04: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-section-16-related-rules-forms
- Phase 39 actual-file artifact: https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078
