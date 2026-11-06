# Phase 157 — SEC 13D/G legacy HTML extraction and PIT feasibility

**Date:** 2026-11-06  
**Status:** COMPLETED — artifact-only feasibility audit; no alpha test  
**Sources:** immutable Phase 124 stratified sample and Phase 127 CUSIP audit

## Scope and integrity

Phase 157 extends the role-aware Phase 156 structured-XML audit to legacy HTML filings in the same Phase 124 sample. It reuses, rather than re-downloads, 600 immutable index/sample rows and the Phase 127 CUSIP crosswalk. All 600 raw submissions pass SHA-256 verification; one index alias is quarantined, 102 structured XML filings are excluded from this legacy parser, and 497 legacy HTML filings are processed. The Phase 124 and Phase 127 source CSV hashes and four previously hand-adjudicated body-issuer controls are checked.

The parser selects a readable SC 13D/G primary document and skips same-TYPE encoded PDF exhibits. Cover-page issuer/class candidates are extracted only from parenthetical cover labels (or the explicit inline “Name of issuer:” form); an Item 1 body label is not treated as a cover-page identity. Candidate names remain provenance fields, not adjudicated issuer/security mappings.

## Coverage observed in the 497 legacy filings

| Field | Candidate/valid rows | Coverage |
|---|---:|---:|
| Body issuer-name candidate | 459 | 92.4% |
| Class-title candidate | 439 | 88.3% |
| CUSIP checksum-valid | 473 | 95.2% |
| First reporting-person candidate | 475 | 95.6% |
| Event date parsed from labelled cover field | 423 | 85.1% |
| SEC acceptance timestamp syntactically valid | 497 | 100.0% |

CUSIP results are inherited from Phase 127: 473 checksum-valid, 23 missing and one checksum-invalid. A valid checksum is only a syntax test; it does not prove the security/class or historical ticker mapping.

First-cover-owner numeric candidates are also extracted for sole/shared voting, sole/shared dispositive, aggregate shares and percent of class. These are raw candidates only. They have not been independently reconciled to every table layout or reporting person and are not approved as positions/features. The parser intentionally does not sum owners.

## Event-date versus filing-time evidence

| Family | Filings | Event dates parsed | Quarter-end dates among parsed | Weighted quarter-end rate among parsed | Median event-to-filing lag |
|---|---:|---:|---:|---:|---:|
| 13D | 180 | 161 | 7/161 | 4.35% (weighted 4.08%) | 4 calendar days |
| 13G | 317 | 262 | 156/262 | 59.54% (weighted 76.81%) | 27 calendar days |

No parsed event date is later than the filing date. Two records have event-to-filing lags over 365 days (one 13D, one 13G); these must be quarantined pending manual review, not used as ordinary timely events. Same-day event/filing dates occur in 22 parsed 13D rows and three parsed 13G rows.

All 497 SEC acceptance timestamps are syntactically present. 242 acceptances occur at or after 16:00 ET (121/180 13D; 121/317 13G). A date-only filing field therefore cannot be used as the decision timestamp. The conservative knowledge boundary remains the verified EDGAR acceptance timestamp, with the first tradable session after acceptance for daily-close tests; an after-close filing must not be backdated to that day's regular-session return.

The family split is directionally consistent with Phase 155's structured-XML subset: 13G event dates are heavily concentrated at quarter-end while 13D event dates rarely are. The samples have different composition, date coverage and extraction regimes; this is descriptive consistency, not a pooled population estimate or predictive alpha.

## 13D purpose text and ownership fields

A labelled Item 4 Purpose of Transaction section is detected in 116/180 sampled 13D filings. This creates a feasible text/event research avenue for a later, manually validated taxonomy (activism, strategic alternatives, board/control, merger, financing, ordinary-course/no-change). It is not yet a machine-classified signal. 13G Item 4 is not treated as 13D purpose text.

The first reporting-person candidate is found in 475/497 filings. This does not identify every reporting person or beneficial-owner group. Phase 156 found repeated identical ownership tuples in 48/102 structured XML filings; the same non-additivity warning applies to legacy cover pages. Do not sum reporting-person rows or infer independent institutional buyers from a filing's cover pages.

## Decisions and remaining gates

1. Legacy extraction is feasible enough for a broader audit, but the 459 issuer-name candidates and 439 class candidates are not yet a security master. Only four manually adjudicated identity controls are asserted here.
2. Build a deterministic, effective-dated CUSIP/class/issuer crosswalk with corporate actions, ADRs, series, mergers and delisted securities before joining returns. Current OpenFIGI is not point-in-time.
3. Resolve every amendment to its parent across quarter boundaries, then diff the original and amendment as states. A 13D/A or 13G/A is not a new independent purchase.
4. Validate first-owner and ownership numeric extraction against a stratified hand-labelled sample, including multiple owners, shared powers, zero/none, footnotes and non-standard layouts.
5. Keep 13D and 13G separate. Event date is not public knowledge time or necessarily a trade date. Use acceptance time and quarantine stale/malformed lags.
6. Expand from the 600-filing sample to a complete, role-correct global index population only after the SEC contact/User-Agent prerequisite for automated retrieval is configured and rate-safe. The sample is not a historical eligible-security universe and does not establish issuer recall or active/delisted coverage.
7. Only after these gates, pre-register an economic mechanism (for example, newly disclosed 13D activist intent or ownership change) and test incremental information versus frozen LTM/F80 with chronological OOS, identical exposure/costs, bootstrap and LOO.

**No forward returns, feature panel, alpha test, final holdout, vendor purchase/contact or production change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**

## Reproducibility

- [Phase 124 source run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379) · artifact 13436764625
- [Phase 127 source run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42079517644) · artifact 13438903901
- Helper: research/phase157_13dg_legacy_html_pit_feasibility.py
- Tests: research/test_phase157_13dg_legacy_html_pit_feasibility.py
- Workflow: .github/workflows/phase157_sec_13dg_legacy_html_pit_feasibility.yml
