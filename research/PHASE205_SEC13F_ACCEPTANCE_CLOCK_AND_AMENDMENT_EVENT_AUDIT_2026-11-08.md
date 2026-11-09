# Phase 205 — SEC Form 13F accession clock and amendment event-state audit

**Date:** 8 November 2026  
**Status:** Completed official-source edge-case audit; 10 accessions reconciled. No holdings panel or alpha test admitted.  
**Research role:** PIT and event-state feasibility only. Form 13F is a delayed, incomplete long-position disclosure, not transaction-level flow or proof of informed trading.

## 1. Why this audit was necessary

The SEC's structured Form 13F data sets cover July 2013–August 2026 and are published quarterly as filed. The SEC explicitly warns that the bulk extracts omit certain filing metadata and are not substitutes for the underlying EDGAR filings. The bulk `SUBMISSION` table provides accession and filing date, but not the accepted time-of-day. A point-in-time panel therefore needs an accession-level EDGAR acceptance join. [SEC Form 13F Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) · [Phase 131 schema/PIT audit](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/PHASE131_SEC_13F_AS_FILED_EVENT_STATE_PIT_AUDIT_2026-11-05.md).

## 2. Ten official EDGAR accessions

This is a **purposive edge-case sample**, not a random sample and not an estimate of population prevalence. It deliberately includes four original 13F-HR filings, four full restatements, and two add-new-holdings amendments following confidentiality events.

| Case | Form/event | Report period end | Accepted (ET) | Filing date | Days from report end to acceptance |
|---|---|---|---|---|---:|
| Irenic | 13F-HR original | 2024-12-31 | 2025-02-14 10:19:17 | 2025-02-14 | 45 |
| Opti | 13F-HR original | 2025-12-31 | 2026-02-17 15:01:02 | 2026-02-17 | 48 |
| Arex | 13F-HR original | 2025-03-31 | 2025-05-14 17:54:36 | 2025-05-15 | 44 |
| Silvercrest | 13F-HR original | 2026-03-31 | 2026-05-15 10:30:18 | 2026-05-15 | 45 |
| Modern Wealth | 13F-HR/A restatement | 2025-03-31 | 2025-05-30 17:32:17 | 2025-06-02 | 60 |
| RK Capital | 13F-HR/A; new holdings after confidentiality denial | 2024-03-31 | 2025-08-14 09:02:51 | 2025-08-14 | 501 |
| Farallon | 13F-HR/A; new holdings after confidentiality expiry | 2026-03-31 | 2026-08-14 09:34:05 | 2026-08-14 | 136 |
| Algert | 13F-HR/A restatement | 2024-03-31 | 2026-08-10 18:34:09 | 2026-08-11 | 862 |
| Algert | 13F-HR/A restatement | 2023-06-30 | 2026-08-10 18:19:56 | 2026-08-11 | 1,137 |
| Algert | 13F-HR/A restatement | 2025-12-31 | 2026-08-10 19:01:07 | 2026-08-11 | 222 |

The four original reports in this purposive sample were accepted 44–48 calendar days after quarter-end, consistent with the ordinary 45-day reporting cadence (weekends/holidays affect the observed calendar-day count). The six amendments were accepted 60–1,137 days after the reported quarter-end; their median lag was 361.5 calendar days. These amendment lags are **not** a prevalence estimate.

## 3. Filing date is not the acceptance clock

In 5/10 sample accessions, `FILING_DATE` differs from the calendar date of EDGAR acceptance. All five were accepted after 4:00 p.m. ET:

- Arex: accepted 14 May 2025 at 17:54:36; filing date 15 May.
- Modern Wealth: accepted Friday 30 May 2025 at 17:32:17; filing date Monday 2 June.
- Three Algert restatements: accepted 10 August 2026 between 18:19:56 and 19:01:07; filing date 11 August.

A bulk-data join on `FILING_DATE` alone can therefore shift the event clock by one to three calendar days and cannot recover intraday acceptance. Use the accession's accepted timestamp. Until first public dissemination is independently measured, use the conservative next-regular-session-after-acceptance convention; do not backdate to quarter-end or the filing date.

