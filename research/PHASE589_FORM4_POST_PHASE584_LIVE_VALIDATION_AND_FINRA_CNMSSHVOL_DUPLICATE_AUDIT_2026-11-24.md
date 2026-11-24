# Phase 589 — Form 4 post-Phase-584 live validation and FINRA CNMS duplicate-symbol audit

**Audit cutoff:** 2026-11-24 06:18 UTC (2026-11-23 23:18 Hermosillo)  
**Main HEAD at cutoff:** `28e6437d4853386c84ef62b86cd4f2c9ed5d61a1`  
**Disposition:** **SEC Form 4 scheduled capture and watermark continuity are live-validated after Phase 583/584; the >20-page catch-up path is not yet exercised. FINRA Reg SHO remains fail-closed because current CNMS files contain repeated symbols with overlapping facility sets. No Smart Money signal or incremental alpha is admitted.**

## 1. Preflight: repository, Actions and branches

Inspected the latest 100 Actions runs, run metadata, jobs, job logs, artifacts, all branch pages, open PRs, workflow files, current research tree and relevant ledgers before making changes.

- Total Actions runs: **8,109**.
- Latest 100: **90 success / 10 failure**.
- Explicit active or queued runs: **0 / 0**.
- Branches: **379**.
- Open PRs: **72**.
- Workflow files on main: **96**.
- Research files: **499**.
- Main HEAD at cutoff: `28e6437d4853386c84ef62b86cd4f2c9ed5d61a1`.
- No workflow was manually dispatched, rerun, cancelled or duplicated.

Latest relevant scheduled runs:
- [45339067236 — Phase 469 FINRA Reg SHO](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236), 2026-11-24 06:15 UTC.
- [45338400329 — Phase 384 CFTC TFF](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329), 2026-11-24 06:09 UTC.
- [45332760566 — Phase 476 SEC Form 4](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566), 2026-11-24 05:21 UTC.
- [45330252226 — Phase 403 SEC Form 144](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226), 2026-11-24 05:00 UTC.
- [45330853390 — Phase 588 parser regression](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330853390), 11/11 tests passed.

The `phase20c-finra-walkforward` branch remains diverged: **12 commits ahead / 589 behind main**. It was not reactivated or merged.

## 2. SEC Form 4 — first natural post-Phase-584 validation

Run [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) was a scheduled main-branch capture. Both the offline-regression and live-capture jobs completed successfully.

### Feed continuity

| Check | Form 4 | Form 4/A |
|---|---:|---:|
| Prior watermark found | Yes | Yes |
| Poll success | Yes | Yes |
| Pages fetched | 20 | 1 |
| New accessions | 516 | 0 |
| Incomplete-poll candidates suppressed | 0 | 0 |

The prior Form 4 watermark `0001493152-26-053593` was found. The prior Form 4/A watermark `0001493152-26-053612` was also found. The run summary reports `all_feeds_successful=true`, persisted the accession-observation ledger and passed the post-persistence integrity gate.

- New canonical Form 4 event observations: **516**.
- Cumulative accession-observation ledger rows: **6,022**.
- Form 4 feed raw pages: **20** (2,000 raw entries).
- Form 4/A raw pages: **1**.
- Feed/page errors: **0**.
- Incomplete-poll suppression: **0**.
- Research-observation eligible rows: **0**.
- Signal-eligible rows: **0**.
- Exact public availability: **not certified**.
- Raw transaction rows in the feed capture: **not stored**; this was a metadata/first-observation capture.

