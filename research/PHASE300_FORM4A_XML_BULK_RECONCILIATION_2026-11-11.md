# Phase 300 — SEC Form 4/A XML-to-bulk reconciliation (2026-11-11)

## Decision

**The Phase 298 cross-quarter Form 4/A candidate-link heuristic is strongly corroborated in this deliberately stratified sample, but it is not an authoritative accession join and is not admitted to trading tests.** Use the original EDGAR ownershipDocument XML as the transaction source of record. Quarantine the one sampled pair with derivative-table field-placement discrepancies in the SEC bulk archive. Preserve footnote and timeliness exceptions rather than silently normalizing them away.

## Scope and reproducibility

Phase 299 downloaded the complete SEC EDGAR submission text for **90 unique accessions** representing **46 original Form 4 / amendment Form 4/A candidate pairs**. The immutable raw files are preserved in Phase 299 artifact 13898356586; all 90 SHA-256 hashes were re-verified in Phase 300.

The sample covers:
- target amendment periods 2012 Q1 and 2026 Q3;
- parent filings in the same quarter or the immediately preceding quarter (25 same-quarter, 21 adjacent-quarter pairs);
- 32 single-owner/equal-owner-set pairs;
- all 13 partial-owner-overlap candidate pairs plus one additional multi-owner/equal-set pair (14 partial/multi-owner pairs total);
- the previously used Eton Pharmaceuticals positive control.

For each target/parent-quarter/candidate-line-difference stratum, the two exact-owner pairs with the smallest deterministic SHA-256 rank were selected. All partial-owner candidates were included. This is a purposive validation sample, **not a random prevalence sample**.

Source archives and their inner SHA-256 values are embedded in the sample manifest and checked by the workflow. Phase 300 re-runs entirely offline from the preserved SEC submissions and immutable Phase 294/298/299 artifacts; it makes no SEC requests.

## Results

### 1. Filing identity and candidate linkage

| Check | Result |
|---|---:|
| Raw EDGAR submissions downloaded and hash-verified | 90 / 90 |
| ownershipDocument XML parsed | 90 / 90 |
| Header/XML accession, form, filing date, issuer CIK and reporting-owner set agree with bulk data | 90 / 90 |
| Original/amendment candidate pairs corroborated by issuer, owner overlap, dateOfOriginalSubmission, and acceptance chronology | **46 / 46** |

For every sampled amendment, the XML dateOfOriginalSubmission equals the candidate parent's SEC filing date; the issuer CIK matches; reporting-owner sets overlap; and the original acceptance timestamp is not later than the amendment's acceptance timestamp.

This is strong independent metadata corroboration of the candidate links. It is **not** an authoritative parent-accession foreign key: the Form 4/A XML provides the original submission date, not the original accession number. Same-issuer/same-day multiple originals can therefore remain ambiguous outside this sample.

### 2. Bulk transaction-row fidelity

The first Phase 299 comparison was deliberately conservative but under-normalized: bulk dates were DD-MMM-YYYY, XML dates were ISO, and XML retained more than two decimals where the bulk archive stored two. Its 3/90 exact-row result is superseded by this Phase 300 reconciliation.

Phase 300 applies two source-comparison normalizations only:
- dates to ISO YYYY-MM-DD;
- numeric fields to the SEC bulk archive's two-decimal precision using ROUND_HALF_UP.

It then reports both the full Phase 153 transaction signature and a core signature that excludes only NATURE_OF_OWNERSHIP and TRANS_TIMELINESS (footnote/timeliness metadata, not transaction identity).

| Reconciliation | Documents |
|---|---:|
| Both Table I and Table II row counts agree | 90 / 90 |
| Full transaction signatures agree at two decimals | 80 / 90 |
| Core transaction signatures agree, excluding footnote/timeliness metadata | **88 / 90** |
| Footnote/timeliness-only differences | 8 / 90 |
| Core transaction-field mapping exceptions | 2 / 90 |

The eight footnote/timeliness-only exceptions comprise six documents with NATURE_OF_OWNERSHIP footnote association differences and two with TRANS_TIMELINESS differences. Their core transaction facts match. These metadata fields remain preserved and must not be silently discarded for ownership interpretation or event-timing work.

