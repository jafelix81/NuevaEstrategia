# Phase 546 — Form 4 live-ledger universe overlap and Rule 10b5-1 negative control

**Audit cutoff:** 2026-11-21 12:26 UTC  
**Base main:** `cb9aab722f905e2df54e349091e42ae7d9bf243a`  
**Disposition:** one exact ticker overlap with the frozen 335-symbol snapshot was found in the current Form 4 structured ledger. It is one filing with seven sale lines and an affirmative Rule 10b5-1 indicator. Treat it as a planned-trading negative control, not discretionary insider flow. No event study or alpha test is authorized.

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs, relevant jobs/logs/artifacts, open PRs, branch pages and current research files before analysis.
- Latest 100 run outcomes: **87 success, 12 failure, 1 cancelled**; zero queued, waiting or in-progress.
- The phase-branch search returned 363 matching branches across four pages (100/100/100/63); 67 open PRs were visible. No Phase 546 branch or PR existed at preflight.
- Relevant completed runs and artifacts:
  - Form 144 [44886726541](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541): offline and live jobs succeeded; 64/64 offline tests; artifact [14700173280](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541/artifacts/14700173280).
  - Form 4 [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134): offline and live jobs succeeded; artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646).
  - FINRA Reg SHO [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600): offline and live jobs completed; artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921).
  - CFTC TFF [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977): prospective-capture job succeeded; artifact [14689726870](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977/artifacts/14689726870).
- PR #198 Phase 542 remains Draft and non-mergeable against the advanced main branch. Its two offline checks passed 21/21 and 16/16 tests. It still requires the repository Actions secret SEC_USER_AGENT before the bounded FTD sample can be tested.
- No workflow was dispatched, rerun, cancelled or duplicated.

## 2. Current Form 4 ledger census

The current committed structured transaction ledger contains:

| Measure | Count |
|---|---:|
| Transaction rows | 70 |
| Distinct accessions | 40 |
| Distinct normalized issuer symbols | 32 |
| Rows in single-reporting-owner filings (filing grain only) | 66 |
| Rows in multi-owner filings, quarantined from line-level attribution | 4 |
| Accessions with owner sidecar parsed | 20 / 40 |
| Owner-sidecar accessions: single owner / multi-owner | 18 / 2 |
| Accessions still awaiting owner sidecar | 20 |
| Research-observation eligible transaction rows | 0 |
| Signal-eligible transaction rows | 0 |

The sidecar has 29 owner rows across 20 accessions. A filing-level count of one reporting owner is not silently promoted to verified transaction-line attribution; the existing schema and Phase 459–461 controls deliberately keep that distinction.

Input provenance:
- `transaction_details.csv` Git blob SHA: `5effbaf9219e440e027909856dba9332a4c7a034`.
- `reporting_owners.csv` Git blob SHA: `fd64c5f46a1fc92316c4ac0bd56ad07039a3ba82`.
- Frozen 335-symbol snapshot from commit `1aa1b91f383ce9cef375a43e775c736a27356a5f`; Git blob SHA-1 `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7`, SHA-256 `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`.

## 3. The only exact symbol overlap: SE

One issuer-symbol match was found: **SE / Sea Ltd**, issuer CIK `0001703399`, Class A ordinary shares.

- One accession: `0001193125-26-469085`.
- Seven transaction-detail rows, all code S with acquired/disposed code D.
- Transaction dates: 2026-11-18 and 2026-11-19.
- Aggregate reported quantity: **1,600 shares**.
- Sum of reported shares × reported transaction prices: approximately **$109,300.43**.
- The filing reports one reporting owner, but its owner-identity sidecar has not yet been appended.
- All seven rows carry `AFF10B5ONE=yes`; the parsed footnote flags also mark a Rule 10b5-1 mention.

**Interpretation:** this is one accession/event, not seven independent observations. The affirmative Rule 10b5-1 indicator makes it unsuitable as a discretionary-insider buying/selling observation. Keep it as a negative control for the planned-transaction exclusion. Do not infer the owner's identity, role or intent before the owner sidecar is available.

The accession is currently rank **10 of 20** in the bounded owner-enrichment queue, sorted by first-seen time. If the queue remains unchanged, it should be included in the next ten-accession owner batch. No manual dispatch was made.

### 3.1 Point-in-time handling

The SE filing's recorded clocks are:

| Clock | UTC | Status |
|---|---|---|
| First-seen interval lower bound | 2026-11-20 10:07:15 | Bounded metadata only |
| SEC acceptance datetime | 2026-11-20 11:00:12 | Parsed, not certified as exact public availability |
| First-seen interval upper bound / poll receipt | 2026-11-20 18:38:51 | Conservative receipt upper bound |

