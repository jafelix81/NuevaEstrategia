# Phase 684 — Smart Money source reconciliation and FINRA CDN rights-hold enforcement

**Audit date:** 2026-11-28 UTC  
**Main HEAD at preflight:** `f7057f5a33e7a9814a56e36783dfd02556f86bfb`  
**Main HEAD after operational hold:** `066380e1e3c018aab9fcf02113f4d8076402add2`  
**Disposition:** enforce the existing Phase 683 direct-FINRA-CDN rights hold; continue only independently gated sources. No alpha or strategy change.

## 1. Repository and Actions preflight

- Latest 100 Actions runs: **80 success / 16 failure / 4 cancelled**; **0 queued or active**. GitHub reported 8,409 total runs.
- Open PRs: 86. Relevant drafts remain separate: #219 (13D/G discovery), #200 (Cboe OPRA), #188 (Massive Options), #204 (FTD credential integration), #159 (FINRA short interest), #262 stacked on #230 (13F report-period selector), and #5 (FTD universe coverage).
- PR #17 (N-PORT identity correction) remains open against an old base; it was not merged into main.
- No workflow was dispatched, rerun, cancelled or duplicated.
- Inspected jobs, logs and artifacts for the latest relevant Form 144, Form 4, FINRA Reg SHO, CFTC TFF, 13F and 13D/G runs. No run was active or queued.

## 2. Latest natural SEC capture — Form 144

Run [46155351208](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46155351208) completed both jobs successfully. Its four artifacts are unexpired; the main capture artifact is [15267855202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46155351208/artifacts/15267855202).

- **52 feed-observation rows** were appended. These are poll observations, not 52 new canonical accessions.
- The canonical event ledger remains **1,104 unique accessions**; no new canonical accession was added in this run.
- Ten previously known accessions were enriched: **49 detail rows** appended.
- Structured detail ledger: **986 accessions / 6,409 rows**; **118 accessions** remain without structured detail.
- Formal Rule 10b5-1 plan-adoption dates: **391 accessions**; 352 are also within the bounded research-observation cohort.
- Public-availability-certified accessions: **0**. Signal-eligible accessions: **0**.

The refreshed Form 144/Form 4 crosswalk remains descriptive only:

| Control | Result |
|---|---:|
| Proposed-sale matches | 17 |
| Distinct Form 4 accessions | 16 |
| Distinct issuers / reporting owners | 12 / 16 |
| Form 4 sale/disposition rows considered | 96 |
| Multi-owner accessions quarantined | 9 |
| Ambiguous transaction-reuse cases quarantined | 3 |
| Unresolved Form 144 acceptance clocks | 2 |
| Signal-eligible matches | **0** |

A Form 144 remains a proposed-sale notice, not proof of execution. The first-seen receipt is an upper bound, not exact public availability.

## 3. Form 4 — correct interpretation of the 156-accession cohort

The latest natural capture is [46099559273](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273), with artifact [15244348107](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46099559273/artifacts/15244348107).

- **156 new unique accessions / 156 canonical issuer events** were captured as bounded metadata.
- Entity ledger: 353 observations (351 candidate entity occurrences plus two watermark-boundary observations).
- 86 distinct issuer CIKs and 180 distinct reporting-owner CIKs.
- **149 filings have one reporting owner; 7 have multiple reporting owners.**
- No missing issuer entity, multiple issuer CIK, unknown entity role, quarantined accession, path/entity mismatch or exact duplicate entity-key group was reported.
- Research-observation-eligible rows: **0**. Signal-eligible rows: **0**.

Important semantic correction: the log field `multi_entity_accession_count=156` counts issuer/reporting-owner entity structure. It does **not** mean 156 filings have multiple reporting owners. The entity reconciliation shows 149 single-owner filings and seven multi-owner filings. The 156 are metadata filings, not 156 independently verified trades.

Bounded backfills on that run added 32 transaction-detail rows, 12 owner-identity rows and 29 footnote-reference rows; transaction-line owner attribution remains unverified. The current UPST purchase candidate remains one issuer cluster, not independent insider observations; venue, historical F80 membership and executable public-availability gates remain unresolved. The TEAM planned-trading case remains a Rule 10b5-1 negative control.

## 4. Other live-source state

