# Phase 67 — Full Form 144 candidate-resolution results and artifact reanalysis

**Date:** 2026-11-04  
**Run:** [41828139052](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41828139052) — completed successfully  
**Job:** 126568067820  
**Artifact:** [13327123059](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41828139052/artifacts/13327123059)  
**Artifact SHA-256:** \`4d5660e6c9edd9fe40a3557919e28890a25971fcff8faf393ca500145e94eedb\`

## 1. Full-census identity result

The artifact contains 11 files, including full candidate-role, issuer-event, filer-only, control, error and summary outputs. Reanalysis of the actual CSVs confirms:

| Metric | Result |
|---|---:|
| Quarterly master-index accessions, 2023Q2–2026Q3 | 56,167 |
| Candidate accessions selected using 309 current CIKs | 21,648 |
| Form 144 original candidates | 21,452 |
| Form 144/A candidates | 196 |
| XML issuer-event rows | 21,634 |
| Form 144 issuer-event rows | 21,438 |
| Form 144/A issuer-event rows | 196 |
| Filer-only false positives excluded | 14 |
| Unresolved candidate rows | 0 |
| XML fetch/processing errors | 0 |
| Duplicate candidate accessions | 0 |
| Unique XML issuer CIKs among event rows | 289 |
| Zero-candidate controls | 280 |
| Control master-pair concordance | 100% |

Candidate role status counts:

- \`issuer_match\`: 21,633
- \`ambiguous_pair_issuer_match\`: 1
- \`filer_only_false_positive\`: 14

The 14 filer-only false positives were all original Form 144 candidates. They remain in the diagnostic file and are excluded from \`issuer_event_raw.csv\`. Their current candidate ticker labels were BIDU (4), JD (2), QCOM (2), HOOD (2), RIOT (1), NVO (1), XOM (1) and GS (1).

All 21,648 candidate rows were explicitly classified. XML issuer and filer CIKs were distinct, both appeared in the unlabelled master-index pair, and XML form matched the index in 100% of parsed candidates. This validates the current-CIK pair-to-XML role-resolution mechanism for this census.

## 2. Proposed-sale field quality

All 21,634 issuer-event rows have separately parsed proposed-sale tranches, with numeric sale units, aggregate value and outstanding-share fields. Acquisition lots and realized sales in the prior three months remain separate XML groups.

However, numeric parse success is not the same as an economically valid positive sale size:

- Two Form 144/A records have zero proposed units and zero proposed value: PayPal accession \`0001972362-23-001045\` and Snowflake accession \`0001959173-26-007025\`.
- One original Form 144 record (Mastercard Foundation, accession \`0000895345-23-000595\`) has positive units but zero aggregate value.

These records remain un-imputed. A future feature panel must flag zero/invalid/not-applicable size rather than replacing it with a positive amount or treating it as ordinary supply.

Across all proposed-sale tranches, the approximate sale date was before filing in 568 cases, the same date in 20,781 cases and after filing in 514 cases. These are XML field diagnostics, not execution evidence. Approximate sale date and notice date are not KnowledgeDate. Filing date remains a conservative public-date proxy, and the first full trading-session close after filing remains the provisional earliest signal boundary until accepted/publication timestamps are verified.

## 3. Amendment-reference audit

There are 196 Form 144/A event rows:

- 195 reference a previous accession present somewhere in the 14-quarter master-index census.
- One reference is outside that census: \`0001766264-23-000002\`, referenced by accession \`0001766264-23-000004\`.
- Of the 195 in-census references, 193 previous accessions are also present in the Phase 67 candidate-role file; three are present in the broad index census but were not selected as candidate rows:
  - \`0001766264-23-000002\`
  - \`0001318751-23-000002\`
  - \`0001959173-23-003484\`
- Among the 193 candidate-row predecessor references, 188 point to Form 144 and five point to another Form 144/A. Recursive amendment chains are therefore required; a previousAccessionNumber is not assumed to identify the immediate original notice.
- All 193 candidate-row predecessor pairs have the same XML issuer CIK and overlapping security-class labels. No issuer-CIK mismatch or disjoint security-class pair was observed in this subset.

Seller-name text is less clean. After conservative Unicode/case/punctuation normalization:

| Seller comparison | Count |
|---|---:|
| Exact normalized text | 174 |
| Same tokens, different order | 6 |
| High token overlap but not exact | 5 |
| One string is a substring/expansion of the other | 4 |
| Low token overlap | 4 |
| Previous accession not in candidate-role rows | 3 |
| Total amendments | 196 |

The 13 non-exact cases include trusts, expanded legal names, middle initials and cases where a person name differs from a trust name. Do not merge sellers solely through fuzzy string similarity. Preserve raw seller names and use a separately audited seller/entity crosswalk. The three predecessor accessions found in the broad index but not in candidate rows and the one out-of-window reference require explicit predecessor XML resolution or a left-censored status.

Of the 193 candidate-row references, 60 amendments were filed on the same calendar day as the referenced accession and 40 one calendar day later. These date gaps do not establish that the referenced filing is the immediate predecessor.

## 4. Phase 68 expansion and Phase 69 incremental scan

Phase 68 run 41828426133 / artifact 13321546076 passed current mapping at 335/335 tickers, 319 candidate registrant CIKs and zero source errors. It adds ten registrant CIKs to the 309-CIK Phase 67 set.

Phase 69 now has a committed incremental script and six regression tests. It:
- Requires the exact Phase 67 baseline artifact (run 41828139052 / artifact 13327123059).
- Rebuilds the 319-CIK Phase 68 map and validates the ten new CIKs.
- Scans the same 14 indexes only for accessions containing a new CIK.
- Reclassifies old/new overlapping pairs using all 319 CIKs and verifies XML issuer/filer identity has not changed.
- Merges new and reclassified rows without duplicating accessions or retaining a superseded filer-only event.
- Preserves fund series/class candidates and does not fan a registrant event out to all tickers.

The six local regression tests passed in an isolated harness. Hosted Phase 69 execution is intentionally held while run 41828179718 remains in progress in the Phase 67 concurrency group. Its job log currently returns BlobNotFound; no conclusion about failure is inferred from that response. Run 41828139052 already supplies a completed, validated baseline artifact with the same Phase 67 production script commit; run 41828179718 adds a later test-only commit.

## 5. What this result does not establish

Phase 67 passes only the current-CIK issuer-role identity and XML field-assembly gate. It does not establish:

- Historical F80 membership or historical ticker/CIK effectiveness.
- Historical predecessor issuers, delisted securities or a broad eligible universe.
- Exact fund series/class-to-security attribution.
- Accepted-time or first-publication availability.
- Complete seller identity and amendment chains.
- Actual execution of proposed sales.
- Predictive or incremental economic value.

Phase 70's historical security-master/universe PIT audit remains a hard blocker for broad cross-sectional alpha claims. The current 335-name universe is a curated present-day list; a perfect current CIK map cannot restore omitted delisted names or prove the original universe-selection rule.

No forward returns, feature selection, portfolio comparison or alpha test was run. No data were purchased. \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
