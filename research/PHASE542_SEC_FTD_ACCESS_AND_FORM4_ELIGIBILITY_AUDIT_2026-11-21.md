# Phase 542 — SEC FTD access gate and Form 4 eligibility census

**Audit cutoff:** 2026-11-21 07:36 UTC  
**Main HEAD at preflight:** `712dbaf7c94e1a3e937edf6dfe2ffeccb0eef940`  
**Disposition:** SEC FTD remains a credible public historical candidate, but its actual-file parser gate is blocked by SEC HTTP 403 because the workflow uses a generic, non-contact User-Agent. The workflow is now wired to the shared `SEC_USER_AGENT` Actions secret. The current Form 4 ledger is descriptive only: identity, exact public availability, transaction semantics and owner-to-line attribution remain unverified. No alpha test or strategy change.

## 1. Actions preflight and evidence reviewed

- Inspected the latest 100 repository Actions runs, jobs, logs, artifacts, branches, open PRs, issues and current research files. No run was in progress or queued.
- Branch pagination returned 364 branches (100 + 100 + 100 + 64). No duplicate workflow was dispatched or rerun.
- Main HEAD was `712dbaf7c94e1a3e937edf6dfe2ffeccb0eef940`.
- Phase 539 PR [#197](https://github.com/jafelix81/NuevaEstrategia/pull/197) is merged. Phase 537 PR [#196](https://github.com/jafelix81/NuevaEstrategia/pull/196) remains Draft and behind the current mainline; it was not merged.

### Latest relevant production captures

| Source | Run | Result |
|---|---:|---|
| FINRA Reg SHO | [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600) | Both jobs succeeded operationally; 8 HTTP-200 files, 8 rejected, 0 valid |
| CFTC TFF | [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977) | Four prospective weekly contract events captured |
| SEC Form 4 / 4-A | [44846461134](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134) | Feed poll, structured detail backfill, owner enrichment and crosswalk succeeded |
| SEC Form 144 / 144-A | [44847230610](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610) | 91/91 acceptance reconciliations, no unresolved events |

FINRA run 44860690600 predates the Phase 539 merge at 05:22 UTC. Its artifact [14688803921](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600/artifacts/14688803921) contains only the compact summary; it has no duplicate-diagnostic output. All eight files failed with `duplicate_symbol_in_consolidated_file`; `state.json` remains empty. The next natural scheduled run is still required to validate the merged diagnostic. No aggregation rule is authorized.

The Form 4 and Form 144 run logs and artifacts were inspected, not just their overall conclusions. Form 4 artifact [14683520646](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44846461134/artifacts/14683520646) contains the owner and crosswalk summaries. Form 144 artifact [14684225291](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44847230610/artifacts/14684225291) contains the structured-ledger summary.

## 2. SEC Form 4 current-ledger census

The persistent `transaction_details.csv` contains 110 detail rows: 40 filing headers and **70 transaction rows** across 40 accessions and 32 issuer CIKs.

| Transaction code | Rows | Interpretation guard |
|---|---:|---|
| P | 27 | SEC definition includes open-market **or private** purchase; not automatically an exchange buy |
| S | 21 | Open-market or private sale; not automatically discretionary |
| A | 13 | Award/grant-related code |
| M | 6 | Exercise/conversion-related code |
| G | 2 | Gift-related code |
| F | 1 | Tax-related code |

The filing-level owner sidecar contains 29 owner rows across 20 accessions: 18 single-owner accessions and two multi-owner accessions (one with five owners, one with six). All 29 owner rows remain `signal_eligible=false`; all have `transaction_line_attribution_verified=false`. Multi-owner filings are filing-grain identities only and cannot be mapped to individual transaction lines.

All 70 transaction rows are currently ineligible on every relevant gate: research observation, signal eligibility, certified public availability, same-day intraday use, security identity, historical F80 membership, owner attribution, transaction semantics and authorization as a new economic trade are all false.

The first-seen intervals are bounded metadata, not exact public availability. Across the 70 transaction rows, interval width is 6.20–8.53 hours (median 8.32 hours). Use the upper bound conservatively; do not infer same-day intraday tradability. EDGAR acceptance time is parsed but is not a certified exact public-web release time.

The latest strict Form 144/Form 4 crosswalk contains three descriptive matches: two proposed Atea sales and one prior sale. It admits zero signals. Both proposed sales contain option-exercise-cost/tax-planning context; execution time is unknown and historical F80 membership is unverified.

The `AFF10B5ONE` indicator is filing-level, not a transaction-line label. An unchecked value does not prove discretionary trading. Code P explicitly includes private purchases. Do not promote raw P/S counts into buy/sell pressure without filing, footnote, owner and security-level adjudication.

## 3. SEC Fails-to-Deliver: actual-file gate failed before parsing

The existing Phase 43 workflow was triggered three times:

| Run | Date | Result |
|---|---|---|
| [40540331780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40540331780) | 2026-10-27 | Download step HTTP 403 |
| [40746722935](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40746722935) | 2026-10-28 | Download step HTTP 403 |
| [41065549815](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41065549815) | 2026-10-30 | Download step HTTP 403 |

The job logs show the workflow hardcoded `User-Agent: NuevaEstrategia research contact` with no monitored contact address. Each run failed on the first SEC ZIP download; parsing and artifact upload were skipped. This is an access/configuration failure, not evidence that the FTD source or its schema is invalid.

The FTD workflow did not consume the repository's shared `SEC_USER_AGENT` Actions secret. This phase changes it to read that secret, fail fast if it is absent, and never print its value. The secret must contain a project identifier and monitored contact email. Do not put the contact email or secret value in source code, issue comments or chat.

**Human prerequisite:** configure `SEC_USER_AGENT` in GitHub Actions repository secrets. The connected interface cannot inspect or set secret values. After configuration, run the existing bounded Phase 43 workflow once; do not start a historical backfill until both representative files parse and their CUSIP/ticker coverage is measured against the historical F80 universe.

FTD remains a conditional candidate. SEC reports the balance of unsettled CNS deliveries, not daily short-sale flow; fails can arise from long or short sales. The settlement date is not the information date. Retain the conservative half-month publication convention from Phase 43 and do not use the settlement date as a tradable timestamp.

## 4. Cross-source status and decisions

- **CFTC TFF:** run 44860341977 added four prospective reports for 2026-11-17, first received 2026-11-21 03:17:36 UTC. The historical archive has 3,043 rows, but no defensible full-history first-publication clock. Two prospective vintages remain insufficient for a predictive test.
- **FINRA Reg SHO:** no post-Phase-539 natural diagnostic capture yet. Eight files in the last pre-merge run were invalid; no first-seen state advanced.
- **SEC 13D/G:** historical event panel remains quarantined for subject/filer identity and event-date errors. The same `SEC_USER_AGENT` secret is still a prerequisite for authorized SEC retrieval; no new crawl was started.
- **Options:** vendor data remain conditional on lawful access, licensing, PIT/vintage and target-universe coverage. No data were purchased.
- **Phase 20C:** latest recorded price-history census remains 328/335. AVB, EA, EQR, LPRO, ROKU, WBD and WBS still require terminal/successor total-return and corporate-action reconstruction; no ticker deletion or imputation.

## 5. Validation and next steps

The workflow change is limited to passing the secret into the download step and failing clearly if it is absent. It does not change the SEC URLs, parser, data scope or strategy. The PR is Draft because the actual SEC request cannot be validated until the repository secret is configured.

Next gates:
1. Human: configure `SEC_USER_AGENT` with a monitored contact.
2. Run the existing Phase 43 two-file sample once; require both downloads and parser checks to pass.
3. Measure CUSIP/ticker completeness, duplicates, date ordering and frozen-universe overlap before any FTD feature.
4. Wait for the next natural FINRA Reg SHO capture to validate Phase 539 diagnostics.
5. Continue prospective SEC/CFTC captures only; preserve all first-seen upper bounds and revisions.

## Frozen controls

- `F80_TOP20_PARTIAL50_BASELINE_C20` unchanged.
- New signals admitted: **0**.
- No backtest, event study, OOS, bootstrap, LOO, cost, exposure, universe, holdout or production change.
