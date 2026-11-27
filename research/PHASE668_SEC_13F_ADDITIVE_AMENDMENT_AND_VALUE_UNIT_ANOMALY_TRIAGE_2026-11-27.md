# Phase 668 — SEC 13F additive-amendment and post-2023 value-unit anomaly triage

**Audit cutoff:** 2026-11-27 18:40 UTC  
**Parent:** Phase 667 branch `phase667-sec-13f-value-unit-restatement-primary-audit` at `733f4c5e3f20401f1876b03d1bac2d572cc47bfd`  
**Disposition:** **Secondary triage only; no signal promotion.** This phase corrects the cohort taxonomy and identifies a broader 13F value-unit data-quality risk. It does not claim primary SEC verification of the new accession.

## 1. Preflight and latest repository state

- Inspected the latest 100 Actions runs, current branches, open PRs, research files, the latest run's jobs/logs/artifact, and the Phase 667 report/JSON before continuing.
- No active, queued or waiting Actions run was present.
- Default branch `main` is `6919a03ca2da8da4b6a428c29e088531cba300f9`.
- Latest run is [Phase 614, run 46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554). Both jobs completed successfully. Its artifact [15212890251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554/artifacts/15212890251) is an 873-byte ZIP containing only `poll_summary.json`; it does not contain filing XML, information tables or holdings rows.
- The live log confirms 15 new 13F-HR/A metadata accessions, 15 bounded metadata observations, zero research-eligible observations, zero signal-eligible observations, and no filing XML/text or holdings-row download.
- PR [#255 / Phase 666](https://github.com/jafelix81/NuevaEstrategia/pull/255) and PR [#256 / Phase 667](https://github.com/jafelix81/NuevaEstrategia/pull/256) remain open drafts. This phase is stacked on the Phase 667 branch; no parent PR was merged.

## 2. Important correction to the 15-event cohort

The Phase 666 cohort is not 15 BI restatements. The better current taxonomy is:

- **14 BI Asset Management accessions:** secondary index classifies all 14 as `RESTATEMENT`; four are primary SEC verified in Phase 667 as value-unit-only restatements, while ten remain primary-unadjudicated.
- **One separate accession, `0001046192-26-000018`:** a secondary EDGAR-derived page identifies it as CANADA LIFE ASSURANCE Co and classifies it as a **combination report / NEW HOLDINGS** amendment for 2026-09-30, with 806 rows. This is not a restatement according to that secondary page.

The Canada Life filing's secondary page identifies base filing `0001046192-26-000015`, filed 2026-11-13 and accepted at 18:01:18 UTC, and the add-only amendment accepted 2026-11-27 at 15:10:56 UTC. The latter's timestamp exactly matches the repository's `feed_updated_utc` field, but that repository field remains unverified and the match is corroborative only. The primary SEC header/XML and acceptance record were not retrieved in this phase.

**Interpretation:** if the secondary classification is correct, the 806 entries supplement a Q3 2026 quarter-end holdings report. They are not 806 trades, and they do not reveal trade dates. The additional holdings become usable no earlier than the amendment's own public-availability time, not the quarter-end date or the base filing date.

## 3. BI Asset Management: what is and is not verified

The secondary index lists the 14 BI accessions as restatements across 14 reporting quarters from 2023-Q1 through 2026-Q3 (no 2026-Q1 entry in this cohort). It supplies report row counts, corrected totals and EDGAR acceptance times. Those fields are recorded in the JSON audit as **secondary-only** except for the four documents already primary-verified in Phase 667.

Phase 667 independently verified four primary SEC XML filings:
- `0001778131-26-000018` — 2025-03-31
- `0001778131-26-000021` — 2025-12-31
- `0001778131-26-000022` — 2026-06-30
- `0001778131-26-000023` — 2026-09-30

Each explicitly states that the whole report is restated to correct Column 4 and the summary value total from thousands to nearest dollars, and that no other report information changed. That conclusion applies only to those four. Do not extrapolate it to the remaining ten merely because the secondary index calls them restatements.

The ten remaining BI accessions are listed in the JSON with their secondary report periods, row counts, reported totals and acceptance timestamps. They remain unverified from primary SEC documents.

## 4. New data-quality hypothesis: post-2023 filers may still use legacy thousands

The SEC's official [EDGAR Release 22.4.1](https://www.sec.gov/filergroup/announcements-old/edgar-release-2241) says the Form 13F Appendix B value unit changed from thousands to nearest dollar effective **2023-01-03**. The official [SEC Form 13F data-set page](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) also records the later incorporation of Release 22.4.1 changes into the 2023 data sets.

However, the secondary Canada Life page labels its post-2023 information-table values as thousands and says it multiplied them by 1,000 after an implied-price check. A separate secondary methodology page reports 365 post-2023 filings (3.7% of its 2026-06-01 to 2026-08-31 sample, 154,638 rows) that still appeared to use thousands. These are **source-reported secondary findings**, not independently reproduced counts in this phase.

This exposes a practical parser risk: a filing-date unit rule is the legal expected convention, but it is not a sufficient data-quality control. A post-2023 filing can still appear to contain legacy-thousands values. The pipeline should flag anomalous units using economic plausibility checks, not silently assume compliance or automatically rescale every row.

### Proposed independent detector

For eligible ordinary-share rows, compute implied price as filed value divided by reported shares, then compare it with a contemporaneous CUSIP-specific reference-price distribution. Use robust medians and wide, pre-specified bands. Exclude or separately adjudicate:
- puts/calls and other option rows;
- principal-amount/debt rows;
- ADRs and depositary ratios;
- non-US securities with currency or unit ambiguity;
- stock splits, class changes and CUSIP transitions;
- stale or unresolvable CUSIPs;
- rows whose quantity/value fields cannot be economically compared.

A filing-level unit inference should require a pre-specified majority/consistency threshold across eligible rows. Ambiguous rows must remain as-filed and flagged. Preserve raw value, inferred unit, rule version, reference price, implied price, ratio, row eligibility and correction decision as separate fields. Never overwrite the raw filing.

## 5. Quantitative disposition

**Decision: `SECONDARY_TRIAGE_ONLY_NO_SIGNAL_PROMOTION`.**

- The Canada Life accession is a high-priority primary-document retrieval candidate, not an eligible institutional signal.
- A new-holdings amendment is an added quarter-end holdings disclosure, not a transaction tape.
- The ten remaining BI amendments remain unadjudicated from primary SEC documents.
- The four verified BI value-unit restatements are reporting corrections, not four new position decisions.
- No holdings in this cohort have verified historical F80 membership or certified public-availability clocks in the repository ledger.

No prices or post-event returns were inspected. No event study, OOS, bootstrap or LOO test was run. Holdout untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No data were purchased; spend USD 0.

## 6. Next gates

1. Primary-verify `0001046192-26-000018` and base filing `0001046192-26-000015`: cover page, amendment type, XML, information table, accession chain and EDGAR acceptance time.
2. Primary-verify the ten remaining BI filings; do not infer value-only from `RESTATEMENT`.
3. Build and test a deterministic implied-price unit anomaly detector on known correct and known legacy-thousands filings, including difficult security types and corporate actions.
4. Diff original and amended information tables by CUSIP, class, put/call, amount, amount type, discretion, manager and value.
5. Keep original and amended filing vintages separate, and timestamp the amendment only when it became public.

## 7. Repository records

- Machine-readable evidence and per-accession secondary classifications: `PHASE668_SEC_13F_ADDITIVE_AMENDMENT_AND_VALUE_UNIT_ANOMALY_TRIAGE_2026-11-27.json`
- State addendum: `SMART_MONEY_RESEARCH_STATE_ADDENDUM_2026-11-27_PHASE668.md`
- Parent primary audit: [Phase 667 report](https://github.com/jafelix81/NuevaEstrategia/blob/phase667-sec-13f-value-unit-restatement-primary-audit/research/PHASE667_SEC_13F_VALUE_UNIT_RESTATEMENT_PRIMARY_AUDIT_2026-11-27.md)

