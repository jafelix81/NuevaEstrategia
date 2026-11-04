# Phase 92 — SEC 13D/G legal-deadline and event-semantics audit

**Date:** 2026-11-04  
**Branch:** `phase92-sec-13dg-deadline-event-semantics`  
**Inputs:** immutable Phase 84 raw artifact (run 41914491120) and corrected Phase 91 event artifact (run 41934402354)  
**Mode:** offline only; no SEC requests, no forward returns

## Motivation

Phase 91 showed that calendar days between XML event date and SEC filing date are not an information-latency measure. The legal filing deadline differs by Schedule 13D/13G, initial/amendment, filer category, quarter-end/month-end thresholds, and weekends/holidays. The SEC's 2023 final rule confirms:
- Revised Schedule 13D initial filing: five business days; material amendments: two business days.
- Revised 13G QII/Exempt initial filings: generally 45 days after quarter-end, with accelerated threshold provisions.
- Passive 13G initial filings: five business days after acquisition.
- 13G material-change amendments: generally 45 days after quarter-end, with faster threshold-specific provisions.
- Revised 13G deadlines applied from 2024-09-30; structured XML became mandatory 2024-12-18 (voluntary from 2023-12-18).

Official source: https://www.sec.gov/file/33-11253 (summary and amended Rules 13d-1/13d-2; see especially lines 141-158, 2211-2223 and 4190-4201 in SEC text).

SEC Exchange Act Rule 0-3(a) allows filing on the next business day when a due date falls on Saturday, Sunday or holiday. SEC final rule discussion expressly applies this weekend/holiday treatment to 13D timing. Official source: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules (Question 135.03) and https://www.sec.gov/file/33-11253.

## Candidate due-date model

The script calculates a **base candidate deadline** from event date, filing family, initial/amendment status and structured rule designation. It adjusts calendar-day deadlines to the next US federal business day. It also calculates accelerated-threshold dates as candidates where the current reported percentage and rule category make them possible.

Important: the filing's rule designation and reported percentage do not prove when a threshold was crossed. For 13G amendments, the XML generally does not identify whether the 45-day quarterly rule or a faster threshold trigger was the operative obligation. These results are diagnostics, not legal compliance determinations.

## Event-semantics triage

The script scans XML narrative fields for transparent keyword groups such as:
- employee equity award / compensation;
- merger or business combination;
- capital reorganization;
- activist/governance intent and litigation;
- investment-adviser / parent holding company;
- aggregated client holdings;
- open-market purchase;
- gifts/transfers.

These are triage tags, not an inference of investor intent or 'smart money'. Matched keywords are preserved for manual review.

## Selected case-study hypotheses already identified from the Phase 91 outlier list

1. `0001213900-26-034697` — INLIF Ltd / Chen Yanting. SEC XML describes an employee stock award, later share-capital reorganization and a fall from 11.8% immediately after reorganization to 0.19% at filing. The form is Schedule 13D while narrative references Rule 13d-1(d), a form/rule mismatch candidate. This is not an open-market institutional purchase.
2. `0001493152-25-023677` — CID HoldCo / William Tremaine Reny. SEC XML describes shares received in a business combination and later litigation/governance intentions. A later 13D/A explicitly references this original accession. This is an activist/former-executive event, not a generic institutional accumulation.
3. `0000914208-26-000224` — Microchip Technology / Invesco Ltd. SEC 13G reports 5.2% aggregate holdings but states no single person has greater than 5% economic ownership and that clients hold the relevant securities. This is an aggregated client/parent-manager disclosure, not one proprietary position.
4. The 48-calendar-day lag from 2025-12-31 to 2026-02-17 can be timely: 45 days after quarter-end fell on Saturday 2026-02-14; Monday 2026-02-16 was Presidents Day; Rule 0-3 rolls the due date to Tuesday 2026-02-17.

## Outputs

- `phase92_summary.json`
- `phase92_event_deadline_audit.csv`

No forward returns, feature selection, alpha test, data purchase or production change is authorized.