## 4. Amendment state machine — a material economic distinction

The sample confirms three different disclosure events:

1. **Original 13F-HR:** first public snapshot of the reported long positions, generally around the 45-day deadline.
2. **Restatement:** a corrected full filing. It supersedes the earlier reported state only from the restatement's own acceptance/availability time. The prior state remains the state known to the market before that event.
3. **Adds-new-holdings / confidentiality release:** a supplement that discloses additional positions previously withheld or omitted. It adds information only from its own acceptance/availability time. It is not evidence that the manager bought those shares on the amendment date.

The SEC FAQ says confidentiality-denial/expiry amendments must be filed within six business days and may require multiple add-only amendments when treatment is partially granted/denied. See [SEC Form 13F FAQ, confidentiality treatment and amendments](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f). The RK Capital sample identifies a 14 July 2025 denial and was accepted 14 August 2025; the Farallon sample identifies confidentiality expiry on 14 August 2026 and was accepted that day. The reported holdings belong to earlier quarter-end snapshots, not to the amendment dates.

## 5. Critical correction to the coverage interpretation

Phase 166's 83.18% figure is **not** Form 13F holdings coverage. It is a 13(f)-eligible-list match for 553 unique CUSIPs in a separate SEC 13D/G sample, using a PDF Run Date sensitivity proxy. The earlier Phase 22C Form 13F mapping audit is the relevant coverage evidence: name/former-name mapping ranged from 70.43% (2016Q1) to 93.02% (2024Q1) on the frozen 335-name set, while a direct report-date CUSIP/common-equity route had a 54.8% minimum in 2016Q1. That remains insufficient for a fair broad-universe or identical-exposure comparison. See [Phase 22C mapping decision](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/PHASE22C_13F_MAPPING_V6_DECISION_2026-10-26.md).

## 6. Decision

**Keep 13F parked for stock selection and production.** The data can support a future delayed public-disclosure hypothesis only if deterministic historical security identity and broad-universe coverage materially improve. If that gate passes, use share quantities (not only reported market values), manager-level deduplication, effective-dated corporate-action/security mappings, and an append-only accession event ledger. Restatements replace state only from their own availability time; add-new-holdings amendments supplement only from their own availability time. Test return-chasing explicitly.

No 13F holdings panel, alpha test, bootstrap/LOO or holdout test was run. No data were purchased, no vendor was contacted, no production/universe change was made, and `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 7. Reproducibility and sources

- Structured result: [phase205_sec13f_acceptance_amendment_event_audit.json](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase205_sec13f_acceptance_amendment_event_audit.json)
- SEC 13F bulk data: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
- SEC 13F FAQ: https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f
- [Irenic original](https://www.sec.gov/Archives/edgar/data/1929389/000192938925000002/0001929389-25-000002-index.html) · [Opti original](https://www.sec.gov/Archives/edgar/data/1738654/000091957426001163/0000919574-26-001163-index.html) · [Arex original](https://www.sec.gov/Archives/edgar/data/1800261/000091957425003057/0000919574-25-003057-index.html) · [Silvercrest original](https://www.sec.gov/Archives/edgar/data/1232395/000119312526225668/0001193125-26-225668-index.htm)
- [Modern Wealth restatement](https://www.sec.gov/Archives/edgar/data/2001900/000200190025000019/0002001900-25-000019-index.html) · [RK Capital confidentiality-denial release](https://www.sec.gov/Archives/edgar/data/1905218/000121465925012049/0001214659-25-012049-index.htm) · [Farallon confidentiality-expiry release](https://www.sec.gov/Archives/edgar/data/909661/000090883426000434/0000908834-26-000434-index.htm)
- [Algert 2024Q1 restatement](https://www.sec.gov/Archives/edgar/data/1275218/000127521826000008/0001275218-26-000008-index.htm) · [Algert 2023Q2 restatement](https://www.sec.gov/Archives/edgar/data/1275218/000127521826000005/0001275218-26-000005-index.htm) · [Algert 2025Q4 restatement](https://www.sec.gov/Archives/edgar/data/1275218/000127521826000015/0001275218-26-000015-index.htm)
