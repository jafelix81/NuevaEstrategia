# Phase 423 — commercial alternative-data catalog and PIT integrity audit

**Audit date:** 2026-11-15 21:28 UTC  
**Disposition:** PUBLIC-CATALOG TRIAGE ONLY. No paid data, account, sample rows, vendor contact, license acceptance or economic test. No source admitted.

## 1. Repository and Actions preflight

- Main HEAD at audit start: `0c37e249421323625c29006716cfff36f123bab6`.
- Latest 100 Actions runs: 7,659 total reported; latest 100 = 62 success, 37 failure, 1 cancelled; zero queued/in-progress/waiting/requested.
- Inspected 261 branches across three pages, 56 open PRs and all 63 workflow files. No workflow was started/rerun and no PR was changed.
- Latest visible run remains SEC Form 144 schedule run [43743993846](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846), created 2026-11-15 17:57:31Z and completed 17:58:08Z. Both jobs succeeded; offline regression 15/15. Live receipt 17:58:03Z; 55 feed observations (50 Form 144 + 5 Form 144/A), zero new accessions/events, zero candidate matches, no feed-window gap. Artifact [14173342433](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43743993846/artifacts/14173342433), SHA-256 `0f00cbcc4b2809f18cd8e7c0292b67713c21d55015aff6c06452d56031e50a10`. Job log confirms append-only state write and artifact upload.
- Latest CFTC Phase 384 run [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200) is still a branch-push bootstrap, not a prospective schedule capture: 11/11 tests, 3,035 historical rows, zero signal-eligible rows; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705), SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`.
- Both Phase 411 CFTC transition regression runs [43681298839](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681298839) and [43681270194](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43681270194) passed their offline jobs.
- The Phase 385 FINRA date-level census remains a completed draft/stacked branch result; mainline Phase 392 already records its 209/209 date-level publication-calendar pass and explicitly leaves intraday receipt, effective-dated identity and return-test gates closed. No stacked PR was merged.

## 2. New candidate provider: Obscura

The public Obscura catalog advertises a normalized, subscription-gated alternative-data API with SEC, FINRA, CFTC and derived market datasets. Catalog and schema pages are public; data rows require an account and active subscription. This audit used public descriptions only. No authenticated query or row-level sample was obtained.

**Important distinction:** a vendor field named `available_date` is not automatically a verified historical first-public timestamp. It must be tied to an upstream dissemination record or a prospectively captured immutable receipt. A calendar date derived from an event/session date is not equivalent to a first-receipt timestamp.

### 2.1 Flow metrics — high research interest, PIT admission blocked

The `flow_metrics` page describes daily derived factors built from top-of-book trade prints, including quote-rule/tick-rule signed volume, order-size buckets, OFI, slippage, impact and volatility. It refreshes every six hours. The public page does not establish a historical start date, per-symbol coverage, raw feed identity, correction-vintage policy, or first-receipt timestamps.

A material public-documentation inconsistency was found:
- The dedicated dataset page says `available_date = date(event_time)` (same session day) and says a prior +1-day rule was corrected.
- The public homepage's worked example shows `event_time=2026-07-14T00:00:00Z` with `available_date=2026-07-15`, and explains the day-after date as necessary because the daily bar is not knowable until the session closes and settles.
- The public descriptions also differ on the factor count (126 vs 127).

Do not choose one interpretation from these conflicting pages. Until the provider supplies a versioned ontology and actual first-receipt/correction evidence, `available_date` is not an admitted PIT clock.

Other methodological gates:
- `dataset` is described only as an internal feed code; the public page does not identify the underlying tape/vendor or exact exchange/SIP scope.
- Daily aggregates are finalized summaries, not intraday executable signals. No quote-event timestamp/quote-age field is described.
- The `flow_toxicity_score` uses post-pass z-scores over a symbol's trailing bucket series in the current upsert run. The exact prior-only window, historical recomputation policy and vintage stability need row-level proof; otherwise old scores may change when later data are ingested.
- `large_trade_reversal` uses five-print-ahead returns inside the bar. It can only be interpreted after the bar is complete and cannot be used as an intraday signal at the start of that session.
- The “large” order bucket is a fixed per-print notional threshold of at least $1,000. That is not a verified institutional identity or stable investor-size class; it is price- and instrument-dependent.
- The source classifies aggressor side from quote rule with tick-rule fallback. Classification error, crossed/stale quotes, trade-condition exclusions, venue coverage and corporate-action handling remain untested.

**Decision:** retain `flow_metrics` as a potentially useful daily microstructure candidate, not an institutional-flow source and not a PIT-admitted historical panel. Re-entry requires a lawful sample across multiple dates and symbols, raw source lineage, exact field/version definitions, immutable first-receipt/correction timestamps, historical inactive-security coverage, and independent reconciliation to raw trades/quotes. No purchase or contact.

### 2.2 SEC insider transactions — normalized convenience layer, not a new source

The `edgar_insider_transactions` schema describes transaction-level Forms 3/4/5, separates `occurred_on` from `available_date`, and derives availability from the EDGAR dissemination date via the filing index. This is directionally consistent with the repository's Phase 39 accession-level PIT work.

However:
- The public dataset page does not state its earliest complete history or frozen-universe security coverage.
- The public schema exposes symbol and issuer/owner fields but no clearly documented effective-dated permanent security identifier on the transaction row.
- Form 4 transaction code P is not guaranteed to be an open-market purchase; SEC instructions and Phase 279 distinguish open-market **or private** purchases. Do not label every P row discretionary open-market buying.
- The existing SEC flat-file route already has 2006–2026 history and reproducible accession acceptance joins. A paid normalized copy is not incremental information unless it materially improves identity, coverage or parser reliability.

**Decision:** keep raw SEC Form 4 as the primary route. Obscura may be considered only as a cross-check after a small lawful sample proves row-level equivalence, historical coverage, amendments, owner attribution and share-class mapping. No `insider_sentiment` aggregate is admitted.

### 2.3 Insider sentiment view — reject current derived grain

The public `insider_sentiment` page explicitly records that its availability leak was fixed by using the maximum constituent filing availability date, but also discloses an unresolved grain issue: the view groups by **filing/dissemination month**, not transaction month, after a column rename changed the bound column. Its `month` field is therefore not the transaction month implied by the product title. The view also nets transaction codes P and S, where P may include private purchases.

**Decision:** do not use this aggregate as a transaction-month insider signal. Use transaction-level rows and define a filing-availability-based aggregation independently, or require the provider to correct and version the view before reconsideration.

### 2.4 13F holdings — broad history, but existing identity/coverage failure remains

The `edgar_13f_holdings` page advertises history back to 2000, with 2009–2012 materially thinner, and provides manager CIK, CUSIP, period end and SEC dissemination availability. It also documents a nontrivial historical value-unit normalization procedure: pre-2013 text filings may require inference from table headings/annotations and median implied share price; XML-era filings use schema version.

This is useful schema transparency, but does not solve the repository's historical security crosswalk or the previously failed 335-name coverage gate. Parser-normalized values need independent validation, amendments and joint-manager attribution need to be retained, and 13F remains a delayed long-position disclosure rather than complete institutional exposure.

**Decision:** keep 13F parked. Do not buy a normalized copy or run a reduced-universe test to bypass Phase 22C/386.

### 2.5 Schedule 13D/G — possible activist-event parser cross-check

The `edgar_sc13` page exposes one row per reporting person, subject CIK, CUSIP where available, reporting person, percent/class, aggregate shares, filing type, `occurred_on` and EDGAR dissemination `available_date`. It notes that older filings may lack structured cover fields and CUSIP may be null.

This could help validate the existing 13D/G extraction path, but it does not itself prove full historical coverage or cure the repository's earlier zero-event-date parser failure. 13D and 13G must remain separate hypotheses because their disclosure deadlines and investor intent differ; amendments must not be backdated.

**Decision:** conditional parser cross-check only. No event or return test until raw-document reconciliation, CUSIP/issuer identity and historical coverage pass.

### 2.6 FINRA short interest and OTC weekly

- `finra_short_interest` is described as twice-monthly settlement-date short interest, separate from daily Reg SHO short volume. Its `available_date` is stated as settlement date plus seven US equity business days. It is symbol-only, with no CUSIP/CIK on the row; historical depth is not specified on the public page. This is a potentially useful complement to daily short volume, but not an independent source from FINRA.
- `finra_otc_weekly` is a normalized copy of FINRA weeklySummary rows. Its `available_date` is based on FINRA's own `initialPublishedDate`; it is a convenience layer, not incremental information beyond the repository's raw FINRA T1 panel and Phase 385 date audit. FINRA's public API documentation describes a rolling four-year historical dataset.

**Decision:** do not pay for duplicated FINRA data unless a lawful sample proves a material improvement in revision-vintage retention, identity or reproducibility. Short interest remains a separate candidate, but needs a full historical coverage and publication-calendar audit before any join/test.

### 2.7 CFTC COT

The `cftc_cot` page describes the **Legacy futures-only** COT classification, with Tuesday survey date and a `available_date` normally on Friday after three US federal business days. This is not the same report as TFF and should not be substituted for the richer TFF categories already being captured. It may be a complementary broad-market positioning series, but public page evidence does not establish a sufficiently deep, complete historical equity-index panel or independent incremental information.

**Decision:** no new COT workflow. Continue the existing TFF capture and only consider Legacy COT as a preregistered macro comparator if a specific incremental hypothesis justifies it.

## 3. Candidate ranking after the audit

| Candidate | Potential role | Binding blocker | Disposition |
|---|---|---|---|
| Obscura flow_metrics | Daily order-flow/microstructure context | Conflicting PIT semantics, unknown raw feed lineage/history/coverage, no sample | Conditional; no alpha |
| Raw SEC Form 4 | Insider purchase/sale events | Frozen-universe security identity and code filtering | Continue existing free SEC route |
| Obscura insider_sentiment | Monthly insider aggregate | Filing-month grain, P-code ambiguity | Reject current view |
| Obscura 13F | Delayed manager holdings | Historical crosswalk and coverage; parser normalization | Park |
| Obscura 13D/G | Activist/passive ownership events | Legacy parser/coverage and CUSIP gaps | Conditional parser cross-check |
| FINRA short interest | Twice-monthly short positioning | Historical coverage and symbol-only identity | Audit separately; not independent |
| FINRA OTC weekly | ATS/non-ATS venue concentration | Duplicates official FINRA feed | No paid acquisition |
| Legacy CFTC COT | Macro positioning comparator | TFF overlap, history/coverage not demonstrated | No workflow |

## 4. Exact evidence required before any provider trial or purchase

1. Written data dictionary/version history and upstream source lineage for each candidate dataset.
2. Historical start/end dates and row counts by symbol/contract, including inactive/delisted securities, for the exact frozen diagnostic universe and historical dates.
3. Raw sample rows from at least 2016, 2020, 2024 and 2026, with file/query hashes and deterministic re-download.
4. First-public/first-receipt timestamps and correction, cancellation, replacement and restatement vintages; do not accept a synthetic `available_date` as proof.
5. Effective-dated CUSIP/FIGI/CIK/share-class crosswalk, including mergers, ticker changes and delisted/predecessor securities.
6. Feature calculation code or exact formula/version, missingness rules, lookback cutoffs and proof that trailing normalizations are prior-only and stable across later refreshes.
7. Written license terms covering the intended research/trading use and cost. No trial, subscription, purchase or contact is authorized by this audit.

## 5. Research controls

- No Obscura account, API key, vendor contact, trial, data purchase or license acceptance.
- No row-level provider data obtained or persisted.
- No source or signal admitted.
- No forward-return, alpha, chronological OOS, bootstrap, LOO or holdout test.
- FINRA Phase 20C remains blocked at 328/329 valid price histories.
- CFTC TFF remains at bootstrap only; no prospective observation yet.
- `F80_TOP20_PARTIAL50_BASELINE_C20`, universe, parameters, holdout, capital, exposure and production remain unchanged.

## Official/public references

- Obscura catalog: https://obscura.trade/datasets/
- Flow metrics: https://obscura.trade/datasets/flow-metrics/
- Form 4 transactions: https://obscura.trade/datasets/edgar-insider-transactions/
- Insider sentiment: https://obscura.trade/datasets/insider-sentiment/
- 13F holdings: https://obscura.trade/datasets/edgar-13f-holdings/
- Schedule 13D/G: https://obscura.trade/datasets/edgar-sc13/
- FINRA short interest: https://obscura.trade/datasets/finra-short-interest/
- FINRA OTC weekly: https://obscura.trade/datasets/finra-otc-weekly/
- CFTC COT: https://obscura.trade/datasets/cftc-cot/
- FINRA Developer Center: https://developer.finra.org/docs
- SEC Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- SEC Form 4 instructions: https://www.sec.gov/files/form4.pdf
