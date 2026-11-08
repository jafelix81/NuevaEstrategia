# Phase 221 — N-PORT missing-row semantics and conditional direct-short disappearance audit

**Audit date:** 2026-11-08  
**Status:** CONDITIONAL_ZERO_SEMANTICS_DEFINED_NO_RAW_PANEL_NO_ALPHA  
**Scope:** regulatory-form semantics, as-of rules and synthetic falsification only. No raw filing retrieval, prevalence estimate, return calculation or production change.

## Executive finding

Phase 219/220 correctly used a conservative default: an absent holding row is unknown, not zero. The SEC's Form N-PORT instructions reveal a narrow, conditional exception that may recover some position disappearances without treating every missing row as a cover.

- Part C says to disclose each investment held by the Fund and consolidated subsidiaries.
- Part D permits certain miscellaneous securities to be reported separately, up to an aggregate amount not exceeding 5% of total assets. To qualify, a security must be unrestricted, held no more than one year, and not previously reported by name to shareholders or an exchange, included in a registration statement/application/report to shareholders, or otherwise made available to the public.
- Part D information is nonpublic.
- Form N-PORT says the information for the third month of each Fund's fiscal quarter is public upon filing; first- and second-month fund-identifiable information is not public.

**Conditional implication:** if an exact security was previously disclosed by name in a public Part-C N-PORT filing, the Part-D prior-public-disclosure exclusion appears to prevent the same security from being moved into confidential Part D in a later filing. If that same instrument is absent from a complete, public, correctly identified later filing, a zero reported direct physical position can be conditionally inferred.

This is not a universal zero-imputation rule. It is not proof of a cover trade, trade date, beneficial owner intent, or total bearish exposure. A fund may replace physical short exposure with derivatives, another share class, an ADR, or a different instrument. Identity and corporate-action controls remain mandatory. The legal reading of "otherwise made available to the public" should remain explicitly documented and conservative.

## 1. Regulatory facts and scope

The SEC reference Form N-PORT is effective December 11, 2023. General Instruction F makes only the third month of each fiscal quarter publicly available upon filing. Use each Fund's fiscal-quarter calendar; do not assume calendar quarters.

Part C requires information for each investment held. Part D is a nonpublic exception for qualifying miscellaneous securities, subject to the aggregate 5%-of-total-assets cap and eligibility conditions above. The prior-public-disclosure restriction is the key condition for the conditional inference.

The SEC's February 18, 2026 Form N-PORT Reporting release (S7-2026-05 / IC-35962) remains classified as a Proposed Rule on the SEC rulemaking page as of this audit date. It is not treated as a final rule or as a change to the current PIT/publication regime.

An amendment to a previously filed report must provide information in response to all Form N-PORT items. Each amendment is still a separate as-filed vintage: it changes what is knowable only from its own EDGAR acceptance time onward. Never use a later amendment to rewrite an earlier signal date.

## 2. Phase 221 state-classification rule

Keep Phase 220's primary measure, delta_short_shares_pct, and its exposure-state distinction. Refine only the handling of a missing current row:

| Current filing evidence | Classification |
|---|---|
| Exact security has valid explicit Short / NS / common-equity Part-C rows | Observed direct short; aggregate absolute shares across matching rows |
| Exact security has complete Part-C rows, but none is Short | Observed zero direct short in Part C |
| No matching Part-C row; prior same security was publicly disclosed in Part C; current report is public and complete; same series/security; Part-D prior-public exclusion applies; corporate-action and as-of-vintage gates pass | Conditional zero by Part-D exclusion |
| No matching row, but the security was never previously public, Part D may apply, or any gate is unresolved | Unknown — never impute zero |

A row parser returning None means the Part-C parse is incomplete/unknown. An empty list means a completed exact-security search found no Part-C row. Those states must never be conflated.

For repeated short rows representing the same exact issue, aggregate absolute BALANCE only after confirming UNIT=NS, PAYOFF_PROFILE=Short, ASSET_CAT=EC, ISSUER_CAT=CORP, common-stock title, negative balance, and exact effective-dated security identity. Do not aggregate across CUSIPs, share classes, ADRs or derivatives.

