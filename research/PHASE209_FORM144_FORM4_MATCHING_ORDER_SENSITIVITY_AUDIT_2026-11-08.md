# Phase 209 — Form 144/Form 4 exact-first matching-order sensitivity audit

**Date:** 2026-11-08  
**Disposition:** material linkage-method correction; descriptive linkage only. Strict PIT, feature admission and alpha remain **NOT ADMITTED**.

## Executive result

A fresh offline reprocessing of the same immutable Phase 69 Form 144 and Phase 39 Form 4 artifacts found that the Phase 208 broad-window uniqueness rule discarded exact date-and-share links because of weaker alternative candidates one or two days away.

The exact-link graph contains **521 edges**, each connecting a distinct Form 144 tranche to a distinct Form 4 accession/date block. There are **zero collisions within the exact graph**. Phase 208 retained only 394 of those exact links after applying uniqueness across every 0–2 calendar-day candidate first. Thus **127 exact links (24.4% of the exact graph) were rejected solely because of weaker near-date alternatives**.

A conservative hierarchical rule that reserves mutually unique exact date-and-share edges first, quarantines any ambiguous exact component, and only then matches remaining nodes in the 0–2 day window produces:

- **521** exact date-and-share links (35.91% of 1,451 eligible notices);
- **49** additional mutually unique fallback links;
- **570** total provisional one-to-one links (39.28% of eligible notices).

This corrects the Phase 208 linkage count. It does not prove that all linked notices became exchange executions: Form 144 is a proposed-sale notice, and Form 4 code S includes open-market or private dispositions.

## 1. Immutable inputs and independent reproduction

| Input | Source |
|---|---|
| Form 144 panel | Phase 69 run 41959603351, artifact 13385365595 |
| Form 144 expanded CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Form 4 Q3 2026 dataset | Phase 39 run 40606706518, artifact 12781850078 |
| Form 4 Q3 inner ZIP SHA-256 | a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3 |

Both hashes match the immutable values recorded in Phase 208. No new SEC request, raw-data purchase or vendor contact was made.

The sample reproduces 21,634 Form 144 panel rows, 1,487 original 2026 Q3 notices, 1,451 notices with a complete observable follow-up window, 1,460 eligible tranches, 38,152 Form 4 submissions, 59,885 non-derivative transaction rows and 10,525 unique-owner sale blocks.

## 2. Why the Phase 208 rule undercounted exact links

Phase 208 first built all candidate pairs in the 0–2 calendar-day window, then retained a pair only when its tranche and Form 4 block each had degree one in that entire broad candidate graph.

That rule is conservative, but it treats a weaker nearby-date candidate as equally capable of invalidating an exact date-and-share match.

| Broad-window collision pattern among the 521 exact edges | Exact edges |
|---|---:|
| Tranche unique; Form 4 block unique | 394 |
| Tranche collision only | 52 |
| Form 4 block collision only | 55 |
| Both tranche and Form 4 block collide | 20 |
| **Total exact edges** | **521** |

The 127 rejected exact edges were not ambiguous relative to other exact edges. They were rejected because at least one endpoint also had a different candidate within the wider date window.

## 3. Exact-edge graph and revised hierarchical linkage

The exact graph requires the same issuer CIK, exact normalized seller/sole reporting-owner name, same calendar date, and exact equality between aggregated Form 4 shares and proposed Form 144 tranche units.

| Measure | Result |
|---|---:|
| Exact edges | 521 |
| Distinct Form 144 tranches | 521 |
| Distinct Form 4 accession/date blocks | 521 |
| Ambiguous exact tranches | 0 |
| Ambiguous exact Form 4 blocks | 0 |
| Mutually unique exact edges | **521** |
| Exact edges agreeing on coarse security-class family | 481 / 521 (92.32%) |
| Class conflict or unresolved | 40 |

The hierarchical fallback reserves all endpoints that participate in an exact edge. Ambiguous exact components, if any, are quarantined rather than re-matched through a weaker edge. Remaining unmatched endpoints are then tested for unique 0–2 day candidates.

| Link tier | Links |
|---|---:|
| Exact date and exact shares | 521 |
| Same date, quantity not exact | 31 |
| One day after approximate sale date | 16 |
| Two days after approximate sale date | 2 |
| **Total** | **570** |

The 49 fallback links are lower-confidence than the 521 exact links and must remain separately labelled.

## 4. Window sensitivity

The original broad-window uniqueness rule is sensitive to the candidate window:

| Candidate window | Candidate pairs | Mutually unique pairs | Exact date-and-share pairs retained |
|---|---:|---:|---:|
| Same day | 577 | 556 | 519 |
| 0–1 days | 659 | 465 | 419 |
| 0–2 days | 695 | 441 | 394 |
| 0–3 days | 732 | 413 | 368 |
| 0–4 days | 765 | 396 | 355 |
| -1 day | 60 | 60 | 0 |
| -2 to -1 days | 92 | 53 | 0 |

The non-monotonic decline in retained exact matches as the window widens is a matching-algorithm artifact, not evidence that fewer exact transactions occurred. The pre-notice 53 links remain a descriptive negative-timing diagnostic, not a randomized placebo.

## 5. Interpretation and limitations

- The revised 570 figure is a **provisional document-linkage count**, not a verified execution-conversion rate.
- The 521 exact date/share links are stronger than date-only links, but the Form 144 approximate sale date is not an execution timestamp.
- Form 4 code S covers open-market or private sales. Venue and exchange execution are not established.
- The 40 class-family conflicts/unresolved links remain quarantined from security-level inference.
- Seller-name equality can miss trusts, entities, aliases, joint owners and name changes.
- The panel is one quarter for the Form 4 side; it is not a survivorship-free historical universe.
- Filing date is date-only. EDGAR acceptance/first-public-availability timestamps and immutable cross-quarter vintages remain unresolved.

## 6. Decision and next gates

**Correct the linkage order in any future Form 144/Form 4 pipeline:** exact date-and-share links first; quarantine ambiguous exact components; then evaluate lower-confidence date-window fallbacks. Preserve the exact and fallback tiers separately.

Do not run forward-return or alpha tests until the adjacent-quarter Form 4 datasets and Form 144 vintages can be retrieved, EDGAR acceptance timestamps are joined, amendments are reconstructed, and an effective-dated security-class crosswalk resolves the 40 exact-link class conflicts.

Phase 153 remains blocked because the repository secret SEC_CONTACT_EMAIL is absent. Its latest preflight made zero SEC requests and downloaded zero adjacent-quarter bytes. An authorized contact email must be configured in GitHub Actions before manually dispatching that workflow.

No forward-return, alpha, bootstrap/LOO, OOS or holdout test was run. The legacy holdout remains CONSUMED_NOT_PRISTINE. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no production or universe change was made.

## Reproducibility

- Code: research/phase209_form144_form4_exact_first_matching_audit.py
- Tests: research/test_phase209_form144_form4_exact_first_matching_audit.py
- Result: research/phase209_form144_form4_exact_first_matching_audit_result.json
- Workflow: .github/workflows/phase209_form144_form4_exact_first_matching_audit.yml
- Inputs are downloaded by immutable run/artifact IDs; the workflow makes no SEC requests.