| Source | Latest relevant evidence | Disposition |
|---|---|---|
| FINRA Reg SHO | [Run 46105917821](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821): seven partial files, 14 duplicate symbols / 28 row occurrences quarantined, 327 unique-symbol observations, one date, zero signal-eligible rows. Artifact [15247531846](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105917821/artifacts/15247531846) is only 2,246 bytes; raw source bytes are not retained. | Rights hold; no predictive use. |
| CFTC TFF | [Run 46105422375](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46105422375): 3,043 total rows, no newly admitted signal-eligible historical rows. | Keep as low-frequency macro positioning context; prospective sample remains insufficient. |
| SEC 13F | Natural capture [46084129349](https://github.com/jafelix81/NuevaEstrategia/actions/runs/46084129349): four new metadata accessions; no holdings XML/table downloaded; zero research/signal rows. PR #262 remains a draft stacked on #230. | Holdings history and PIT/security identity still required; no flow inference. |
| SEC 13D/G | [Run 45988473657](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45988473657): offline regression succeeded; live-sample job was skipped. | Highest-priority free institutional-disclosure path, but the 44-accession/five-quarter Phase 616 sample remains blocked on review/merge and manual `workflow_dispatch` with `run_live_sample=true` plus the `SEC_USER_AGENT` secret. |
| Form 4 / Form 144 | Current crosswalk has 17 proposed-sale matches and zero eligible matches. | Continue bounded owner, transaction-line, plan and PIT reconciliation; no return test. |

## 5. FINRA direct-CDN rights hold — operationally enforced

Phase 683 identified a material contract-scope uncertainty: FINRA Website Terms contain database, bulk-copy and predictive-analytics restrictions, while the direct `cdn.finra.org/equity/regsho/daily/` path is not expressly named in the current terms page. This remains a conservative risk hold, **not** a legal finding of breach.

The Phase 469 workflow still had cron `30 22,23 * * 1-5` after Phase 683. Leaving that schedule active would continue automatic collection while the rights question remained unresolved. I therefore updated `.github/workflows/phase469_finra_regsho_daily_first_seen_capture.yml` in commit `066380e1e3c018aab9fcf02113f4d8076402add2`:

- Removed the scheduled direct-CDN polling trigger.
- Kept offline regression on PR/push validation.
- Kept manual dispatch only with required boolean `rights_clearance_confirmed=true`.
- The live job is skipped unless that explicit acknowledgement is true.
- Reduced workflow permissions to `contents: read`; the paused workflow no longer commits/persists a direct-CDN ledger.
- No FINRA request, rerun, dispatch, raw-file download or additional observation was made.

This does **not** migrate the collector to the FINRA Query API. That is a separate channel under separately accepted API terms, with a rolling 12-month dataset window. The account holder would need to review/accept those terms and provision a Public credential before a migration is considered. No secret was requested or changed.

The existing Phase 20C branch remains a separate no-go: it uses signal-date close as the entry price even though the daily FINRA file is published after the regular session. The branch is now 12 commits ahead and 828 behind main; it was not merged or rerun.

## 6. Non-FINRA source feasibility — what is actually usable

### SEC MIDAS

The official SEC catalog currently lists 59 quarterly per-security ZIPs from 2012 Q1 through 2026 Q3, covering more than 4,800 securities. The catalog does not supply per-quarter first-publication timestamps or permanent security IDs. The public fields are ticker/name based. `HiddenVol` measures on-exchange executions against hidden resting orders; it is **not** dark-pool/off-exchange volume and does not identify buyer/seller or participant type.

Disposition: retain only as a conditional liquidity/market-quality or risk-context source. No ZIP payload was successfully downloaded or parsed in this phase; no historical PIT or 335-name identity gate is passed. Official catalog: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security

### OCC Volume Query

The Phase 53B audit passed short-window schema/coverage checks: 645/670 ticker-date responses valid (**96.27%**) across 2025-01-03 and 2026-11-02. The documented 24-month retention fails a multi-cycle OOS-history gate. The returned data provide account-type and call/put volume but no buy/sell aggressor side, opening/closing status, strike-level OI or expiry-level flow. Retain only as a possible recent complementary descriptor; do not call it informed flow.

### SEC Fails-to-Deliver

Phase 44's representative files covered 253/335 symbols (75.522%) in 2018 H1 and 316/335 (94.328%) in 2026 H2; 237/335 appeared in both. FTD is an aggregate balance outstanding at settlement date, not daily short-sale flow and not proof of naked shorting. Missing symbols cannot be treated as zero without an independent date-appropriate active universe. Phase 45's public-FTD-only identity gate is designed to fail for exactly this reason; its branch is 17 ahead / 755 behind main and was not run or merged. Park pending a reproducible effective-dated security master.

### Options / OPRA

Massive's published Options Advanced price was USD 199/month at the Phase 530 audit; its individual terms and the public-repository exposure are not cleared for this project. Cboe OPRA Option Trades/Quotes and Open-Close remain conditional on exact universe coverage, delivery/correction vintages, license and price. No account, sample, quote, purchase or vendor contact was made. The authorized data budget remains USD 0.

### N-PORT / 13F

N-PORT's 280-presentation / 28-quarter sample found short-position rows in only two filings; 156 of 176 short rows lacked ticker identity. It is too sparse and poorly mapped for a broad equity signal. The prior N-PORT share-balance-growth hypothesis remains killed. The 13F current capture is metadata-only; delayed holdings snapshots are not transaction flow.

## 7. Research decision and next gates

1. Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
2. Keep Phase 20C no-go; any successor requires authorized data, verified first receipt, next-session executable entry, frozen price/security snapshots and identical exposure/costs.
3. Prioritize Phase 616 SEC 13D/G only after its draft is reviewed/merged and the bounded manual sample is run with the configured secret.
4. Continue Form 4/144 identity, transaction-line owner and plan-negative-control work; do not turn metadata filings or proposed sales into trades.
5. Keep SEC MIDAS and FTD parked until historical PIT and effective-dated identity/coverage are established.
6. Keep paid options data parked until the user explicitly authorizes a budget and the terms are cleared.

**Quantitative result:** zero new signals promoted; no incremental alpha demonstrated; no new OOS, bootstrap or LOO result. No holdout was opened. No change to universe, model, parameters, exposure, costs, capital or holding-period policy. Paid data spend: **USD 0**.
