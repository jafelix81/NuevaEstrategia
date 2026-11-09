# Phase 230 — Cboe Option Quotes locale reclassification and parser-gate correction

**Date:** 2026-11-09  
**Disposition:** Phase 174's ISO-only expiration parser caused a large false rejection of sample rows. Phase 175 resolves most date values uniquely without guessing locale, but 3,304 row instances remain ambiguous. Full sample/schema admission, PIT, and alpha remain **NOT ADMITTED**.

## Executive finding

Phase 174 downloaded the same Cboe Option Quotes public sample later examined by Phase 175. Its parser accepted only ISO-extended expiration dates. As a result, it marked 94,607 of 115,617 populated row instances as invalid contract rows, all under the single error code `invalid_expiration_format`.

Phase 175 tested multiple date formats without choosing between competing interpretations. It shows that:
- 91,303 of those 94,607 previously rejected row instances have exactly one expiration-date interpretation.
- 3,304 row instances have multiple distinct interpretations and must remain quarantined.
- All 115,617 quote-datetime values have one unique candidate interpretation.
- The sample contains 5 data members and 4 schema-width variants, but only two quote dates.

This is a parser-gate correction, not evidence that 112,313 unique option contracts exist or that the product is historically point-in-time usable. Phase 175 deliberately did not persist raw symbols, rows, expirations, or contract keys. Phase 230 therefore reclassifies only the metadata and does not claim that the full Phase 174 row gate has been rerun.

## 1. Source provenance

| Audit | Run / artifact | Result |
|---|---|---|
| Phase 174 Option Quotes public sample | [42562292847](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42562292847) / [13650205761](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42562292847/artifacts/13650205761) | 115,617 populated rows; 94,607 ISO-only expiration failures |
| Phase 175 date-locale diagnostic | [42562292743](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42562292743) / [13649604168](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42562292743/artifacts/13649604168) | Download and date-locale diagnostic complete; sample not admitted |

Both runs observed the same source archive SHA-256:

`7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782`

The Phase 175 artifact ZIP SHA-256 is `7a3f988b6edb6e41e987399f94b85122ae7b712b8922326203e03087e877ea7f`. Its condensed, sanitized metadata summary is committed separately and pinned by SHA-256 `c69f4aa08b220d00a11903339d57c60a0deb6c84492286487d0fff74440f831d`.

## 2. Reclassification of the Phase 174 failures

| Measure | Phase 174 strict ISO-only parser | Phase 175 locale diagnostic |
|---|---:|---:|
| Populated row instances | 115,617 | 115,617 |
| Expiration rows previously rejected | 94,607 | — |
| Previously rejected rows with one unique expiration interpretation | — | 91,303 |
| Ambiguous expiration row instances | — | 3,304 |
| Total row instances with one unique expiration interpretation | — | 112,313 |
| Quote-datetime rows with one unique candidate interpretation | Not evaluated for rows rejected earlier | 115,617 |
| Quote-datetime ambiguous / unparsed | — | 0 / 0 |

The 91,303 unique interpretations are within the 94,607 rows that Phase 174 rejected. The remaining 3,304 are 826 ambiguous row instances in each of the four 2023 sample members. They are not assigned a date. The fifth member (21,010 rows) already used ISO-extended expiration dates.

**Important denominator:** 112,313 is a count of row instances across five sample members, not a count of unique contracts. The same contract may occur in more than one member; Phase 175 did not persist keys needed to deduplicate it.

## 3. Timestamp and schema observations

- Four members (17, 18, 25, and 26 columns) contain 94,607 quote-datetime values in a uniquely parseable US-slash, minute-precision format. Their timestamps cover 2023-09-21 10:30 through 16:15 ET, with eight distinct times in each member.
- One 26-column member contains 21,010 ISO-second timestamps, all at 2022-02-02 09:39 ET.
- Expiration formats observed: 94,607 US-slash candidates, 3,304 DMY-slash candidates (the same ambiguous row instances also match US slash), and 21,010 ISO-extended values.
- Header variants: 17 columns without Calcs/OI; 18 with OI; 25 with Calcs; 26 with Calcs and OI. Required headers were present and no unknown headers were reported in the Phase 174 sample.
- Phase 174's timestamp parser was not reached for most rows because expiration validation failed first. Therefore its `invalid_timestamp_rows=0` must not be read as proof that all timestamps had already passed validation. Phase 175 supplies the separate unique-interpretation timestamp check.

The 2023 minute-only slash format differs from the current product specification's documented ISO-style timestamp. It is parseable as a sample value, but the format/precision regime still needs confirmation against a versioned production file specification. No seconds are invented.

## 4. What is and is not established

**Established at metadata level**
- The ISO-only expiration parser was too restrictive for this public sample.
- 91,303 previously rejected expiration row instances have one unique date interpretation.
- 3,304 expiration row instances are genuinely ambiguous under the tested formats and must be quarantined.
- All quote-datetime values have one unique candidate interpretation in the diagnostic.

**Not established**
- Full row-gate pass after locale-aware parsing. The raw sample was not retained, so contract keys, duplicates, numeric checks, quote-crossing checks, and SOD-OI consistency were not rerun with the new date parser.
- Unique contract count or underlying coverage.
- Continuous interval coverage; the sample contains only two quote dates and a small set of times.
- First-received timestamps, immutable correction vintages, historical inactive/delisted-underlying coverage, or license/price.
- Any predictive or incremental value.

## 5. Research decision

Keep Cboe Option Quotes as a **conditional option-market context source**, not signed institutional flow. The product includes NBBO, interval OHLC/volume, optional IV/Greeks, and optional OCC start-of-day open interest. It does not identify beneficial owners or participant aggressor identity. The SEC/market-structure sources and the broader source-admission matrix remain separate.

The next technical gate is a full sample re-run with a locale-aware expiration parser that:
1. accepts a date only when all supported formats produce one unique calendar date;
2. quarantines ambiguous rows without choosing US versus DMY;
3. keeps timestamp precision as supplied (minute versus second), with no fabricated seconds;
4. recomputes the entire contract, duplicate, numeric, quote, and OI checks;
5. still refuses sample/PIT/alpha admission until first receipt, correction lineage, historical universe, and license gates pass.

Cboe's current product page advertises historical data from January 2012, while its FAQ table says January 2010. Retain January 2012 as the conservative floor until Cboe resolves the discrepancy. The FAQ says open interest is prior-night OCC EOD OI, static through the session; it is not intraday opening flow.

Official references:
- [Cboe Option Quotes product page](https://datashop.cboe.com/option-quote-intervals)
- [Cboe DataShop FAQ](https://datashop.cboe.com/faqs)
- [Cboe Option Quotes v1.1 file specification](https://datashop.cboe.com/documents/Option_Quotes_Layout.pdf)

## 6. Reproducibility and controls

- Condensed Phase 175 metadata input: `phase175_cboe_option_quotes_date_locale_audit_result_2026-11-09.json`
- Auditor: `phase230_cboe_quotes_locale_reclassification.py`
- Tests: `test_phase230_cboe_quotes_locale_reclassification.py`
- Result: `phase230_cboe_quotes_locale_reclassification_result.json`
- Local tests: **10/10 passed**.
- This is a metadata-only deterministic reclassification; no raw row values, symbols, or contract keys are emitted.
- No dedicated Phase 230 workflow was launched. The source Phase 175 hosted job completed successfully; the Phase 230 auditor and tests were run locally.

No forward returns, alpha test, bootstrap/LOO, chronological OOS, or holdout use. No data purchase, vendor contact, production change, or universe change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.
