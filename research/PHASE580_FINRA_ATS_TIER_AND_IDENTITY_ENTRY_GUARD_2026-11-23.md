# Phase 580 — FINRA ATS tier-specific clock and entry-date identity guard

**Date:** 2026-11-23  
**Base:** `main` at `b0bda48f94611014ef151bef65c7b63ee8006ee2`  
**Branch:** `phase580-finra-ats-tier-and-identity-entry-guard`  
**Disposition:** Narrow code-integrity correction to Phase 579. Synthetic tests only. No FINRA API calls, raw data, vendor identity sample, return test, alpha test or signal admission.

## 1. Why this correction was necessary

The Phase 579 gate was derived from the Phase 385 Tier 1 publication-clock census. The Phase 579 implementation enforced a 21/22-calendar-day publication lag but did not inspect `tierIdentifier`. That allowed the T1 clock rule to be applied to a caller-supplied T2 or OTC group if its dates happened to satisfy the same lag. The implementation also checked an identity mapping's `effective_to` against the report-week start, but did not require the mapping to remain effective on the first executable session.

Both gaps were fail-open at the metadata-classification layer. They did not create a demonstrated trade or alpha result, but could incorrectly label an input as PIT-eligible.

## 2. Official source semantics

FINRA's [OTC Transparency (ATS and Non-ATS) Reporting API Specifications, version 0.4](https://www.finra.org/sites/default/files/OTC-Transparency-Data-File-Download-API-v04.pdf) defines:

- `tierIdentifier`: T1 = NMS Tier 1; T2 = NMS Tier 2; OTCE = OTC equity securities (data dictionary, p. 3).
- `initialPublishedDate`: first Monday or next business day after the reporting delay, with a two-week delay for T1 and a four-week delay for T2 and OTC (p. 3).
- `lastReportedDate`: the last time a firm sent an update to underlying data; it is not a public revision-release timestamp (p. 3).

The 21/22-calendar-day rule is therefore explicitly T1-specific. This phase does not attempt to define or admit T2/OTCE publication clocks.

## 3. Corrections

### Tier scope

- Require every row in the symbol-week group to contain one common `tierIdentifier`.
- Admit only `T1` under the existing 21/22-day rule.
- Missing, mixed or non-T1 groups fail closed with explicit rejection reasons.
- Include the resolved tier in the classifier output.

### Identity validity through execution

- Require the effective-dated security-master interval to cover both the report-week start and the first executable session date.
- Continue to require the record-known timestamp to be no later than the executable session open.
- Preserve the written-semantics certification and unique listing/security/issuer tuple requirements.
- If a mapping expires before entry, return `no_effective_known_mapping`; do not accept it merely because it was valid at the report-week start.

## 4. Validation

The offline regression suite now covers **25 synthetic cases**, including:

- T2 rejection under the T1 21/22-day clock.
- Mixed-tier rejection.
- Missing-tier rejection.
- Identity expiry between publication and entry.
- Identity remaining effective through the entry session.
- All 20 Phase 579 stable-row, revision, date, calendar, identity and concentration controls.

The workflow is offline-only. It has no credentials, network access, live FINRA request, raw source artifact or vendor call. No historical data were reprocessed.

## 5. Explicitly not established

- No real FINRA rows were passed through the corrected gate.
- No T2 or OTC publication clock was reconstructed.
- No effective-dated security master or Databento `ts_record` semantics were certified.
- No historical F80 membership or active/inactive universe continuity was reconstructed.
- No total-return, corporate-action or delisting-return panel was joined.
- No returns, alpha, walk-forward/OOS, bootstrap or LOO test was run.

## 6. Decision and controls

This is a PIT-contract correction, not a new Smart Money hypothesis or an economic result. Economic-test eligibility and signal admission remain false. Do not merge or use this gate for investment decisions until the branch workflows pass and the real identity/universe/return prerequisites are independently satisfied.

- New signal admitted: **0**.
- Incremental alpha demonstrated: **none**.
- Production, universe, exposure, cost, holdout and holding-period rules: unchanged.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