**Important boundary:** the new 50-page maximum and fail-closed integrity gate are present, and the first natural post-merge capture succeeded. However, the run found the old watermark within 20 pages. It does **not** prove the extended >20-page / 50-page path under a real live gap. Issue [#210](https://github.com/jafelix81/NuevaEstrategia/issues/210) remains open for that boundary test; no manual dispatch is warranted.

### Bounded structured enrichment

The same scheduled job then performed separate, bounded enrichment:

- Form 4 transaction-detail parser: 10 accessions attempted, 10 parsed, 24 detail rows appended, zero parse errors; **2,273** bounded accessions remain.
- Reporting-owner parser: 10 accessions attempted, 10 parsed, 11 owner rows appended; 9 single-owner and 1 multi-owner accession; **20** bounded accessions remain. Transaction-line attribution is still unverified.
- Crosswalk: 5 descriptive rows, 4 Form 4 accessions matched, 1 prior-sale match and 4 proposed-sale matches; **0 eligible matches**.
- Six Form 4 accessions still lack a single owner identity; four multi-owner accessions remain quarantined.
- The two UPST purchase accessions from Phase 586 are still absent from the canonical owner sidecar. Manual filing review does not override pipeline identity/attribution flags.

Artifact: [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135).

**Conclusion:** the prior operational Form 4 feed gap is closed for this natural poll. Phase 583/584 live continuity is validated; the extended 50-page catch-up capacity is not stress-tested.

## 3. SEC Form 144 — natural capture resumed

Run [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) completed both Form 144 and 144/A feeds successfully and found both prior watermarks.

- New accession events: **118**.
- XML resolutions: **118**.
- Feed observations appended: **153**.
- Acceptance-clock reconciliations: **113 of 118**; 5 unresolved.
- New structured detail rows: **801**.
- Separate bounded backfill appended: **73** detail rows.
- Current ledger: **477 accessions / 3,360 detail rows**.
- Remaining bounded backfill: **238 accessions**.
- Candidate-manifest matches: 22 accessions across 13 issuer CIKs.
- Research-observation eligible rows: 118.
- Signal-eligible rows: **0**.

The 290-CIK candidate manifest is not an effective-dated F80 security master. Form 144 is a proposed-sale notice, not execution confirmation. First-observation/acceptance reconciliation does not establish an exact public-release timestamp.

Artifacts:
- [14891955642 — capture/quality summary](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642)
- [14891416912 — post-capture 10b5-1 audit](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912)
- [14890729923 — descriptive current refresh](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923)

The natural Form 144 and Form 4 runs establish that both SEC scheduled collectors resumed. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) was updated with both run IDs and closed as completed. This does not guarantee every future cron slot.

## 4. FINRA Reg SHO — new live duplicate-symbol blocker

Run [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) fetched six CNMS daily files successfully (HTTP 200) for trade dates 2026-11-23, 2026-11-20, 19, 18, 17 and 16.

All six were rejected as `duplicate_symbol_in_consolidated_file`:

- Two repeated symbols in each file: **BCPC** and **TPC**.
- 12 duplicate-symbol occurrences / 12 extra rows across the six files.
- Facility-market sets overlap; some TPC rows share the same facility set but have different row hashes.
- No raw volume values or raw market rows were persisted.
- No file was accepted into state; `files={}`.
- Valid files: **0**.
- First-seen observations: **0**.
- Research-observation eligible: **0**.
- Signal-eligible: **0**.

The Phase 515 parser repair supports comma-separated Market tokens but assumes symbol uniqueness once a composite market list appears. The current live sample shows that this assumption does not hold for the six observed files. It does not establish whether repeated tickers represent distinct security identifiers, overlapping aggregates, or a source anomaly.

**Do not sum or deduplicate by ticker.** Overlapping facility sets can double-count, and the file does not provide enough identity to resolve the row grain. The parser remains fail-closed; no code change was made.

### Official source semantics

- FINRA's [2020 Short Sale Volume Daily User Guide](https://www.finra.org/sites/default/files/2020-12/short-sale-volume-user-guide.pdf) documents the separate Trade Facility dimension and shows the same symbol across NQTRF, NCTRF and NYTRF rows. This facility-grain user view does not, by itself, define the current CNMS composite-row grain.
- FINRA's [May 10, 2019 Information Notice](https://www.finra.org/sites/default/files/2019-07/information-notice-051019.pdf) explains that daily short-sale files are published separately by FINRA facility, exclude non-publicly-disseminated trades, and are not consolidated with exchange volume.
- FINRA's [Short Interest explainer](https://syndication.finra.org/content/short-interest-what-it-what-it-not) distinguishes daily short-sale volume from open short-interest positions; same-day short sales may be closed and never appear in the short-interest snapshot.
- FINRA's [Reg SHO API dataset page](https://developer.finra.org/docs/api-explorer/query_api-equity-reg_sho_daily_short_sale_volume) describes daily volume aggregated by security for trades reported to a FINRA facility, but the public page does not resolve the observed duplicate-symbol CNMS row identity.

