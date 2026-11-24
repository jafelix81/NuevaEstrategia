# Phase 595 — SEC Form 4 Atom accession-alias adjudication and SEC 13F PIT feasibility re-prioritization

**Audit cutoff:** 2026-11-24 12:35 UTC  
**Main HEAD at preflight:** `f8a0c71728cb7625399e2bda23c9377b5d1c9e65`  
**Disposition:** Form 4 repeat observations are not equivalent to duplicate filings; SEC 13F passes a two-snapshot accession join gate and is worth advancing to a strict effective-dated CUSIP coverage audit. No source or signal is admitted.

## 1. Actions / repository preflight

The current state checkpoint records 8,109 total Actions runs, latest 100 = 90 success / 10 failure, and 0 in-progress / 0 queued at the Phase 594 cutoff. This run refreshed the four relevant run-specific jobs, logs and artifacts:

| Line | Run | Jobs | Artifact(s) |
|---|---:|---|---|
| FINRA Reg SHO | [45339067236](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236) | offline-regression success; live-capture success | [14895571787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45339067236/artifacts/14895571787), 1,774 bytes |
| CFTC TFF | [45338400329](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329) | prospective-capture success | [14895036288](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45338400329/artifacts/14895036288), 1,110 bytes |
| SEC Form 4 | [45332760566](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566) | offline-regression success; live-capture success | [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135), 3,649 bytes |
| SEC Form 144 | [45330252226](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226) | offline-regression success; live-capture success | [14891955642](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891955642), [14891416912](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14891416912), [14890729923](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45330252226/artifacts/14890729923) |

All listed jobs completed and all listed artifacts were unexpired when checked. FINRA's successful workflow conclusion still means diagnostics were recorded, not that the six market files were accepted. The repository-wide Actions run-list cannot be refreshed through the currently exposed GitHub actions in this run; the 8,109 / 90-10 / zero-active snapshot remains the Phase 594 inventory, not a newly certified global count. No workflow was dispatched or rerun.

Relevant branch comparisons against main: `phase20c-finra-walkforward` 12 ahead / 600 behind; `phase372-finra-shortflow-next-session-open-retest` 20 / 600; Phase 547 Cboe 5 / 102; Phase 548 MIDAS 2 / 102; Phase 546 Form 4 5 / 102; Phase 45 13F 8 / 528; Phase 47 13F 10 / 528. Open PRs #199, #200, #201, #6 and #8 remain unmerged. None was merged or rerun.

## 2. Form 4: adjudicating the 653 same-feed repeat observations

Downloaded and inspected the actual Phase 476 artifact [14892950135](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45332760566/artifacts/14892950135), then parsed the current `accession_observations.csv` blob (6,022 total rows).

For run `45332760566`:

- 1,239 accession-observation rows: 1,228 from feed `4`, 11 from feed `4/A`.
- 1,237 candidate accession occurrences and 579 unique candidate accessions.
- 516 canonical new accession events; 516 canonical observation rows emitted.
- 653 same-feed repeated occurrences: 648 in feed `4`, five in feed `4/A`.
- Six cross-feed repeats; these are expected to be possible because the `4` parser accepts both `4` and `4/A`, while a separate `4/A` feed is polled.
- Feed `4` contains 580 accession groups; 575 groups repeat. Of those 575, 560 have exactly two distinct `feed_path_cik_unverified` values; the remaining groups have 3–10 path CIK values. Only 21 repeated groups span more than one page offset; most repeats occur within the same page.

**Interpretation:** 653 is a count of repeated *observations*, not 653 duplicate filings or 653 independent transactions. The repeated rows share an accession but can carry different `/data/{CIK}/` archive paths. This is consistent with EDGAR indexing the same ownership filing through multiple issuer/reporting-owner CIK views, but the path CIK is explicitly unverified and must not be promoted to issuer or owner identity without checking the filing XML. SEC documentation says an accession number identifies one accepted submission and that the accession prefix is the submitting entity's CIK (which may be an agent); the SEC ownership XML specification permits multiple reporting owners and does not define a primary owner. See [SEC EDGAR access/index documentation](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) and [SEC Ownership XML technical specification](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf).

The current collector's accession-level canonicalization is appropriate for a filing-level event: it emits one canonical event per accession while preserving all accession-observation rows. Do not count repeated Atom entries as independent events, do not infer owner identity from `feed_path_cik_unverified`, and do not call every repeat a pagination defect. A future summary should report both repeated-occurrence count and distinct repeated-accession-group count. The 21 cross-page cases remain candidates for a separate pagination/index-alias check.

This does not change signal eligibility: the artifact still reports 516 new metadata events, zero research-observation-eligible rows and zero signal-eligible rows. No forward-return study was run.

## 3. SEC Form 13F: positive source-feasibility result

Inspected the full log and downloaded artifact for the existing Phase 47 run [40859618228](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40859618228), artifact [12890962085](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40859618228/artifacts/12890962085). The historical workflow completed successfully on 2026-10-29.

