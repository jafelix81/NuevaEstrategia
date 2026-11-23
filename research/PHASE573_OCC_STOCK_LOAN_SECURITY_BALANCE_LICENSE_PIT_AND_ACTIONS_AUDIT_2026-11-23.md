# Phase 573 — OCC stock-loan security-level data gate and cross-source Actions audit

**Audit cutoff:** 2026-11-23 11:37 UTC  
**Main HEAD at preflight:** `424011a05c444edabdf1ef82b4b538b70162be47` (Phase 572 snapshot)  
**Disposition:** OCC Stock Loan Balance by Security is a potentially useful *partial-market borrow-pressure context* source, but automated collection is not authorized by the published OCC website terms. Keep it parked pending written authorization and a schema/coverage sample. No source, signal, alpha, or production admission.

## 1. Repository and Actions preflight

- Actions total: **8,074**. Latest 100: **96 success / 4 failure**. Active, queued, waiting, requested or pending runs: **0**.
- Branch census: **373** (100 + 100 + 100 + 73). Open PRs: **72**.
- Main HEAD remained `424011a05c444edabdf1ef82b4b538b70162be47` at the final pre-write check.
- Latest scheduled runs in the Actions API:
  - Form 144 / Phase 403: [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123), 2026-11-23 08:18:38 UTC, success.
  - Form 4 / Phase 476: [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578), 2026-11-23 07:48:40 UTC, success.
  - FINRA Reg SHO / Phase 469: [44860690600](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860690600), 2026-11-21 03:21:20 UTC, success but predates the Phase 539 parser fix.
  - CFTC TFF / Phase 384: [44860341977](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44860341977), 2026-11-21 03:17:21 UTC, success.
- No run was active, so no workflow was duplicated, dispatched, rerun, cancelled, or replaced.

### 1.1 Form 144 — first natural post-Phase-565 validation rechecked

Run [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123) completed both `offline-regression` and `live-capture` successfully. I inspected the job steps and logs and downloaded the relevant artifacts. ZIP hashes match GitHub's artifact digests.

| Artifact | Purpose | ZIP SHA-256 |
|---|---|---|
| [14800551409](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800551409) | Current descriptive refresh | `97a317d501a908ae2340e6f900bc3fdf241c7a6e1755bfd50a45338802770047` |
| [14800277734](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800277734) | Phase 565 post-capture 10b5-1 audit | `7d8d62289b21ce28de22ebf408fd461534d1cea0b95034f00379b0e51e741c58` |
| [14799993648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14799993648) | Phase 403 capture + Phase 516 quality audit | `3ec04baa014f21361478ea2110f2601278dd7122cdb9bfbb9a09c7eabde9f821` |

Verified live-capture facts:

- Feed responses: 53 observation rows (51 unique Form 144 accessions and 2 unique Form 144/A accessions); no new accession/event.
- Ledger: **305 accessions / 2,244 detail rows**.
- Backfill: 10 existing accessions parsed; 48 detail rows appended; 258 accessions remain.
- Parsing errors: 0. Source-hash matches: 2,244. Mismatches: 0.
- Phase 516 count/hash reconciliation passed.
- Phase 549 post-capture reconciliation passed. This is the first natural production run validating the dedicated post-capture artifact after Phase 565 integration.
- Public-availability-certified headers: 0. Signal-eligible filings: 0.

Phase 549 descriptive result (not a signal):

- 118/305 accessions have a formal plan-adoption date (38.69%), across 70 distinct dates.
- Plan-date-to-notice lag: median 183 days; range 72–546 days.
- Remarks classification: 10 positive explicit, 4 negative explicit, 1 ambiguous, 290 no mention.
- 107 of the 118 formal plan dates have no explicit Rule 10b5-1 mention in remarks.
- Four negative Fermi notices total 2,253,270 proposed units and describe sell-to-cover/tax-withholding context. Form 144 is a proposed-sale notice, not confirmation of execution.

The 10b5-1 audit explicitly records no alpha, OOS, bootstrap or LOO test; no signal admitted; F80 remains frozen.

### 1.2 Form 4 — latest natural capture rechecked

Run [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578) completed both jobs successfully. Artifact [14798359037](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578/artifacts/14798359037) was downloaded and inspected; its ZIP SHA-256 is `55a7d8fa26c06b523318c5b7e829d396a7afbcfadcdf181904ad834c18297033`.

