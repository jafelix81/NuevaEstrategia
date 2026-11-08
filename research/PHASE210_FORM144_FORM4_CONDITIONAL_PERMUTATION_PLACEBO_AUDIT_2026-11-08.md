# Phase 210 — Form 144/Form 4 conditional permutation placebo audit

**Date:** 2026-11-08  
**Disposition:** exact-link alignment is materially stronger than conditional placebo assignments; descriptive linkage only. Strict PIT, feature admission and alpha remain **NOT ADMITTED**.

## Executive result

Using the same immutable Phase 69 Form 144 panel and Phase 39 Form 4 Q3 2026 artifact as Phases 208–209, the exact-first graph contains **521 mutually unique exact-date/exact-share links**. The graph has 521 distinct Form 144 tranches, 521 distinct Form 4 owner/date blocks, and no ambiguous exact endpoints.

A conditional permutation audit tested whether the alignment could be reproduced by reassigning reporting-owner identities within issuer, or by shuffling transaction dates and share quantities within issuer-owner groups. Across 500 deterministic permutations per null, **no replicate reached the observed mutable-link count**.

This supports the integrity of the document linkage under these specific conditional placebos. It is not evidence of predictive returns, informed trading or economic alpha.

## 1. Immutable inputs and sample

| Input | Source |
|---|---|
| Form 144 expanded CSV | Phase 69 run 41959603351, artifact 13385365595 |
| Form 144 CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 Q3 2026 inner ZIP | Phase 39 run 40606706518, artifact 12781850078 |
| Form 4 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

The audited sample contains 21,634 Form 144 panel rows, 1,451 eligible Q3 2026 notices, 1,460 proposed-sale tranches, 38,152 Form 4 submissions, 59,885 non-derivative transaction rows and 10,525 unique-owner sale blocks.

No new SEC requests were made. No raw rows, owner names or ticker-level records are persisted in the Phase 210 result.

## 2. Exact-link and security-class diagnostics

The exact graph requires issuer CIK, normalized seller/sole reporting-owner name, exact proposed-sale/transaction calendar date and exact equality between proposed units and aggregated Form 4 shares.

| Measure | Result |
|---|---:|
| Exact graph edges | 521 |
| Mutually unique exact edges | 521 |
| Ambiguous tranches | 0 |
| Ambiguous Form 4 blocks | 0 |
| Same broad class family | 481 (92.32%) |
| Exact normalized class text equality | 52 (9.98%) |
| Same family, different normalized text | 429 |
| Class-family conflict or unresolved | 40 (7.68%) |
| Additional mutually unique 0–2 day fallback links | 49 |
| Total hierarchical links | 570 |

The 481 class-family agreements are not CUSIP-level security identity. The Form 144 notice and Form 4 security title can describe the same broad family using different text, such as COMMON versus COMMONSTOCK. Conversely, a generic COMMON description paired with a specific CLASS_A title is not proof of the same class. The 40 conflicts/unknowns remain unresolved, and the absence of CUSIP in the Form 144 event panel prevents a definitive security-level join.

## 3. Conditional permutation design

All permutations preserve the issuer, the Form 144 sample, the number of Form 4 blocks and the marginal values being shuffled. The count is recomputed as a mutually unique exact-date/exact-share graph, then restricted to blocks whose corresponding dimension was actually permutable.

- **Owner-identity null:** shuffle Form 4 owner labels among blocks within each issuer that has more than one distinct reporting owner. There are 8,956 mutable blocks across 1,195 such issuer groups. The 46 exact links in single-owner issuer groups are excluded from this null's observed count.
- **Date null:** shuffle Form 4 transaction dates among blocks within the same issuer-owner group when that group has at least two blocks. There are 7,216 mutable blocks across 1,967 multi-block groups. The 181 exact links in singleton issuer-owner groups are excluded.
- **Share-quantity null:** independently shuffle transaction share quantities within the same issuer-owner groups.
- **Joint null:** independently shuffle both transaction dates and share quantities within issuer-owner groups.

Each null uses 500 permutations and a fixed seed. The empirical plus-one tail frequency has a minimum resolution of 1/501 = 0.001996; it must not be interpreted as a return-alpha p-value.

## 4. Results

| Conditional null | Observed mutable exact links | Null mean | Null p95 | Null max | Replicates at/above observed |
|---|---:|---:|---:|---:|---:|
| Owner identity within issuer | 475 | 156.606 | 171 | 183 | 0/500 |
| Date within issuer-owner | 340 | 194.352 | 208 | 218 | 0/500 |
| Shares within issuer-owner | 340 | 194.962 | 208 | 223 | 0/500 |
| Date and shares within issuer-owner | 340 | 195.284 | 209 | 218 | 0/500 |

The observed mutable-link counts are 3.03×, 1.75×, 1.74× and 1.74× their respective null means. The alignment is therefore not reproduced by these simple owner/date/quantity reassignment placebos.

## 5. Interpretation and limitations

This is a **linkage-validity diagnostic**, not an event-study result.

- Form 144 reports a proposed sale and does not prove that the sale was completed.
- Form 4 code S can represent open-market or private dispositions; this sample does not establish that all linked transactions were exchange executions.
- The comparison is one Q3 2026 Form 4 sample, not a multi-quarter replication or an out-of-sample investment test.
- The conditional permutations are not a universal model of random matching. Repeated owners, issuer-specific transaction patterns, clustered events and common reporting conventions can affect exchangeability.
- Exact date and quantity agreement does not establish first public availability. Accession acceptance/first-receipt timestamps remain unresolved.
- Broad class-family agreement does not replace an effective-dated security identifier or corporate-action crosswalk.

**Decision:** retain the exact-first cross-document linkage as a stronger descriptive data-quality result. Do not admit Form 144 as a PIT feature, do not run a return/alpha test, and do not use the consumed historical holdout.

## 6. Next gates

1. Reconstruct EDGAR acceptance and conservative first-public-availability time for each Form 144 and Form 4 accession.
2. Extend the same linkage rules to additional Form 4 quarters without changing thresholds after seeing outcomes.
3. Resolve the 40 class-family conflicts and improve security identity for the 429 family-only text differences using source evidence, not fuzzy matching alone.
4. Distinguish open-market from private dispositions and reconcile Form 4/A parent lineages.
5. Only after strict PIT and security identity admission, preregister a next-session supply-pressure study with return-chasing controls, costs, capacity and a new prospective final holdout.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No production change, data purchase, vendor contact, holdout use or alpha test occurred.
