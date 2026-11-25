# Phase 607 — bounded original EDGAR XML reconciliation for 13F manager-reference exceptions

**Status at branch creation:** bounded live source-document audit pending.  
**Samples:** six accessions selected from Phase 606 exceptions and controls across 2018 Q1 and 2026 Jun–Aug.  
**Scope:** retrieve original EDGAR filing XML and information-table XML; compare cover-page OTHERMANAGER2 sequence numbers with information-table OTHERMANAGER references. No holdings signal or return calculation.

## Why this gate exists

Phase 606 found:
- 20 / 3 duplicate accession-sequence pairs in OTHERMANAGER2.
- Material unmatched numeric references and nonnumeric tokens.
- Exact SUMMARYPAGE included-manager count reconciliation.
- No nonzero INFOTABLE reference tokens matched OTHERMANAGER.OTHERMANAGER_SK; the dominant hypothesis remains OTHERMANAGER2.SEQUENCENUMBER.

The SEC's Form 13F data-set documentation says INFOTABLE.OTHERMANAGER is the sequence number of another manager included in the report. The Form 13F XML technical specification and SEC filer guidance describe the XML submission structure and the information-table other-manager field. The source filing, not the flattened TSV, is the adjudication authority.

Official references:
- https://www.sec.gov/files/form_13f.pdf
- https://www.sec.gov/files/info/edgar/specifications/form13fxmltechspec.htm
- https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/create-xml-information-table-form-13f-using-excel

## Bounded sample

1. 2018 accession 0001325091-18-000003 — unmatched numeric token 2811304.
2. 2018 accession 0001683168-18-000798 — sequence-match control.
3. 2018 accession 0000728889-18-000299 — duplicate sequence pair.
4. 2026 accession 0001951757-26-001605 — unmatched numeric token 4.
5. 2026 accession 0001828822-26-000007 — nonnumeric tokens XXEC / INC.
6. 2026 accession 0001890906-26-000061 — duplicate sequence pair.

The script locates XML documents through each accession's EDGAR index.json, prefers primary-document and information-table XML files, parses namespaces safely, records source URLs and SHA-256, and compares source sequence/reference values. Only six accessions are queried; no full backfill is performed.

## Interpretation

- If the source XML contains the same anomaly, classify it as an as-filed/filer-level exception and preserve it without guessing.
- If source XML is internally consistent but the TSV differs, classify it as a structured-dataset extraction discrepancy.
- If the source document cannot be located or parsed, retain the accession as unresolved.
- Duplicate sequence numbers are ambiguous; a matching token is not treated as a unique manager attribution when multiple source entries share it.
- Nonnumeric values and zero sentinels remain separate categories.

## Limits

This is a bounded source-integrity audit, not a complete 13F manager graph. It does not infer beneficial ownership, control, investment decision-maker, net exposure, short positions, informed behavior, alpha, OOS, bootstrap, LOO or production eligibility.

No data purchase, vendor contact, options request, production change, exposure or capital change. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; options budget USD 0.
