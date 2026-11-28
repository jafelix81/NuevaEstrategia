# Phase 683 — FINRA Reg SHO source-channel rights and research-use gate

**Audit date:** 2026-11-28 UTC  
**Main base:** `1192a6c28a3da86ee84109497857a5a0bc8cd8d4`  
**Disposition:** place the direct FINRA CDN Reg SHO collector and all FINRA-CDN-derived predictive use on a rights hold pending written scope clarification or migration to the separately licensed FINRA Query API. This is a conservative contract-risk gate, not a legal opinion or a finding of breach.

## 1. Why this phase was opened

The current Reg SHO collector does not use the FINRA Query API. `research/phase469_finra_regsho_daily_first_seen_capture.py` downloads daily files from:

`https://cdn.finra.org/equity/regsho/daily/CNMSshvol{yyyymmdd}.txt`

The scheduled workflow `.github/workflows/phase469_finra_regsho_daily_first_seen_capture.yml` polls those direct CDN files and persists an append-only database of polling events and symbol observations under `research/data/finra_regsho_daily_first_seen/`.

The latest inspected run, [46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821), appended 327 symbol observations for 2026-11-27, preserved source hashes and receipt bounds, quarantined 28 row occurrences across 14 duplicate symbols, and kept every row `signal_eligible=false`. The raw file bytes were not persisted. The existing Phase 20C branch uses FINRA data in a trading-prediction experiment; its historical close-of-signal-day entry defect remains a separate no-go.

## 2. Official FINRA Website Terms — direct CDN channel

FINRA's [Terms of Use](https://www.finra.org/terms-of-use), last modified 2023-11-09, define the “FINRA Website” as the FINRA.ORG site including its content and state:

- Permitted use is only the user's own non-commercial personal or professional use (section “Permitted Uses”).
- The restrictions prohibit creating a database of data using the FINRA Website, except where other specific terms expressly permit it.
- They prohibit bulk copying, data mining, scraping or similar harvesting.
- They prohibit using any portion of the FINRA Website in the development of software or in conjunction with machine learning, predictive analytics or other AI software, expressly including a model, algorithm or process designed to predict trades for or within a portfolio, fund or investment vehicle.

The SEC-approved FINRA rule filing describes the Daily Short Sale Volume File as being posted on FINRA's website after regular trading hours ([SR-FINRA-2009-064 filing](https://www.finra.org/sites/default/files/RuleFiling/p120030.pdf)). The current file is delivered from the `cdn.finra.org` subdomain.

**Scope limitation:** the current public Terms page does not expressly name the `cdn.finra.org/equity/regsho/daily/` path or separately state whether those direct CDN files are governed by a distinct license. The historical rule filing says the daily files are posted on FINRA's website, but that alone is not a definitive legal interpretation of the current CDN distribution. A third-party description is not treated as authoritative. Accordingly, this audit does not conclude that a breach occurred; it concludes that continuing to bulk-capture and use the CDN data in predictive research without clarification presents a material avoidable risk.

## 3. Separate FINRA Query API route

The FINRA Developer Center has a separate contractual route:

