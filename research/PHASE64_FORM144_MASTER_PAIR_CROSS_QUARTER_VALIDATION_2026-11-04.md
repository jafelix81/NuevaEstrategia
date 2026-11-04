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


# Phase 64 — SEC Form 144 master-index CIK-pair cross-quarter validation

**Date:** 2026-11-04  
**Status:** DATA IDENTITY GATE PASS; PIT universe and economic gates remain open.

## Why this phase exists

Phase 50 run 41793724389 (run 7) completed with failure. Its 2025Q1 census fetched and parsed all 9,104 Form 144/144-A accessions with zero index-page errors, but the HTML detail-page parser returned 0% Subject/Reporting CIKs. Because target selection depended on that parser, its 50-row XML sample contained only non-target rows.

I downloaded and independently reanalyzed artifact 13309238537. All 9,104 accessions had exactly two master-index CIKs. Against 309 current candidate CIKs:
- 1,618 accessions had exactly one candidate CIK (1,608 Form 144; 10 Form 144/A).
- 7,486 had no candidate CIK.
- None had two candidate CIKs.
In the 50 XML rows, both XML issuerCik and filer CIK were present in the pair and distinct in 50/50; all nine unique-candidate rows were the XML issuer (6/6 Form 144; 3/3 Form 144/A).

That was encouraging but too small and not target-stratified, so Phase 64 tested the identity rule across six separated quarters.

## Phase 64 implementation

The new audit selects samples directly from master-index CIK pairs, avoiding the broken HTML Subject parser:
- 2023Q2, 2024Q1, 2024Q4, 2025Q1, 2025Q4 and 2026Q1.
- Up to 25 unique-candidate and 25 zero-candidate control accessions per form per quarter; ambiguous pairs sampled separately.
- Deterministic SHA-256 accession sampling.
- Primary XML fetched directly under both master-index CIK archive paths.
- XML issuerCik and filer CIK are parsed separately. A unique candidate is accepted only when it equals issuerCik; a candidate matching filer CIK is explicitly rejected as issuer identity.

Implementation:
- research/phase64_form144_master_pair_cross_quarter_audit.py
- research/test_phase64_form144_master_pair_cross_quarter_audit.py
- .github/workflows/phase64_form144_master_pair_cross_quarter_audit.yml

The first workflow attempt, run 41809763468, failed because the script was invoked as a file while importing the research namespace package. The workflow was corrected to run it as a module. The successful run is 41809802277, job 126505915044, commit c0e27577341c00c3cfed4e6a7003ec9a8e2fad3d. Both test suites passed (10 Phase 50 regression tests and 8 Phase 64 tests). Artifact 13312525216, SHA-256 b40b1e9926c8093dcad8638a72e81ab503bfd4b01f55b46e36d3e78242ef72b1.

## Results

The six master indexes contained 56,167 unique Form 144/144-A accessions:
- 55,558 original Form 144 filings.
- 609 Form 144/A amendments.
- Every accession had exactly two distinct master-index CIKs.

Using the current candidate map (308 of 335 tickers mapped; 309 candidate CIKs):
- 9,432 original Form 144 accessions had exactly one candidate CIK in the pair (16.98% of originals).
- 76 Form 144/A accessions had exactly one candidate CIK (12.48% of amendments).
- One additional Form 144 accession in 2025Q4 had two candidate CIKs and remains ambiguous.
- 46,658 accessions had no current candidate CIK in the pair.

Per-quarter unique-candidate accessions:

| Quarter | Form 144 | Form 144/A |
|---|---:|---:|
| 2023Q2 | 1,207 | 22 |
| 2024Q1 | 1,850 | 11 |
| 2024Q4 | 1,643 | 13 |
| 2025Q1 | 1,608 | 10 |
| 2025Q4 | 1,461 | 16 |
| 2026Q1 | 1,663 | 4 |
| **Total** | **9,432** | **76** |

The XML validation sample contained 527 rows and zero fetch errors:
- Form 144: 150 unique-candidate targets, all 150/150 were XML issuerCik; zero were filer CIK or unresolved. These 150 rows represented 97 distinct issuer CIKs.
- Form 144/A: 76 unique-candidate targets, all 76/76 were XML issuerCik; zero were filer CIK or unresolved. These 76 rows represented 51 distinct issuer CIKs.
- Controls: 150/150 per form had both XML issuer and filer CIK present in the master-index pair.
- Across all 527 rows, both XML CIKs were present and distinct in 527/527, and XML submission form matched the master index in 527/527.
- The single sampled ambiguous pair remains classified as ambiguous; it was not forced into an issuer mapping.

