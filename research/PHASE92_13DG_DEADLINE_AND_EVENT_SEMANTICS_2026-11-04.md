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


## Completed Phase 92 result — run 41934907207

<badge>OFFLINE AUDIT COMPLETE</badge>

| Control | Result |
|---|---:|
| Phase 91 structured filings replayed | 200/200 |
| XML parsing errors | 0 |
| Candidate base deadlines met | 188 |
| Candidate base deadlines missed | 12 |
| Candidate misses more than 5 days | 7 |
| Form/rule mismatch candidates | 2 |
| Accelerated threshold candidate dates | 0 |

The 12 candidate deadline misses are **not** legal conclusions. The calculator uses the reported event date, form family, initial/amendment status and rule designation; the precise trigger date and any filing-specific legal exception may not be recoverable from the XML. All accelerated-threshold triggers remain unverified.

### Narrative triage counts

Counts are non-exclusive keyword tags across 200 filings:

| Tag | Count |
|---|---:|
| Activist/governance intent | 33 |
| Business combination/merger | 27 |
| Investment adviser/parent | 23 |
| Issuer employee/officer | 23 |
| Capital reorganization | 21 |
| Employee equity award | 7 |
| No recent transactions declared | 7 |
| Aggregated client holdings | 1 |
| Open-market purchase phrase | 1 |
| Litigation/dispute | 1 |
| Unclassified narrative | 126 |

The single `open_market_purchase` count means only one filing contained one of the explicit phrases in the initial keyword dictionary. It does **not** establish that only one filing involved open-market purchases. The 63% unclassified rate shows the classifier is still a triage tool and needs broader, manually validated coverage.

### Seven base-deadline outliers greater than five days

| Accession | Filing | Event date | Base due date | Days after base due | Preliminary event context |
|---|---|---|---|---:|---|
| 0001493152-25-023677 | 13D, 2025-11-14 | 2025-06-18 | 2025-06-26 | 141 | Business combination; former executive; litigation/governance intent |
| 0000914208-26-000224 | 13G, 2026-07-15 | 2025-12-31 | 2026-02-17 | 148 | Invesco parent/adviser; aggregated client holdings |
| 0001193125-26-041563 | 13D/A, 2026-02-06 | 2026-01-27 | 2026-01-29 | 8 | TSSP Sub-Fund HoldCo; merger/business-combination tag |
| 0001213900-26-034697 | 13D, 2026-03-26 | 2025-06-09 | 2025-06-16 | 283 | Employee award and capital reorganization; form/rule mismatch candidate |
| 0001104659-26-077298 | 13D, 2026-06-24 | 2026-06-10 | 2026-06-17 | 7 | Etika Automotive / Lotus Technology |
| 0001213900-26-051862 | 13G/A, 2026-05-04 | 2025-12-15 | 2026-02-17 | 76 | Brink Holding / Lakeside Holding |
| 0001193125-26-212575 | 13D, 2026-05-07 | 2026-04-24 | 2026-05-01 | 6 | Michael & Susan Dell Foundation private placement |

### Three case studies that materially change signal interpretation

**1. INLIF Ltd / Chen Yanting — not a market purchase.** The SEC XML says the reporting person received an employee stock award, then a share-capital reorganization caused the reported Class A ownership to exceed 5%; the filing later showed 0.19% ownership. The narrative references Rule 13d-1(d) despite the filing being Schedule 13D. This is a compensation/corporate-action event and a form/rule review case, not evidence of institutional accumulation. SEC documents: https://www.sec.gov/Archives/edgar/data/1991592/000121390026034697/primary_doc.xml

**2. CID HoldCo / William Tremaine Reny — activist/former executive and business-combination consideration.** The original 13D says the 17.9% position was received in a business combination; the filing also describes litigation and possible governance actions. The later 13D/A explicitly references the original accession and reports gifts/transfers that reduced the position to 8.9%. This is a potentially informative activist disclosure, but not a generic institutional buying signal. SEC documents: https://www.sec.gov/Archives/edgar/data/2033770/000149315225023677/primary_doc.xml and https://www.sec.gov/Archives/edgar/data/2033770/000149315225029552/primary_doc.xml

**3. Invesco / Microchip Technology — aggregated client holdings.** The 13G reports 5.2% aggregate beneficial ownership, but explicitly says no single person has more than 5% economic ownership and the relevant clients hold the securities. This is not one proprietary Invesco position. SEC filing: https://www.sec.gov/Archives/edgar/data/827054/000091420826000224/xslSCHEDULE_13G_X02/primary_doc.xml

### A 48-day lag can be timely

For a 2025-12-31 quarter-end, 45 calendar days ended on Saturday 2026-02-14. Monday 2026-02-16 was Presidents Day. Rule 0-3 rolls the filing deadline to Tuesday 2026-02-17. Thus a filing accepted on 2026-02-17 can have a 48-calendar-day event-date lag and still be timely. SEC Rule 0-3 guidance: https://www.sec.gov/file/33-11253 and https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules (Question 135.03).

## Research decision

- Do not use event-date-minus-filing-date as a signal or as a proxy for disclosure latency.
- Preserve SEC acceptance UTC as the first observable disclosure timestamp; next-session execution is required.
- Separate 13D activist/control-intent events from employee compensation, merger consideration, corporate reorganizations and passive/aggregated 13G holdings.
- Keep 13G lower priority until person/entity identity and filing category are resolved.
- The 12 candidate deadline misses and two form/rule mismatch candidates require manual review before any compliance label is used.
- No forward returns, no alpha test, no production changes. The F80 baseline remains frozen.
