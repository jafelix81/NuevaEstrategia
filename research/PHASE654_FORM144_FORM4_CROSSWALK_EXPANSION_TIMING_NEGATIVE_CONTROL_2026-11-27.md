# Phase 654 — SEC Form 144 / Form 4 crosswalk expansion and timing negative-control audit

**Audit cutoff:** 2026-11-27 00:58 UTC  
**Main HEAD before documentation:** `5275278627941034a25c1a157524eee75b37f859`  
**Disposition:** completed descriptive event-semantics and timing audit. The current bounded crosswalk expanded to 13 proposed-sale matches across 12 Form 4 accessions, but none is signal-eligible. The transaction-date comparison provides a negative control against treating Form 144 proposed-sale notices as pre-execution signals. No returns were inspected.

## 1. Preflight: Actions, jobs, logs, artifacts, branches and research files

- Repository Actions total: **8,358**.
- Latest 100: **73 success / 17 failure / 10 cancelled**.
- Explicit in-progress and queued queries: **0 / 0**.
- The repository has **407 branches** across five API pages (100 + 100 + 100 + 100 + 7) and **85 open pull requests**. The current main head is `5275278627941034a25c1a157524eee75b37f859`.
- Relevant open research PRs remain Draft/stacked: #8 (13F PIT join), #37 (13D/G parent identity), #48 (Cboe options ranking), #50 (FINRA T1 ATS revision stability). PR #247 / Phase 650 is merged. The large historical PR #13 was not merged.
- No workflow was dispatched, rerun, cancelled or duplicated.

### Latest natural SEC Form 4 run

Run [45917890802](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45917890802), 2026-11-27 00:38:23 UTC, was a scheduled run on main. Both jobs succeeded:

- `offline-regression`: **82 tests passed**.
- `live-capture`: capture, bounded transaction-detail backfill, footnote-reference backfill, filing-level owner enrichment, descriptive crosswalk, append-only persistence and artifact upload all succeeded.

Artifact [15163420232](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45917890802/artifacts/15163420232) was downloaded and inspected. ZIP SHA-256: `882aac1184a258162e9ac1b16e4d116f157211f6daf578e97206452ed47311f6`.

Verified poll and backfill results:

- Form 4 and Form 4/A feeds both passed continuity/watermark checks.
- **0 new accessions**, **0 new canonical events**; two prior-watermark accession observations and two entity-observation rows were recorded. No exact entity duplicates, duplicate page offsets or quarantined entity accessions were found.
- Public availability remains uncertified. No filing XML/text or raw transaction rows were persisted by the first-seen poll.
- Ten bounded Form 4 accessions were parsed; **53 structured transaction-detail rows** were appended; zero parse errors; 3,394 bounded accessions remain in the structured-detail queue.
- The transaction-detail backfill summary records 206 linked footnote-reference rows. A separate ten-accession footnote-only pass appended another **29** references, with zero parse errors; 60 footnote accessions remain.
- Ten owner accessions were parsed; **13 owner rows** appended (nine single-owner filings and one multi-owner filing); 20 bounded owner accessions remain. Transaction-line attribution is still not verified for multi-owner filings.

The live poll interval was 00:38:41–00:38:42 UTC. The feed `updated` values were 2026-11-26 02:47:25 UTC (Form 4) and 2026-11-25 21:23:20 UTC (Form 4/A); they are feed metadata, not exact first-publication timestamps.

## 2. Expanded Form 144 / Form 4 crosswalk

The run generated a 14-row descriptive crosswalk artifact:

| Measure | Result |
|---|---:|
| Crosswalk rows | 14 |
| Proposed-sale matches | 13 |
| Prior-sale-history matches | 1 |
| Distinct matched Form 4 accessions | 12 |
| Multi-owner accessions quarantined | 8 |
| Form 4 accessions without single-owner identity | 10 |
| Form 144 acceptance clocks unresolved | 2 |
| Signal-eligible matches | **0** |

The 13 proposed-sale rows are matches on the existing strict keys: issuer CIK, filing-level owner CIK/name, transaction date, exact share quantity, security class and Form 4 `S/D` disposition. The one prior-sale-history match remains a historical-sale control, not a new proposed-sale event. Form 144/A detail rows remain excluded from new-sale matching pending amendment-chain reconciliation.

### Timing negative control

I independently compared the 13 matched Form 4 transaction dates with the calendar date of each Form 144 collector first-seen upper bound:

- **10 of 13** Form 4 transaction dates precede the Form 144 first-seen upper-bound calendar date.
- **3 of 13** share the same calendar date; the sources do not provide an intraday execution timestamp, so their ordering is unresolved.
- Two Form 144 acceptance timestamps are missing; those rows remain explicitly acceptance-clock-unresolved even though a collector first-seen upper bound exists.

