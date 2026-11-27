# Phase 666 — SEC 13F-HR/A amendment-burst and point-in-time audit

**Audit cutoff:** 2026-11-27 16:36 UTC  
**Base:** `main` at `6919a03ca2da8da4b6a428c29e088531cba300f9`  
**Branch:** `phase666-sec-13f-amendment-burst-pit-audit`  
**Disposition:** PASS for feed reconciliation; **metadata-only / no research or signal eligibility**. This is a filing-vintage and source-identity audit, not an alpha test.

## 1. Preflight

- Reviewed the latest 30 Actions runs, open PRs, branches, relevant job logs, artifacts, and current research ledgers before analysis.
- No queued, in-progress, waiting, requested, or pending run was present in the latest 30.
- Latest SEC 13F first-seen capture: [run 46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554). Both `offline-regression` and `live-capture` succeeded; artifact [15212890251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554/artifacts/15212890251) (873 bytes).
- The live capture committed the append-only ledgers at main HEAD above. All four feed polls completed successfully.
- The most recent Form 144 live capture was [run 46015828465](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46015828465); later Phase 665 PR checks [46025579803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025579803) and [46025629671](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46025629671) passed offline and skipped live capture. No duplicate capture was started.

## 2. SEC 13F first-seen cohort

Run 46026323554 recorded 44 accession observations across the feeds: 18 `13F-HR`, 24 `13F-HR/A`, and 2 `13F-NT`; the `13F-NT/A` feed returned no accession. Fifteen new canonical events were emitted, all `13F-HR/A` with Filing Date 2026-11-27:

- 14 rows carry `feed_path_cik_unverified=0001778131`.
- 1 row carries `feed_path_cik_unverified=0001046192`.
- All 15 were first observed in the same page receipt at **2026-11-27 15:36:23 UTC**.
- The prior successful poll ended **05:22:19 UTC**, leaving a 10h14m04s first-seen interval.
- The 13F legal Filing-Date floor is **11:00:00 UTC (06:00 ET)**. The conservative knowledge upper bound remains **15:36:23 UTC**.
- EDGAR acceptance was not retrieved for any of the 15 in the repository ledger. `feed_updated_utc` remains unverified and is not substituted for EDGAR acceptance.

Eligibility gates for these 15 events:

| Gate | Eligible |
|---|---:|
| Metadata observation | 15 |
| Manager identity verified | 0 |
| Security identity verified | 0 |
| Historical F80 membership verified | 0 |
| Public availability certified | 0 |
| Research observation | **0** |
| Signal | **0** |

The exact event accessions and current flags are preserved in the accompanying JSON. The rows remain `BOUNDED_METADATA_ONLY`; no accession was promoted.

## 3. A concentrated amendment batch — not 14 independent managers or trades

A secondary EDGAR-derived index maps the 14 accessions with the unverified path CIK 0001778131 to BI Asset Management Fondsmaeglerselskab A/S and to 14 different quarter-end periods:

| Accession | Report period | Secondary-index accepted time (UTC) |
|---|---|---:|
| 0001778131-26-000010 | 2023-03-31 | 11:51:20 |
| 0001778131-26-000011 | 2023-06-30 | 11:56:47 |
| 0001778131-26-000012 | 2023-09-30 | 11:59:37 |
| 0001778131-26-000013 | 2023-12-31 | 12:01:53 |
| 0001778131-26-000014 | 2024-03-31 | 12:03:47 |
| 0001778131-26-000015 | 2024-06-30 | 12:06:11 |
| 0001778131-26-000016 | 2024-09-30 | 12:08:52 |
| 0001778131-26-000017 | 2024-12-31 | 12:11:05 |
| 0001778131-26-000018 | 2025-03-31 | 12:19:02 |
| 0001778131-26-000019 | 2025-06-30 | 12:20:57 |
| 0001778131-26-000020 | 2025-09-30 | 12:22:50 |
| 0001778131-26-000021 | 2025-12-31 | 12:29:28 |
| 0001778131-26-000022 | 2026-06-30 | 12:38:00 |
| 0001778131-26-000023 | 2026-09-30 | 12:47:23 |

