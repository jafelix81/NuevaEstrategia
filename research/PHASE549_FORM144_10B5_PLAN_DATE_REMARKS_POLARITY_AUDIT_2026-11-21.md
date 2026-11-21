# Phase 549 — SEC Form 144 Rule 10b5-1 plan-date and Remarks-polarity audit

**Audit cutoff:** 2026-11-21 18:24 UTC  
**Base main HEAD:** 9624d7a5404d339e83aeca72c9adc5cd47994ca8  
**Disposition:** the structured Form 144 plan-adoption field is the primary positive declaration of Rule 10b5-1 reliance; a free-text keyword-presence flag is not a polarity classifier. Four same-issuer Form 144 notices explicitly say the sales are **not** made under a Rule 10b5-1 plan and describe automatic sell-to-cover for tax withholding. They are a useful negative control, not discretionary insider selling. No alpha or return test.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs, in-progress/queued filters, jobs, logs, artifacts, main research files, 368 branches and 70 open PRs.
- Latest 100 run outcomes: **88 success, 11 failure, 1 cancelled**. No in-progress or queued runs at the audit cutoff. No existing workflow was dispatched, rerun, cancelled or duplicated.
- Latest natural SEC Form 144 capture: [44927447674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44927447674), started 2026-11-21 16:58:30 UTC. Offline regression passed **64/64**; live capture completed successfully. Artifact [14715874942](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44927447674/artifacts/14715874942) was downloaded and inspected.
- Both Form 144 feeds completed pagination and found the prior latest accession. There were 53 feed observations, zero new accessions, zero feed errors and possible_feed_window_gap=false. The bounded detail backfill parsed 10 accessions and appended 39 rows with zero parse errors and zero hash mismatches. Ledger: **245 accessions / 1,751 detail rows**; 318 accessions remain. Public availability is not certified; same-day use is unauthorized; signal-eligible count is zero.
- The successful poll's first-seen interval is bounded by the previous successful poll start (08:50:22 UTC) and receipt at 16:58:30 UTC. It is not an exact public-release timestamp. The next hourly slot, 17:47 UTC, was absent from the Actions run list at the 18:24 UTC cutoff. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) was updated; no manual poll or cron change was made.
- FINRA [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) predates the Phase 539 merge. Its artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921) confirms 8 HTTP-200 files, 8 invalid, 0 valid and 0 eligible. Phase 539's merged diagnostic identifies duplicate_symbol_in_consolidated_file as the rejection reason. The workflow is scheduled at 22:30 and 23:30 UTC on weekdays, so the next natural post-merge validation is a later weekday capture; no manual dispatch.
- CFTC TFF [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977), artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870), recorded four newly received prospective reports (report date 2026-11-17; first received 2026-11-21 03:17:36 UTC). The archive has 3,043 rows, but historical rows remain PIT-ineligible.
- Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134), artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646), retains three descriptive Form 144/Form 4 crosswalk rows (two proposed-sale matches and one prior-sale-history match), with zero signal-eligible matches. PRs #200 and #201 remain Draft; neither was merged.

## 2. Current Form 144 ledger: accession-grain results

Source: research/data/sec_form144_first_seen/sale_details.csv at main 9624d7a5404d339e83aeca72c9adc5cd47994ca8 (Git blob b6cd40234df037c30dd7e124f4b7d3bce59126c7). The parser extracts planAdoptionDate from the Form 144 noticeSignature node and stores it as plan_adoption_dates_json. That field is repeated across detail rows, so counts below are grouped by accession, not by detail row.

| Measure | Result |
|---|---:|
| Detail rows | 1,751 |
| Unique accessions | 245 |
| Form 144 / Form 144-A | 243 / 2 |
| Accessions with a formal plan-adoption date | **85** (84 Form 144, 1 Form 144-A) |
| Distinct plan-adoption dates | 53 |
| Formal plan dates before / same as / after notice date | **85 / 0 / 0** |
| Plan-to-notice lag, days | min 72; p25 97; median 185; p75 263; max 546 |
| Raw Remarks keyword-mention flag | 10 accessions |

The 85/245 (34.69%) figure describes this bounded, newest-first ledger only; it is not a population prevalence estimate. The 85 plan dates are one per accession in this snapshot. The lag quantiles use the lower-index order statistic floor((n-1)*p).

### Remarks polarity, not keyword presence

The current parser's mentions_10b5_1_in_remarks is a raw presence flag (regex 10b5[\\s-]*1). It intentionally does not parse negation. Reclassification of the 10 unique accessions with a mention gives:

| Accession-level Remarks class | Count |
|---|---:|
| Explicit positive reliance language | 5 |
| Explicit negative / not pursuant language | 4 |
| Ambiguous mention | 1 |
| No mention | 235 |

Cross-tabulation:

- Formal plan date + positive Remarks: 5.
- Formal plan date + ambiguous Remarks: 1.
- Formal plan date + no Remarks mention: 79.
- No formal plan date + explicit negative Remarks: 4.
- Neither formal date nor mention: 156.

