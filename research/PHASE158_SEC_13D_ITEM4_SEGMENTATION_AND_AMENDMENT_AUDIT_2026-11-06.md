# Phase 158 — SEC Schedule 13D Item 4 segmentation and amendment-contamination audit

**Date:** 2026-11-06  
**Status:** COMPLETED — deterministic extraction/feasibility audit only; no alpha test

## Scope and immutable inputs

This phase reuses the Phase 124 stratified SEC 13D/G sample and the Phase 157 legacy-HTML field audit. No SEC requests were made.

- Phase 124: run [42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379), artifact 13436764625; 600 source submissions and 600 raw-file hashes.
- Phase 157: run [42224436013](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42224436013), artifact 13504962007; 497 legacy HTML filings.
- All 600 Phase 124 raw submission hashes were reverified. The Phase 124 and Phase 157 CSV hashes and accession joins were checked before extraction.

The Phase 157 sample contains 180 legacy HTML Schedule 13D filings (72 initial filings and 108 amendments). The remaining legacy sample rows are 13G and are not part of this Item 4 audit.

## Results

### 1. Phase 157 undercounted one valid Item 4 section

Phase 157 flagged 116 of the 180 13D filings as containing Item 4. Its detector scanned only the first 1,000 extracted text lines. Phase 158 scans the full primary document up to 2,500 lines and recovered one additional heading:

- Accession: `0001140361-18-032832`
- Heading: extracted line 1,317
- Cleaned section text: `No material change.`

This is a valid Item 4 section but not a new economic event. The revised total is **117/180 (65.0%)**, versus 116/180 previously. Every prior Phase 157 positive was reproduced; one additional section was recovered.

### 2. Section extraction and filing role

| Filing role | Filings | Item 4 sections | Coverage | Median cleaned characters | P75 cleaned characters |
|---|---:|---:|---:|---:|---:|
| Initial 13D | 72 | 59 | 81.94% | 1,879 | 2,791 |
| 13D amendments | 108 | 58 | 53.70% | 1,045 | 1,784.25 |
| **Total** | **180** | **117** | **65.00%** | — | — |

There are 63 filings where the parser did not find an Item 4 heading (13 initial filings and 50 amendments). This is a parser/extraction status, not proof that the filing contains no relevant information.

### 3. Boundary correction

The earlier extraction expected Item 5 as the next section boundary. Five amendment filings instead proceed from Item 4 to Item 6 or Item 7. The corrected extractor accepts a conservative next numbered item heading (5–9), while ignoring narrative references such as “see Item 7 below.”

| Next section boundary | Sections |
|---|---:|
| Item 5 | 112 |
| Item 6 | 2 |
| Item 7 | 3 |
| **Total** | **117** |

No section in this sample remains without a recognized next-item boundary after the correction.

### 4. Amendments are not independent flows

All 58 extracted amendment sections are labelled `AMENDMENT_STATE_UPDATE`, not new transactions or independent events. One amendment's cleaned Item 4 text consists only of “No material change.” The difference in median text length (1,879 characters for initial filings versus 1,045 for amendments) is a parsing diagnostic only; it does not measure intent, novelty, conviction or economic importance.

Without a confirmed original accession and line-level comparison, an amendment can repeat, supplement, replace or restate prior text. Its information becomes available only at its own EDGAR acceptance time. It must not be backdated or counted as another purchase.

## Decision

- **Pass:** Item 4 section-level extraction is feasible on this immutable sample after the scan-limit and boundary corrections.
- **Not passed:** issuer/security identity, historical active-universe coverage, cross-quarter amendment-parent lineage, and a validated purpose/activism taxonomy.
- No keyword-based sentiment or activism labels were generated. No analyst gold-label set exists yet.
- No predictive feature panel, forward-return test, bootstrap, LOO or OOS test was run.
- No final holdout was used; no vendor was contacted or purchased; production was not modified.

## Next gate

1. Resolve 13D/A parent accessions across quarters and diff Item 4 as a filing-state update.
2. Build a manually adjudicated taxonomy on initial 13D filings only, with explicit “ordinary investment/no stated plan,” governance/board, strategic transaction, financing/restructuring, opposition/activism, and mixed/unclear labels. Preserve source excerpts and confidence; do not train a classifier until inter-rater or adjudication quality is established.
3. Complete effective-dated issuer/class/CUSIP and historical active-universe mapping before any return join.
4. Only then preregister an economic hypothesis and test incremental value against frozen LTM/F80 and momentum controls with strict acceptance-time PIT, identical exposure/costs, chronological OOS, bootstrap and LOO.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.**

## Reproducibility

- Helper: `research/phase158_13d_item4_segmentation_audit.py`
- Tests: `research/test_phase158_13d_item4_segmentation_audit.py`
- Workflow: `.github/workflows/phase158_sec_13d_item4_segmentation_audit.yml`
