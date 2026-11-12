# Phase 344 — N-PORT optional Series ID and fund identity reconciliation

**Date:** 2026-11-12 UTC  
**Branch:** \`phase344-nport-optional-series-id-identity\`  
**Final run:** [43288306677](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43288306677)  
**Artifact:** [13976801076](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43288306677/artifacts/13976801076)  
**Draft PR:** [#33](https://github.com/jafelix81/NuevaEstrategia/pull/33)

## Scope

Reconcile five purposively selected original SEC N-PORT-P filings (2020–2025) for which Phase 192 had identified direct short-equity positions. This is a raw-source and fund-identity feasibility audit, not a representative prevalence sample.

## Final result

<badge>RAW_SAMPLE_RETRIEVED_ACCEPTANCE_RECONCILED</badge>

- 5/5 original accessions retrieved.
- 20/20 raw files retrieved (filing index, complete submission, accession directory index and primary XML for each filing).
- 1,722,110 source bytes staged in the 90-day workflow artifact; raw bytes were not committed to the repository.
- 5/5 SEC-HEADER acceptance timestamps reconciled to filing metadata.
- 5/5 fund identities resolved.
- 5/5 expected CUSIP checks passed.
- 5/5 expected row-count gates passed.
- 4/5 filings contain an EDGAR Series ID; 1/5 has no Series ID but has a complete fund identity through registrant CIK, registration file number and series name.
- 327 direct short-equity rows were parsed across the five selected filings; all 327 were sign-concordant.

The artifact ZIP SHA-256 is \`7e8a19d918aa9729c2319e0ca9b6cee06e9a8b0bacc3528a180d92f2ca7c5fbd\`.

## Identity correction

The official Form N-PORT identifies the EDGAR series identifier as optional: Item A.2(b) is “EDGAR series identifier (if any)” ([SEC Form N-PORT](https://www.sec.gov/about/forms/formn-port.pdf)). Requiring a Series ID on every filing was therefore too strict.

The 2025 ACAP Strategic Fund filing has no Series ID in either its primary XML or filing index. It does contain:

- Registrant CIK: \`0001467631\`
- Registration file number: \`811-22312\`
- Series name: \`ACAP Strategic Fund\`
- Monthly-return class IDs: \`C000843102\`, \`C000843201\`

The filing's [original primary XML](https://www.sec.gov/Archives/edgar/data/1467631/000114554925033457/primary_doc.xml) confirms those fields. The missing Series ID is a valid optional-ID state, not a retrieval or parser failure.

A second false-negative defect was CIK zero-padding. The curated manifest stores registrant CIKs without leading zeros, while N-PORT XML uses ten digits. The parser now normalizes both sides to ten digits. It keeps registrant CIK separate from accession identity and requires the registration file number and series name to reconcile. Conflicting CIK/file-number/Series-ID evidence still fails closed.

## Accession-level direct short rows

| Filing year | Accession | Fund | Direct short rows |
|---:|---|---|---:|
| 2020 | \`0001752724-20-163166\` | AdvisorShares Dorsey Wright Short ETF | 100 |
| 2022 | \`0001145549-22-056239\` | Nuance Concentrated Value Long-Short Fund | 46 |
| 2023 | \`0001145549-23-060491\` | Otter Creek Long/Short Opportunity Fund | 27 |
| 2024 | \`0001145549-24-075135\` | Leuthold Grizzly Short Fund | 86 |
| 2025 | \`0001145549-25-033457\` | ACAP Strategic Fund | 68 |
| **Total** | | | **327** |

These five filings were selected because they were known short-position candidates. Their 327 rows cannot be used to estimate market-wide N-PORT short-position prevalence.

A separate broad Phase 316 stratified sample found direct-short rows in only 2 of 280 filings: 194 rows across 173 unique CUSIPs, with no ticker fields. That is evidence of sparse filing-level prevalence in that sample, not evidence that the source has no value.

## Tests and controls

- 22/22 offline regression tests passed.
- Raw XML and complete submission SHA-256 checks passed for all five accessions.
- \`first_public_receipt_verified=false\`.
- \`strict_pit_admitted=false\`.
- \`alpha_test_authorized=false\`; no return test, OOS, bootstrap/LOO or holdout use.
- No vendor contact, data purchase, production change or F80 change.

Acceptance timestamps are preserved as knowledge-time metadata but are not promoted to proof of first public receipt. No same-session use is authorized.

## Research decision

N-PORT remains a **conditional, low-prevalence institutional short-exposure source**, not an admitted stock-level signal.

Before an event or panel test:

1. Build an effective-dated CUSIP/ISIN-to-security crosswalk covering share classes, ADRs, ticker changes, mergers, delistings and historical universe membership.
2. Audit N-PORT amendments and correction lineage; distinguish report-period holdings from later amendments.
3. Verify first-public availability or use a conservative next-full-session knowledge date.
4. Expand beyond the five purposive short-focused funds and estimate actual security/quarter coverage.
5. Only then test changes in direct short exposure versus frozen LTM/F80 under identical exposure/costs, chronological OOS, bootstrap/LOO and untouched holdout discipline.

No minimum or maximum holding period is imposed. The quarterly reporting cadence is a property of the source, not a strategy constraint.
