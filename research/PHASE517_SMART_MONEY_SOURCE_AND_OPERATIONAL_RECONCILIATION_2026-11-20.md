# Phase 517 — Smart Money source and operational reconciliation

**Audit cutoff:** 2026-11-20 06:52 UTC  
**Main HEAD:** `2f50cd7d92ca08b2d0c27aaa0baff6e4debf3a19`  
**Disposition:** **NO SIGNAL ADMITTED. FINRA CNMS REPAIR IS MERGED BUT HAS NOT YET PASSED A POST-MERGE LIVE POLL. SEC 13D/G HISTORICAL PANEL REMAINS QUARANTINED; TWO ACCESS/CREDENTIAL GATES REQUIRE HUMAN ACTION.**

## 1. Repository and Actions preflight

- Inspected the latest 100 Actions runs, jobs, relevant logs and artifacts, the first 100 branches, all 61 open PRs, current workflow files, and the current research/data directories.
- Latest 100 runs: 77 success, 22 failure, 1 cancelled; **zero active or queued runs**.
- No workflow was dispatched, rerun, cancelled, or duplicated.
- Main HEAD is `2f50cd7d92ca08b2d0c27aaa0baff6e4debf3a19`, following the Phase 516 merge.
- PRs #168 (Phase 515) and #169 (Phase 516) are merged. PRs #166 and #167 remain open drafts documenting the SEC live validations; #164, #165 and #159 remain open drafts for OptionMetrics, CFTC PIT and FINRA Short Interest respectively.

## 2. FINRA Reg SHO — repair merged; live proof still pending

The last scheduled live run is [44669121290](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290). It ran on main SHA `8850828f`, **before** the Phase 515 parser repair:

- Offline regression: 56 tests passed.
- Live poll: eight requested files returned HTTP 200.
- Valid files: 0; invalid files: 8; reason: `market_code_invalid`.
- First-seen and research-eligible observations: 0.
- No raw market rows were persisted; the append-only poll ledger retained response hashes and byte counts.
- Artifact: [14598783309](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44669121290/artifacts/14598783309).

