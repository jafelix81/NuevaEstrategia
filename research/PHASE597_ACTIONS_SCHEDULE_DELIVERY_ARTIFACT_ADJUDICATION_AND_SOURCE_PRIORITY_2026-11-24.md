# Phase 597 — Actions schedule-delivery recheck, artifact adjudication and source-priority checkpoint

**Audit cutoff:** 2026-11-24 14:12 UTC  
**Main HEAD at preflight:** `d37624a1daea559a8e916c34ae2803290797f891`  
**Disposition:** renew the SEC scheduled-capture delivery escalation; retain FINRA Reg SHO fail-closed; clarify that the same-day 2026-11-24 HTTP 403 is a not-yet-available poll rather than evidence of an OAuth failure; keep Schedule 13D rebuild ahead of 13F and retain options sources as conditional, separately licensed research candidates. No signal or return test admitted.

## 1. Repository and Actions preflight

The repository-wide Actions API and schedule-filtered inventory were queried before further work:

- Total runs: **8,109**.
- Latest 100: **90 success / 10 failure**.
- `in_progress`, `queued`, `waiting`, `requested`: **0 each**.
- Schedule-triggered runs returned: **59**.
- Branches: **380** (all four pages enumerated).
- Open PRs: **72**.
- Workflow files on main: **96**.
- Research directory entries: **490**.
- Main HEAD: `d37624a1daea559a8e916c34ae2803290797f891`.

No workflow was dispatched, rerun, cancelled, merged, rebased, or duplicated.

### Relevant open research PRs

Compared against current main, the principal open options/insider branches remain stale and divergent:

| PR | Line | Ahead | Behind | Disposition |
|---|---|---:|---:|---|
| #199 | Form 4 / F80 overlap | 5 | 108 | Draft; keep as historical audit |
| #200 | Cboe OPRA PIT feasibility | 5 | 108 | Draft; do not merge stale state |
| #202 | Form 144 10b5-1 polarity | 17 | 107 | Draft; core audit is already reflected in main captures |
| #204 | SEC FTD credential integration | 11 | 88 | Draft; separate credential work |
| #188 | Massive Options license/PIT | 5 | 152 | Draft; license-gated |

No PR was merged. The old Phase 20C branch remains separate and is not promoted.

## 2. Latest scheduled runs, jobs, logs and artifacts

| Source | Run | Jobs | Artifacts |
|---|---:|---|---|
| FINRA Reg SHO / Phase 469 | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | offline-regression + live-capture succeeded | [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787) |
| CFTC TFF / Phase 384 | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | prospective-capture succeeded; 17 offline tests passed | [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288) |
| SEC Form 4 / Phase 476 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | offline-regression + live-capture succeeded | [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135) |
| SEC Form 144 / Phase 403 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | offline-regression + live-capture succeeded; post-capture audits passed | [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642), [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), [14890729923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923) |

All relevant jobs were completed and artifacts were unexpired at audit. Job logs and artifact contents were inspected; the artifacts were downloaded and their JSON/CSV summaries parsed. A successful workflow conclusion is not equivalent to accepting market observations.

### SEC Form 4

Artifact 14892950135 confirms:

- 516 new canonical accession events; 1,239 accession-observation rows; 579 unique candidate accessions.
- 653 same-feed repeat observations and six cross-feed repeats are Atom path observations, not separate filings.
- Both Form 4 and Form 4/A watermarks passed; no incomplete-poll candidates were suppressed.
- Bounded transaction backfill parsed 10 accessions, appended 24 detail rows, and left **2,273** accessions in the bounded queue.
- Owner enrichment parsed 10 accessions, appended 11 owner rows, and left **20** accessions pending; one parsed accession was multi-owner.
- Crosswalk contains five descriptive rows; four multi-owner accessions remain quarantined.
- Public availability is not certified; research-observation-eligible and signal-eligible rows remain **zero**.

Persisted state still records last successful poll [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) ending **05:22:13 UTC**.

### SEC Form 144

Artifact 14891955642 and the post-capture Phase 565 artifact confirm:

- 118 new accession events, 118 XML resolutions and 153 feed-observation rows.
- 477 structured accessions / 3,360 detail rows; 801 new detail rows in this run.
- 113 of 118 acceptance reconciliations added; **five remain unresolved**.
- 238 bounded detail-backfill accessions remain.
- 174 accessions have formal Rule 10b5-1 plan adoption dates across 89 distinct dates; no plan date is after its notice date.
- The proposed-sale notice is not execution confirmation; formal plan date is not a public-availability timestamp.
- 118 headers are research-observation eligible under the conservative first-seen receipt upper bound, but public-availability-certified headers remain **zero** and signal-eligible filings remain **zero**.

Persisted state still records last successful poll [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) ending **05:01:16 UTC**.

### FINRA Reg SHO

The downloaded artifact 14895571787 and live log show:

- Six historical CNMS files returned HTTP 200 (trade dates 2026-11-16, 17, 18, 19, 20 and 23).
- All six were rejected by the duplicate-symbol fail-closed gate.
- BCPC and TPC repeat in every file: 12 repeated-symbol occurrences / 12 extra rows.
- Facility sets overlap and none of the repeated rows is an exact raw-row duplicate.
- Zero valid files, zero first-seen events, zero eligible observations; persistent state remains `files: {}`.
- No raw rows or volume values were persisted; diagnostics retain hashes, byte counts, line numbers and facility-token sets only.

For BCPC, the repeated market sets include {B,N,Q} and {N,Q}; for TPC, both rows show {B,N,Q}. These facts do not establish whether the rows are separate securities, duplicate aggregates or a source anomaly. Do not sum or drop them by ticker/facility overlap.

