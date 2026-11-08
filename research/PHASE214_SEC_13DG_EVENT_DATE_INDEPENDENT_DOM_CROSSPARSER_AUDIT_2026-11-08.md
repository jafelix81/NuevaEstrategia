# Phase 214 — SEC 13D/G event-date independent DOM cross-parser audit

**Date:** 2026-11-08  
**Disposition:** PASS for parser-engine reproducibility; no alpha admission.

## Executive result

Phase 214 independently reprocessed the immutable Phase 124 SEC submission sample with a BeautifulSoup/lxml DOM parser and compared every legacy-HTML result with the Phase 213 Python html.parser implementation.

- **497/497 legacy HTML submissions:** identical event-date and unresolved-status outcomes.
- **451/497:** a date was recovered.
- **35/497:** no recognized event-date label.
- **11/497:** label present but no unambiguous four-digit-year date.
- **0 date/status conflicts.**
- The 102 structured-XML event dates also reproduced exactly against the Phase 124 CSV.
- All 600 raw submission SHA-256 values and SEC-header accession/acceptance/filed-date fields were reverified; all 599 actual 13D/G primary documents were found and matched their form family. One non-13D/G index alias remains quarantined.

This is a parser-engine cross-check, not an independently adjudicated gold-standard sample: both engines apply the same conservative event-label and nearest-date rule. It demonstrates that Phase 213's result is not an artifact of one HTML parser implementation; it does not prove that the labelled date is a trade date, acquisition date or market-knowledge time.

## Immutable source and integrity

- Phase 124 run: 42073725379.
- Phase 124 artifact: 13436764625.
- Artifact ZIP SHA-256: 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc (reverified).
- Source CSV SHA-256: be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5.
- Raw submissions: 600/600 SHA-256 verified.
- SEC headers: 600/600 accession, acceptance datetime and filed-as-of date verified.
- Actual primary documents: 599/599; the single SC TO-T/A index alias is excluded.

## Cross-parser method

1. The reference engine is the Phase 213 Python html.parser implementation.
2. The independent engine uses BeautifulSoup 4.14.3 with lxml 6.1.1 to create a DOM and flatten visible text.
3. Both engines use the same event-date label regex and the same conservative nearest-date search within 220 characters of the label.
4. The audit compares both the parsed date and the classification of unresolved rows (NO_LABEL versus LABEL_NO_DATE).
5. Structured XML is checked separately against the Phase 124 event-date field: 102/102 exact.

The nearest valid date was 2 characters from the event label at the median, 59 characters at the 90th percentile and 96 characters at the maximum. All recovered labels were within the configured 220-character search window.

## Reproduced Phase 213 cohort semantics

| Family | Sample | Parsed | Sample-weighted coverage | Quarter-end share among parsed (weighted) | Median filing minus event date | Maximum lag |
|---|---:|---:|---:|---:|---:|---:|
| 13D | 214 | 205 | 96.04% | 2.63% | 4 days | 921 days |
| 13G | 385 | 348 | 90.73% | 76.44% | 31 days | 379 days |

The 13D sample has 19 parsed dates more than 30 days before filing, 12 more than 90 days and two more than 365 days. The 13G sample has 175 more than 30 days before filing, seven more than 90 days and one more than 365 days.

These weighted rates are descriptive estimates within the Phase 124 stratified sample; they are not a complete population estimate. The format-dependent missingness and the small XML subset require caution.

## Research interpretation and next gate

The independent parser confirms the Phase 213 extraction is reproducible. It reinforces the decision to keep 13D and 13G separate:

- 13G event dates are often quarter-end reporting references, not observable accumulation dates.
- 13D event dates are less often quarter-end, but can be stale by years.
- Neither event date is the public-knowledge timestamp.

Preserve the SEC-header ACCEPTANCE-DATETIME separately. The SEC does not provide a guaranteed first-public-dissemination timestamp in these records; for daily research, retain the conservative rule of no same-session use and first candidate availability at the next full regular session.

Amendment markers remain separate: index /A suffix, cover-page Amendment No. and structured XML amendmentNo are not interchangeable. previousAccessionNumber remains a raw reference only, not an automatic immediate-predecessor edge; see Phases 161–163. The next 13D/G gate is effective-dated issuer/security identity and amendment-state reconstruction, not a return test.

**No forward returns, features, alpha, bootstrap/LOO, chronological OOS or holdout were used.** No production or universe changes were made. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. The legacy holdout remains CONSUMED_NOT_PRISTINE.

## Reproduction

Download Phase 124 artifact 13436764625, verify its ZIP SHA-256, extract it, then install beautifulsoup4==4.14.3 and lxml==6.1.1.

Run:

python research/phase214_13dg_event_date_parser_crosscheck.py --input-dir phase124_input --zip-path phase124_source_artifact.zip --output-json phase214_output/phase214_result.json

Offline regression suite: python -m unittest discover -s research -p 'test_phase214_*.py' -v.

The full-artifact integration test runs when PHASE124_INPUT_DIR and PHASE124_ZIP_PATH are set; otherwise it is skipped, while the parser unit tests remain runnable offline.