Issue [#214](https://github.com/jafelix81/NuevaEstrategia/issues/214) records the live diagnostics and next audit. The next step is a controlled comparison of the current raw CNMS file with the FINRA API/query representation or other authoritative security-level identifiers, followed by a historical frequency audit. No flow feature is constructed until row grain, PIT availability and universe identity are resolved.

## 5. CFTC TFF and SEC 13D/G

### CFTC TFF

Run [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) completed successfully; offline tests passed 19/19. The prospective ledger remains at **3,043 rows**, with no new report or revision and zero historical signal-eligible rows. This is still too little prospective history for a predictive test. Artifact: [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288).

### SEC 13D/G

Phase 588's line-boundary parser correction is merged (PR #213); its regression run passed **11/11** tests. This fixes empty-header-field parsing but does not rebuild or validate the 20,266-accession historical panel. Subject-issuer identity remains quarantined pending the repository's authorized `SEC_USER_AGENT` configuration and a bounded reconstruction. No secret was read or changed.

## 6. Other source feasibility gates

| Source | Current disposition |
|---|---|
| SEC Form 4 | Natural capture restored; owner/security/availability gates remain; no signal |
| SEC Form 144 | Natural capture restored; proposed-sale and acceptance-clock limitations remain; no signal |
| SEC 13D/G | Parser repaired; historical filer-to-subject identity still quarantined |
| FINRA daily Reg SHO | Live files currently rejected for unresolved duplicate-symbol row grain |
| FINRA Short Interest | Next publication is 2026-11-24 for settlement 2026-11-13; no authorized credential/request used in this run |
| Cboe OPRA/options | Historical data remain conditional on written strategy-use rights, exact universe/date coverage and PIT/correction vintages |
| SEC MIDAS | Market-structure context only; not participant identity or proof of institutional flow |
| CFTC TFF | Prospective regime/crowding candidate; insufficient vintages for prediction |
| SEC N-PORT / 13F | No promoted signal; prior share-growth hypothesis remains rejected/unstable |

FINRA's official [2026 Short Interest Reporting calendar](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest) lists November 13 settlement, November 17 broker due date and November 24 publication. The release had not yet occurred at the audit cutoff. Short interest remains a lagged aggregate position snapshot, not a daily flow or participant identifier.

## 7. Strategy and statistical disposition

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

- New Smart Money signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New independent/OOS results: **0**.
- No event study, return test, portfolio simulation, bootstrap or LOO was run.
- No changes to universe, parameters, holding-period policy, exposure, costs, holdout or production.

The UPST cluster remains discovery-only: the two Form 4 purchase accessions are not in the owner sidecar, the P code does not prove open-market execution, and this inspected cluster cannot be used as confirmatory OOS evidence.

## 8. Next gates

1. Continue natural Form 4/Form 144 polling; keep Issue #210 open until the >20-page/50-page boundary is actually exercised or separately proven under a production-equivalent controlled test.
2. Investigate FINRA CNMS duplicate rows without summing, deduplicating or weakening the parser. Determine whether the source needs a security identifier beyond ticker and whether the API provides an authoritative row grain.
3. At the November 24 FINRA Short Interest publication, use only authorized credentials and verify full snapshot coverage, corrections and point-in-time publication time.
4. Configure the authorized SEC user-agent and reconstruct 13D/G subject-issuer identity in a bounded, auditable run.
5. Continue Form 4 owner-sidecar enrichment; explicitly reconcile the UPST purchase accessions and keep all eligibility flags false until owner, transaction-line, venue, public availability and historical-universe checks pass.
6. Do not acquire or use options data for strategy research until written data-use rights and PIT/universe coverage are verified.

No workflow was duplicated. No raw market data, credentials or secrets were committed. No signal was admitted and the frozen baseline was not modified.