The same-day **2026-11-24** request returned HTTP 403 at **06:15 UTC / 01:15 ET**, before the same-day FINRA file would ordinarily be available. The collector counts one `not_available` response. This is consistent with an unpublished same-day file and is **not evidence by itself of an authentication or OAuth failure**. The six historical requests returned HTTP 200. Keep the parser fail-closed.

### CFTC TFF

Artifact 14895036288 confirms:

- 3,043 rows across four tracked futures-only contracts.
- No new reports or revisions; no state change.
- Latest report date remains 2026-11-17.
- 17 offline tests passed, including late-arrival/revision suppression, prior-row-only z-score and cadence controls.
- Historical rows remain signal-ineligible; no alpha test authorized.

## 3. Renewed SEC schedule-delivery gap — human action required

The main workflow definitions still declare:

- Form 4 / Phase 476: `17 * * * 1-5`.
- Form 144 / Phase 403: `47 * * * *`.

The schedule-filtered Actions inventory contains no run after FINRA [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) at 06:15:11 UTC.

At the 14:12 UTC cutoff:
- Form 4 has no scheduled run for **06:17–13:17 UTC** (eight expected weekday slots). Its last successful poll ended 05:22:13 UTC.
- Form 144 has no scheduled run for **05:47–13:47 UTC** (nine hourly slots). Its last successful poll ended 05:01:16 UTC.
- The next Form 4 slot (14:17 UTC) and Form 144 slot (14:47 UTC) had not yet occurred.
- All listed runs are complete; no active or queued run exists.

The YAML crons are present. The read-only GitHub connection does not expose workflow enabled/paused state or repository Actions schedule-policy settings. This is an observed delivery gap, not proof of administrative disablement or deliberate event dropping.

Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) was updated with this 14:12 UTC recheck and the exact missing windows. Human action: verify Phase 403 and Phase 476 are enabled and scheduled Actions are permitted. Do not manually dispatch, rerun, change cron or create replacement workflows solely to test delivery.

## 4. Source-priority and data-feasibility disposition

### Schedule 13D/G and 13F

- Schedule **13D** remains the first ownership-disclosure rebuild after the SEC User-Agent prerequisite, consistent with Phase 555's event-specific activist/control-intent hypothesis and faster reporting clock.
- The old 20,266-accession 13D/G panel remains quarantined: filer/subject issuer misattribution is confirmed; zero rows are certified from the old artifact alone.
- Phase 485/588 parser logic is on main; Phase 588 regression passed 11/11. This is parser quality, not historical reconstruction.
- The bounded 44 exact-parent SEC retrievals remain gated by maintainer confirmation of a descriptive, monitored `SEC_USER_AGENT` secret. No secret was inspected or changed; no SEC retrieval was made.
- Schedule 13G remains a separate, slower ownership-state/context family.
- Form 13F remains parked. Phase 595's 100% accession join in two samples does not resolve effective-dated CUSIP/security-class identity or historical 335-name coverage (212/335 in 2016 Q1, 246/335 in 2020 Q1, 280/335 in 2024 Q1). No 13F return test is authorized.

### Options

The current ranking is retained, not promoted:

1. **OptionMetrics IvyDB TradeFlow** — best conditional all-venue signed-flow candidate, but current product launch is dated 2026-09-30 while the advertised archive reaches 2016. Historical recomputation/version lineage, first-delivery and correction vintages, exact 335-name coverage, pricing and business-use rights remain unverified. Its Institutional 1 bucket is nested within Institutional 2; neither bucket identifies beneficial owners or all institutional activity.
2. **Cboe Option Trades + Quotes** — independent OPRA-wide raw-data validation candidate with advertised history from 2012. It lacks participant capacity and open/close labels; quote-conditioned aggressor side remains inferred. Historical first-receipt/correction vintages, 335-name coverage and permitted use remain unverified.
3. **Cboe Open-Close EOD** — complementary capacity × buy/sell × open/close source on Cboe venues only, with historical convention breaks and internal-use licensing restrictions.
4. **Massive Options** — historical fields are technically attractive, but the current Options Advanced plan is individual/nonprofessional; organization/employer and derived-data restrictions are not cleared for this public repository or organizational research. No sample, purchase or vendor contact.

No options data were acquired, no licensed raw/derived data were placed in the public repository, and no options signal or return test was run.

### Other lines

- FINRA ATS remains venue-concentration/market-structure data, not investor identity or institutional positioning.
- CFTC TFF remains prospective-only until enough independently timestamped observations accumulate.
- Form 144 remains a proposed-sale/plan-context dataset, not confirmed executions.
- Form 4 remains descriptive until transaction semantics, owner linkage, security identity and public-availability clocks pass.

## 5. Research decision

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO results: **0**.
- Phase 20C same-day-close implementation: **NO-GO** due to publication-time look-ahead.
- Phase 372 next-open retest: **untested**, not rejected; its previous attempt stopped before results because historical price coverage was incomplete.
- Six final FINRA holdout dates remain sealed.
- No model, universe, parameter, exposure, cost, holding-period, holdout or production change.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## 6. Actions taken in this phase

- Downloaded and inspected the four current source artifacts (FINRA, CFTC, Form 4, Form 144) and the additional Form 144 10b5-1 artifact.
- Inspected all relevant job summaries/logs and the current main workflow YAML cron definitions.
- Enumerated all 380 branches; inspected relevant open PR divergence against current main.
- Added a fresh 14:12 UTC delivery-gap comment to [Issue #194](https://github.com/jafelix81/NuevaEstrategia/issues/194).
- Added a FINRA artifact/HTTP-403 clarification to [Issue #214](https://github.com/jafelix81/NuevaEstrategia/issues/214).
- No code, workflow, credential, raw data, strategy or production changes.
