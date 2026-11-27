# Phase 670 — SEC 13F Canada Life primary-source and value-unit anomaly audit

**Audit cutoff:** 2026-11-27 20:49:57 UTC  
**Base:** `main` at `833ffe6057336de47a73dcc29628d44a191ef5a6`  
**Disposition:** **Primary-source unit anomaly strongly confirmed in the Q3 2026 base report and corroborated by four common-stock rows exposed from the 806-row additive amendment table; full-table normalization and PIT admission remain blocked. No signal promotion.**

## 1. Preflight: Actions, branches, PRs and artifacts

Reviewed the latest 20 Actions runs, jobs, logs, artifacts, open PRs, branches and relevant research files before starting. No queued, in-progress, waiting or pending run was present.

The current `main` head is `833ffe6057336de47a73dcc29628d44a191ef5a6`. PRs [#255](https://github.com/jafelix81/NuevaEstrategia/pull/255), [#256](https://github.com/jafelix81/NuevaEstrategia/pull/256), [#257](https://github.com/jafelix81/NuevaEstrategia/pull/257) and [#258](https://github.com/jafelix81/NuevaEstrategia/pull/258) are merged. The older SEC 13F sequence/knowledge-clock PRs #221–#230 remain open and were not modified.

Relevant latest evidence:

| Run | Workflow | Result | Artifact / limitation |
|---|---|---|---|
| [46057111964](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46057111964) | Phase 476 Form 4 | Scheduled capture success; 82 offline tests passed | 5,979-byte compact ZIP; no raw filing XML; 94 new bounded metadata events; zero research/signal-eligible rows |
| [46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554) | Phase 614 13F | Scheduled capture success | 873-byte ZIP containing only `poll_summary.json`; 15 new 13F-HR/A metadata events; zero research/signal-eligible rows; no filing XML or holdings rows |
| [45988473657](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45988473657) | Phase 616 13D/G | Offline regression success | Live sample skipped because this was a pull-request event; `run_live_sample=true` was not exercised |
| [45978861267](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45978861267) | Phase 469 FINRA | Offline regression success | Live capture skipped because this was a pull-request event |

No manual capture was started and no scheduled workflow was duplicated. The 13D/G 44-accession live sample and a post-Phase-661 natural FINRA symbol-volume capture remain outstanding.

## 2. Primary SEC verification: Canada Life Q3 2026 base filing

The SEC filing detail page identifies accession `0001046192-26-000015` as Canada Life Assurance Co's Form 13F-HR for the quarter ended 2026-09-30. It shows filing date 2026-11-13 and displayed acceptance time 13:01:18 (the rendered page does not state a timezone). The cover summary reports 1,785 information-table entries and total value `61,098,083`, with the label “round to nearest dollar”.

Sources:
- [SEC filing detail / acceptance display](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000015/0001046192-26-000015-index.html)
- [SEC primary cover page](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000015/xslForm13F_X02/primary_doc.xml)
- [SEC information table](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000015/xslForm13F_X02/13F_Filing_Sep26.xml)

### Row-level implied-price test

The SEC information table labels Column 4 as value “to the nearest dollar”. Yet two ordinary common-stock rows imply prices that are almost exactly one-thousandth of the market price when the filed value is divided by reported shares.

| Ticker | Filed value | Shares | Implied price as filed | Implied price ×1,000 | 30-Sep-2026 close | Scaled deviation |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 3,812,648 | 11,461,129 | $0.332659 | $332.659 | $333.02 | -0.1084% |
| AMZN | 1,997,269 | 8,026,987 | $0.248819 | $248.819 | $249.15 | -0.1327% |

The same-date market-price checks are available at [Yahoo Finance AAPL history](https://finance.yahoo.com/quote/AAPL/history/) and [StatMuse AMZN history](https://www.statmuse.com/money/ask/amazon-stock-price-september-2026).

This is strong primary row-level evidence that the **base filing's value fields still use legacy thousands**, despite the displayed nearest-dollar header. The scale factor is not a subtle rounding difference: multiplying by 1,000 reproduces the 30 September prices within approximately 0.14% for both large-cap common-stock rows.

The SEC's [EDGAR Release 22.4.1](https://www.sec.gov/filergroup/announcements-old/edgar-release-2241) changed Form 13F Appendix B's value unit from thousands to nearest dollar effective 2023-01-03. The Canada Life Q3 2026 filing is therefore a post-rule unit anomaly, not a reason to revert the parser globally to the legacy convention.

**Scope limit:** two clean common-stock rows establish a strong filing-level anomaly candidate, not a license to rescale every row. The full table still requires a deterministic filing-level check, with exclusions for options, principal amounts, ADR ratios, non-US securities, splits, CUSIP changes and stale identifiers.

## 3. Primary SEC verification: the 806-row amendment

The SEC-indexed primary `primary_doc.xml` for accession [`0001046192-26-000018`](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000018/primary_doc.xml) identifies:

- CIK `0001046192`, Canada Life Assurance Co.
- Form `13F-HR/A`, report period 2026-09-30.
- Amendment number 1, with amendment type **NEW HOLDINGS**.
- Report type **13F COMBINATION REPORT**.
- 806 information-table entries.
- Filed summary value total `8,531,520`.
- Signature date 2026-11-27.
- Keyridge Asset Management Ltd. (CIK `0001427274`) as an included manager.

This upgrades the Canada Life amendment from secondary-only triage to **primary-verified identity and amendment classification**. It is an additive holdings disclosure, not a restatement and not evidence of 806 trades.

The amendment's 8,531,520 summary total is consistent with the same legacy-thousands hypothesis, but its 806-row information table has not yet been retrieved. Do not normalize that amendment's rows until the table is available and checked.

The primary amendment document does not expose an explicit previous-accession field. The same-quarter base candidate `0001046192-26-000015` is supported by the same filer and report period and by the secondary index, but the exact parent link remains unadjudicated from the primary document.


### Follow-up: amendment information-table row-level unit corroboration

The SEC archive's primary information-table URL for accession `0001046192-26-000018` is:

- [SEC amendment information table — 13F_Filing_Sep26.xml](https://www.sec.gov/Archives/edgar/data/1046192/000104619226000018/13F_Filing_Sep26.xml)

The indexed primary XML exposes four ordinary common-stock rows. For each, the filed value divided by reported shares is approximately one-thousandth of the contemporaneous 2026-09-30 close; multiplying the filed value by 1,000 reproduces the close within 0.11%.

| Ticker | CUSIP | Filed value | Shares | Implied price as filed | Implied price ×1,000 | 2026-09-30 close | Scaled deviation |
|---|---|---:|---:|---:|---:|---:|---:|
| B (Barrick Mining) | 06849F108 | 71,766 | 1,764,862 | $0.040664 | $40.663803 | $40.67 | -0.0152% |
| BBWI | 070830104 | 2,214 | 139,134 | $0.015913 | $15.912717 | $15.92 | -0.0457% |
| BLK | 09290D101 | 111,382 | 105,330 | $1.057458 | $1,057.457514 | $1,058.29 | -0.0787% |
| MRVL | 573874104 | 223,843 | 848,130 | $0.263925 | $263.925342 | $264.21 | -0.1077% |

The four row values and quantities are exposed by the SEC-hosted XML index result. Same-date closing-price checks use secondary historical-price pages: [B](https://stockanalysis.com/stocks/b/history/), [BBWI](https://stockanalysis.com/stocks/bbwi/history/), [BLK](https://www.tipranks.com/stocks/blk/historical-prices) and [MRVL](https://stockanalysis.com/stocks/mrvl/history/). Prices are used only to adjudicate the scale factor, not to evaluate post-event returns.

**Interpretation:** the amendment's sample rows independently corroborate the legacy-thousands anomaly already found in AAPL and AMZN in the base report. This is strong evidence for a filing-level unit anomaly, but it is a purposive four-row sample, not a complete audit of all 806 entries. No row has been normalized in the repository.

**Retrieval limitation:** the SEC XML endpoint is publicly discoverable and its indexed content is readable, but the current reader rejects the `text/xml` response and the direct download attempt did not return the raw file. Consequently, the full table's row count, file hash and row-by-row reconciliation remain unverified in this run.

### Acceptance-time corroboration (secondary only)

The secondary filing-chain index reports acceptance at `2026-11-27 15:10:56 UTC` and ingestion at `15:11:30 UTC`; it also links the amendment to base accession `0001046192-26-000015`. The repository's SEC Atom poll independently recorded `feed_updated_utc=2026-11-27T15:10:56Z`. The exact timestamp match is useful corroboration, but the secondary index is not the official SEC filing index and the Atom `updated` value is not itself an EDGAR acceptance/public-availability timestamp. The primary parent link and public-availability clock therefore remain unadjudicated.

Source: [secondary amendment chain](https://disclosery.com/filings/0001046192-26-000018). The SEC notes that filing content often appears within 1–3 minutes of EDGAR acceptance but does not provide a timestamp for first public availability; therefore this secondary acceptance time is not sufficient to certify the first tradable moment.

## 4. Timestamp and point-in-time treatment

The repository's Phase 614 accession ledger records the amendment in run [46026323554](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46026323554):

- SEC Atom `updated`: `2026-11-27T10:10:56-05:00` (`15:10:56Z`).
- Page received: `2026-11-27T15:36:23Z`.
- Event interval status: `BOUNDED_METADATA_ONLY`.
- Public availability certified: false.

The Atom `updated` field is a feed timestamp, not a certified EDGAR acceptance/public-availability timestamp. The primary document's signature date is also not an acceptance timestamp. The amendment's official filing-index acceptance time remains unresolved in this phase.

The reported holdings are a 2026-09-30 quarter-end snapshot. The 806 additional rows become usable only after the amendment itself is publicly available; they must never be backdated to the quarter-end date or to the original filing.

## 5. Research decision

**Decision:** `PRIMARY_BASE_REPORT_UNIT_ANOMALY_STRONGLY_CONFIRMED_ADDITIVE_AMENDMENT_PRIMARY_CLASSIFIED_NO_SIGNAL_PROMOTION`.

- The base report's AAPL and AMZN rows strongly support a factor-1,000 legacy-unit anomaly.
- The 13F-HR/A is primary-verified as a NEW HOLDINGS amendment with 806 entries.
- The amendment's row-level values and exact parent link remain unresolved.
- No holdings from this cohort have verified historical F80 membership or a certified public-availability clock in the repository.
- No position change is interpreted as a transaction; no signal is promoted.

Contemporaneous 30-Sep prices were used only to validate the value-unit scale. No post-event returns, event study, OOS test, bootstrap or LOO test were run. The holdout was untouched. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. Data spend: **USD 0**.

## 6. Next gates

1. Retrieve and SHA-256 hash the amendment's complete information-table XML and official filing index using the established SEC User-Agent path.
2. Parse all 806 rows and reconcile them against the original Q3 2026 table by CUSIP, class, put/call, quantity, discretion and other-manager assignment.
3. Verify the exact parent accession and official acceptance/index clock from SEC primary records; retain a separate first-public-availability bound.
4. Implement a deterministic, fail-closed unit anomaly detector; preserve as-filed values and store any normalized value separately with rule version and row evidence.
5. Test the detector on Canada Life, the four already verified BI value-unit restatements, and a broader control sample.
6. Primary-verify the ten remaining BI amendments; do not extrapolate the four verified cases.
7. Continue the independent 13D/G and FINRA capture gates without duplicating scheduled workflows.

## Repository records

- Machine-readable audit: `PHASE670_SEC_13F_CANADA_LIFE_PRIMARY_UNIT_ANOMALY_AUDIT_2026-11-27.json`
- State addendum: `SMART_MONEY_RESEARCH_STATE_ADDENDUM_2026-11-27_PHASE670.md`
