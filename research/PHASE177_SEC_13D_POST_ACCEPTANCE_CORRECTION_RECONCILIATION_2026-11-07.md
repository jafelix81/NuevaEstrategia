# Phase 177 — SEC 13D acceptance timestamp vs filed-as-of date reconciliation

**Date:** 2026-11-07  
**Status:** COMPLETE — SEC header semantics reconciled; exact PDS correction payload and first public-availability timestamp remain unavailable. No feature or return test.

## Executive decision

Phase 176 correctly identified two records whose SEC-HEADER acceptance calendar date is one day later than the filing-date field. They should **not** be described as unexplained timestamp anomalies. The SEC's own definitions explicitly allow `FILED AS OF DATE` to be a post-acceptance new filing date and define `DATE AS OF CHANGE` as the date of the last post-acceptance correction (PAC).

For both records, the raw header's `DATE AS OF CHANGE` equals the acceptance calendar date and is later than `FILED AS OF DATE`. This is **consistent with a PAC-related filing-date revision**, but the actual `.pc` correction message was not retrieved. Therefore the PAC payload is not independently verified and the records remain quarantined for same-day/intraday PIT use.

The key modeling rule is unambiguous: **never use the filed-as-of date to backdate public knowledge**. Preserve the SEC acceptance timestamp as an acceptance-time floor; the SEC says first availability on sec.gov is often 1–3 minutes later but is not timestamped or guaranteed. Until a first-receipt/delivery timestamp exists, a daily feature must not become eligible before the next full regular session after the acceptance date.

## 1. Source and immutable-input verification

The two raw submissions were read from the immutable Phase 124 artifact (run [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379), artifact 13436764625). The Phase 176 audit had independently reverified all 600/600 source hashes. The two file hashes below were recomputed from the downloaded artifact in this phase:

| Accession | Subject issuer | Subject CIK | Filer CIK | Raw SHA-256 |
|---|---|---:|---:|---|
| 0001213900-19-010653 | Medicine Man Technologies, Inc. | 0001622879 | 0001779135 | `a89650a858558a6d7e564257bcf448b888bb1c54b146ff7d867962705f40841b` |
| 0000898822-19-000061 | Braemar Hotels & Resorts Inc. | 0001574085 | 0001786586 | `56ac3a8e0db0cef9f86de45677e081c176be3206803aecf5b07b87d03fc0f1ce` |

The accession prefix identifies the submitting CIK/account (which may be a filing agent); it is not necessarily the issuer CIK or the beneficial owner's CIK. The issuer and filer identities above are retained as separate fields.

## 2. Exact header reconciliation

| Field | 0001213900-19-010653 | 0000898822-19-000061 |
|---|---|---|
| Phase 124 filing date | 2019-06-13 | 2019-08-29 |
| `<SEC-DOCUMENT>` date | 20190614 | 20190830 |
| `<SEC-HEADER>` date | 20190614 | 20190830 |
| `<ACCEPTANCE-DATETIME>` | 20190614090012 | 20190830093859 |
| `FILED AS OF DATE` | 20190613 | 20190829 |
| `DATE AS OF CHANGE` | 20190614 | 20190830 |
| Acceptance date vs filed-as-of date | +1 calendar day | +1 calendar day |
| Date-as-of-change vs acceptance day | Match | Match |

No timestamp was shifted, imputed, converted to UTC, or replaced with the filing date.

## 3. SEC documentation and what it does—and does not—prove

The SEC Webmaster FAQ defines:
- `FILED AS OF DATE` as the EDGAR-assigned official filing date **or a post-acceptance new filing date (Post Acceptance Correction)**;
- `DATE AS OF CHANGE` as the date when the last post-acceptance occurred;
- acceptance date/time as when EDGAR accepted the submission;
- and explicitly states that there is **no timestamp indicating when filing content first becomes available on sec.gov**. The FAQ says filings are often available within 1–3 minutes after the EDGAR system timestamp, but the lag is not guaranteed.