The two core-field exceptions are:
- 0001474427-12-000001
- 0001474427-12-000002

They form candidate pair P299-022 (issuer CIK 0000822370, ticker as filed CNSO.OB). The bulk derivative rows place values differently from the original XML across TRANS_SHARES, TRANS_TOTAL_VALUE, SHRS_OWND_FOLWNG_TRANS and the corresponding XML underlying/post-transaction fields. Both filings are multi-owner/partial-overlap records. **Quarantine the derivative rows for this pair; do not use the bulk derivative amounts or attribute the transactions to one owner.**

### 3. Pair-level line-difference reproduction

| Pair-level check | Result |
|---|---:|
| Both filings fully match bulk at two decimals | 38 / 46 |
| Both filings match bulk on core transaction fields | **45 / 46** |
| Full-signature bulk/XML amendment-difference summary parity | 44 / 46 |
| Core-signature bulk/XML amendment-difference summary parity | 46 / 46 |

The one pair failing core row-level equivalence is P299-022, the derivative mapping exception above. Its aggregate difference summary happens to reproduce because the same field-placement issue occurs in both filings; that does not make the underlying derivative fields reliable.

For the 45 remaining pairs, both the original and amended transaction tables match the original XML on core fields. The core line-difference summary is reproducible across all 46 pairs, but no line is automatically labelled a new trade, deletion, reversal, or confirmed modification. A same-coarse-key unmatched line remains ambiguous.

## Interpretation

1. The Phase 298 candidate-link rule is credible enough to carry forward as a **high-confidence metadata candidate** in this sample.
2. The SEC Form 345 bulk archive reproduces core transaction rows in 88/90 documents after appropriate date/precision normalization; the original XML remains the authoritative source for any future event construction.
3. Footnote association and timeliness fields need a separate, explicit reconciliation layer.
4. Derivative rows need XML-first parsing or a dedicated schema audit; the P299-022 pair is quarantined.
5. Multi-owner filings cannot be treated as transactions of a single reporting owner. Fourteen sampled pairs are partial/multi-owner; only 32 pairs have one owner in both documents with equal owner sets.

## Next gates

1. Expand the same stratified XML validation to at least one intermediate historical era and to ambiguous/no-candidate amendments; do not infer population precision from the 46-pair sample.
2. Build a versioned original-to-amendment graph with explicit states: metadata-corroborated candidate, ambiguous same-day parent, no parent in covered quarters, multi-owner attribution unresolved, and derivative mapping exception.
3. Preserve XML footnotes and timeliness fields separately. Use original XML for derivative transactions until a larger field-mapping audit passes.
4. Resolve effective-dated issuer/security-class identity, including inactive/delisted securities, before mapping events to tradable symbols.
5. Continue the Phase 281 daily-index knowledge-clock audit. Acceptance chronology is not exact first-public availability; no event may enter a strict PIT test until the conservative first-observed index date and next-full-XNYS-session rule are validated.
6. Only after source, identity and PIT gates pass, preregister a new chronological test against frozen LTM/F80 with identical exposure/costs, label-maturity embargo, clustered bootstrap/LOO and a fresh holdout.

## Controls

- No return, alpha, bootstrap/LOO, or OOS test was run.
- No holdout was used.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
- No production, universe, capital, parameter, or PR merge changes were made.
- No vendor was contacted and no data was purchased.
- Phase 300 was offline; Phase 299 made the 90 SEC retrievals using the configured User-Agent contact string. No email was sent.

## Execution and artifacts

- Phase 299 source-capture run: [43115460066](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43115460066)
- Phase 299 raw EDGAR artifact: [13898356586](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43115460066/artifacts/13898356586)
- Phase 300 offline reconciliation run: [43116245184](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43116245184)
- Phase 300 result/manifest artifact: [13898537038](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43116245184/artifacts/13898537038)
- Phase 300 regression suite: 6/6 tests; Phase 299: 6/6; Phase 153: 17/17.
