# Phase 604 — SEC registered-fund series/class ticker-to-CIK crosswalk audit

**Status: PASS — bounded live SEC retrieval and exact crosswalk reconciliation completed.**  
**Audit cutoff:** 2026-11-24 22:58 UTC  
**Workflow:** [Run 45505786670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45505786670)  
**Artifact:** [14972004133](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45505786670/artifacts/14972004133)  
**Branch:** `phase604-sec-series-class-ticker-cik-crosswalk-audit`

## Executive result

The SEC registered-fund ticker sources resolve **28 of the 35 symbols** left unmatched by Phase 603. This raises current discovery coverage from **300/335 (89.6%) to 328/335 (97.9%)** without fuzzy matching or inferred CIKs.

- Current company-ticker files: 300/335 tickers, 299 distinct CIKs, zero ticker-to-CIK conflicts.
- Current SEC mutual-fund ticker file: 28/335 target tickers, 11 distinct registrant CIKs, zero conflicts.
- 2026 Series/Class CSV: the same 28 ticker/CIK pairs as the current mutual-fund file, with series and class IDs.
- Combined current discovery union: 328/335 tickers, 310 distinct CIKs, zero conflicts.
- Seven remain unmatched by the sources in this phase: AVB, EA, EQR, LPRO, ROKU, WBD and WBS.

The recovered symbols are predominantly ETF/registered-fund share classes. Their registrant CIKs are not automatically equivalent to an operating-company issuer CIK, beneficial-owner CIK, or a 13D/G filing's SUBJECT COMPANY. Role-aware filing-header validation remains mandatory.

## Source retrieval and coverage

All nine source files returned HTTP 200 and parsed successfully. Source row counts are parser row counts, not counts of F80 matches.

| Source | Snapshot / update date | Parsed rows | F80 ticker matches |
|---|---:|---:|---:|
| company_tickers.json | Current; exact effective date not supplied | 10,400 | 300 |
| company_tickers_exchange.json | Current; exact effective date not supplied | 10,400 | 300 |
| company_tickers_mf.json | Current; exact effective date not supplied | 28,669 | 28 |
| Series/Class CSV 2010 | 2010; exact update day not supplied | 39,867 | 15 |
| Series/Class CSV 2016 | 2016-09-23 | 43,344 | 25 |
| Series/Class CSV 2020 | 2020-07-13 | 43,194 | 26 |
| Series/Class CSV 2024 | 2024-06-05 | 40,694 | 27 |
| Series/Class CSV 2025 | 2025-06-02 | 40,822 | 27 |
| Series/Class CSV 2026 | 2026-06-01 | 43,122 | 28 |

The historical download URLs are not uniform across years. Phase 604 corrected the older SEC directory and filename conventions and replaced delimiter guessing with deterministic comma/tab/pipe header discovery. The parser accepts documented CIK and class-ticker header variants and fails closed when it cannot locate both fields.

