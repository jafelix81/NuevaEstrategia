# Phase 35 — SEC 13D/13G PIT crosswalk continuation

Date: 2026-10-25

## State audit
- Latest Phase 35 Actions run: 40240500361, completed successfully.
- Phase 34 options research remains feasibility-only and access-gated; no options alpha test has been run.
- Existing SEC 13D/13G work is the strongest currently executable public-data Smart Money candidate.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Phase 35 artifact result
The completed artifact was inspected directly rather than relying on workflow success alone.
- Frozen universe: 335 names.
- Historical window: 2020-10-01 through 2026-09-30.
- CIKs selected: 307.
- Unresolved tickers: 27.
- Candidate filings: 20,266.
- Resolved filings: 19,353.
- Unique resolved issuers/tickers: 303.
- Initial filings: 5,425 (5,220 SC 13G; 205 SC 13D).
- Amendments: 13,928.
- Event/acquisition date coverage: 0. Event date is therefore not usable for PIT timing.
- Filing date is the PIT knowledge date and the only timing field accepted for any future alpha test.
- SEC document resolution errors: 913, all recorded as retrieval failures dominated by HTTP 429 rate limiting. No submission-list errors.

### Important audit correction
The summary's boolean `field_coverage` entries for `event_date_available` and `is_amendment` are misleading because the coverage calculation treated `False` as available. The raw CSV confirms `event_date_available` is false for all 19,353 resolved rows. Therefore those boolean coverage numbers must not be used as evidence of field completeness.

## Feasibility decision
Phase 35 is **NOT ALPHA EVIDENCE** and is **not yet killed**. The identity/filing panel is potentially large enough to study, but the 27 unresolved names and 913 rate-limit retrieval failures require a corrected retrieval/coverage audit before an economic test. In particular, no universe shrinkage is permitted merely to manufacture coverage.

## PIT rules
- `filing_date` is the earliest public knowledge date.
- Event/acquisition dates are diagnostic only and never substitute for filing availability.
- A signal may enter only on the next trading session after the filing becomes public.
- Historical CIK mapping is identity discovery only; SEC submissions validate selected CIKs.
- Amendments are separate records and must not be double-counted as independent acquisitions without an explicit economic change.

## Next gate
1. Correct the boolean field-coverage calculation.
2. Separate identifier/CIK coverage from successful document retrieval coverage.
3. Explicitly report 429-induced missingness by issuer and period.
4. Rerun with SEC-safe pacing/concurrency and verify reproducibility.
5. Only if the corrected coverage gate passes, pre-register a small set of hypotheses: initial 13D vs 13G, ownership-change magnitude, multi-filer clustering, and repeated ownership increases.
6. Test incremental information versus frozen LTM/F80 on identical dates/exposure using chronological OOS, bootstrap and LOO. No threshold/horizon optimization on OOS data.

## External rule verification
The SEC states that initial Schedule 13D filings are due within five business days of crossing 5%, while amended 13D filings generally follow within two business days; Schedule 13G deadlines depend on filer type and were accelerated under the 2023 amendments. These rules reinforce the use of actual filing availability rather than transaction/event dates.

## Current decision
Phase 35 is **FEASIBILITY-AUDIT CORRECTION REQUIRED — NOT ALPHA EVIDENCE**. The raw artifact is preserved in Actions artifact `12621711791` from run `40240500361`. The frozen baseline remains untouched.