## 3. Mandatory gates for a conditional zero

All must pass:

1. The prior report is an as-filed public third-month filing and contains the exact security by name in Part C.
2. The current report is also a public third-month filing for the same Fund series.
3. The current Part-C holdings parse is complete for the entire filing and the exact security has no matching row.
4. The prior public disclosure makes the same security ineligible for Part D under the form's prior-public-disclosure condition.
5. Series identity is exact and stable; registrant CIK alone is not a series identifier.
6. Security identity is exact and effective-dated (CUSIP/ISIN plus issue/title/listing checks); no fuzzy ticker fallback.
7. Splits, ADR-ratio changes, mergers, recapitalizations, class changes and other identity/quantity-changing corporate actions are resolved.
8. The selected filing vintage was accepted by EDGAR before the signal's knowledge cutoff. A later amendment is not backdated.
9. The trading boundary remains the first full regular U.S. equity session whose open is strictly after EDGAR acceptance, pending independent first-public-receipt evidence.

If any gate fails, status is unknown. The inferred zero refers only to the reported direct physical common-equity short in that exact instrument, not synthetic or total economic short exposure.

## 4. Economic feature implications

- A valid transition from a positive reported direct-short quantity to conditional zero can be represented as a reported direct-short disappearance event, not as an observed transaction or exact cover date.
- If the previous snapshot was not itself a known zero under the same rules, the change remains unknown.
- The feature may be -100% for a fully disappearing reported direct position only when both endpoint states are admissible. Otherwise do not calculate a percentage change.
- A current filing that reports the same exact issue only as Long can establish zero direct Short in Part C if the complete parser confirms there are no separate Short rows for that issue. It does not establish zero total bearish exposure.
- The signal is observed at filing availability, not at the unknown intra-quarter trade time. It is a quarterly snapshot transition and must be tested as such.

## 5. Synthetic audit coverage

The evidence manifest contains 13 deterministic cases covering: eligible prior-public disappearance; never-public absence; Part-D eligibility not excluded; nonpublic first/second fiscal-quarter month; incomplete filing; incomplete parser; series mismatch; security mismatch; unresolved corporate action; later amendment not yet knowable; multiple valid short rows; long-only Part-C rows; and malformed short rows.

These are logical counterexamples only. They are not observations from actual filings and do not estimate how often Part D is used.

## 6. Current evidence boundary and next gate

No raw N-PORT bytes were downloaded or hashed in this phase. Phase 217's 23 selected rows remain one purposive filing sample, not a complete panel. Phase 193 remains fail-closed: the Actions log showed SEC_CONTACT_EMAIL empty, zero accessions attempted, zero files downloaded and zero raw hashes verified.

Before any economic test:
- retrieve and hash the five original Phase 193 accessions using an authorized SEC contact;
- parse every public Part-C holding and retain accession/amendment vintages;
- validate series lineage and exact issue identity;
- build a public quarter-end state panel with explicit OBSERVED_SHORT, OBSERVED_ZERO_IN_PART_C, CONDITIONAL_ZERO_BY_PART_D_EXCLUSION and UNKNOWN states;
- estimate coverage and missingness by year, fund series, issuer and historical active/delisted universe;
- only then run the fixed-direction, chronological test versus frozen LTM/F80 with identical exposure/costs, bootstrap and LOO.

No alpha test is authorized. The legacy holdout remains CONSUMED_NOT_PRISTINE.

## Sources

- SEC, [Form N-PORT reference form](https://www.sec.gov/files/formn-port.pdf), General Instructions F and G; Part C; Part D; amendment instruction.
- SEC, [Form N-PORT Reporting, S7-2026-05](https://www.sec.gov/rules-regulations/2026/02/s7-2026-05), still listed as Proposed Rule as of 2026-11-08.
- Federal Register, [91 FR 8582 (Feb. 23, 2026)](https://www.federalregister.gov/documents/2026/02/23/2026-03460/form-n-port-reporting).

**Decision:** refine Phase 219/220 missingness handling only for a narrowly gated prior-public Part-C security. Default absence remains unknown. This is a measurement/data-semantics advance, not evidence of alpha. F80 remains frozen.
