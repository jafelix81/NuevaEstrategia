# Phase 606 — SEC Form 13F actual manager-table cardinality and reference audit

**Status at branch creation:** live public-data audit pending.  
**Samples:** 2018 Q1 and 2026 June–August SEC Form 13F data sets.  
**Scope:** actual TSV schema, OTHERMANAGER / OTHERMANAGER2 key cardinality, INFOTABLE sequence references, SUMMARYPAGE reconciliation and bounded CIK / Form 13F file-number resolution. No holdings signal or return calculation.

## Why this gate is necessary

Phase 605 passed 18 offline synthetic tests, but it explicitly did not parse the actual manager tables. Its parser treats (ACCESSION_NUMBER, SEQUENCENUMBER) as a provisional logical key for OTHERMANAGER2.

The SEC's Form 13F Data Sets PDF states that OTHERMANAGER2 contains ACCESSION_NUMBER as its key, while also defining SEQUENCENUMBER and describing INFOTABLE.OTHERMANAGER as a sequence reference to another manager. This is a potential schema/key-cardinality ambiguity, not something synthetic fixtures can settle. The actual data must be inspected before manager attribution is admitted.

Official sources:
- SEC Form 13F Data Sets: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
- SEC Form 13F Data Sets specification: https://www.sec.gov/files/form_13f.pdf
- SEC Form 13F FAQ: https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f

## Audit design

The live workflow downloads only two public SEC ZIPs already used by Phase 47:
- 2018 Q1, pre-FIGI sample.
- 2026 June–August, current sample.

It records archive byte size and SHA-256; required TSV member names and headers; accession and row counts; OTHERMANAGER composite-key duplicates; OTHERMANAGER2 accession-only collisions, (accession, sequence) duplicates and maximum rows per accession; CIK / Form 13F file-number resolution categories; INFOTABLE.OTHERMANAGER resolved, dangling and malformed tokens; and SUMMARYPAGE declared included-manager counts versus actual OTHERMANAGER2 rows.

The large INFOTABLE is streamed rather than materialized in memory. Raw holdings values are not exported. The artifact contains aggregate counts, a small sample of manager-table rows/accessions, and exception examples only.

## Interpretation rules

- If one accession has multiple OTHERMANAGER2 rows with distinct sequence numbers, the published accession-only key notation is not unique in the observed data. (ACCESSION_NUMBER, SEQUENCENUMBER) remains a candidate logical key, but original EDGAR filing XML must corroborate it.
- If the sample has no multi-row accessions, the one-to-many sequence design remains untested; do not infer that the accession-only key is sufficient.
- INFOTABLE sequence references are counted only as resolved within the same accession.
- CIK is preferred when explicit. File-number-only resolution is accepted only when the number maps to exactly one CIK within the bounded sample. Names are never identity keys.
- Unresolved managers remain unresolved; no beneficial ownership, investment control, or decision-maker identity is inferred.
- 13F notices remain notice events, not zero-holdings portfolios.

## Evidence and limitations

The initial live result will be stored as a GitHub Actions artifact. A clean aggregate audit is not equivalent to original-filing reconciliation. The next gate is a stratified sample of original EDGAR XML filings that verifies manager lists, sequence numbers, and information-table references, including notices and combination reports.

This phase does not build an as-of manager graph across amendments, a historical CUSIP-to-F80 security master, or an investable signal. It does not infer short exposure, because Form 13F does not report short positions.

**No purchase, vendor contact, options-data request, production change, alpha test, OOS test, bootstrap, LOO, exposure or capital change.** F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. Options budget remains USD 0.