Descriptive issuer-cluster Wilson 95% lower bounds for the observed 100% role concordance are 96.2% for Form 144 (97 distinct issuers) and 93.0% for Form 144/A (51 distinct issuers). Sampling is deterministic hash-based and issuer-clustered; these bounds are diagnostics, not a calibrated random-sample population guarantee.

**Decision: PASS for the master-index pair + XML issuerCik identity mechanism in the tested samples.** This does not certify all 9,508 candidate accessions, does not establish historical ticker mapping, and does not prove economic value.

## Form 144 event timing and economic interpretation

The regulatory timing makes Form 144 more interesting than a generic retrospective insider-sale report, but also imposes strict event-time controls:

- Rule 144(h)(3) requires Form 144 to be transmitted concurrently with placing a sell order with a broker or executing directly with a market maker. The filer must have a bona fide intention to sell within a reasonable time after filing; filing is not proof that the proposed quantity was actually sold.
- SEC staff CFI 120.01 (updated April 25, 2025) clarifies that adopting a Rule 10b5-1 plan does not change the Form 144 filing trigger; the filing is tied to order placement. It also states that the notice is effective for a maximum of three months.
- The SEC extended the EDGAR Form 144 filing window to 10:00 p.m. ET on Commission business days (effective March 20, 2023). A filing can therefore become public after the regular market close.
- Form 144 is required for affiliates' proposed sales relying on Rule 144 above the applicable threshold (more than 5,000 shares/units or more than $50,000 over three months). Non-affiliates no longer need to file Form 144. It is therefore a selective large-affiliate-supply feed, not a complete record of all insider or affiliate sales.

Sources:
- eCFR 17 CFR 230.144(h): https://www.ecfr.gov/current/title-17/chapter-II/part-230/section-230.144
- SEC Exchange Act Rules CFI 120.01: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules
- SEC final rule on filing hours: https://www.sec.gov/rules-regulations/2023/02/extending-form-144-edgar-filing-hours
- SEC small-entity guide (non-affiliates no longer required to file Form 144): https://www.sec.gov/resources-small-businesses/small-business-compliance-guides/revisions-rules-144-145
- Investor.gov Form 144 overview: https://www.investor.gov/introduction-investing/investing-basics/glossary/form-144

Implications for event construction:
- Treat original Form 144 as a proposed-supply/order-placement event, not a confirmed executed sale.
- Keep 144/A amendments separate and link them to prior accessions; previousAccessionNumber is not assumed to be the immediately preceding amendment.
- Preserve seller, relationship, security class, units, aggregate value, approximate sale date, notice date, 10b5-1 remarks and plan-adoption dates.
- Do not use approximate sale date as execution proof or KnowledgeDate.
- Until acceptance-time publication is independently captured, use the first full trading-session close after the filing date as the conservative EOD knowledge/execution boundary. A later sensitivity may use same-day close only when the accepted timestamp and a pre-registered dissemination buffer make it executable.

## Remaining gates

1. Confirm all candidate accessions by XML, not only the stratified sample.
2. Reconstruct point-in-time F80 membership and CIK/ticker history; current mapping is not PIT. 27 current universe tickers remain unmapped.
3. Reconcile original/amendment lineage and seller/security-level duplicate events.
4. Measure coverage by historical F80 issuer-days, filing year, liquidity and issuer size.
5. Only then preregister a proposed-sale-pressure hypothesis and compare it incrementally with frozen LTM/F80.

No forward returns were used, no alpha test was run, no data vendor was purchased, and no production strategy was changed. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## Post-Phase65 clarification — candidate CIK role is not implied by pair membership

The larger Phase 65 sample found two unique-candidate master-index pairs in which the sole current-universe candidate CIK was the XML **filer**, not the XML issuer. These are validly resolved non-target filings, not parser errors:

- `0001970673-23-000004`: candidate JD CIK 0001549802 is XML filer/seller JD.com, Inc.; XML issuer is GigaCloud Technology Inc. (CIK 0001857816).
- `0001104659-26-005774`: candidate QCOM CIK 0000804328 is XML filer/seller QUALCOMM INC; XML issuer is MNTN, Inc. (CIK 0001891027).

Phase 64's 150/150 Form 144 and 76/76 Form 144/A issuer matches remain correct for that sample only. They do not justify assuming that every unique candidate CIK in a master-index pair is the issuer. The robust rule is: fetch primary XML, separately parse issuerCik and filer CIK, retain an event only when issuerCik belongs to the candidate issuer set, and classify filer-only candidate matches as false positives. Phase 65's 99.714% unique-candidate issuer match in its Form 144 sample is descriptive only because the sample is deterministic/stratified.
