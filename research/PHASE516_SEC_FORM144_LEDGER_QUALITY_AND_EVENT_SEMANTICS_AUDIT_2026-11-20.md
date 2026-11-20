# Phase 516 — SEC Form 144 live-ledger completeness and event-semantics audit (2026-11-20)

## Executive disposition

**The Form 144 detail ledger is structurally complete for the 80 captured accessions, but it contains event types that must not be collapsed into a single “proposed insider selling” signal.** The formal Rule 10b5-1 plan-date field is materially more informative than a keyword search of free-text Remarks. One amendment explicitly terminates a plan and says no further sales will be made; two other filings have approximate sale dates preceding their notice dates and remain in a manual semantic-review queue.

No return test or alpha test was run. All observations remain signal-ineligible. F80 remains frozen.

## 1. Preflight and provenance

- Repository: `jafelix81/NuevaEstrategia`.
- Main HEAD at audit start: `cca5224c0980d6b0765b203ea618a335d9b88510`.
- Latest scheduled Form 144 capture: [Run 44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343).
- Earlier scheduled Form 144 capture contributing to the same ledger: [Run 44614323236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44614323236).
- Current append-only source: `research/data/sec_form144_first_seen/sale_details.csv`.
- The ledger contains 596 detail rows and 80 unique filing headers across 61 issuer CIKs.
- All 596 rows have exact source-XML hash agreement with the original event ledger; zero hash mismatches and zero non-comparable rows.
- All 596 rows parse successfully.

The audit is reproducible from the committed ledger using `research/phase516_form144_ledger_quality_audit.py`.

## 2. Field completeness and economic content

| Section | Rows | Filings represented |
|---|---:|---:|
| Filing headers | 80 | 80 |
| Proposed-sale tranches | 80 | 80 |
| Acquisition lots | 169 | 80 |
| Prior-three-month sales | 267 | 49 |

All 80 proposed-sale rows contain numeric proposed units, aggregate market value, units outstanding, and a parseable approximate sale date. The units/outstanding ratio has:
- Minimum: 0.0000135%.
- 25th percentile: 0.0018879%.
- Median: 0.0074741%.
- 75th percentile: 0.0631935%.
- Maximum: 0.3864266%.

This is a reported proposed amount divided by the reported number of units of the class outstanding. It is **not** a float ratio, not an executed-sale ratio, and not a realized supply shock. Class and denominator semantics still require validation before use as a feature.

Forty-nine filings have prior-three-month sale rows (267 total); 31 carry the “nothing to report” flag. The flag reconciles with the row ledger in all 80 filings. There are 169 acquisition-history rows.

## 3. Rule 10b5-1: formal date field versus Remarks text

The official Form 144 contains a separate field titled “Date of Plan Adoption or Giving of Instruction, if Relying on Rule 10b5-1.” The SEC form itself states that the representation about undisclosed material adverse information is made as of that plan/instruction date when this field is supplied. See [SEC Form 144](https://www.sec.gov/files/form144.pdf).

Observed in this ledger:
- 27/80 filing headers have at least one formal plan-adoption/instruction date.
- 6/80 mention “10b5-1” in free-text Remarks.
- Only 2 filings have both.
- 25 have a formal date without a free-text mention.
- 4 have a free-text mention without a formal date.
- All 27 formal dates precede the notice date; the lag ranges from 72 to 528 days, with a median of 183 days.

**Conclusion:** `mentions_10b5_1_in_remarks` is not an adequate plan classifier. The structured `planAdoptionDate` field is the primary explicit field; Remarks should remain a separate corroborating/semantic field. Neither should be interpreted as proof that a plan was active, unmodified, or still governing the proposed sale without amendment lineage and text review.

The SEC's 2025 Rule 120.01 interpretation also clarifies that adoption of a Rule 10b5-1 plan does not change the Form 144 filing due time: the notice is transmitted concurrently with order placement or execution with a market maker, and the notice is effective for a maximum of three months. See [SEC Exchange Act Rules C&DI, Question 120.01](https://www.sec.gov/files/corpfin/exchange-act-rules-042525-120-1.pdf). This makes the notice, plan date, and actual sale date distinct clocks.

## 4. Past-date proposed-sale rows: semantic review queue

Of 80 proposed-sale rows:
- 77 have an approximate sale date equal to the notice date.
- 3 have an approximate sale date before the notice date.

The three accessions are not automatically discarded:

1. `0001493152-26-053320` — Verano Holdings Corp., Form 144/A. Its Remarks state that it amends an earlier Form 144, the Rule 10b5-1 plan was terminated effective November 18, 2026, 15,100 shares were sold from November 11–17, and no further sales will be made under the plan. This is a **plan-termination / completed-sales amendment**, not a fresh forward-supply event. Its retained Table I proposed-sale row must not be treated as new selling intent.
2. `0001974078-26-000422` — Clean Energy Fuels Corp., Form 144. The approximate sale date is November 10, while the notice date is November 19. No prior accession or explanatory Remarks were captured. Keep in manual review; do not assume a future sale.
3. `0001972649-26-000002` — Eagle Bancorp Montana, Inc., Form 144. The approximate sale date is November 18, while the notice date is November 19. Keep in manual review; do not assume a future sale.

The first case demonstrates why Form 144/A lineage and Remarks must be interpreted before constructing a directional supply feature. The latter two remain unresolved, not silently excluded.

## 5. Point-in-time and collection timing

All 80 filing headers are marked research-observation eligible by the collector, but:
- Public availability certified: 0.
- Signal eligible: 0.
- Same-day intraday use: not authorized.
- First-seen time is a successful-poll upper bound, not an exact public-release timestamp.

First-seen intervals by capture run:
- Run 44662324343: 70 filings; interval 5.6531 hours (lower bound 2026-11-19 21:00:26 UTC, upper bound 2026-11-20 02:39:37 UTC).
- Run 44614323236: 10 filings; interval 18.1647 hours (lower bound 2026-11-19 02:50:33 UTC, upper bound 2026-11-19 21:00:26 UTC).

The wide polling intervals reinforce the need to use the upper bound and enter only at the first supported exchange session strictly after it. The first-seen ledger does not certify the exact SEC public-availability instant.

## 6. Research implications and next gates

A future Form 144 feature panel should keep separate:
- proposed units / reported class units outstanding;
- formal plan-adoption date and plan age;
- prior three-month sales and gross proceeds;
- acquisition lots and acquisition/payment nature;
- amendment lineage and plan termination/cancellation language;
- seller/issuer identity and effective-dated security mapping;
- first-seen interval upper bound and next-executable-session time.

Before any return test:
1. Resolve issuer CIK to the exact traded security/share class and historical F80 membership.
2. Add explicit amendment/termination/cancellation event typing; do not count a 144/A as a new sale event by default.
3. Manually resolve the two unexplained past-date cases and retain a quarantine status until resolved.
4. Validate that units outstanding refer to the same class and do not substitute shares outstanding for float.
5. Use conservative first-seen upper bounds, total-return prices, terminal/delisting outcomes, identical exposure and costs.
6. Test incremental information against frozen LTM/F80 chronologically, then use block bootstrap and leave-one-event/issuer-out checks.

No backtest, event study, OOS, bootstrap, LOO, or holdout test was run in this phase.

## 7. Strategy controls

- New Smart Money signals admitted: 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: frozen.
- Universe, parameters, exposure, costs, holding-period rules, holdout, and production: unchanged.
