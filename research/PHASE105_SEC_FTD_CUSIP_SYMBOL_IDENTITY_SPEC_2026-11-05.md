# Phase 105 — SEC FTD CUSIP/symbol same-day identity audit

Date: 2026-11-05  
Status before execution: identity diagnostics pending  
Scope: source identity and HTTP metadata only; no returns, alpha test, vendor contact, purchase, or F80 modification.

## Motivation

Phase 102 confirmed that the official SEC FTD archives contain CUSIP and ticker in almost all rows, but its CUSIP/symbol counts were pooled across each sample. Pooled many-to-many mappings may simply represent symbol changes over time or share classes. They do not show whether a mapping is ambiguous on the same settlement date.

## Fixed sample

Reuse the seven actual official SEC archives already selected in Phase 102:
- 2004 Q2
- 2008 Q3
- 2008 Q4
- 2009 Q2
- July 2009 first half
- January 2018 first half
- September 2026 second half

Download each archive again, record GET and HEAD metadata when available, verify actual six-field parsing, and calculate mappings at the settlement-date level.

## Required diagnostics

1. For each settlement_date/CUSIP pair, count distinct symbols.
2. For each settlement_date/symbol pair, count distinct CUSIPs.
3. Separately report cross-sample CUSIP-to-symbol and symbol-to-CUSIP changes; do not conflate these with same-day ambiguity.
4. Report blank/invalid CUSIP and blank symbol rows, duplicate (date, CUSIP, symbol) keys, and representative ambiguous cases.
5. Record HTTP Date, Last-Modified, ETag and Content-Length for GET and HEAD. These are metadata diagnostics, not assumed publication timestamps.
6. Preserve the SEC's stated release convention (first half at month-end, second half about the 15th of the next month) and its explicit warning that it cannot guarantee posting by a particular date.

## Decision rules

- Any same-day many-to-many mappings remain visible and require resolution; never fuzzy-map ticker.
- CUSIP is an effective-dated security key, not a permanent return-source ID. It still requires a defensible CUSIP-to-PERMNO/FIGI/security-master crosswalk with inactive/delisted coverage and record-known time.
- The SEC's release convention alone does not pass exact historical PIT availability. A conservative lag may be used only as a documented assumption, never described as a verified posting timestamp.
- No forward-return or alpha test is authorized by this phase.
