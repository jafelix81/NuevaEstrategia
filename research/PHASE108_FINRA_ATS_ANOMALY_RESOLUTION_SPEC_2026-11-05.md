# Phase 108 — FINRA ATS anomaly-resolution probe

**Date:** 2026-11-05  
**Parent audit:** Phase 100 / 107, run 41978867803  
**Status:** completed successfully in Actions run 41983989795; targeted anomaly objective passed; no returns or alpha test.

## Purpose

Resolve two integrity ambiguities from Phase 100 without repeating the ten-partition broad audit:

1. Two rows in 2022-01-03 / T2 lacked `issueSymbolIdentifier`, one `OTC_W_SMBL_FIRM` and one `OTC_W_SMBL`.
2. Two coarse-key collision groups for LND in 2025-01-06 / T2 had different quantities and `lastReportedDate` values.

Phase 100's row validator incorrectly grouped missing-symbol checks with week/tier partition checks. Phase 108 reports these dimensions separately.

## Fixed targeted sample

- 2022-01-03 / T2
- 2025-01-06 / T2

The query re-downloads both complete partitions and reconciles every page to FINRA `Record-Total`. It does not rely on the 100-row sample from Phase 100.

## Expanded fields

In addition to the Phase 100 fields, request:

- `MPID`
- `firmCRDNumber`
- `marketParticipantName`
- `issueName`
- `tierDescription`
- `summaryStartDate`

These fields may reveal whether coarse collisions are distinct reporting participants, update records, or source-quality defects.

## Identity diagnostics

Report both:

1. **Coarse key:** symbol, week, tier, summary type, product type.
2. **Expanded candidate key:** coarse key plus MPID, firm CRD number and `lastReportedDate`.

The expanded key is explicitly a diagnostic candidate, not a declared FINRA natural key. No duplicate is dropped, no conflicting quantity is summed, and no row is selected as the “correct” record without evidence about the source's aggregation and revision semantics.

## Separate validations

- Exact requested week/tier agreement.
- Missing symbol rows by summary type.
- Symbol-firm rows without MPID and firm CRD number.
- Coarse-key collisions versus expanded-key collisions.
- LND rows with all requested identity and publication/update fields.
- First-publication versus latest-update dates.
- Exact page/partition reconciliation and page hashes.

## Decision rules

- If LND rows differ by MPID or CRD, treat them as distinct participant-level observations only for the relevant symbol-firm dataset. Do not assume symbol-only aggregates are per-firm without schema evidence.
- If rows differ only by `lastReportedDate`, preserve the separate records and seek FINRA documentation clarifying whether these are reporting vintages or independent contributions. Do not sum or select latest by assumption.
- Missing-symbol rows remain excluded from security-level features unless an independent, effective-dated identifier can recover them.
- If expanded candidate keys still collide with differing quantities, retain a hard integrity failure pending source clarification.
- A clean anomaly probe does not establish historical original-vintage availability, permanent security identity, broad-universe coverage, or alpha.

## Economic interpretation

FINRA symbol/firm rows can identify a reporting ATS or broker-dealer, not the beneficial owner or the ultimate customer. Participant concentration is a market-structure hypothesis, not proof of informed trading.

## Controls

No prices or forward returns are downloaded or joined. No alpha test is authorized. No vendor is contacted or purchased. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-05 result (supersedes the in-progress status above)

The full result is recorded in `research/PHASE108_FINRA_ATS_ANOMALY_RESOLUTION_RESULT_2026-11-05.md`.

- Both targeted partitions completed (2022-01-03/T2: 139,176 rows; 2025-01-06/T2: 136,362 rows), 56 pages total, exact FINRA Record-Total reconciliation, zero week/tier mismatches, zero request errors.
- Coarse-key collisions (9,653 and 8,964 groups) disappear under the expanded diagnostic key (coarse key + MPID + firmCRDNumber + lastReportedDate): zero expanded-key collision groups in either partition.
- LND's apparent symbol-level collisions are distinct reporting-date cohorts; no row was discarded. OTC symbol-level values match the corresponding De Minimis Firm rows; ATS symbol-level rows show a cohort/cumulative relationship that must be reconciled across all ten Phase 100 partitions before feature construction.
- The two 2022 blank-symbol rows are unallocated OTC rows (De Minimis Firms and UTP), not week/tier mismatches. Exclude from security-level features but preserve in completeness accounting.
- 129/35,210 symbol aggregate rows (0.366%) have lastUpdateDate later than initialPublishedDate. Current records do not provide the original post-publication vintages.
- Decision: Phase 108 objective PASS; FINRA ATS remains conditional. No alpha/returns test until expanded-key and aggregation reconciliation across all ten Phase 100 partitions, PIT/revision handling and permanent security identity pass.
