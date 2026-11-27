# Phase 664 — Form 144 plan-date denominator and PIT-scope correction

**Audit cutoff:** 2026-11-27 14:26 UTC  
**Source run:** [Phase 403 run 46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465) — both jobs successful  
**Artifacts:** [poll audit 15206147627](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465/artifacts/15206147627) · [post-capture 10b5 audit 15205892828](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465/artifacts/15205892828)  
**Disposition:** correct a mislabeled denominator; preserve the descriptive 10b5-1 results; do not infer PIT overlap or promote a signal.

## 1. Latest Form 144 capture

The scheduled poll completed with no new accessions and no feed-window gap.

- 53 feed-observation rows were appended across the two Form 144 feeds; no new feed entries or economic events were recorded.
- The structured ledger contained 855 accessions and 5,651 detail rows.
- A bounded backfill parsed 10 previously known accessions and appended 56 detail rows; 148 accessions remained in the detail-backfill queue.
- Source-hash reconciliation: 5,651 matches, zero mismatches and zero non-comparable rows.
- The Phase 516 ledger audit classified 807 filing headers as research-observation eligible and 48 initial-baseline headers as having no lower bound.
- Public-availability-certified filing headers: 0. Signal-eligible filing headers: 0.
- The first-seen interval remains a poll-receipt upper bound, not an exact public-receipt timestamp.

The poll is an operational/data-quality success, not a new event or signal sample.

## 2. Denominator defect

The prior Phase 549 output reported:

- Formal plan-adoption-date accessions: **322**.
- All structured-ledger accessions: **855**.
- Reported percentage: **37.66%**.
- Field name: `formal_plan_date_pct_of_bounded_accessions`.

The implementation divided 322 by all 855 accessions. That denominator includes 48 initial-baseline accessions with no bounded first-seen interval. Therefore the value is **37.66% of all structured-ledger accessions**, not 37.66% of bounded/PIT-eligible accessions.

There are 807 research-observation-eligible accessions, but the Phase 516 summary supplies aggregate PIT counts, not an accession-level join to the plan-date rows. It is not valid to divide 322 by 807: the intersection is unknown. The corrected output renames the metric to `formal_plan_date_pct_of_all_accessions`, states its denominator scope, and reports PIT counts separately while explicitly leaving the plan-date/PIT overlap null.

## 3. Descriptive 10b5-1 context retained

The post-capture Phase 549 artifact reports:

| Measure | Count |
|---|---:|
| Formal plan-adoption date present | 322 |
| Distinct plan-adoption dates | 134 |
| Explicit positive 10b5-1 remarks | 24 |
| Explicit negative remarks | 4 |
| Ambiguous mentions | 3 |
| No remarks mention | 824 |
| Sell-to-cover plus tax-withholding context | 21 |

The plan-date/remarks cross-tab is internally consistent: 24 formal-date/positive, 3 formal-date/ambiguous, 295 formal-date/no-mention, 4 no-date/negative and 529 no-date/no-mention.

Across 322 filings with formal dates, the notice-minus-plan-date lag has median 181 days, p25 97, p75 272 and maximum 1,687 days; 321 dates precede the notice, one equals it and none follows it. These dates are descriptive filing content, not signal-availability timestamps.

### Negative control

Four explicit negative sell-to-cover/tax-withholding notices cluster on Fermi Inc. (CIK 0002071778), notice date 2026-11-19, with 2,253,270 proposed units in aggregate. All four lack a formal plan-adoption date and explicitly state that the sale is not pursuant to a Rule 10b5-1 plan. They are a useful mechanical-sale negative control, not evidence of discretionary insider selling.

Form 144 is a proposed-sale notice, not execution confirmation. A formal plan date or a remarks mention does not prove that a sale occurred, nor when the information became public.

## 4. Code and validation change

Phase 549 now:
- renames the percentage field to `formal_plan_date_pct_of_all_accessions`;
- labels the denominator as all structured-ledger accessions, not PIT-filtered;
- accepts the Phase 516 PIT summary and checks that its filing count reconciles to the Form 144 ledger;
- reports baseline, research-observation, public-availability and signal-eligibility counts separately;
- sets plan-date/PIT overlap to null with status `NOT_COMPUTED_NO_ACCESSION_LEVEL_PIT_JOIN` rather than fabricating an intersection.

The Phase 403 workflow passes the Phase 516 summary to Phase 549 in both offline and post-capture paths. Its pull-request job is offline-only; the live-capture job remains excluded for pull-request events.

## 5. Research decision and controls

- Keep formal plan dates as descriptive context only.
- Keep remarks polarity as a separate classifier; a raw mention flag is not polarity.
- Keep sell-to-cover/tax-withholding cases as mechanical-sale negative controls.
- Do not compute the plan-date percentage over the 807 PIT-eligible accessions until an accession-level eligibility join exists.
- No returns, event study, alpha, chronological OOS, bootstrap, LOO or holdout test was run.
- No production, universe, capital, exposure or parameter change.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No vendor contact or data purchase; budget remains USD 0.

**Next gate:** preserve accession-level PIT status alongside the Form 144 detail ledger, then compute the exact plan-date/PIT intersection. Even after that join, a Form 144 notice remains a proposed sale, and no signal is admitted without a separate execution/availability and incremental-OOS test.
