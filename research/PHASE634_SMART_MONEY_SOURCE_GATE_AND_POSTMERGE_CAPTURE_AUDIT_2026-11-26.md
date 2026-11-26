# Phase 634 — Smart Money source gates and post-merge capture audit

**Audit cutoff:** 2026-11-26 07:51 UTC  
**Main HEAD before checkpoint:** `367533fff72fb6068667ed50d9754e40a61a49a3`  
**Disposition:** no source earned signal admission. The audit narrows the next work to post-merge Form 4 validation, SEC 13F/13D-G credential and identity gates, and a separate CFTC regime hypothesis. F80 remains frozen.

## 1. Actions / repository preflight

- Repository-wide Actions inventory: 8,316 total runs; latest 100 inspected.
- Latest 12 runs reviewed; 0 queued or in-progress in the latest 100.
- Latest main commit before this checkpoint: `367533fff72fb6068667ed50d9754e40a61a49a3`.
- Open PRs and branch ancestry reviewed. No workflow was dispatched, rerun, cancelled or duplicated.
- Latest Form 4 PR check [45769730992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45769730992): offline regression succeeded; live-capture job was skipped as designed.
- Latest natural Form 4 capture [45759597509](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509) predates the Phase 626 merge. A natural post-merge poll is still required.

## 2. SEC Form 4 — artifact-level adjudication

Inspected artifact [15089685727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45759597509/artifacts/15089685727), not only the console summary.

- 90 new canonical issuer events; 192 entity observations; both 4 and 4/A feed polls completed.
- The pre-Phase-626 poll summary reports 100 same-feed repeat occurrences. Do not treat that legacy counter as 100 exact entity duplicates: Phase 626 deliberately separates accession repeats from strict entity-key duplicates.
- Scheduled detail backfill appended 37 transaction-detail rows, 66 transaction-linked footnote references, and 26 additional footnote-reference rows. Ten filing-level owner rows were added.
- Owner enrichment remains filing-grain only; transaction-line attribution is not verified.
- The descriptive Form 144/Form 4 crosswalk has 11 rows, 10 proposed-sale matches and one prior-sale match; signal-eligible matches remain zero.
- No filing XML was persisted; public availability, security identity, historical F80 membership and signal eligibility remain false.

Phase 626 / PR #240 is merged. Its latest PR regression [45769730992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45769730992) passed 80/80, but the live job was skipped. The new `entity_duplicate_audit.csv` sidecar has not yet been validated by a natural post-merge poll.

## 3. SEC Form 144 — artifact-level adjudication

Inspected [Phase 403 run 45747356670](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670) and its artifacts, including [Phase 565 summary 15083916912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45747356670/artifacts/15083916912).

- Latest poll: 82 new accessions from 105 feed observations; both feeds completed.
- Cumulative structured ledger: 815 accessions / 5,443 detail rows; 188 bounded detail backfills remain.
- The 82 new first-seen observations have bounded collector intervals. They are not exact public-release timestamps; signal-eligible count remains zero.
- 295 accessions contain a formal Rule 10b5-1 plan-adoption date (126 distinct dates); median adoption-to-notice lag is 183 days. 294 dates precede the notice, one coincides, none follows.
- Remarks classification: 23 positive explicit plan mentions, four negative explicit mentions, three ambiguous and 785 with no mention.
- Four Fermi notices form a sell-to-cover/tax-withholding negative-control cluster totaling 2,253,270 proposed units. These are notices, not verified executions or discretionary bearish trades.

Retain Form 144 as descriptive event context and a negative-control source. Do not convert proposed-sale volume or remarks presence into a directional signal.

## 4. FINRA Reg SHO — quarantine confirmed

Inspected [run 45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) and artifact [15086513251](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648/artifacts/15086513251).

- Eight daily files returned HTTP 200; all eight were rejected by the duplicate-symbol / overlapping-facility integrity gate.
- 16 duplicate extra-row occurrences across BCPC and TPC; none were exact row duplicates.
- BCPC contains overlapping facility sets (for example B/N/Q versus N/Q); TPC also has repeated B/N/Q facility sets. The raw volume rows were not persisted.
- Accepted files: 0; eligible first-seen observations: 0.

Keep the feed quarantined. Do not sum, drop, max-select or deduplicate the rows until security/facility grain is reconciled using authorized source data and storage rights.

## 5. CFTC TFF — useful history, wrong grain for stock-level flow

Inspected [run 45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) and artifact [15086462804](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471/artifacts/15086462804).

- 3,043 historical rows across four index-futures contracts.
- DJIA, E-mini S&P 500 and Nasdaq Mini history begins 2010-07-20; Russell E-mini begins 2017-08-15.
- Latest report date: 2026-11-17; no new report or revision in this poll.
- The capture's cadence control suppresses weekly 4-report / 52-report features when the observed release gaps are semiweekly or irregular. No derived feature or signal is currently eligible.

Retain CFTC as a possible broad market-positioning/regime covariate, not security-level institutional flow. Any future test must preregister the actual report cadence and release-time clock, then compare incremental information against F80's existing market-regime controls.

