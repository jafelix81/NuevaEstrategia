# Phase 123 — SEC 13D/13G regulatory point-in-time regime audit

Date: 2026-11-05  
Status: COMPLETED — methodology gate, not an alpha test  
Scope: translate the SEC's beneficial-ownership reporting amendments into explicit historical knowledge-time and schema regimes for any future 13D/13G event panel.

## Why this matters

A filing's reported event date is not the date the market learned the information. Filing deadlines changed at different dates for Schedule 13D and Schedule 13G, and mandatory XML arrived later still. A single lag rule across 2016–2026 would create avoidable timing error and potentially backdate information.

The controlling source is the SEC's final rule, Release Nos. 33-11253 / 34-98704, published in the Federal Register on 2023-11-07. The amendments became effective on 2024-02-05, but the SEC expressly delayed compliance with the revised Schedule 13G deadlines until 2024-09-30 and with mandatory 13D/G XML until 2024-12-18. Voluntary XML compliance was allowed from 2023-12-18.

Official SEC source: https://www.sec.gov/files/rules/final/2023/33-11253.pdf

## Three separate regime clocks

| Regime | Start | Research implication |
|---|---|---|
| General / Schedule 13D deadline amendments | 2024-02-05 | 13D initial and amendment disclosure lags change |
| Revised Schedule 13G deadlines | 2024-09-30 | 13G deadline regime changes later than 13D |
| Mandatory structured XML | 2024-12-18 | Before this date, legacy HTML/ASCII remains necessary; voluntary XML can appear earlier |

Do not collapse these into one 2024 break. In particular, a 13G filing dated between 2024-02-05 and 2024-09-29 remains under the old 13G deadlines even though other amendments were already effective.

## Deadline regimes that the event panel must encode

### Schedule 13D

- Initial filing after crossing beneficial ownership above 5%: old rule was 10 calendar days; new rule is five business days.
- Amendment after a material change: old rule was “promptly”; new rule is two business days.
- The 10 p.m. Eastern EDGAR cutoff can assign the same business-day filing date to a transmission made by that time. Acceptance timestamp, filing date and first tradable session must therefore remain separate fields.

### Schedule 13G

The revised deadline regime applies only beginning 2024-09-30.

- Qualified institutional investors (QIIs) and exempt investors: initial filing moves from 45 days after calendar year-end to 45 days after the quarter-end in which ownership first exceeds 5%. QIIs retain an accelerated filing when ownership exceeds 10% at month-end, now five business days after month-end rather than 10 calendar days.
- Passive investors: initial filing after crossing above 5% moves from 10 calendar days to five business days.
- General amendments: the trigger changes from any change to a material change; the deadline moves from 45 days after calendar year-end to 45 days after the calendar quarter in which the material change occurs.
- QII amendments at the >10% / 5%-change thresholds move to five business days after month-end.
- Passive-investor amendments at the >10% / 5%-change thresholds move to two business days after the threshold event.

The filer category matters. Do not treat all 13G filings as the same institutional signal. Rule 13d-1(b) QII, Rule 13d-1(c) passive and Rule 13d-1(d) exempt filings have different disclosure mechanics and economic interpretations.

## Knowledge-time rule

1. Preserve the reported event date as an event attribute only. Never use it as the public signal date.
2. Preserve SEC-HEADER acceptance datetime in Eastern Time and its UTC conversion, plus filing date and source retrieval time.
3. For conservative daily research, the earliest tradable session is the first regular U.S. equity session whose open occurs after the verified acceptance timestamp. If actual public dissemination is not independently verified, use this conservative rule and record the assumption.
4. Never backdate a current amendment's reported ownership snapshot to the event date or predecessor filing date.
5. Treat the 2024-12-18 XML compliance date as a parser-coverage break, not an economic signal. Pre-compliance HTML/ASCII needs a separately validated parser; voluntary early XML does not imply complete XML coverage.
6. Separate initial filings from amendments, and separate 13D from 13G. Validate any previousAccessionNumber link against issuer, filer, form family, chronology and security identity; the pointer alone is not a same-security key.

## Hypotheses and interpretation

- Schedule 13D can reflect an activist/control-oriented position and campaign disclosure; it is not equivalent to a passive institutional accumulation signal.
- Schedule 13G is heterogeneous: QII, passive and exempt filers must remain separate. A 13G amendment's reported ownership change is a snapshot, not observed transaction flow.
- The SEC's own economic analysis discusses the possibility that other traders may buy ahead of a 13D filing based on foreknowledge. That is a market-mechanism discussion, not evidence that the public filing itself predicts future returns. Any future study must distinguish pre-filing run-up/return-chasing from post-publication incremental information.
- Schedule 13D Item 6 derivative disclosures may contain relevant derivative exposures, including cash-settled instruments; do not convert notional amounts into common-share ownership without contract terms and a separately validated method.

## Decision and next gates

The Phase 120–122 pilot now has reproducible predecessor retrieval and a narrow exact-CUSIP XML ownership comparison, but it is not ready for economic testing. Before any 13D/G feature test:
- reconstruct global subject-issuer discovery across the 2016Q1–2026Q3 index history rather than relying on the current 319-CIK candidate map;
- build an effective-dated issuer/CUSIP/security crosswalk including inactive and delisted securities and corporate actions;
- validate the legacy HTML/ASCII parser and its reporting-person/ownership fields;
- classify 13G filer rule/category and all applicable deadline regimes without guessing;
- use the acceptance-based next-session knowledge rule and test incremental information versus frozen LTM/F80 under chronological OOS, costs, bootstrap and LOO.

No forward returns, predictive features, alpha tests, vendor purchases, or production changes were performed in Phase 123. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Reproduction references

- [SEC final rule PDF](https://www.sec.gov/files/rules/final/2023/33-11253.pdf)
- [Federal Register publication](https://www.govinfo.gov/content/pkg/FR-2023-11-07/html/2023-22678.htm)
- [Phase 122 ownership continuity report](PHASE122_SEC_13DG_XML_OWNERSHIP_CONTINUITY_AUDIT_2026-11-05.md)