- [FINRA API Terms of Service](https://developer.finra.org/terms-and-conditions), last updated 2026-03-19. They require the Developer to accept the terms and use FINRA-issued access credentials. The general restrictions include not using the licensed materials to create a product or service that competes with FINRA, not distributing licensed material except as specifically allowed, and not bulk-copying through non-API methods.
- [Specific Terms for Equity Data](https://developer.finra.org/specific-terms-equity-data) govern Query API datasets in the `otcMarket` group. They allow internal use only for non-commercial personal or professional purposes, permit creation of derivative/resultant data, and prohibit further redistribution to end users. They list no additional dataset-specific restrictions.
- [Reg SHO Daily Short Sale Volume API documentation](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume) identifies the `otcMarket/regShoDaily` dataset and its public, firm and organization credential types. The dataset is limited to a rolling 12-month period; it is not a multi-year historical source.
- FINRA's [API support FAQ](https://developer.finra.org/support) states that individual users may create Public and Mock credentials; Public credentials are available at no cost and capped at 10 GB/month. Production access requires a Public, Firm or Organization credential, not a Mock credential.

This is a potentially viable alternative for internal non-commercial research, subject to the user personally accepting the applicable terms and provisioning a Public credential. The terms reviewed do not contain the same express predictive-analytics prohibition found on the FINRA Website Terms page; this is not an affirmative legal opinion that every proposed use is permitted. The API route also sacrifices historical depth beyond the rolling year unless another separately authorized dataset becomes available.

## 4. Source-channel decision matrix

| Channel | Contract / access position | Research disposition |
|---|---|---|
| Direct daily CDN files | Website Terms scope over the CDN path is not expressly resolved; Website Terms contain database, bulk-copy and predictive-analytics restrictions | **Rights hold** for further scheduled ingestion, database expansion and predictive use pending written clarification |
| FINRA Query API `otcMarket/regShoDaily` | Separate accepted API terms; Equity Specific Terms allow non-commercial internal use and derivative data; Public credential free; 12-month rolling window | Conditional alternative only after user acceptance and credential provisioning |
| FINRA Consolidated Short Interest API | Separate dataset and terms/credential route; not assumed covered by the Reg SHO CDN finding | Keep separately gated; audit its exact dataset terms before use |
| SEC EDGAR filings, CFTC public reports, other sources | Not FINRA materials; assess each source under its own terms, availability and PIT gates | Continue independent work where existing rights and source-quality gates pass |

## 5. Required handling pending resolution

1. Do not use the direct-CDN Reg SHO observations to fit, rank, optimize, backtest or promote a predictive trading signal while the scope question remains unresolved.
2. Do not add raw FINRA CDN payloads to GitHub, Actions artifacts or another archive pending rights clarification. Existing hashes and audit metadata do not grant additional rights.
3. Do not broaden the direct-CDN collector's lookback, frequency, storage or universe.
4. Do not merge or rerun the defective Phase 20C backtest. Its no-lookahead issue remains independent of this rights gate.
5. Continue other Smart Money research lines that have their own valid source-rights, PIT, identity and coverage controls; do not make FINRA the sole research path.
6. If the user elects the API alternative, first have the account holder review and accept the current FINRA API Terms, then provision a **Public** credential. Do not ask for or expose a secret in chat; store it only in the repository's approved secret mechanism. Before coding, verify the exact production metadata/schema, fields, date filters, pagination and source publication semantics.
7. If the user wants to retain the CDN route, obtain written clarification/permission from FINRA covering automated collection, persistent storage/database creation, and use in predictive analytics. No contact was made in this phase.

## 6. Repository and Actions preflight

- Inspected the latest 100 Actions runs and explicit active/queued states: zero active and zero queued.
- Inspected jobs, logs and artifacts for the latest Form 144, FINRA Reg SHO, CFTC TFF, Form 4 and 13F scheduled runs.
- Latest source runs inspected: Form 144 [46110032075], FINRA Reg SHO [46105917821], CFTC TFF [46105422375], Form 4 [46099559273], 13F [46084129349].
- No duplicate run, dispatch, rerun, cancellation, branch merge, code change, schedule change, credential change, vendor contact or data purchase occurred.
- Main base at audit start: `1192a6c28a3da86ee84109497857a5a0bc8cd8d4`.

## 7. Strategy disposition

- FINRA CDN-derived predictive use: **rights hold pending clarification**.
- FINRA API alternative: **conditional, not activated**.
- Signals promoted: **0**.
- Incremental alpha demonstrated: **none**.
- New OOS/bootstrap/LOO result: **none**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- No source, universe, feature, parameter, exposure, cost or holding-period change.
- Paid data spend: **USD 0**.

**Conclusion:** this phase identified a material source-rights gate that changes the priority of the FINRA line. The direct CDN feed must not be treated as automatically interchangeable with FINRA's separately licensed Query API. The safest next step is either written clarification for the CDN channel or a user-provisioned free Public API credential under the API terms. Broad Smart Money research continues on independently cleared sources.
