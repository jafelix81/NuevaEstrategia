# Phase 222 — Form 144 daily PIT clock from SEC filed date and next XNYS session

**Audit date:** 2026-11-08  
**Disposition:** DAILY EVENT-TIMING GATE PASSED CONDITIONALLY; FULL PANEL / SECURITY / UNIVERSE ADMISSION STILL CLOSED. No alpha test.

## Executive result

The Phase 207/211 requirement to recover ACCEPTANCE-DATETIME for every Form 144 row is unnecessarily strict for a **daily** event strategy. The SEC's current electronic Form 144 guide states that EDGAR accepts submissions from 6:00 a.m. to 10:00 p.m. ET on business days, deems submissions in that window filed the same business day, and disseminates accepted Form 144 submissions publicly the same day. Electronic filing became mandatory for Form 144 notices involving securities of Exchange Act reporting companies on April 13, 2023.

The immutable Phase 69 panel begins on that exact date and carries the SEC master-index filing date for every event. Therefore a conservative daily rule is reproducible without each row's acceptance second:

**A Form 144 notice filed on date D becomes eligible only at the first XNYS regular-session open strictly after D. No same-day use.**

This is a daily clock only. It does not authorize intraday use or prove the exact dissemination second. Five Phase 211 filing-detail/header examples independently match the panel filing date and the next-session mapping (5/5).

## 1. Immutable panel audit

Source: Phase 69 run 41959603351, artifact 13385365595. The artifact ZIP SHA-256 is f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519. The 67,014,714-byte expanded issuer-event CSV SHA-256 is 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659.

| Check | Result |
|---|---:|
| Issuer-event panel rows | 21,634 |
| Unique accessions | 21,634 |
| Clean issuer-match rows | 21,633 |
| Ambiguous issuer-match rows quarantined | 1 |
| Filer-only false positives excluded before panel | 14 |
| Original 144 notices | 21,438 |
| 144/A amendments | 196 |
| 144/A with previous accession | 196/196 |
| 144/A parent inside 14-quarter census | 195/196 |
| Unique issuer CIKs / current tickers with events | 289 / 289 |
| Filing-date missing | 0 |
| Filing-date range | 2023-04-13 to 2026-09-30 |
| Unique filing dates | 861 |
| Weekend / non-XNYS filing-date rows | 0 / 0 |

The 289/335 current-ticker event incidence (86.27%) is not historical active-universe coverage and does not establish a survivorship-free universe. The one ambiguous issuer pair remains quarantined from issuer-level feature use.

## 2. Official SEC timing rule

The SEC's current “File Form 144 Electronically” guide (last reviewed December 22, 2025) states:

- EDGAR accepts electronic Form 144 from 6:00 a.m. to 10:00 p.m. ET, Monday–Friday, except federal holidays.
- A Form 144 submitted within that window is deemed filed the same business day.
- Form 144 submissions are disseminated publicly on SEC.gov the same day.
- Electronic filing for Form 144 involving securities of an Exchange Act reporting company became mandatory on April 13, 2023.

Thus the SEC master-index filing date is a sufficient conservative **date-level** public-availability anchor for this daily strategy, provided same-day use is prohibited. The SEC's 2023 final rule confirms the 10:00 p.m. deemed-filing deadline and same-day EDGAR dissemination for Forms 144/144-A.

## 3. Reproducible daily boundary

The 861 unique filing dates were mapped using XNYS sessions from exchange_calendars 4.13.1:

- 861/861 filing dates have a subsequent XNYS session.
- 861/861 next-session mappings are unique.
- Eight next sessions are scheduled early-close sessions; they remain valid regular trading sessions, and their shortened hours are preserved in the calendar output.
- The first mapping is 2023-04-13 → 2023-04-14.
- The last mapping is 2026-09-30 → 2026-10-01.

The 2023Q2–2026Q3 panel contains 168 rows where the Form 144 notice date differs from the SEC filing date (differences range from -4 to +3 calendar days). Do not use the notice date, approximate sale date, 10b5-1 adoption date or Form 4 transaction date as the public-knowledge clock.

## 4. Independent acceptance-clock cross-check

The five manually verified Phase 211 EDGAR examples all have:
- SEC-header ACCEPTANCE-DATETIME calendar date equal to the panel's SEC filing date: 5/5;
- first XNYS session after the filing date equal to the recorded first-session open date: 5/5.

The five examples are targeted, not a representative timing sample. The general same-day rule comes from the SEC's filing guide, not extrapolation from these five cases.

## 5. Amendments and event semantics

A Form 144/A is a new public information vintage for the same notice, not a new independent sale by default. Its own filing date starts the amendment's knowledge clock; never backdate an amendment to the original notice or the proposed sale date. Form 144 remains a proposed-sale notice and does not prove completion. The broker/market-maker field still does not identify the legal route; Phase 212's mixed-route/unknown conclusion remains unchanged. Form 4 remains ex-post only.

## 6. Admission decision

**Passed:** a reproducible conservative daily public-availability clock for the existing electronic Form 144 panel, without bulk ACCEPTANCE-DATETIME recovery.

**Still not admitted as a complete signal panel:** 
- effective-dated issuer/security-class/listing identity and corporate-action continuity;
- historical active/delisted universe membership (the 335-name list is current and historically arbitrary);
- the one ambiguous issuer row;
- seller identity and reporting-person continuity;
- independent PIT shares-outstanding/float/ADV denominator (the Form 144 units-outstanding field is unreliable);
- threshold censoring and proposed-versus-completed-sale semantics;
- broad, adjacent-quarter Form 4 linkage and amendment-vintage completeness.

For a daily EOD strategy, use the next XNYS session as the first eligible signal/decision session and execute no earlier than its close under the project's end-of-day discipline. Intraday strategies remain unadmitted until exact acceptance and dissemination timestamps are available. No return/alpha test, bootstrap/LOO, OOS or holdout test is authorized in this phase.

## Sources

- SEC, [File Form 144 Electronically](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically), last reviewed Dec. 22, 2025; same-business-day filing and same-day dissemination FAQs.
- SEC, [Final Rule: Extending Form 144 EDGAR Filing Hours, Release 33-11159](https://www.sec.gov/files/rules/final/2023/33-11159.pdf).
- SEC, [Phase 69 immutable panel run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41959603351), artifact 13385365595.
- SEC acceptance-clock pilot, [Phase 211 source manifest](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase211_form144_form4_acceptance_clock_pilot.json).

**Decision:** supersede Phase 207/211 only on the need for per-row acceptance timestamps for a daily event clock. Use SEC filing date plus next XNYS session. Keep full security/universe admission and alpha gates closed. F80 remains frozen.