| Snapshot | SUBMISSION rows | INFOTABLE holdings | Join rate | Unique managers (CIKs) | Unique CUSIPs | Unique FIGIs | Median report-to-filing lag |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2018 Q1 | 6,570 | 1,879,731 | 100% | 4,683 | 25,816 | 0 | 44 days |
| 2026 Jun–Aug | 11,852 | 3,830,274 | 100% | 8,872 | 34,951 | 22,519 | 42 days |

Both samples had zero unmatched INFOTABLE accessions, zero missing CUSIPs and zero filings before the report period. Combined, the samples contain 18,422 accession submissions and 5,710,005 holdings rows. The median reporting delay is about six weeks; the 75th percentile is 45 days in both samples.

**Why this matters:** the SEC structured 13F files can support a manager/accession/holding panel with a defensible filing-date knowledge clock. Use `filing_date`, not `period_of_report`, as the first date the position may enter a strategy. Because the sampled field is date-only, the conservative executable rule is the first regular session strictly after the filing date. The report quarter-end is not a trade date.

**What still fails / remains unknown:**

- FIGI is absent in the 2018 sample, so a FIGI-only historical join is impossible. CUSIP is present, but a reproducible effective-dated CUSIP-to-security/ticker crosswalk and historical 335-name coverage have not been demonstrated.
- Only two snapshots were audited; this is not yet an exhaustive 2013–2026 quarterly coverage audit.
- The 2018 and 2026 filing-lag distributions have extreme maxima (1,125 and 9,101 days). The current join script does not classify amendment number/type, confidential-treatment releases, late filings or superseded accessions. Do not interpret those observations as ordinary quarter-end reports or double-count amendments.
- 13F is delayed holdings disclosure, not trade-level order flow or proof of informed buying. Changes in reported dollar value can be price appreciation rather than net purchases. Any future feature should use shares/position changes, corporate-action-adjusted units, manager and amendment lineage, and filing-date availability; test whether it adds information beyond momentum/price chasing and frozen LTM/F80.
- No universe coverage, event study, return test, OOS, bootstrap or LOO was run.

**Disposition:** promote SEC 13F to the next *data-feasibility* gate, not to alpha testing. Next: audit amendment lineage and report-period uniqueness; build a CUSIP-to-security crosswalk with effective dates and inactive/delisted names; measure date-appropriate coverage against the historical investable universe; use filing-date-plus-next-session execution; only then preregister incremental tests versus frozen LTM/F80.

## 4. SEC access-control issue in legacy 13F PRs

Static review found both Phase 45 and Phase 47 scripts hard-code `User-Agent: ... contact research@example.com`. SEC's published access guidance asks automated clients to declare a descriptive User-Agent with a real contact. Phase 47's workflow executes the live download script on `pull_request`; Phase 45 executes it on branch pushes and manual dispatch. These are not safe patterns for future live retrieval.

Comments were posted on [PR #6](https://github.com/jafelix81/NuevaEstrategia/pull/6) and [PR #8](https://github.com/jafelix81/NuevaEstrategia/pull/8): migrate to the repository's `SEC_USER_AGENT` secret contract, fail closed before network access when absent, keep push/PR validation offline-only, and reserve live samples for explicit `workflow_dispatch`. PR #204 proposes the newer secret contract for SEC FTD but remains open; no secret values were inspected or changed. No new SEC request was made.

## 5. Research decision

- Form 4: preserve accession-level dedupe; retain all path aliases; no owner/issuer inference from path CIK.
- SEC 13F: **PASS** for sampled accession join; **NOT YET ADMITTED** for historical universe coverage, PIT feature construction or alpha.
- FINRA same-day-close Phase 20C: remains NO-GO for look-ahead; Phase 372 next-open retest remains untested because the historical price panel failed its 329/335 gate.
- New signals admitted: 0. Incremental alpha demonstrated: none. New valid OOS/bootstrap/LOO results: 0.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No model, universe, exposure, costs, holdout, holding-period or production changes.
- No workflow was dispatched, rerun, merged or cancelled.

## 6. Persisted capture freshness at audit cutoff

Current main-branch state files still point to these latest successful/persisted capture times as of 2026-11-24 12:35 UTC:

- SEC Form 4: run `45332760566`, poll ended `2026-11-24T05:22:13Z`.
- SEC Form 144: run `45330252226`, successful poll `2026-11-24T05:01:16Z`.
- FINRA Reg SHO: run `45339067236`, poll completed `2026-11-24T06:15:25Z`; persistent file state remains empty because the six daily files were rejected.
- CFTC TFF: last prospective capture `2026-11-21T03:17:36Z`; latest report date in the four tracked contracts remains `2026-11-17`.

No later successful capture is reflected in these persistent state files. This alone does not establish that a scheduled workflow was disabled, missed or failed; the connected GitHub actions in this run do not expose a fresh repository-wide scheduled-run list or the workflow schedule definitions. No schedule was changed and no workflow was dispatched.