## 6. SEC 13F — promising historical structure, not yet an integrated PIT panel

The prospective metadata collector is on main, but the historical reconstruction and knowledge-clock work remains a stacked Draft PR chain (#221–#230), not merged into main.

Verified branch/PR evidence:

- PR #226 full-quarter structural audit: SUBMISSION/COVERPAGE joins 6,570/6,570 (2018 Q1) and 11,852/11,852 (2026 Jun–Aug); group-aware INFOTABLE references match 97.63% and 99.01%; unmatched references remain explicit and unrepaired.
- PR #224 original EDGAR XML established that OTHERMANAGER2 sequence numbers identify **groups**, not unique individual managers. Position references must attach to groups; member rows must remain separate.
- PR #228 acceptance-time sample: 48/48 filing-detail pages passed across the two datasets. Four same-day filings accepted after 17:30 ET are treated as filed the next SEC business day.
- PR #229 XNYS clock: 3,496 sessions from 2013-01-01 through 2026-11-24, including 29 early closes. Daily-bar execution is delayed until the next full session after the conservative knowledge time.
- PR #230 adds the 06:00 ET legal filing-date floor and quarantines same-date observations accepted after 17:30 ET.

These are substantial source-feasibility and chronology results, but all remain in a Draft dependency chain. Effective-dated CUSIP/security-class-to-F80 identity, amendment-state integration and complete inactive-security coverage remain mandatory. Do not describe the main-branch metadata collector as a holdings signal or run returns from the unmerged chain.

The latest scheduled 13F run [45751086501](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45751086501) failed closed before an SEC request: the log shows `SEC_USER_AGENT` empty. The workflow references `${{ secrets.SEC_USER_AGENT }}` and has no Environment declaration. A likely configuration mismatch to check is whether the value exists only as an Environment secret or a variable rather than a repository Actions secret. The connected interface cannot read or set secret values.

## 7. SEC 13D/G — identity discovery is promising, 44-header gate remains open

- Phase 603's 147-submission stratified discovery sample passed its subject/filer/header identity checks, but it was deliberately stratified and is not a population estimate.
- That sample found 24 subject-company matches to current F80 CIKs and 45 FILED BY matches; only two overlapped. Subject identity and filer identity must not be conflated.
- The 335-name current snapshot had 35 unresolved ticker mappings at that audit point.
- Phase 616's preregistered 44-header sample has not been run. Its workflow requires manual dispatch with `run_live_sample=true` and the SEC User-Agent secret. A PR regression is not a substitute for the live sample.

Keep 13D subject-issuer discovery ahead of 13G as a potential event source, but do not use filing-agent CIK, archive-path CIK or FILED BY as a substitute for the subject issuer.

## 8. Options, MIDAS, N-PORT and independent-alpha controls

- Options: OptionMetrics TradeFlow remains the conditional signed-flow candidate; ThetaData Pro the conditional raw-OPRA reconstruction; Cboe Open-Close a venue/capacity complement. Historical first-receipt/correction vintages, F80 and inactive-underlying coverage, sample bytes and commercial rights remain unverified. No vendor contact, quote, trial or purchase; authorized options budget remains USD 0.
- SEC MIDAS: retain only as a conditional exchange market-structure/liquidity-state source. Its hidden-volume measure is not dark/off-exchange institutional accumulation or participant identity.
- N-PORT: the simple aggregate share-balance-growth directional hypothesis remains killed under Phase 526; do not retune it.
- Phase 20C: same-day-close FINRA entry remains NO-GO because the daily file is posted after the regular session. The next-session-open successor remains blocked by the missing prospective label bridge and incomplete inactive/delisted price histories.
- MOM120: Phase 499 rejected standalone replacement as a reliable incremental portfolio edge over LTM. Phase 574 is historical cycle-boundary sensitivity only, not fresh OOS; the all-cycle boundary treatment crosses zero.

## 9. Research disposition and next gates

1. Wait for the next natural Form 4 poll after Phase 626 merge; validate the entity-duplicate sidecar against live Atom pages. Do not dispatch a duplicate poll.
2. Resolve the SEC User-Agent injection at repository-secret scope without exposing the value; then run the bounded 44-header 13D/G sample once.
3. Keep FINRA Reg SHO quarantined until BCPC/TPC facility-grain semantics are reconciled.
4. Review and integrate the stacked 13F PIT/identity PR chain only after its dependency order and all changed files are independently reviewed; no holdings return test before complete effective-dated security mapping and chronology are frozen.
5. If CFTC is pursued, preregister a broad-market regime feature with the observed semiweekly/irregular cadence and test it only as an incremental covariate against F80.
6. Keep options research at documentation/feasibility level while the budget and commercial-use authorization remain zero.

**Quantitative result:** no new alpha, valid incremental OOS, bootstrap or LOO evidence was produced.  
**Strategy control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no universe, exposure, costs, parameters, holding-period policy, holdout or production changes.