This is not evidence that Form 144 predicted those sales. In ten cases, the reported Form 4 transaction date is on an earlier calendar day than the Form 144 first-seen upper bound. In the remaining three, same-day ordering cannot be established. Form 144 acceptance preceding Form 4 acceptance does **not** prove the notice preceded execution; Form 4 reports the transaction date but not intraday execution time. The collector's first-seen value is an upper bound, not an exact public-availability timestamp.

### Economic interpretation

- **11/13** proposed-sale matches have no specific remarks flag. Absence of a flag is not evidence of discretionary intent.
- **2/13** carry exercise/tax context. The two previously documented Atea examples are included; their Form 4 remarks tie the sales to option-exercise costs and tax planning, so they remain mechanical/administrative negative controls rather than bearish insider signals.
- All 13 rows are reported Form 4 `S/D` dispositions, but transaction code `S` alone does not establish discretionary selling, investor intent or predictive information.
- The crosswalk is an artifact, not a persistent event ledger. It does not establish historical F80 membership.

The Phase 525 crosswalk implementation explicitly reports `signal_eligible_matches=0`, `historical_f80_membership_verified=false`, `execution_intraday_time_known=false` and `alpha_test_authorized=false`. No matching rules were relaxed.

## 3. Other latest source captures

| Source | Latest natural run | Result |
|---|---|---|
| SEC 13F | [45910142871](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45910142871) | Both jobs succeeded; all four feeds completed full snapshots; 29 existing accession observations, 0 new accessions, 4 page observations, 0 holdings/XML downloaded, 0 research-eligible and 0 signal-eligible. Artifact [15159084837](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45910142871/artifacts/15159084837) downloaded and inspected (SHA-256 `5eb48cb2e4245e27c77ccc975552d85909c107eb0eeb2e9be87f784c709e70fb`). The 29 initial-baseline observations still have no lower bound; repeat sightings do not retroactively bound them.
| SEC Form 144 | [45906061652](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45906061652) | Latest natural capture remains successful: 835 accessions / 5,537 structured detail rows; 807 bounded intervals, 18 initial baselines, 168 detail backfills remain; no signal admitted.
| FINRA Reg SHO | [45754121648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45754121648) | Latest natural run predates Phase 650 merge; eight files were rejected by the old parser. PR validation [45895296971](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45895296971) passed 62/62 offline tests but correctly skipped live capture.
| CFTC TFF | [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471) | 3,043 rows; no new report/revision; two prospective Russell observations remain insufficient and the price-source rights gate remains open.

### FINRA post-merge schedule gap

Phase 650's parser is merged as PR #247 (merge commit `c7379f42ffffd631e8ce1bc3b9b3261871e3480d`). The FINRA workflow still declares `30 22,23 * * 1-5`. The two weekday slots after the merge (2026-11-26 22:30 and 23:30 UTC) passed without a natural scheduled run appearing in the current Actions inventory. The only post-merge Phase 650 run visible is PR CI; its live-capture job was skipped. This is an observed delivery gap, not proof that the workflow is administratively disabled. Repository workflow enabled-state / scheduled-workflow permission remains unavailable through the read connection; issue #194 retains the human verification request.

## 4. Source priority and next actions

- Keep SEC Form 4 as the leading public event candidate, but continue to require effective-dated security identity, historical F80 membership, owner attribution, transaction semantics and conservative availability clocks before any event-return study.
- Preserve Form 144 as proposed-sale disclosure and cross-source context, not an execution feed. The current 13 matched rows are not admitted as predictive events.
- Keep SEC 13F at metadata-only baseline until holdings, amendment lineage, public-availability clocks and historical universe coverage are solved.
- Await the next natural FINRA run to validate Phase 650 against real CNMS files; do not retrospectively promote the eight old rejected files.
- Keep Phase 20C same-day-close FINRA NO-GO; no same-day use of daily short-volume data.
- Continue CFTC Russell prospectively, outcome-blind, until a rights-cleared price source and sufficient sample exist.
- Options data remain unpurchased; authorization ceiling remains USD 0. No quote requests, vendor contacts or license acceptances.

## 5. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- Incremental alpha demonstrated: **none**.
- New valid OOS / bootstrap / LOO: **none**.
- Holdout untouched.
- No changes to universe, parameters, exposure, costs, capital, production or holding-period policy.
- No option-data spend.

**Phase 654 result:** a broader Form 144/Form 4 crosswalk now provides a reproducible timing negative control: the matched proposed-sale notices are already executed on a prior calendar day in 10/13 cases, while 3/13 are intraday-unresolved. No predictive or economic edge is established.
