# Phase 600 — SEC Form 144 delayed capture, Form 4 cadence gap and cross-source event triage

**Audit cutoff:** 2026-11-24 17:14 UTC  
**Main HEAD before documentation:** `0fc20749b411f8965e85735dfd87345ca14ff049`  
**Disposition:** Form 144 captured a new bounded batch after a long delivery gap, but the 11h28m50s first-seen interval is too wide for exact release-time claims. Form 4 has no post-morning natural capture. No event is signal-eligible and no alpha test is authorized.

## 1. Repository / Actions preflight

- Actions total: **8,110**.
- Latest 100: **90 success / 10 failure**.
- Explicit status queries: **0 in-progress / 0 queued / 0 waiting / 0 requested**.
- Branches: **380** (four pages enumerated); open PRs: **72**; workflow files: **96**; research entries: **495**.
- No workflow was dispatched, rerun, cancelled, duplicated, merged or rebased.
- Latest relevant natural runs:
  - Form 144: [45437675674](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674), created 2026-11-24 16:29:14 UTC; both jobs succeeded.
  - Form 4: [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566), created 05:21:36 UTC; both jobs succeeded.
  - FINRA Reg SHO: [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236), 06:15:11 UTC; both jobs succeeded at workflow level.
  - CFTC TFF: [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329), 06:09:53 UTC; job succeeded.

### Schedule interpretation

- Form 144 still declares `47 * * * *`. Run 45437675674 is an actual `schedule` event created at 16:29:14 UTC, approximately 42 minutes after the 15:47 nominal slot. Treat it as a delayed scheduled event, not proof of regular cadence recovery. The next nominal 16:47 slot was not visible by the 17:14 cutoff.
- Form 4 still declares `17 * * * 1-5`. Its 16:17 weekday slot was absent by the 17:14 cutoff; persisted `state.json` still points to run 45332760566, poll end 05:22:13 UTC.
- The read-only connection cannot inspect individual workflow enabled/paused state or repository schedule policy. Issue #194 remains open. No manual dispatch or cron change was made.

## 2. Form 144 — new natural capture, but broad first-seen interval

Run 45437675674:
- `offline-regression` and `live-capture`: success.
- Artifacts: [14941267954 poll / quality](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14941267954), [14941742508 post-capture 10b5-1](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14941742508), [14942785496 current 10b5-1 refresh](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45437675674/artifacts/14942785496). All unexpired.
- Both 144 and 144/A feeds completed; 53 feed observations, 27 new accession events, 27 XML resolutions, zero feed errors, zero cross-feed overlap, and no pagination/watermark gap.
- 32 acceptance-clock reconciliations added; zero unresolved.
- New batch first-seen upper bound: **2026-11-24 16:29:37 UTC**. Previous successful poll start/lower bound: **05:00:47 UTC**. Interval width: **11h28m50s**. This is a bounded interval, not exact public availability or subscriber receipt.
- All 27 new records are research-observation eligible under the bounded-poll rule, but **zero signal-eligible**, public availability remains uncertified, and same-day intraday use is unauthorized.
- Current structured ledger: **514 accessions / 3,549 detail rows**. New accessions parsed: 27; new detail rows: 130; bounded backfill appended another 59 rows; remaining backfill: **228**. Zero parse errors and zero source-hash mismatches.

### Candidate-manifest matches and cross-source check

Four of the 27 new Form 144 accessions matched the current 290-CIK candidate manifest: **JD.com, Axon Enterprise, Amazon.com and Verizon Communications**. This manifest is explicitly **not** a historical F80 security master; none of these is certified as an F80 historical constituent by this match alone.

The current Form 4 ledgers contain 61 owner rows and 199 transaction-detail rows. There is no issuer-CIK overlap for these four issuers in the current Form 4 owner/transaction ledgers. This is a descriptive cross-source non-match, not a negative predictive test and not proof that no related filing exists outside the bounded ledgers.

Form 144 remains a proposed-sale notice, not confirmation that the proposed sale occurred. Trust, tax, vesting and other transaction context must be preserved; repeated notices and amendments must not be treated as independent trades.

## 3. Form 144 Rule 10b5-1 / negative controls

The post-capture Phase 549 artifact reconciles to 514 accessions / 3,549 detail rows:
- 183 accessions have a formal plan-adoption date across 91 distinct dates.
- Median plan-date-to-notice lag: 183 days (range 18–546).
- 15 positive explicit 10b5-1 remarks, 4 negative explicit, 1 ambiguous; 494 accessions have no remarks mention.
- 16 accessions mention sell-to-cover or tax withholding.
- The four Fermi notices remain a negative-control cluster (2,253,270 proposed units).
- All 183 formal plan dates precede notice; none are same-day or after-notice.

A formal plan date is historical context, not the event's availability time. These counts are descriptive only; no signal, return test, OOS, bootstrap or LOO was run.

## 4. Other collectors re-adjudicated

| Source | Latest verified result |
|---|---|
| Form 4 | 516 new canonical accession events; 1,239 feed observations; 24 transaction-detail rows and 11 owner rows appended; both feed watermarks found; 2,273 transaction backfills and 20 owner accessions remain; zero signal-eligible rows. |
| FINRA Reg SHO | Six HTTP-200 CNMS files rejected; BCPC and TPC each repeated in every date; 12 extra rows; zero exact-row duplicates; zero valid files/first-seen/eligible observations. Raw market rows and volume values were not persisted. |
| CFTC TFF | 3,043 rows; no new reports/revisions; three index contracts have 853 weekly observations each since 2010-07-20; Russell E-mini has 484 since 2017-08-15. No signal. |

FINRA's successful workflow conclusion means the fail-closed diagnostic completed, not that the files were accepted. CFTC remains a broad index-positioning context source, not a single-stock smart-money signal.

## 5. Source ranking and next work

- Keep Databento OPRA as the leading **conditional** modern options-flow sample route, subject to written commercial/non-display rights, sample cost, historical F80/delisted coverage and prospective first-receipt logging.
- Keep IvyDB TradeFlow as the leading direct-flow hypothesis, subject to vendor sample, methodology, rights and vintage/PIT validation.
- Keep ORATS as volatility context only; it does not identify signed aggressor or beneficial owner.
- Do not merge PR #200: the Cboe branch is 5 commits ahead / 114 behind main and diverged. The standard DataShop license remains uncleared for strategy creation.
- Continue Form 4 owner/transaction backfill and monitor natural captures; preserve Form 144's 10b5-1/tax/vesting negative controls.
- Keep FINRA CNMS fail-closed until row-grain identity and raw-data rights are resolved.
- No new vendor account, credentials, data purchase or license acceptance.

## 6. Strategy disposition

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO results: **0**.
- No event-return study or backtest was run.
- No universe, exposure, cost, parameter, holdout or production change.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
