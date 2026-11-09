# Phase 227 — SEC 13D/G: exclude repeated zero tuples and adjudicate ownership overlap

**Date:** 2026-11-08  
**Status:** completed measurement correction; no ownership graph or alpha feature admitted.

## Decision

Phase 226 grouped repeated six-field reporting-person signatures. Its predicate treated the string "0" as truthy, so repeated all-zero tuples entered the repeated-signature totals. They are not positive ownership positions.

I re-ran the full hash-pinned Phase 124 structured-XML sample, separated positive signatures from all-zero signatures, and reviewed 12 purposively selected filings against their original XML item text. This corrects the measurement label without rewriting Phase 226's historical output.

**Corrected result:** 58 repeated-signature groups = 50 positive-position groups + 8 all-zero groups. The zero groups contain 27 reporting-person rows. Of 48 filings with any repeated signature, 41 have at least one positive repeated group and 7 are zero-only; one of those 41 positive-repeat 13G filings also contains a separate zero group.

## Source integrity

- [Phase 124 run 42073725379](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379)
- [Original artifact 13436764625](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42073725379/artifacts/13436764625)
- ZIP SHA-256: 85f69e083b5af65731c9bcfe24e8c75821fc0f2c2476bfa8ba573e2e884570dc
- CSV SHA-256: be2c592c6c26d9f1ea49bda5d29d20e944004b2e2f4a3c3f4fe1f732319c55d5
- 600 index rows; 599 actual 13D/G filings; one non-13D/G index alias quarantined.
- 102 structured XML filings (34 13D, 68 13G), covering 2024Q4–2026Q3.
- Reverified the ZIP, CSV and all 102 XML-bearing raw-submission hashes.

The 102-document sample is stratified/purposive, not a random census. Do not interpret its rates as population prevalence.

## Corrected counts

| Cohort | XML filings | Any repeated signature | Positive groups | Positive owner rows | Zero groups | Zero owner rows | Zero-only filings | Both positive and zero |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 13D | 34 | 21 | 25 | 90 | 1 | 4 | 1 | 0 |
| 13G | 68 | 27 | 25 | 72 | 7 | 23 | 6 | 1 |
| **Total** | **102** | **48** | **50** | **162** | **8** | **27** | **7** | **1** |

The seven zero-only filings are Mobiquity (0001535610-25-000004), Instructure (0000950170-25-015856), Endeavor (0001140361-25-017757), SatixFy (0000902664-25-003482), CARGO Therapeutics (0001699737-25-000017), BlackRock MuniVest Fund II (0002052595-26-000045) and Palisade Bio (0001172661-26-000720). Savara (0001415889-25-021787) is the mixed 13G filing with both a positive repeated group and a zero repeated group.

All-zero signatures have zero aggregate, zero percent and zero voting/dispositive power. A zero row is not proof of a trade, a short position or a position that was necessarily closed during the reporting interval.

## Source-linked case adjudication

Eight filings show explicit common-holder, adviser, GP, trustee or indirect attribution. Repeated rows are not additive:

| Issuer / accession | Repeated rows | Aggregate shares | Source-supported interpretation |
|---|---:|---:|---|
| Guardian Pharmacy / 0001412741-24-000004 | 3 | 751,084 | Item 2 identifies the same J. Goldman Master Fund as underlying holder. |
| Red Violet / 0001104659-24-119165 | 3 | 452,466 | Item 4 identifies fund/SMA shares under Nantahala control and attribution to its managing members. |
| Teradata / 0001415889-25-008727 | 3 | 9,416,666 | Item 5 identifies Lynrock Lake Master Fund as direct holder and its manager/control chain; the filing disclaims group status. |
| Ramaco / 0001140361-25-011456 | 2 | 3,662,881 | Item 5 identifies Yorktown IX as direct owner and its GP chain as attributed power; a third reporting person has a different signature. |
| SiriusPoint / 0000902219-25-000034 | 3 | 10,694,214 | Items 6–7 describe client-owned securities through a parent/controlled-adviser chain. |
| Celcuity / 0001493215-26-000098 | 2 | 3,039,621 | Item 2 identifies RTW Funds as direct holders and the adviser/managing partner relationship. |
| Commonwealth Credit Partners BDC I / 0001104659-26-086334 | 2 | 632,140.12 | Item 5 identifies three direct-holding plans and the trust/CIO as indirect owners of the same aggregate. |
| Liftoff Mobile / 0002148208-26-000002 | 3 | 9,939,671 | Item 2 identifies the Ellis Trust as direct holder and co-trustees sharing power; retain the pecuniary-interest caveat. |

