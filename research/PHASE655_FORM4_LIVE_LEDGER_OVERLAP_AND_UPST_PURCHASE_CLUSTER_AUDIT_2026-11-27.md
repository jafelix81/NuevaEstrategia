# Phase 655 — SEC Form 4 live-ledger overlap expansion and UPST purchase-cluster adjudication

**Audit cutoff:** 2026-11-27 02:37 UTC  
**Main HEAD before documentation:** `4833e40c4b5b38fab7e6fcafa1610571b891ebbb`  
**Disposition:** the current structured Form 4 ledger has expanded from the earlier 70-row audit to 276 transaction rows. Exact-symbol overlap with the static 335-ticker reference now yields 41 rows across 21 accessions and 12 symbols. A two-owner UPST purchase cluster is worth preserving as a research hypothesis, but neither open-market execution nor historical F80 membership is established. All 41 rows remain signal-ineligible. No returns were inspected.

## 1. Preflight and controls

- Latest 100 Actions runs: **73 success / 17 failure / 10 cancelled**.
- Queued, waiting, requested, pending or in-progress runs: **0**.
- Open pull requests: **85**; the latest full branch census remains 407 branches.
- Current main HEAD verified as `4833e40c4b5b38fab7e6fcafa1610571b891ebbb`.
- Latest natural Form 4 run [45917890802](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45917890802) succeeded: **82/82 offline tests**; both feeds passed continuity/watermark checks; no new accession/event; the bounded backfill appended 53 transaction rows, 206 transaction-linked footnote references, 29 additional footnote references and 13 owner rows.
- Latest natural SEC 13F run [45910142871](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45910142871) succeeded; 29 existing accession observations, no new accession, no holdings/XML downloaded and zero eligible rows.
- Latest natural Form 144 run [45906061652](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652) succeeded; 835 accessions / 5,537 detail rows, no signal admitted.
- FINRA Phase 650 PR validation [45895296971](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45895296971) passed 62/62 offline tests; live capture was skipped. No natural post-merge capture was visible.
- PR [#199](https://github.com/jafelix81/NuevaEstrategia/pull/199) remains Draft and unmerged. This phase updates its earlier one-overlap finding using the current mainline ledgers; it does not merge or modify that branch.
- No workflow was dispatched, rerun, cancelled or duplicated. No schedule, secret, workflow permission or production setting was changed.

## 2. Immutable inputs and method

The exact static reference is `research/phase44_frozen_universe_335_tickers.csv`, recovered from commit `1aa1b91f383ce9cef375a43e775c736a27356a5`, Git blob SHA-1 `7edbd62b4fb34a6123276e4ce45cb3c1c62479c7` (335 unique tickers; SHA-256 recorded in Phase 455 as `f850655a22a8843dad90e9562b3152b9ca064560586109022b5bfd205a003dda`).

Current mainline inputs:
- `research/data/sec_form4_first_seen/transaction_details.csv` — blob `a314421b76333f050a3228071025e448ac8ca840`
- `research/data/sec_form4_first_seen/reporting_owners.csv` — blob `1dea0f28d44e4d0a2a76ac2c24bddb916747fcf0`
- `research/data/sec_form4_first_seen/footnote_references.csv` — blob `941a7cb2342ce063ac4f912d184f86cce52f905e`

Method: include only `transaction_row` records; compare `issuer_trading_symbol_normalized` after outer trim and uppercase to the 335 static tickers; group by accession before counting events. No ticker aliases, issuer-name fuzzy matches, security-class inference, corporate-action adjustment or historical membership inference is applied. This is an exact-symbol overlap audit, not a point-in-time security-master join.

## 3. Current live-ledger overlap

| Measure | Result |
|---|---:|
| Structured detail records, all types | 416 |
| Transaction rows | 276 |
| Distinct issuer symbols in transaction rows | 98 |
| Exact-symbol overlap transaction rows | **41** |
| Distinct overlap accessions | **21** |
| Distinct overlap symbols | **12** |
| Overlap accessions with complete owner sidecar | 13 |
| Overlap accessions still missing owner sidecar | 8 |

The 12 exact-match symbols are **AAPL, ANET, APO, BLK, CVX, DELL, LITE, LYV, SE, SYK, TEAM and UPST**. Accessions by symbol: UPST 6, LYV 4, DELL 2, and one each for the other nine symbols.

Transaction-code counts across the 41 rows: **S 20, P 11, J 2, M 2, F 5, G 1**. The filing-level Rule 10b5-1 indicator is affirmative for 26 rows and negative for 15. Non-exclusive parsed footnote flags across rows: Rule 10b5-1 mention 26, compensation/vesting 10, tax/withholding 8, trust 14 and gift/donation 1. A missing plan flag or absent remarks flag is not proof of discretionary intent.

Every one of the 41 rows remains:
- `research_observation_eligible=false`
- `signal_eligible=false`
- `public_availability_certified=false`
- `security_identity_verified=false`
- `historical_f80_membership_verified=false`
- `owner_attribution_verified=false`
- `transaction_semantics_verified=false`
- `economic_event_new_trade_authorized=false`

The static 335-symbol snapshot does not establish that any issuer was an active F80 member on its transaction date. The eight missing owner sidecars and filing-grain-only owner links remain unresolved.

## 4. Purchase-cluster hypothesis: UPST

The current ledger contains two non-10b5-1-flagged `P` purchase accessions for Upstart Holdings (UPST), by two different reporting owners on consecutive trading dates:

| Reporting owner | Filing role | Transaction date | Reported purchase | Reference value | Ownership |
|---|---|---|---:|---:|---|
| Paul Gu | CEO, director | 2026-11-19 | 50,000 @ $17.2013 | $860,065 | Indirect, Gu Qiao Family Trust |
| Dave Girouard | Director, 10% owner | 2026-11-20 | 60,000 @ $15.8498 | $950,988 | Indirect, 2008 D&T Girouard Revocable Trust |

Combined reported quantity: **110,000 shares**. Combined quantity-times-weighted-average-price reference value: **$1,811,053**. This arithmetic is not a confirmed cash payment or proof of execution venue.

Source adjudication:
- The Paul Gu SEC submission reports transaction code `P`, `aff10b5One=0`, 50,000 shares acquired, indirect ownership by trust, and a weighted-average purchase price based on multiple transactions at $17.1959–$17.39. [SEC submission text](https://www.sec.gov/Archives/edgar/data/1647639/000183281226000016/0001832812-26-000016.txt).
- The Dave Girouard filing reports code `P`, 60,000 shares acquired at a weighted average of $15.8498, indirect trust ownership, and the 10b5-1 box unchecked. Its footnote identifies the 2008 D&T Girouard Revocable Trust and a weighted-average price range of $15.76–$15.95. [SEC filing index](https://www.sec.gov/Archives/edgar/data/1832805/000183280526000011/0001832805-26-000011-index.htm) · [parsed filing/footnotes mirror](https://form4.troubledyouth.org/filings/1647639/0001832805-26-000011).
- The SEC defines transaction code `P` as **“open market or private purchase”**. The code alone does not distinguish those venues. [SEC ownership transaction codes](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html).

Both owner sidecars are complete at filing grain, but the repository still marks transaction-line owner attribution unverified. The shares are reported indirectly through trusts. The absence of a 10b5-1 checkbox does not establish discretionary intent, and code `P` does not prove an open-market execution. This is one issuer-level cluster with two owner filings, not two independent issuer observations.

### Conservative availability clock

Both SEC acceptance timestamps are after the Friday 2026-11-20 regular-session close:
- Girouard: `2026-11-21T01:21:55Z`
- Gu: `2026-11-21T01:22:19Z`

The collector interval for both accessions is bounded by `2026-11-21T00:51:03Z` and `2026-11-23T07:48:52Z`; the upper bound is Monday 2026-11-23 at 02:48:52 ET. It is a collector-observation upper bound, not an exact public-release timestamp. Conservatively, the first regular session after that upper bound is Monday 2026-11-23. Under the project's daily-bar rule, the first completed bar is Monday's close and the next executable session would be Tuesday 2026-11-24. This is a timing rule only; no price series or return was inspected.

**Disposition:** retain the UPST two-owner purchase cluster as a narrowly scoped hypothesis for later research, conditional on proving transaction venue, effective-dated security identity/F80 membership and rights-cleared prices. It is not an admitted signal and has no demonstrated predictive or economic edge.

## 5. Negative controls and interpretation

- **SE:** the previously known seven sale lines are one accession, not seven events. The owner sidecar is now complete: Wang Yanjun, CCO and General Counsel. The filing has an affirmative Rule 10b5-1 indicator and all seven lines carry that plan context. Retain as a planned-trading negative control, not a discretionary bearish insider event.
- **TEAM:** nine `P` lines are one accession by Michael Cannon-Brookes, not nine events. The filing explicitly says the transactions were effected pursuant to a Rule 10b5-1 plan adopted 2026-08-09; the shares are held by CBC Co Pty Ltd as trustee for the Cannon-Brookes Head Trust. Exclude from discretionary purchase hypotheses.
- **UPST:** the two `P` accessions are the only non-plan `P` lines in this overlap cohort. They remain ambiguous as to open-market versus private purchase and are trust-held. Do not infer that all remaining non-plan `S` rows are discretionary sales.

The expanded overlap corrects the earlier narrow one-symbol snapshot, but it does not establish historical F80 membership or signal power. The 41 rows are not independent observations; accession and issuer clustering must be respected.

## 6. Next gates

1. Continue bounded owner and footnote enrichment; eight of the 21 overlap accessions still lack owner sidecars. Do not infer owners from issuer or accession prefixes.
2. Preserve transaction-level footnote resolution and multi-owner quarantine. A filing-level owner record is not automatically a verified owner-to-line link.
3. Build or obtain an effective-dated issuer CIK / security-class / CUSIP / FIGI / ticker / listing crosswalk and historical F80 membership before any event study.
4. Resolve open-market versus private-purchase semantics for the UPST `P` lines. Until then, treat the event as a reported purchase, not a confirmed market buy.
5. The Phase 649 price/volatility rights gate remains unresolved. No price download, quote, vendor contact, trial or purchase is authorized; the data budget remains **USD 0**.
6. Only after those gates pass, preregister an issuer-cluster event test using conservative availability, chronological OOS, identical exposure/costs, bootstrap and LOO. No forward outcomes were inspected in this phase.

## 7. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- New signal promoted: **none**.
- Incremental alpha demonstrated: **none**.
- New OOS / bootstrap / LOO: **none**.
- Holdout untouched.
- No universe, feature, parameter, cost, exposure, capital, production or holding-period change.
- No paid data or options-data spend.
