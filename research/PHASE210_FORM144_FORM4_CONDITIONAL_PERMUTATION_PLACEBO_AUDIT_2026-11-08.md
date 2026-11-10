# Phase 210 — Form 144/Form 4 linkage validation: conditional placebos and price concordance

**Date:** 2026-11-08  
**Disposition:** cross-document linkage is strongly corroborated in this Q3 2026 sample; descriptive only. Strict PIT, feature admission and alpha remain **NOT ADMITTED**.

## Executive result

Using the same immutable Phase 69 Form 144 panel and Phase 39 Form 4 Q3 2026 artifact as Phases 208–209, the exact-first graph contains **521 mutually unique exact-date/exact-share links**. All 521 have a Form 4 weighted-average execution price and a Form 144 implied price (aggregate market value divided by proposed units). Every exact link is within 5% on price; 503/521 are within 1%.

A conditional permutation audit also tested owner, date, share-quantity and price alignment. Across 500 deterministic permutations per null, no replicate reached the observed mutable-link count.

This is meaningful evidence that the documents refer to the same underlying sale events in this sample. It is not evidence that the events predict future stock returns, identify institutional beneficial owners or create economic alpha.

## 1. Immutable inputs and sample

| Input | Source |
|---|---|
| Form 144 expanded CSV | Phase 69 run 41959603351, artifact 13385365595 |
| Form 144 CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 Q3 2026 inner ZIP | Phase 39 run 40606706518, artifact 12781850078 |
| Form 4 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

The sample contains 21,634 Form 144 panel rows, 1,451 eligible Q3 2026 notices, 1,460 proposed-sale tranches, 38,152 Form 4 submissions, 59,885 non-derivative transaction rows and 10,525 unique-owner sale blocks. No new SEC requests were made.

## 2. Exact-link and security-class diagnostics

The exact graph requires issuer CIK, normalized seller/sole reporting-owner name, exact proposed-sale/transaction calendar date and exact equality between proposed units and aggregated Form 4 shares.

| Measure | Result |
|---|---:|
| Exact graph edges / mutually unique edges | 521 / 521 |
| Ambiguous tranches / Form 4 blocks | 0 / 0 |
| Same broad class family | 481 (92.32%) |
| Exact normalized class text equality | 52 (9.98%) |
| Same family, different normalized text | 429 |
| Class-family conflict or unresolved | 40 (7.68%) |
| Additional mutually unique 0–2 day fallback links | 49 |
| Total hierarchical links | 570 |

The 481 family agreements are not CUSIP-level identity. Descriptions such as COMMON and COMMONSTOCK can map to the same broad family, while generic COMMON paired with specific CLASS_A is not proof of the same class. The 40 conflicts/unknowns remain unresolved. Form 144 has no CUSIP in this event panel.

## 3. Cross-document price and plan-field concordance

For each exact link, Form 144 implied price is aggregate market value divided by proposed units. Form 4 price is the shares-weighted average of TRANS_PRICEPERSHARE across eligible non-derivative S/D transaction rows in the linked owner/date block.

| Exact-link price check | Result |
|---|---:|
| Links with both prices | 521 / 521 |
| Links with all Form 4 shares priced | 521 / 521 |
| Within 1% absolute relative price difference | 503 / 521 |
| Within 2.5% | 517 / 521 |
| Within 5% | 521 / 521 |
| Median absolute relative difference | 0.000295% |
| 90th percentile | 0.057979% |
| 95th percentile | 0.584595% |
| Maximum | 3.788235% |

Among the 481 family-compatible links, 481/481 are within 5%. Among the 40 class-family conflicts/unknowns, 40/40 are also within 5%; this corroborates the same economic event but does not resolve the legal security class.

The 49 lower-confidence fallback links also have price observations: 44/49 are within 5%, 48/49 within 10%, and 49/49 within 20%. Their actual/proposed share ratio is much less stable (median 0.823; p10 0.199; p90 1.024; range 0.046–2.995), so they remain a separate provisional tier and are not counted as exact conversions.

The 10b5-1 field cross-check is concordant in 512/521 exact links (98.27%): 323 plan-date-present/Form 4 true, 189 no-plan-date/Form 4 false, with 9 discordant cases (2 and 7 in the opposite cells). This is a document-field consistency check, not evidence of discretionary intent.

