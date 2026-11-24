# Phase 586 — Form 4 current-ledger refresh and UPST insider-purchase cluster

**Audit cutoff:** 2026-11-24 03:37 UTC (2026-11-23 20:37 Hermosillo)  
**Main HEAD before this report:** \`d89c30c6880cc9f61d1b8ad2917082fa8d0ec490\`  
**Disposition:** **UPST is a discovery-only candidate for a clustered, non-10b5-1 indirect insider-purchase hypothesis. No event study, alpha, OOS test, or signal admission.**

## 1. Repository and Actions preflight

- 8,104 total Actions runs; latest 100: 90 success / 10 failure.
- Explicit in-progress: 0; queued: 0.
- 378 branches (100 + 100 + 100 + 78 across four pages); 72 open PRs; 96 workflow files.
- Latest overall run: Phase 584 PR check [45268079558](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45268079558), successful. It is not a live capture.
- Latest scheduled Form 4 run: [45257913619](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619), 2026-11-23 20:18 UTC. It predates the Phase 583/584 merge.
- Latest scheduled Form 144 run: [45261140072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072), 2026-11-23 20:36 UTC.
- No workflow was dispatched, rerun, cancelled, or duplicated.

### Schedule delivery

The main-branch Form 4 workflow retains cron \`17 * * * 1-5\`; Form 144 retains \`47 * * * *\`.

At the audit cutoff, no scheduled run appeared after the 20:36 UTC Form 144 run:
- Form 4 slots absent: 2026-11-23 21:17, 22:17, 23:17 UTC and 2026-11-24 00:17, 01:17, 02:17, 03:17 UTC.
- Form 144 slots absent: 2026-11-23 21:47, 22:47, 23:47 UTC and 2026-11-24 00:47, 01:47, 02:47 UTC. The 03:47 UTC slot had not yet become due.

The read-only API does not expose repository Actions enabled/paused or scheduled-workflow permission settings. This is an observed delivery gap, not proof that an administrator disabled the workflows. The next nominal slots are 03:47 UTC (Form 144) and 04:17 UTC (Form 4). No manual dispatch was used.

## 2. Capture state, jobs and artifacts

### Form 4 / 4-A

Run 45257913619 completed its jobs and uploaded artifact [14859736409](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45257913619/artifacts/14859736409). Its live log shows:
- Form 4 feed: 20 pages / 2,000 raw entries; prior watermark not found; \`PaginationLimitReached\`; poll unsuccessful.
- 408 unique candidate accessions / 938 observations were correctly suppressed from the incomplete poll.
- Form 4/A feed: one page; prior watermark found; poll successful.
- No research-observation or signal-eligible rows.

The current state file still records Form 4 as \`GAP_OR_FETCH_ERROR\`, with last successful Form 4 poll ending 2026-11-23 07:48:52 UTC. Form 4/A last succeeded at 20:18:55 UTC. Phase 583/584's 50-page (5,000 raw-entry) guard is present in main, but **there is no natural post-merge run validating it**. Do not treat the old 20-page run or the PR's offline tests as live validation.

### Form 144

Run 45261140072 completed both feeds with no errors or source-hash mismatches:
- 349 structured filing accessions;
- 2,486 detail rows;
- 248 accessions still awaiting bounded detail backfill;
- zero signal-eligible events.

Artifacts [14860501976](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860501976) and [14860761702](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45261140072/artifacts/14860761702) were present and unexpired at audit time.

## 3. Refreshed Form 4 ledger census

Inputs on main:
- \`research/data/sec_form4_first_seen/transaction_details.csv\`, blob SHA \`f92a58fa7b3cfa18499fe39249b38a8bb6efa9b9\`;
- \`research/data/sec_form4_first_seen/reporting_owners.csv\`, blob SHA \`23d04d36b3d385c115b109bf5216c426b421938f\`;
- \`research/data/sec_form4_first_seen/state.json\`, blob SHA \`c9888fe90332f173ec33e34ce07c4a9e169b388d\`.

Current ledger:
- 175 CSV data rows: 60 filing-header rows and 115 transaction rows;
- 60 unique accessions;
- 45 normalized symbol labels, including one \`N/A\` sentinel;
- owner sidecar: 50 rows across 40 accessions; the six UPST accessions identified below are not yet in that sidecar;
- zero research-observation-eligible rows and zero signal-eligible rows;
- zero rows with certified public availability, verified security identity, verified historical F80 membership, verified owner attribution, verified transaction semantics, or authorized new-trade status.

### Exact overlap with the static 335-ticker snapshot

The strict exact-symbol join against \`research/phase44_frozen_universe_335_tickers.csv\` (335 unique tickers; source commit \`1aa1b91f383ce9cef375a43e775c736a27356a5f\`; blob SHA-1 \`7edbd62b4fb34a6123276e4ce45cb3c1c62479c7\`; SHA-256 \`f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda\`) now finds:

- 8 accessions;
- 15 transaction rows;
- 3 symbols: APO, SE, UPST.

This refresh supersedes the smaller Phase 546 descriptive count (70 transaction rows / 40 accessions at its earlier cutoff). **The static 335-symbol file is not an effective-dated security master and does not prove historical membership in F80 on the event dates.** No ticker change, share class, listing date, or historical F80 membership is inferred from this exact-symbol join.

## 4. UPST: two-purchaser cluster, with controls

Six UPST accessions contribute seven transaction rows to the static-snapshot overlap. Manual review of the underlying public Form 4 filings resolves the two purchase candidates:

| Reporting person | Reported role | Transaction | Reported weighted-average price | Approx. value | Ownership |
|---|---|---:|---:|---:|---|
| Paul Gu | CEO and director | 50,000 shares acquired, 2026-11-19 | $17.2013 | $860,065 | Indirect, Gu Qiao Family Trust |
| Dave Girouard | Director and 10% owner | 60,000 shares acquired, 2026-11-20 | $15.8498 | $950,988 | Indirect, 2008 D&T Girouard Revocable Trust |
| **Combined** | **Two reporting persons / one issuer** | **110,000 shares** | — | **$1,811,053** | **Both indirect through trusts** |

Both filings use Table I code P with acquired indicator A. Neither has the Rule 10b5-1 checkbox selected. Their footnotes describe weighted-average purchases across multiple transactions and price ranges. The SEC's official General Instruction 8 defines P as **“open market or private purchase”**; code P alone does not prove exchange execution or exclude a private transaction. Venue remains unresolved.

Public filing references:
- Paul Gu, accession [0001832812-26-000016](https://www.sec.gov/Archives/edgar/data/1832812/000183281226000016/0001832812-26-000016-index.htm); Form 4 document [SEC HTML/XML rendering](https://www.sec.gov/Archives/edgar/data/1647639/000183281226000016/xslF345X06/wk-form4_1795224137.xml).
- Dave Girouard, accession [0001832805-26-000011](https://ir.upstart.com/sec-filings/sec-filing/4/0001832805-26-000011); issuer-hosted Form 4 [HTML](https://ir.upstart.com/node/13556/html).
- SEC Form 4 General Instruction 8: [official instructions](https://www.sec.gov/files/form4.pdf).

### Exclusions and negative controls

- Sanjay Datta's 8,568-share sale, Natalia Mirgorodskaya's 562-share sale, and Scott Darling's 7,372-share sale each explicitly state that the shares were sold to cover tax withholding on RSU vesting. Exclude them from discretionary selling flow. See [Datta Form 4](https://www.sec.gov/Archives/edgar/data/1647639/000183280826000024/xslF345X06/wk-form4_1795224216.xml), [Mirgorodskaya Form 4](https://www.sec.gov/Archives/edgar/data/1647639/000183385126000025/xslF345X06/wk-form4_1795224238.xml), and [Darling Form 4](https://www.sec.gov/Archives/edgar/data/1558259/000155825926000024/xslF345X06/wk-form4_1795224189.xml).
- Andrea Blankmeyer's 3,000-share sale is explicitly reported under a Rule 10b5-1 plan adopted 2026-05-16; retain as a planned-trade negative control, not discretionary selling. [Filing](https://ir.upstart.com/node/13571/html).
- Dave Girouard's 419,290-share J/D line is a transfer for no consideration to a gift trust, not a market sale; exclude from trading flow.
- SE's seven sale rows are one accession and carry the Rule 10b5-1 filing flag; they are one planned-trading negative-control event, not seven independent observations.
- APO's 1.5-million-share J/D row has no transaction price and no owner sidecar in the current ledger; keep quarantined until its footnote and identity are reconciled.

The UPST purchase accessions are not yet present in the canonical owner sidecar. Manual public-document review identifies the reporting persons and trust relationships, but the pipeline's owner-attribution and transaction-semantics flags remain false. Do not manually flip eligibility fields or promote these rows.

## 5. Point-in-time and statistical disposition

For both UPST purchase accessions, the current ledger records a first-seen interval lower bound of 2026-11-21 00:51:03 UTC and a conservative poll-receipt upper bound of 2026-11-23 07:48:52 UTC. The ledger's parsed acceptance clocks are 2026-11-21 01:22:19 UTC (Paul Gu) and 01:21:55 UTC (Dave Girouard). Acceptance is not treated as exact first public availability.

If a later research-only event study is authorized, the conservative executable anchor is the next full regular session after the upper-bound receipt: **2026-11-23**. Same-day intraday use is not authorized. Historical F80 membership, effective-dated issuer/security-class identity, and a complete point-in-time return panel remain unresolved.

**Hypothesis generated, not confirmed:** clusters of sizeable, non-10b5-1 P/A purchases by multiple distinct senior insiders may contain incremental information beyond LTM/F80. Treat the two UPST filings as **one issuer-level discovery cluster**, not two independent cross-sectional observations. This case was identified after inspecting the current sample and must not enter a confirmatory holdout/OOS set.

Before testing:
1. Backfill and reconcile the two UPST owner-sidecar accessions and preserve filing-level versus transaction-line attribution.
2. Resolve open-market versus private-purchase status from complete filing context; keep unknown venue as unknown.
3. Build effective-dated CIK/ticker/security-class/listing and historical F80 membership joins.
4. Accumulate a broad, survivorship-aware Form 4 panel with exact first-receipt intervals and conservative executable clocks.
5. Predefine issuer-level clustering, purchase-size normalization, 10b5-1/tax/vesting/gift/transfer/exercise exclusions, and duplicate/joint-filing handling on a discovery sample separate from confirmation.
6. Only then compare against frozen LTM/F80 with identical exposure and costs, chronological OOS, issuer/event-cluster bootstrap and leave-one-issuer/year-out sensitivity. Do not impose a holding-period limit; evaluate any dynamic exit or horizon selection inside training only.

No forward returns were calculated. No event study, backtest, alpha, OOS, bootstrap, LOO, or holdout test was run. No signal was admitted.

## 6. Other source gates and strategy protection

- FINRA Short Interest remains conditional on authorized credentials/terms; the next scheduled release is 2026-11-24 for settlement 2026-11-13, published by 4:40 PM ET (2:40 PM Hermosillo). No request was initiated.
- FINRA ATS and Reg SHO remain subject to symbol identity, complete snapshots, and the post-merge production validation gates.
- Cboe OPRA/options remains gated by written strategy-use authorization, exact 335-name/date coverage, and historical first-receipt/correction vintages.
- SEC 13D/G and FTD remain gated by the repository's SEC_USER_AGENT secret and subject-issuer identity reconstruction.
- CFTC TFF remains a prospective regime/crowding candidate with too few vintages for a predictive test.
- MIDAS remains market-structure context, not participant identity or dark-pool institutional flow.

Baseline \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. New signals admitted: **0**. Incremental alpha demonstrated: **none**. Universe, parameters, holding-period policy, exposure, costs, holdout and production are unchanged.