- 28 unique new Form 4 accession IDs; 57 candidate occurrences (29 same-feed duplicate occurrences); 59 accession-observation rows including 2 pre-existing observations.
- Feed's latest `updated` timestamp: 2026-11-21 02:48:30 UTC. Collector first receipt: 2026-11-23 07:48:51 UTC. This is a collector receipt upper bound, not exact public availability.
- New filing XML/text and raw transaction rows were not downloaded/stored. Public availability is not certified.
- Structured backfill: 10 prior accessions parsed, 39 detail rows appended, 0 parse errors; 1,776 bounded accessions remain in that queue.
- Owner identity backfill: 10 single-owner accessions parsed, 10 owner rows appended; 20 bounded owner accessions remain. Transaction-line owner attribution is not verified.
- Crosswalk: 3 descriptive rows (2 proposed-sale matches and 1 prior-sale match), 0 signal-eligible matches. The matched remarks point to option exercise/exercise-price/tax-planning/withholding context; execution intraday time and historical F80 membership are not verified.

### 1.3 Schedule-delivery gap at cutoff

No newer schedule-triggered run appeared in the latest 100-run inventory by 11:37 UTC.

- Form 144 cron is `47 * * * *`. Since the 08:18:38 UTC natural run, the 08:47, 09:47 and 10:47 slots are absent; 11:47 had not yet arrived.
- Form 4 cron is `17 * * * 1-5`. Since the 07:48:40 UTC natural run, the 08:17, 09:17, 10:17 and 11:17 weekday slots are absent.

This is an observed schedule-delivery gap, **not proof that either workflow is administratively disabled**. The available read interface does not expose the workflow's administrative enablement or the repository's scheduled-action policy. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) is updated with the new missing slots; an administrator still needs to verify both workflow states and repository Actions policy. No cron or workflow configuration was changed.

The latest logs also emit a non-blocking GitHub Actions warning: `actions/checkout@v4`, `actions/setup-python@v5`, and `actions/upload-artifact@v4` target Node 20 and are currently being forced onto Node 24. Track this as maintenance; no dependency upgrade was mixed into the research phase.

### 1.4 PR and branch status

- Branches: 373. Open PRs: 72.
- PR #159 (FINRA Short Interest): Draft, **7 ahead / 155 behind** main; diverged.
- PR #204 (SEC FTD): Draft, **11 ahead / 32 behind** main; diverged.
- Neither branch is a safe merge candidate. No PR was merged or rebased.

## 2. New source sub-audit — OCC Stock Loan Balance by Security

OCC's current Stock Loan Volume area exposes a report family including Stock Loan Balance by Security. The batch-processing documentation provides a CSV endpoint example:

`stock-bal-by-security?reportType=Daily&dailyDate=10/2025&format=csv`

The parent Stock Loan Volume page lists report availability for the past 24 months. The endpoint is potentially useful because a security-level cleared-loan balance could provide a borrow-pressure/stock-loan activity context that is complementary to (not a replacement for) FINRA short interest, FINRA Reg SHO and SEC FTD.

**What is and is not established:**

- The public page labels the report as Daily and exposes a date parameter, but its example uses a month/year string. Exact row cadence, date-parameter semantics, field schema, revisions, first-publication time, and per-security history/gaps have **not** been verified from a sample.
- OCC's stock-loan programs cover loans cleared through OCC's Stock Loan/Hedge and Market Loan programs. They are not the entire U.S. securities-lending market. OCC's 2026 at-a-glance sheet lists 85 Hedge Loan Program members and $185.2B average daily loan value at year-end 2025; that is program scale, not proof of full-market or frozen-universe coverage.
- A loan balance is not short interest, short-sale flow, borrow availability, utilization, rebate/borrow fee, or beneficial-owner identity. It may include loans associated with market-making/intermarket hedges. Do not label a rise as institutional shorting without further evidence.
- OCC's Stock Loan Eligible Securities report is only retained for up to five days, so it is not a historical supply-availability panel.
- The public OCC Terms of Use (updated 2025-02-05) prohibit automated systems (including robots, spiders and offline readers) from accessing Services/Data and prohibit reproduction or exploitation for commercial purposes. A public batch URL is not an automated-use license.

**Decision:** conditional candidate only; no automated request, manual sample, account, subscription, or data acquisition was made. Revisit only after written OCC authorization/data-subscriber terms expressly cover automated capture and the intended quantitative research use. Then perform a bounded schema, timestamp/vintage, 24-month coverage, frozen-universe and delisted-security audit before any prospective ledger or feature construction.