Official source documentation: [SEC Investment Company Series and Class Information](https://www.sec.gov/data-research/sec-markets-data/investment-company-series-class-information). The SEC states that the report covers active registered investment-company series/classes assigned IDs, but it is not comprehensive for all closed-end funds or UITs and includes filer-maintained information whose accuracy the SEC does not guarantee.

## Recovered exact crosswalk

The following 28 symbols are present in both the current SEC mutual-fund ticker file and the 2026 Series/Class snapshot. CIK, Series ID and Class ID are retained separately.

| Ticker | Registrant CIK | Series ID | Class ID |
|---|---:|---|---|
| ARKF | 0001579982 | S000064752 | C000209702 |
| ARKG | 0001579982 | S000042975 | C000133119 |
| ARKK | 0001579982 | S000042977 | C000133121 |
| ARKQ | 0001579982 | S000042976 | C000133120 |
| ARKW | 0001579982 | S000042978 | C000133122 |
| BITO | 0001174610 | S000073908 | C000231184 |
| IEFA | 0001100663 | S000038930 | C000119715 |
| IWM | 0001100663 | S000004344 | C000012074 |
| JETS | 0001540305 | S000048544 | C000153068 |
| KRE | 0001064642 | S000012325 | C000033541 |
| OIH | 0001137360 | S000034408 | C000105866 |
| QQQ | 0001067839 | S000101292 | C000271435 |
| SMH | 0001137360 | S000034411 | C000105869 |
| SOXX | 0001100663 | S000004354 | C000012084 |
| VEA | 0000923202 | S000004386 | C000051262 |
| VNQ | 0000734383 | S000002924 | C000032424 |
| VWO | 0000857489 | S000005786 | C000015902 |
| XBI | 0001064642 | S000010018 | C000027706 |
| XLB | 0001064641 | S000006414 | C000017600 |
| XLE | 0001064641 | S000006410 | C000017596 |
| XLF | 0001064641 | S000006411 | C000017597 |
| XLI | 0001064641 | S000006413 | C000017599 |
| XLK | 0001064641 | S000006415 | C000017601 |
| XLP | 0001064641 | S000006409 | C000017595 |
| XLRE | 0001064641 | S000051152 | C000161049 |
| XLU | 0001064641 | S000006416 | C000017602 |
| XLV | 0001064641 | S000006412 | C000017598 |
| XLY | 0001064641 | S000006408 | C000017594 |

## Historical snapshot consistency

Across the available 2010, 2016, 2020, 2024, 2025 and 2026 snapshots:

- 27 tickers have an unchanged single CIK across every snapshot in which they appear.
- QQQ appears in only one available Series/Class snapshot (2026); its 2026 CIK/series/class pair agrees with the current mutual-fund ticker file.
- Zero tickers have changed or conflicting CIKs across the available snapshots.
- Snapshot presence is not continuous coverage: a symbol absent from an older snapshot is not assigned an inferred start date.

The 27 stable results establish repeated identifier consistency, not continuous listing, effective-dated ticker history, or historical F80 membership.

## Operational validation

- GitHub Actions run 45505786670 completed successfully.
- All **11/11 offline regression tests** passed.
- All nine SEC source downloads and parses passed.
- Artifact contains ticker/CIK rows, source hashes/manifest and summary.
- The workflow's SEC_USER_AGENT secret environment variable was empty; the existing Phase 401 contact fallback was used and accepted for all nine HTTP 200 downloads. The secret's repository configuration is therefore still not independently confirmed, but it did not block this audit.
- The branch is 10 commits ahead of main and zero commits behind at the audit cutoff.
- No production collector, universe, strategy, exposure, cost, parameter or capital setting was changed.

## Hard limitations and decision

1. SEC ticker files are discovery aids with no exact effective date supplied; current matches cannot be backdated.
2. Annual Series/Class files are snapshots, not effective-dated security masters. They do not prove when a ticker/class first became active, when a CIK association changed, or when the file was publicly available to a strategy.
3. Series/Class CIK identifies the investment-company registrant. Series and class IDs are separate keys. A ticker-to-registrant match does not by itself identify the subject of a 13D/G filing or the beneficial owner.
4. Seven Phase 603 symbols remain unresolved by this registered-fund crosswalk. Do not force a match.
5. No historical F80 membership, exact public-dissemination time, signal-eligible row, event return, predictive edge, OOS, bootstrap or LOO result is established.

**Disposition:** PASS for current registered-fund ticker/registrant discovery and cross-snapshot consistency; NOT PASS for historical point-in-time security identity or signal admission. Next gate: resolve the seven remaining symbols using issuer filings and effective-dated security evidence, then join Form 13D/G by verified SUBJECT COMPANY role. Keep Form 4 owner identity and transaction attribution as separate gates.

**Research controls unchanged:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Options-data budget remains USD 0; no sample, license, purchase, vendor contact or quote request was initiated.