Three cases remain deliberately unresolved or require special treatment:

- **Korsana Biosciences, 0001738048-26-000069:** nine identical group aggregates of 4,552,277, but Item 5 decomposes exposure across several funds and instruments (preferred shares, pre-funded warrants and options). Preserve the instrument decomposition; do not count nine positions or convert everything to common shares.
- **Vislink Technologies, 0000921895-25-000362:** five repeated rows of 295,415 and a GP/manager chain, but Item 2 expressly preserves non-admission as to beneficial ownership by each reporting person. Do not force a unique owner.
- **Plum Acquisition Corp IV, 0001301396-26-000004:** five repeated rows of 597,999; Item 2 says joint filing but not as a group and includes beneficial-ownership disclaimers. Joint filing alone does not resolve economic overlap.

**Zero control:** Mobiquity Technologies, 0001535610-25-000004, has three repeated rows of zero. It is excluded from positive overlap counts.

These are filing-text measurement judgments, not legal determinations. The exact evidence phrases were checked against each original XML item. The case set is purposive, not a prevalence estimate.

## Binding rules

1. Positive repeated signatures require a complete numeric tuple and aggregate shares strictly greater than zero.
2. All-zero signatures stay in a separate ZERO_POSITION bucket; never count them as positive overlap.
3. Missing/partial/non-numeric values remain unknown, never coerced to zero.
4. A repeated positive signature triggers narrative/exhibit review; it does not itself prove a common underlying holder.
5. Group flags a, b and missing are contextual metadata, not unique group IDs or deduplication keys. Source-supported overlap appears with all three statuses.
6. Joint filing is a filing mechanism, not proof of a unique legal group or separate economic positions.
7. Do not sum attributed reporting-person rows. For group aggregates, preserve underlying funds and instrument types.
8. Keep 13D/13G separate and retain event date, filing date and SEC acceptance datetime separately.

## Reproducibility and decision

Reproducibility files:
- Auditor: [phase227_13dg_overlap_adjudication.py](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase227_13dg_overlap_adjudication.py)
- Tests: [test_phase227_13dg_overlap_adjudication.py](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/test_phase227_13dg_overlap_adjudication.py)
- Result: [phase227_13dg_overlap_adjudication_result.json](https://github.com/jafelix81/NuevaEstrategia/blob/phase99-broad-pit-universe-charter/research/phase227_13dg_overlap_adjudication_result.json)

The standalone auditor rechecks the pinned ZIP/CSV, all 102 raw-submission hashes and expected positive/zero counts. **7/7 local tests passed**, including full-artifact integration and expected-count assertions. No hosted Phase 227 Actions run is claimed; the commits use skip-ci to avoid broad PR workflow fan-out.

No forward returns, alpha test, bootstrap/LOO, final-holdout use, vendor purchase, production change, universe change or F80 change. The case review is not admitted as a predictive feature.

Next gate: extend source-linked adjudication to referenced exhibits/joint-filing agreements and predecessor/current filing chains, then build an effective-dated beneficial-owner/security identity graph. Do not train an automated overlap classifier or run returns until those gates pass.

**F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.** The legacy holdout remains CONSUMED_NOT_PRISTINE.

Official references: [SEC Schedule 13D/G technical specifications](https://www.sec.gov/submit-filings/technical-specifications), [17 CFR 240.13d-101](https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.13d-101), [17 CFR 240.13d-102](https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.13d-102).