Official references:
- OCC Stock Loan Volume: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/stock-loan-volume
- OCC Stock Loan Balance by Securities batch-processing specification: https://beta-md.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/stock-loan-balance-by-securities
- OCC Stock Loan Programs and clearing scope: https://www.theocc.com/clearance-and-settlement/stock-loan-programs
- OCC at a Glance — Stock Loan Programs (January 2026): https://www.theocc.com/getcontentasset/96bbe3ee-1ff1-4c0c-a643-d4180c4a4ed5/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/occ-toolkit-at-a-glance-stockloan-jan2026-f.pdf
- OCC Website Terms and Conditions: https://www.theocc.com/specialpages/legal/terms-and-conditions

## 3. OCC options-volume account-type recheck

The public OCC Volume by Account Type / Volume Query pages document daily, weekly, monthly and longer aggregation options over a stated 24-month window. The query can distinguish Customer, Firm and Market Maker account types and Calls/Puts for equity/index options, keyed by option or underlying symbol.

This is **not** directional investor flow:
- No signed buyer/seller aggressor side.
- No opening/closing classification.
- No beneficial-owner identity; Customer/Firm/Market Maker are clearing account categories, not retail/institutional identity labels.
- No per-stock open-interest series from the separate OCC Daily Open Interest endpoint; Phase 531 already rejected that endpoint as it returned market-wide monthly totals rather than security-level OI.
- No historical public-vintage/first-receipt ledger was established.

The same OCC Terms of Use restriction on automated access and commercial exploitation applies. Phase 531 already parked OCC Volume Query pending written authorization; this recheck confirms the account-type categories and available query grain but does not change that disposition. Do not build a “firm buying” or “customer selling” signal from unsigned volume.

Official references:
- OCC Volume by Account Type: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-by-account-type
- OCC Volume by Account Type Search Batch Processing: https://www.theocc.com/market-data/market-data-reports/other-market-data-info/batch-processing/volume-by-account-type-search-batch-processing
- OCC Volume Query: https://www.theocc.com/market-data/market-data-reports/volume-and-open-interest/volume-query
- Prior Phase 531 adjudication: `research/PHASE531_OBSCURA_MULTISOURCE_PIT_AND_OCC_RECONCILIATION_2026-11-20.md`

## 4. Other source gates retained

- **SEC Schedule 13D/G:** Schedule 13D remains the highest-priority public ownership-disclosure event hypothesis, but the 20,266-row legacy panel remains quarantined because subject-issuer identity and public-availability clocks are not certified. The Phase 485 parser is a building block, not a full rebuild. Rebuild remains blocked on the repository secret `SEC_USER_AGENT`; acceptance time is not exact public availability. Do not place the contact/user-agent value in code, PR text or chat.
- **FINRA Short Interest:** next publication is 2026-11-24 for settlement 2026-11-13. Existing Phase 447 single-date validation only; credentials and permitted-use confirmation are prerequisites. No query or dispatch made.
- **FINRA Weekly Summary / ATS:** approximately five years of query-API history remains conditional on row-level publication-vintage, identity and universe gates. The separate ATS archive endpoint remains blocked by HTTP 530; no challenge bypass or scraping workaround.
- **FINRA Reg SHO:** latest natural run predates Phase 539; corrected parser awaits a natural post-fix capture.
- **CFTC TFF:** 3,043 historical rows remain excluded from feature eligibility; only two prospectively captured vintages per tracked contract, insufficient for the preregistered test.
- **Options OPRA / Cboe:** history and features are promising, but license, per-symbol coverage and historical PIT/vintage rights remain unresolved.
- **13F / N-PORT:** broad 13F remains parked for identity/universe/45-day lag constraints; the N-PORT aggregate-share-growth hypothesis remains killed.

## 5. Research decision and next gates

1. Ask a repository administrator to verify Phase 403 and Phase 476 are enabled and that scheduled Actions are permitted. Do not create replacement workflows or change cron before that check.
2. Obtain the authorized FINRA credentials/terms for the existing Phase 447 one-date validation; use `settlement_date=2026-11-13` only after authorization.
3. Configure the SEC `SEC_USER_AGENT` secret for a bounded 13D/G sample; do not launch the 20,266-accession rebuild before identity, schema, hashes and PIT checks pass.
4. Keep OCC stock-loan and account-type data parked until written authorization; if cleared, first establish exact schema, release/vintage timestamps and universe coverage.
5. Continue natural Form 144/Form 4, FINRA Reg SHO and CFTC captures without backdating missed slots.

**Quantitative result:** new sources admitted = 0; new signals admitted = 0; incremental alpha demonstrated = none; new OOS/bootstrap/LOO results = 0; production changes = 0. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, costs, exposure, holding-period policy, holdout or model parameters changed.