For these 14 records, the secondary index's accepted timestamps match the repository's `feed_updated_utc` values exactly (14/14). This is a useful cross-check hypothesis for a future primary SEC filing-detail audit, **not** sufficient to change the ledger's acceptance-clock status: the comparison source is secondary, and the SEC filing-detail pages have not yet been independently retrieved for this cohort.

Two individual filing pages identify their amendment type as **restatement**:
- `0001778131-26-000022`, for 2026-06-30, supersedes original `0001778131-26-000007`.
- `0001778131-26-000023`, for 2026-09-30, supersedes original `0001778131-26-000008`.

The remaining 12 amendment types have **not** been adjudicated individually. Do not infer that all 14 are restatements merely because they share the same filing date and filer candidate.

The fifteenth event, `0001046192-26-000018`, has feed-updated time 15:10:56 UTC. Its manager, report period, amendment type, original filing, and primary acceptance time remain unverified.

Secondary references used only for triage:
- [BI Asset Management filing history and 14-quarter batch](https://disclosery.com/funds/bi-asset-management-fondsmaeglerselskab-a-s-1778131?page=2)
- [Q2 2026 amendment #22](https://disclosery.com/filings/0001778131-26-000022)
- [Q3 2026 amendment #23](https://disclosery.com/filings/0001778131-26-000023)

These secondary mappings are not written into the repository's verified manager-identity fields.

## 4. Why amendment type matters for a no-lookahead holdings panel

The SEC's [Form 13F FAQ 58b–58c](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) distinguishes two economically different amendment types:

- A **restatement** resubmits the full corrected report and supersedes the original.
- An amendment **adding new holdings** contains only the additional entries and supplements the original report.

The SEC also notes that multiple amendments can be required. Therefore, a historical holdings database must preserve every filing vintage and apply the correct amendment state by the amendment's own public-availability time. A later restatement must never overwrite the historical record as if its corrected holdings had been known at the original quarter-end or original filing date. An add-only amendment must not be mistaken for a complete portfolio.

The observed 14-accession burst is one filer-candidate's batch across historical quarters, not 14 independent manager observations and not evidence of 14 new trading decisions. At least two are confirmed restatements; the others remain unclassified. The holdings themselves describe quarter-end snapshots, not transaction dates.

## 5. Research decision and next gates

**Decision: `KEEP_METADATA_ONLY_NO_PROMOTION`.**

Before any 13F signal construction:
1. Retrieve the primary SEC filing-detail page and submission documents for all 15 accessions.
2. Verify filer CIK from the SEC submission/header, not from the accession prefix or archive-path candidate alone.
3. Parse report period, amendment number, amendment type (restatement vs new holdings), original/superseded accession, and the full information table.
4. Retrieve and verify EDGAR Accepted timestamps; compare them against Atom `updated` and first-seen bounds without replacing the conservative clock prematurely.
5. Reconcile CUSIP/class to issuer and effective-dated ticker, then verify historical F80 membership.
6. Store original and amended vintages separately and calculate **revision deltas** separately from quarter-to-quarter portfolio changes.
7. Only after those gates pass, consider an event-time test against frozen LTM/F80 with the same exposure, costs, chronological splits, bootstrap/LOO, and untouched holdout.

No prices or post-event returns were inspected. No event study, OOS, bootstrap, or LOO test was run. No signal or portfolio change was made. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No data were purchased; budget used: USD 0.

## 6. Repository artifacts

- Machine-readable cohort and gates: `PHASE666_SEC_13F_HR_A_AMENDMENT_BURST_PIT_AUDIT_2026-11-27.json`
- Research state: `SMART_MONEY_RESEARCH_STATE_ADDENDUM_2026-11-27_PHASE666.md`
