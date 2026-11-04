# Phase 64 — SEC Form 144 master-index CIK-pair cross-quarter validation

**Date:** 2026-11-04  
**Status:** Validation workflow added; no economic test authorized.

## Why this phase exists

Phase 50 run 41793724389 (run 7) completed with failure, not still running. Its 2025Q1 census successfully fetched and parsed all 9,104 Form 144/144-A accessions with zero index-page errors, but the HTML detail-page parser returned 0% Subject/Reporting CIKs. Its XML sample therefore contained 50 non-target rows because target selection depended on the broken Subject CIK field.

I downloaded and independently reanalyzed artifact 13309238537 (SHA-256 \`7171bb25407517256345298bcf1d630fff1286b7d8073fd04d9f63f8cb1e45e3\`). The 9,104 accessions each have exactly two distinct master-index CIKs. Against the 309 current candidate CIKs:
- 1,618 accessions contain exactly one candidate CIK (1,608 Form 144; 10 Form 144/A).
- 7,486 contain no candidate CIK.
- No accession in this quarter contains two candidate CIKs.

In the artifact's 50 XML validation rows, both XML \`issuerCik\` and XML filer CIK were present in the two-CIK master-index pair in 50/50 cases and were distinct in 50/50. Exactly one current candidate CIK appeared in 9/50 pairs; all 9 were the XML issuer and none was the filer (6/6 Form 144; 3/3 Form 144/A).

This is promising but not a coverage or precision claim: the XML sample is small, not designed as a random candidate sample, and current ticker/CIK mappings are not historical PIT mappings.

## Phase 64 design

The new audit selects samples using the master-index pair itself, avoiding the broken HTML Subject parser:
- six separated quarters: 2023Q2, 2024Q1, 2024Q4, 2025Q1, 2025Q4 and 2026Q1;
- up to 25 unique-candidate and 25 zero-candidate control accessions per form per quarter;
- up to five ambiguous-pair accessions per form when present;
- deterministic SHA-256 accession sampling;
- primary XML fetched directly under each of the two CIK archive paths, trying both;
- XML confirms issuerCik and filer CIK separately; a unique candidate is accepted only when it equals issuerCik;
- Form 144 and 144/A are measured separately.

The report includes per-quarter candidate-pair counts, XML identity concordance, form concordance, control checks, fetch errors and Wilson 95% lower bounds. The proposed gate requires at least 100 Form 144 target XML rows and 20 Form 144/A target XML rows, high issuer concordance, at least 98% pair/form consistency and zero XML fetch errors.

## Point-in-time and economic limits

The current candidate CIK map is used only to test identity mechanics. It is not historical active-universe membership, does not resolve the 27 currently unmapped tickers, and does not prove that the CIK-to-ticker relationship was valid at every historical date.

For any later event panel, retain SEC filing date and use the first full trading-session close after that date as the conservative KnowledgeDate/execution boundary. Never treat approximate sale date as execution proof. Preserve \`previousAccessionNumber\` as a prior-filing reference, not as an assumed immediate predecessor. Normalize reporting persons and consolidate amendments before event counting.

Form 144 is a proposed-sale notice, not proof that a sale occurred. Any future predictive hypothesis must be preregistered and tested against frozen LTM/F80 with identical exposure, timing, costs, chronological OOS, block bootstrap and issuer LOO.

## Decision

Phase 64 is a data-identity validation only. No vendor data was purchased, no forward returns were calculated, no alpha claim was made, and no production code or baseline was changed. \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
