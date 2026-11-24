# Phase 592 — Form 4 current-ledger purchase-cluster triage (2026-11-24)

**Audit cutoff:** 2026-11-24 09:12 UTC  
**Main HEAD at preflight:** `5347dfe5bb591e7c58a8e57680703bac1991597e`  
**Disposition:** retain UPST as an in-universe descriptive purchase-cluster candidate; retain HOS and PICS as out-of-universe controls/watchlist observations. No event is signal-eligible and no return test is authorized.

## 1. Repository and Actions preflight

- Actions runs API: **8,109 total runs**; latest 100 contain **90 success / 10 failure**; **0 active** and **0 queued**.
- Branches: **380** (four pages); open PRs: **72**; workflow files: **96**.
- Main HEAD: `5347dfe5bb591e7c58a8e57680703bac1991597e`.
- Inspected latest relevant runs, jobs, logs and artifact metadata:
  - Form 4 [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) — complete; both watermarks found.
  - Form 144 [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) — complete; 118 new accessions, 801 new detail rows.
  - FINRA Reg SHO [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) — complete at workflow level, but six CNMS files rejected for duplicate BCPC/TPC rows.
  - CFTC TFF [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) — complete; no new reports/revisions.
- No relevant workflow was running, queued, dispatched, rerun or cancelled. The global Actions run list is now retrievable through the repository Actions runs API; this supersedes the Phase 591/590 statement that the connected interface exposed only specific run retrieval.

## 2. Current Form 4 ledger census

Inputs:
- `research/data/sec_form4_first_seen/transaction_details.csv` (129 transaction rows; 41 rows coded P/A).
- `research/data/sec_form4_first_seen/reporting_owners.csv` (61 owner-sidecar rows).
- Frozen 335-symbol snapshot recovered from commit `1aa1b91f383ce9cef375a43e775c736a27356a5f`, blob `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7`, SHA-256 `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`.

Exact static-snapshot match:
- 15 transaction rows across **SE, APO and UPST**.
- This is descriptive ticker overlap only; the 335 file has no effective dates and does not establish historical F80 membership or security-class identity.

### UPST — in the frozen snapshot

- Two Form 4 purchase rows (code P, acquired) dated 2026-11-19 and 2026-11-20: **110,000 shares**, approximately **US$1,811,053**.
- Both rows carry a trust mention; neither has a 10b5-1 filing flag in the current ledger.
- The same issuer ledger also contains four disposal rows (19,502 shares in total; compensation/tax-withholding context on three rows and a 10b5-1 mention on one) and one 419,290-share code-J gift/transfer row. These are different economic events and are **not netted** against the purchases.
- The two purchases are one issuer-level cluster for research counting, not two independent issuer observations.
- Both purchase rows remain `research_observation_eligible=false`, `signal_eligible=false`; public-availability, security identity, historical F80 membership, owner attribution and transaction-semantics gates are not all certified.
- The observed first-seen upper bound is 2026-11-23 07:48:52 UTC. It is a conservative receipt bound, not the exact SEC publication time.

### HOS — out of the frozen snapshot

Two direct Form 4 purchases on 2026-11-20:
- Todd M. Hornbeck, President & CEO, director and 10% owner: 202,300 shares at a reported weighted-average US$5.024 (approximately US$1,016,355).
- Benjamin M. Fink, director: 47,000 shares at a reported weighted-average US$4.90 (approximately US$230,300).
- Combined: **249,300 shares / approximately US$1,246,655**.
- SEC filing pages identify the reporting persons and roles:
  - [Todd M. Hornbeck Form 4, accession 0001284591-26-000004](https://www.sec.gov/Archives/edgar/data/866829/000128459126000004/0001284591-26-000004-index.htm)
  - [Benjamin M. Fink Form 4, accession 0001312482-26-000001](https://www.sec.gov/Archives/edgar/data/866829/000131248226000001/0001312482-26-000001-index.htm)
- Both filings report weighted-average prices across multiple transactions and do not have the Rule 10b5-1 box selected. Code P and weighted-average pricing do **not** establish that executions were open-market rather than private; no venue claim is made.
- HOS is absent from the frozen 335-symbol snapshot, so it is an out-of-universe observation, not an F80 candidate. Canonical owner-sidecar enrichment is still pending.
- The current capture's first-seen upper bound is 2026-11-24 05:22:13 UTC; no signal is authorized.

### PICS and other F80 matches

- PICS has three director purchase filings totaling 114,962 shares / approximately US$556,660. It is outside the frozen 335 snapshot.
- SE's seven matched rows are sales with a Rule 10b5-1 mention; treat as a negative-control/plan-context observation, not discretionary selling.
- APO's matched row is a 1.5-million-share code-J disposition with no transaction price; it is a transfer/other transaction, not a priced market sale.

## 3. Interpretation

- The new HOS cluster is a descriptive insider-purchase event, but outside the F80 universe and not proof of informed trading.
- UPST is the only current purchase cluster among the exact F80 snapshot matches. It remains a candidate only: trusts, transaction venue, owner-line attribution, filing-time bounds and historical security membership require adjudication.
- Form 4 code P, absence of a 10b5-1 flag, direct/indirect ownership and a weighted-average price are not individually sufficient to classify an event as discretionary open-market buying.
- Cluster by issuer and event window; do not count multiple insiders or multiple accessions as independent observations. Keep gifts, option exercises, tax withholding, vesting and plan-driven sales in separate categories.

## 4. Next gate

1. Complete canonical owner-sidecar enrichment for the new HOS accessions and recheck UPST's owner-to-transaction links.
2. Resolve remarks/footnotes and transaction venue where the filing supports it; leave venue unknown otherwise.
3. Reconcile each issuer/security to an effective-dated listing/class master and historical F80 membership.
4. Apply the first-seen/next-executable-session clock; never use filing date or transaction date as the knowledge timestamp.
5. Only after enough independent eligible issuer-events accumulate, preregister an issuer-cluster event panel and test incremental information against frozen LTM/F80 with identical exposure/costs, chronological OOS, block bootstrap and leave-one-event/time-block-out controls.

No forward returns, event-study statistic, alpha test, OOS, bootstrap or LOO was run. New signals admitted: **0**. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, exposure, costs, holdout or production changes.