## 4. Conditional permutation design and results

All permutations preserve issuer, the Form 144 sample, the number of Form 4 blocks and the marginal values being shuffled. Each count is recomputed as a mutually unique exact-date/exact-share graph and restricted to blocks whose dimension was actually permutable.

- Owner-identity null: shuffle Form 4 owner labels within issuer groups with more than one distinct owner (8,956 mutable blocks; 1,195 issuer groups). The 46 exact links in single-owner issuer groups are excluded.
- Date null: shuffle transaction dates within issuer-owner groups with at least two Form 4 blocks (7,216 mutable blocks; 1,967 groups). The 181 exact links in singleton owner groups are excluded.
- Share null: independently shuffle share quantities within the same issuer-owner groups.
- Joint null: independently shuffle both dates and shares within issuer-owner groups.
- Price null: shuffle weighted-average Form 4 prices within issuer-owner groups while keeping the exact-link graph fixed; count mutable exact links whose shuffled price remains within 5% of the Form 144 implied price.

| Conditional null | Observed mutable links | Null mean | Null p95 | Null max | At/above observed |
|---|---:|---:|---:|---:|---:|
| Owner identity within issuer | 475 | 156.606 | 171 | 183 | 0/500 |
| Date within issuer-owner | 340 | 194.352 | 208 | 218 | 0/500 |
| Shares within issuer-owner | 340 | 194.962 | 208 | 223 | 0/500 |
| Date and shares within issuer-owner | 340 | 195.284 | 209 | 218 | 0/500 |
| Price within issuer-owner | 340 | 214.982 | 228 | 240 | 0/500 |

The empirical plus-one tail frequency is 1/501 = 0.001996 for each null because no replicate reached the observed count. This is the Monte Carlo resolution of these linkage placebos, not a return-alpha p-value.

## 5. Interpretation and limitations

This phase validates document linkage, not investment predictability.

- Form 144 reports a proposed sale and does not prove that the sale was completed.
- Form 4 code S can represent open-market or private dispositions; the sample does not establish that all linked transactions were exchange executions.
- The price check is cross-document, not an independent market-data source. The Form 144 aggregate market value is an estimate and may be based on the same transaction context.
- The sample uses one Q3 2026 Form 4 quarter. Multi-quarter replication is still required.
- The conditional permutations are not a universal model of random matching; repeated owners, issuer-specific event patterns and clustered transactions can affect exchangeability.
- Acceptance/first-public-availability timestamps remain unresolved.
- Broad class-family agreement does not replace effective-dated security identity or a corporate-action crosswalk.

**Decision:** retain the exact-first cross-document linkage as a strong descriptive data-quality result. Keep the 49 fallback links separate. Do not admit Form 144 as a PIT feature and do not run a return/alpha test.

## 6. Next gates

1. Reconstruct EDGAR acceptance and conservative first-public-availability time for each Form 144 and Form 4 accession.
2. Extend the same matching and price rules to additional Form 4 quarters without changing thresholds after seeing outcomes.
3. Resolve the 40 class-family conflicts and the 429 family-only text differences using source evidence, not fuzzy matching alone.
4. Distinguish open-market from private dispositions and reconcile Form 4/A parent lineages.
5. Only after strict PIT and security identity admission, preregister a next-session supply-pressure study with return-chasing controls, costs, capacity and a new prospective final holdout.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production change, data purchase, vendor contact, holdout use or alpha test occurred.


## Superseding Phase 256 correction (2026-11-10)
The Phase 210 raw transaction-date and joint date/share permutation nulls are superseded for conditional date inference. Phase 256 showed that raw-date shuffling while holding Form 4 filing dates fixed moves an average 40.35% of blocks outside the original 0–4 calendar-day filing-lag eligibility filter. Use the Phase 256 lag-preserving nulls instead: shuffle filing lag within issuer × reporting-owner groups, keep filing dates fixed and reconstruct transaction dates. The observed exact-link result remains above every corrected 1,000-replicate null, but this is document linkage only, not return alpha. Phase 210 owner-identity and shares-only nulls remain descriptive; see the Phase 256 report and result JSON for corrected metrics.