Official source: [SEC Webmaster FAQ — “How can I understand EDGAR Timestamps?”](https://www.sec.gov/about/webmaster-frequently-asked-questions).

The [EDGAR PDS Technical Specification v2.0 (March 2025)](https://www.sec.gov/info/edgar/specifications/pds_dissemination_spec.pdf) separately describes post-acceptance correction `.pc` disseminations. It says PACs can change header tags, delete a prior submission, or change form/document type; the PAC message does not update document text. Its control-block priority 3 denotes a post-acceptance correction.

**Inference boundary:** the two headers are PAC-compatible because the filed-as-of date differs from the acceptance date and the date-as-of-change equals the acceptance day. The actual `.pc` message and the precise field changed were not recovered, so the audit does not claim to have verified the correction payload. The 2025 PDS format is used to interpret SEC field semantics, not to claim that a historical 2019 PAC message was retrieved.

## 4. Cohort-wide context (the 55-row Phase 176 subset)

A re-extraction of the 55 non-/A, non-numbered legacy 13D Item 4 rows from the Phase 158/159 artifacts and Phase 124 raw submissions gives:

- Acceptance calendar date vs Phase 124 filing date: **42 same, 11 earlier, 2 later** (13/55 differ).
- `DATE AS OF CHANGE` vs acceptance calendar date: **54 match, 1 missing**.
- `DATE AS OF CHANGE` vs `FILED AS OF DATE`: **11 earlier, 41 same, 2 later, 1 missing**.

The high equality of `DATE AS OF CHANGE` with acceptance day means this field alone is not a discriminating PAC detector in this subset. Do not infer PAC status from equality alone. The two later-date cases are specifically classified as PAC-compatible, not confirmed, pending the underlying `.pc` record or equivalent PDS audit evidence.

The 11 acceptance-before-filed-date cases are not reclassified as PACs here. They may reflect EDGAR filing-date assignment/calendar rules, but this phase does not infer a cause for each row.

## 5. PIT policy correction

For all SEC ownership filings, retain separate immutable fields:
1. reported/event date;
2. official `FILED AS OF DATE`;
3. raw `ACCEPTANCE-DATETIME` (SEC wall-clock; preserve without guessed timezone conversion);
4. `DATE AS OF CHANGE`;
5. first observed public availability / vendor receipt timestamp, if independently recorded;
6. correction/deletion lineage and each version's knowledge time.

For these two cases:
- do not backdate the event to 2019-06-13 or 2019-08-29;
- retain acceptance time 2019-06-14 09:00:12 and 2019-08-30 09:38:59 as EDGAR acceptance-time floors;
- do not claim exact first public availability;
- keep same-day/intraday use quarantined;
- for daily research, do not allow use before the next full regular session after the acceptance date, unless a historical dissemination/first-receipt record later proves earlier availability.

This does not clear the broader Phase 176 cohort for predictive use: parent accessions remain unresolved for 55/55, effective-dated issuer/class identity remains incomplete, and the Item 4 categories remain single-reviewer provisional labels.

## 6. Decision and next gates

- **Supersedes Phase 176 wording:** the two later acceptance-date cases are not unexplained anomalies; they are PAC-compatible filed-date discrepancies with correction payload still unverified.
- Keep the two records quarantined for same-day/intraday PIT until correction/delivery history is recovered.
- Keep all 55 rows out of predictive features and returns tests until parent lineage, identity and independent content-label adjudication pass.
- No forward-return test, bootstrap/LOO, chronological OOS, or final-holdout use.
- No vendor contact/purchase and no production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Reproducibility

- Input metadata: `research/phase177_sec_13d_pac_date_reconciliation.json`.
- Pure audit: `research/phase177_sec_13d_pac_date_reconciliation.py`.
- Tests: `research/test_phase177_sec_13d_pac_date_reconciliation.py`.
- Workflow: `.github/workflows/phase177_sec_13d_pac_date_reconciliation.yml`.
- The workflow uses only local metadata and performs no SEC network requests.