Do not backdate the event to its transaction dates or treat the acceptance datetime as exact first public availability. If a later research-only event study is authorized, the conservative executable clock is the first full regular session after the receipt upper bound: **Monday 2026-11-23**, not same-day Friday execution.

The current ledger keeps all 70 transaction rows ineligible: public availability is not certified; same-day intraday use is unauthorized; security identity, historical F80 membership, owner attribution, transaction semantics and new-trade status are unverified. The exact SE ticker match is descriptive overlap with a static snapshot, not proof of historical F80 membership.

## 4. Form 144 artifact clarification and delivery status

The downloaded Form 144 artifact [14700173280](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44886726541/artifacts/14700173280) confirms:
- 53 feed observations (51 Form 144, 2 Form 144-A);
- 3 new accessions/events and 3/3 acceptance reconciliations, zero unresolved;
- `research_observation_eligible_count=3` at the all-feed metadata-observation scope, but **zero candidate-issuer matches and zero signal-eligible events**;
- first-seen remains a poll-receipt upper bound; public availability is not certified and same-day intraday use is unauthorized;
- 10 bounded accessions / 55 detail rows parsed without error; cumulative ledger 235 accessions / 1,712 detail rows, 328 remaining.

The successful poll at 08:50:22–08:50:23 UTC followed the prior successful poll at 00:58:15 UTC, a 7h52m interval. The collector found its prior accession watermark and reported no feed-window gap for that poll; this does not establish scheduler continuity. At the 12:26 UTC audit cutoff, the 09:47, 10:47 and 11:47 hourly schedule slots were absent from the Actions run list; 12:47 had not yet become due. Issue #194 remains open for this observed delivery gap. Administrative enabled/paused state is not exposed by the read-only connector.

## 5. Other source status — no FINRA-only assumption

- **FINRA Reg SHO:** run 44860690600 predates the Phase 539 merge. It received eight HTTP-200 files but rejected all eight as `duplicate_symbol_in_consolidated_file`; zero valid/eligible. The new metadata-only diagnostics still await the first natural post-merge capture.
- **CFTC TFF:** run 44860341977 recorded four prospective contract-report events (report date 2026-11-17; first receipt 2026-11-21 03:17:36 UTC). The 3,043-row archive remains excluded from full-history PIT features; two prospective vintages are not enough for a predictive test.
- **Options:** Cboe Open-Close EOD remains the strongest conditional participant-capacity × position-side × open/close complement: its one C1 sample passed schema/accounting checks, but four-venue paired history starts no earlier than 2018-01-02 and overnight first-receipt/correction vintages and licensing remain unresolved. Cboe OPRA Option Trades/Quotes is the independent broad-market trade/NBBO reconstruction candidate, but no authorized sample or first-receipt proof is available. IvyDB TradeFlow remains a conditional all-venue signed-flow candidate with unresolved archive lineage/methodology/PIT; Obscura flow_metrics still has conflicting available_date documentation and no verified 335-name coverage. Massive/ThetaData remain gated by sample, PIT, coverage and license terms. No vendor data were purchased.
- **SEC MIDAS / 13F / N-PORT:** MIDAS has 59 official quarterly distributions listed from 2012 Q1 through 2026 Q3, but per-quarter first-publication timestamps and historical universe identity remain unverified. The existing N-PORT raw share-growth hypothesis remains killed; 13F remains parked pending effective-dated security identity and coverage.
- **Phase 20C:** latest recorded census remains 328/335 price histories; seven inactive/acquired/renamed names still need terminal-return and corporate-action reconstruction.

## 6. Decision and next gates

1. Keep the SE accession as a Rule 10b5-1 negative control; do not count its seven rows as seven events or as discretionary insider flow.
2. Let the existing natural owner-enrichment queue run. Reconcile the single reporting owner, remarks and filing-level checkbox when the accession reaches the sidecar; do not infer an owner from transaction rows.
3. For any future Form 4 research, group by accession/issuer/event, use the first-seen receipt upper bound and a next-full-session execution rule, and require effective-dated CIK/security/F80 identity before constructing returns.
4. Continue the natural post-Phase-539 FINRA capture, prospective CFTC collection and options-source feasibility work without purchasing or automating unlicensed data.

No forward returns, event study, backtest, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. No changes to universe, exposure, costs, holding-period policy, parameters or production.

**Frozen control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains unchanged.