Phase 515 is now merged through [PR #168](https://github.com/jafelix81/NuevaEstrategia/pull/168), merge commit `cca5224c0980d6b0765b203ea618a335d9b88510`. Its PR validation [44674320007](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44674320007) passed **59/59 offline tests**; the live job was correctly skipped. Main now accepts comma-separated CNMS Market facility lists as already-consolidated security rows without re-summing volume, while retaining the legacy single-facility-row aggregation path.

**The next existing scheduled Phase 469 poll is the live gate.** The current run inventory contains no post-merge scheduled capture. Do not manually dispatch or backdate the eight invalid dates. An earlier `invalid_file` response is not proof that FINRA had not published a file.

## 3. SEC Form 144 and Form 4 — real parsers operating, but non-signal

### Form 144

Scheduled run [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343) completed both feeds and pagination:

- 103 feed-observation rows; 70 new accession XML blocks resolved and parsed into 542 detail rows.
- A separate bounded backfill processed 10 older accessions and appended 54 rows.
- Current ledger: 80 filing headers / 596 structured rows / 61 issuer CIKs.
- 596/596 source XML hashes match the event ledger.
- 368 accessions remain in the bounded backfill queue.
- The Phase 516 descriptive audit found 27 formal Rule 10b5-1 plan-adoption/instruction dates; this is distinct from free-text Remarks. One Form 144/A explicitly reports a terminated plan and no further sales, so it is not a new forward-supply event.

Phase 516 was merged through [PR #169](https://github.com/jafelix81/NuevaEstrategia/pull/169). CI [44680495072](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44680495072) passed **64/64 offline tests**; live capture was skipped for PR CI.

### Form 4

Scheduled run [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) recorded 457 new canonical accessions. Its bounded parser processed 10 documents and appended 22 rows (10 headers, 12 transaction rows), with zero parse errors; 1,190 accessions remain. The original metadata ledger did not contain XML hashes, so retrieved XML hashes are non-comparable, not mismatches.

For both SEC feeds, first-seen intervals are poll bounds, not exact public-release timestamps. Public availability certified = 0; signal-eligible rows = 0. No same-day intraday use is authorized.

## 4. CFTC TFF — prospective only

Scheduled run [44668300202](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44668300202) passed and retained **3,039 rows**, with no new report or revision. The historical archive's `Updated` field remains rejected as a universal PIT clock after the Phase 512 falsification. Only prospectively received, validated events may feed features.

The existing preregistered ES/NQ crowding protocol requires a prospective 52-observation reference and matured training outcomes. Static archive rows cannot substitute. No CFTC return test is authorized.

## 5. Broader source adjudication

### FINRA T1 ATS — viable market-structure candidate, not “smart money”

The completed Phase 375/385 work covers 209 consecutive T1 weeks (2021-11-15 to 2025-11-10), 10,917,933 rows and 2,292 pages. Revision-stable coverage is 98.634% of symbol-week groups and 96.943% of mapped aggregate share volume. The date-level publication-clock audit passed 209/209 weeks, using the first NYSE session strictly after the documented initial publication date.

The missing gate is effective-dated security identity and historical F80 membership, including inactive/delisted securities and terminal returns. Phase 392 correctly reclassified MPID/CRD keys as ATS/firm reporting venues. HHI and top-share values measure **venue concentration**, not beneficial owners, customers or informed investors. PRs #50 and #61 remain drafts on older base branches; their results do not authorize returns.

### SEC Schedule 13D/G — historical panel quarantined

The 20,266-row Phase 28D/35 panel is not safe for event or return tests. Phase 484 found 10,085 rows (49.76%) where the accession filer CIK equals the stored “issuer” CIK, and two original SEC filings confirmed that the stored Morgan Stanley filer identity was incorrectly used for different subject issuers. The panel must remain quarantined.

Phase 485 provides a fail-closed parser for separate SEC-HEADER `SUBJECT COMPANY` and `FILED BY` blocks, but the complete 20,266-row rebuild and effective-dated CUSIP/security mapping are not complete. Filing date remains the only conservative knowledge date; the two future-dated event-date anomalies remain quarantined.

**Human action required:** PR [#37](https://github.com/jafelix81/NuevaEstrategia/pull/37) remains open and draft. Its first exact-parent retrieval [43327053770](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43327053770) stopped after one HTTP 403 and retrieved 0/44 parents because the SEC User-Agent lacked a monitored contact. Configure the repository Actions secret `SEC_USER_AGENT` with a project identifier and monitored contact email before any retry. Do not paste the email or secret into chat. No request was retried in this phase.

### FINRA Consolidated Short Interest

PR #159 remains conditional. The prior synchronous pulls hit the 5,000-row cap, and no complete snapshot was proven. The async client has not passed its live credential gate. Human action: configure authorized `FINRA_CLIENT_ID` + `FINRA_CLIENT_SECRET` or `FINRA_ACCESS_TOKEN`, after confirming personal/non-commercial versus organization/commercial usage rights. Then run only the existing one-settlement validation; do not launch the 106-settlement batch until Record-Total and row-count reconciliation pass.

### Options

OptionMetrics TradeFlow and Implied Dividend Gap remain conditional candidates. Advertised backfill history does not prove the current classifier or filter was available at those historical dates. Historical methodology/version vintages, actual first-delivery/correction times, business-use license, price and exact F80/inactive-underlying coverage remain unverified. No vendor sample, trial, account or purchase was initiated.

## 6. Next gates

1. Wait for the existing scheduled Phase 469 run after the Phase 515 merge; require valid CNMS files, correct row grain, trailer reconciliation and stable hashes.
2. Continue the existing SEC Form 144/Form 4 bounded backfills; retain all first-seen and hash limitations.
3. Resume SEC 13D/G parent retrieval only after `SEC_USER_AGENT` is configured; rebuild subject/filer identity before any event analysis.
4. Resume FINRA Short Interest only after authorized credentials and terms are confirmed, starting with one asynchronous settlement.
5. For FINRA T1 ATS, complete the effective-dated security-master/F80 overlap and inactive-price gate before any market-structure return test.
6. Keep CFTC prospective-only; do not substitute historical archive rows for the 52-observation reference.
7. Obtain OptionMetrics version, delivery, coverage and license evidence before spending or testing.

## 7. Strategy controls

- New Smart Money signals admitted: **0**.
- New backtests, event studies or OOS tests: **0**.
- Bootstrap/LOO: no new tests.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen: universe, parameters, holding period, exposure, costs, holdout and production unchanged.

**Conclusion:** the current strongest progress is data infrastructure, not alpha. FINRA CNMS repair is merged but awaits a post-merge live poll; SEC structured ledgers are operating but remain non-signal; the historical 13D/G panel is quarantined until subject-issuer identity is rebuilt. The next work should clear these admission gates rather than add more unvalidated indicators.


## 8. Schedule cadence recheck

A separate schedule-only Actions query returned 36 scheduled runs in total. The most recent relevant events were:

- Phase 476 Form 4: five schedule-triggered runs in the inventory; latest [44656159115](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44656159115) at 2026-11-20 01:47:28 UTC. The workflow YAML remains configured for `17 * * * 1-5`; no later Phase 476 schedule event appears through the 06:52 UTC cutoff.
- Phase 403 Form 144: sixteen schedule-triggered runs in the inventory; latest [44662324343](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44662324343) at 2026-11-20 02:39:13 UTC. The workflow YAML remains configured for `47 * * * *`; no later Phase 403 schedule event appears through the 06:52 UTC cutoff.

The last captures succeeded, so this does not invalidate their persisted data. It does show intermittent schedule delivery relative to the configured cadence. The latest 100-run inventory had zero active/queued runs. The connected read interface does not expose the administrative workflow enabled-state endpoint; absence of schedule events alone does not prove that either workflow is disabled.

Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) was reopened at 06:58 UTC with this evidence. Human action: inspect Actions → Workflows, confirm Phase 403 and Phase 476 are enabled on default branch `main`, and review any schedule failures or paused state. No manual dispatch, rerun, cron change or replacement poller was made.