The four negative cases are all Form 144 notices for **Fermi Inc. (CIK 0002071778)**, all with notice/approximate sale date 2026-11-19. Each says the proposed sale is an automatic sell-to-cover to satisfy tax withholding and explicitly says it is **not** being made pursuant to a Rule 10b5-1 plan. Their proposed units sum to **2,253,270 shares**; this is a sum of proposed notice amounts, not verified executed volume. The four accessions are:

- 0001213900-26-122355 — Charles Lynn Hamilton, 761,629 proposed shares.
- 0001213900-26-122358 — Jacobo Ortiz Blanes, 847,810.
- 0001213900-26-122359 — Lee A. McIntire, 20,544.
- 0001213900-26-122362 — George R. Wentz, Jr., 623,287.

The first filing's official [SEC filing-detail page](https://www.sec.gov/Archives/edgar/data/2071778/000121390026122355/0001213900-26-122355-index.htm) confirms Form 144, Fermi Inc., filing date 2026-11-19 and acceptance at 21:17:03 ET. All four records share a first-seen upper bound of 2026-11-20 02:39:27 UTC. The notices are not evidence that all proposed shares actually traded.

This is a concrete false-positive control: a boolean keyword detector marks all four as “mentions 10b5-1,” even though the remarks expressly negate reliance. A separate positive/negative/ambiguous polarity field is required; the append-only source flag should not be overwritten.

### Amendment control

One of the two Form 144/A accessions with a formal plan date is Verano Holdings (0001493152-26-053320). Its remarks say the plan adopted 2026-08-11 was terminated effective 2026-11-18 and that no further sales will be made under it. Preserve the plan history, but classify this amendment as a **plan termination / completed-sales notice**, not a new forward-sale signal.

## 3. Regulatory meaning and PIT consequence

The SEC's current [electronic Form 144 guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically) says that, if securities are sold in reliance on Rule 10b5-1, the filer should indicate the date of adoption of the relevant plan(s). That structured date is stronger positive evidence of declared reliance than a bare text mention. It still does not establish that the plan remained active, unmodified or un-terminated at every later date; amendments and remarks must be reconciled.

The SEC's [Exchange Act Rules C&DI 120.01](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-rules) says adoption of the plan does not change Form 144's due time: the notice is transmitted concurrently with placement of a sell order for a brokerage transaction or execution directly with a market maker. Consequently:

1. The plan-adoption date is a historical classification/context date, **not** the signal-availability timestamp.
2. A Form 144 is a proposed-sale/order-placement or execution notice, not proof of completed execution and not necessarily a long-lead warning.
3. The approximate sale date and notice date do not reveal an intraday execution timestamp.
4. Use the conservative first-seen interval upper bound and the next supported full exchange session; do not backdate to the plan date or transaction/approximate-sale date.

### Form 4 cross-check and grain

The current bounded Form 4 detail ledger has 110 rows across 40 accessions. Grouping the filing-level AFF10B5ONE field by accession yields **3 checked and 37 unchecked filings**. Counting repeated transaction rows would incorrectly inflate the checked count to 20 rows. The field is submission-level, not transaction-row-level. SEC C&DI 135.04 also says the Form 4 checkbox does not apply to plans adopted before the amendments' effective date; unchecked is not a general proof of discretionary trading. The current bounded Form 144 and Form 4 owner ledgers have no exact issuer-CIK plus filer-CIK/owner-CIK pair overlap, so no direct cross-form validation is claimed.

## 4. Reproducibility and validation

Added a standalone offline audit script, accession-grain polarity classifier and six unit tests. The initial audit run [44936177659](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44936177659) passed all six new tests and generated artifact [14719697917](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44936177659/artifacts/14719697917). The subsequent existing Phase 403 PR regression [44936297763](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44936297763) passed **70/70 tests**, including all six Phase 549 tests, and generated aggregate artifact [14720010278](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44936297763/artifacts/14720010278). Its live-capture job was skipped as designed for a pull-request event. To avoid a duplicate Form 144 workflow, the branch extends the existing Phase 403 offline-regression path; no live collector or schedule was changed.

The classifier preserves four states: POSITIVE_EXPLICIT, NEGATIVE_EXPLICIT, AMBIGUOUS_MENTION, and NO_MENTION. It separately records formal plan-date presence, plan termination and sell-to-cover/tax context. It never upgrades a row to signal eligibility.

## 5. Decision

- Form 144 plan-date field: retain as an explicit plan-reliance context/exclusion control, subject to amendment/termination state.
- Remarks keyword flag: retain only as raw text-presence metadata; do not interpret it directionally.
- Fermi four-filer cluster: negative control for naive insider-sale clustering; not a bearish signal.
- Form 144/A plan termination: not a new forward-sale event.
- New signals admitted: **0**.
- New backtests / event studies / OOS / bootstrap / LOO: **0**.
- No data acquisition, no live poll, no changes to costs, exposure, universe, holdout or production.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.
