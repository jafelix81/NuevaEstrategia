# Phase 291 — N-PORT direct-short public filing positive control

**Audit date:** 2026-11-11  
**Status:** REAL_PUBLIC_FILING_POSITIVE_CONTROL_PASS_PARSER_CORRECTION_NO_RAW_BYTES_NO_ALPHA

## Executive result

A real public SEC N-PORT filing contains at least three explicit short positions in U.S. common equity. The current Phase 221 classifier rejected all three because it required the descriptive issuer-title field to contain the literal phrase "Common Stock". The official filing reports the issuer name as the title (for example, "Dayforce Inc") while the structured asset category is Equity-common. This was a concrete false-negative in the parser, not a failed short-position hypothesis.

The classifier has been corrected to use the structured combination UNIT=NS, ASSET_CAT=EC and ISSUER_TYPE=CORP for direct physical common equity. ISSUER_TITLE remains descriptive metadata, not a required substring. Non-finite balances now fail closed.

## Public filing inspected

- Form: NPORT-P
- Accession: 0001145549-24-071567
- CIK: 0001872253
- Series: S000074017 — Cromwell Long Short Fund
- Report date: 2024-09-30
- Filed/accepted: 2024-11-22; acceptance 12:10:57 ET
- Report-to-acceptance lag: 53 calendar days
- Conservative first full XNYS session after acceptance: 2024-11-25

## Actual public Part-C short rows

| Ticker | Issuer title | CUSIP | Balance (shares) | Value (USD) | % NAV |
|---|---|---|---:|---:|---:|
| DAY | Dayforce Inc | 15677J108 | -4,447 | -272,378.75 | -0.2848831381 |
| CLX | Clorox Co/The | 189054109 | -1,920 | -312,787.20 | -0.3271466629 |
| CDW | CDW Corp/DE | 12514G108 | -1,115 | -252,324.50 | -0.2639082358 |

All three rows show payoff profile Short, number-of-shares units, Equity-common asset type and Corporate issuer type. None of the three issuer-title strings contains "Common Stock". The SEC's structured schema separately identifies balance, unit, currency value, percentage, payoff profile, asset category and issuer type.

## Parser correction

Old predicate:
- UNIT=NS
- ASSET_CAT=EC
- ISSUER_TYPE=CORP
- and the text "common stock" must occur in ISSUER_TITLE

The final condition is invalid as a universal requirement. Item C.1 title is a description/issuer name and need not repeat the asset classification already supplied by Item C.4. It excluded all three observed public short rows.

New predicate:
- UNIT=NS
- ASSET_CAT=EC
- ISSUER_TYPE=CORP
- PAYOFF_PROFILE=Short
- BALANCE<0

Exact series/security identity, corporate-action resolution, filing completeness and vintage/PIT gates remain separate mandatory upstream conditions. The change does not relax those gates or make missing rows equal zero.

## Validation

- Actual public filing positive controls: 3/3 now classify as OBSERVED_SHORT_POSITION (4,447; 1,920; 1,115 shares).
- Before correction, all 3/3 were rejected by the title substring predicate.
- Existing Phase 221 synthetic semantics: 13/13 rechecked against the corrected logic.
- New negative controls: non-finite balance -> UNKNOWN; non-common-equity asset category -> UNKNOWN.
- No return test, alpha test, bootstrap, LOO or holdout was run.

## PIT and scope limits

The report date is not the knowledge date. This filing was accepted 53 days after its report date, during the 2024-11-22 session. The conservative trading boundary is the next full XNYS session, 2024-11-25. Do not backdate the position to 2024-09-30.

This is one filing from one fund series and one reporting period. It establishes that direct physical common-equity short positions are observable in public N-PORT Part C and validates a row-classification path. It does not establish prevalence, broad-universe coverage, stable series/security lineage, historical availability for a full panel, fund-level predictive skill, or incremental alpha versus F80.

The public SEC filing detail and EDGAR-rendered primary document were inspected, but raw XML/ZIP bytes were not downloaded or hashed. This is a real public filing positive control, not a raw-byte or bulk-history admission.

## Source links

- [SEC filing detail and acceptance timestamp](https://www.sec.gov/Archives/edgar/data/1872253/000114554924071567/0001145549-24-071567-index.html)
- [SEC primary N-PORT document](https://www.sec.gov/Archives/edgar/data/1872253/000114554924071567/xslFormNPORT-P_X01/primary_doc.xml)
- [SEC Form N-PORT instructions](https://www.sec.gov/files/formn-port.pdf)
- [SEC N-PORT data dictionary](https://www.sec.gov/files/nport_readme.pdf)
- [SEC 2026 proposal discussing negative values for reported short holdings](https://www.sec.gov/files/rules/proposed/2026/ic-35962.pdf)

## Controls

F80 remains frozen. No production, universe, capital, parameters or holdout changes. No SEC automated request, vendor contact, data purchase or trial was initiated. SEC_CONTACT_EMAIL remains unconfigured for automated bulk retrieval.
