# Phase 488 — SEC Form 4/4-A first scheduled baseline capture adjudication

**Audit cutoff:** 2026-11-18 20:41 UTC  
**Disposition:** **FIRST SCHEDULED CAPTURE VERIFIED; INITIAL BASELINE ONLY; NO RESEARCH OR SIGNAL ADMISSION.**

## 1. Preflight

- Default branch: main.
- Main HEAD at capture: 8f41ace5b6f5ffc795fbdb79fa55ff2d56bfff62 (Phase 487).
- Latest repository Actions inventory: 7,862 total runs; latest 100 = 72 success / 26 failure / 2 cancelled; explicit in-progress = 0 and queued = 0.
- Repository inventory: 316 branches, 56 open PRs, 4 open issues, 86 workflow files, 447 tracked tree entries.
- No workflow was dispatched, rerun, cancelled, or duplicated.
- The latest scheduled run was Phase 476 run [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679).

## 2. Scheduled run and job evidence

Run 44380395679 was triggered by schedule on main at 2026-11-18 19:25:35 UTC and completed at 19:26:15 UTC.

Both jobs succeeded:

- offline-regression: 37/37 tests passed.
- live-capture: compile, Form 4/4-A capture, append-only commit, and artifact upload all succeeded.

The live job started the poll at 19:26:00 UTC and completed it at 19:26:08 UTC. It queried the existing SEC Atom feeds; no manual dispatch or schedule change was used.

## 3. First baseline observations

Two feeds completed one page each with HTTP_OK and no page error:

| Feed | Raw Atom entries | Parsed accession entries | Latest Atom updated (UTC) | Page SHA-256 |
|---|---:|---:|---|---|
| Form 4 | 100 | 20 | 2026-11-18 19:16:37 | 21f4faf38fd8f4e3c626195be13ee65500e9244574010edd67b37fc67e69e658 |
| Form 4/A | 50 | 50 | 2026-11-18 16:46:44 | f00d453c3ff20fa4e523ced5609f383716f158b017a8c92aba33081ec4f54fc9 |

The canonical append-only ledger contains **35 unique accessions**:

- 10 original Form 4 records.
- 25 Form 4/A records.
- Two page-observation rows.

The per-feed parsed-entry/new-accession counters in poll_summary.json are pre-global-dedup counts (20 and 50); they must not be summed as unique accessions. The compact artifact does not retain the raw Atom bodies, so the exact composition of repeated accession entries cannot be reconstructed from this poll alone. The canonical ledger is the authoritative deduplicated record.

All 35 rows have first_seen_interval_status = INITIAL_BASELINE_NO_LOWER_BOUND. Both feeds had no prior watermark. The local receipt interval was 19:26:00–19:26:08 UTC; the feed updated timestamps are consistency metadata, not proof of exact public availability.

Eligibility controls remain closed:

- bounded metadata rows: 0
- research-observation eligible rows: 0
- signal-eligible rows: 0
- public availability certified: false
- alpha test authorized: false
- security identity, historical F80 membership, owner attribution and transaction semantics verified: false
- filing XML/text downloaded: false
- raw transaction rows stored: false

No filing content, transaction rows, prices, or market data were downloaded.

## 4. Artifact and append-only commit

- Artifact: [14463211992](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679/artifacts/14463211992)
- Name: phase476-sec-form4-first-seen
- Size: 680 bytes; contains poll_summary.json only.
- ZIP SHA-256: 7765d6bd966aa2370b8ba5baff37a0bb3f3ba9445a0e278b3caa8c971532f5e6
- Artifact retention expiry: 2027-02-16 19:25:36 UTC.

The workflow committed three files (62 insertions) to main:

- research/data/sec_form4_first_seen/events.csv
- research/data/sec_form4_first_seen/feed_observations.csv
- research/data/sec_form4_first_seen/state.json

Commit: [93c1d7e6ea5c27044e0fb607b9511045a252aa43](https://github.com/jafelix81/NuevaEstrategia/commit/93c1d7e6ea5c27044e0fb607b9511045a252aa43).

Both feed state records now have a successful baseline watermark and last successful poll end of 2026-11-18 19:26:08 UTC.

## 5. Next SEC Form 4/4-A gate

The first scheduled capture confirms the existing Phase 476 workflow is executing. Issue [#142](https://github.com/jafelix81/NuevaEstrategia/issues/142) is therefore closed as completed.

The next successful scheduled poll must find each feed's previous accession watermark. Only a new event whose timezone-aware Atom updated timestamp is strictly after the prior successful poll end and no later than its local first receipt can be classified BOUNDED_METADATA_ONLY. A bounded metadata interval is still not an exact public-availability timestamp and does not itself authorize research use.

Before any Form 4 event study, each event still requires:
1. issuer/security identity reconciliation;
2. historical membership in the frozen universe;
3. reporting-owner and joint-owner attribution;
4. transaction semantics, including transaction code, direct/indirect ownership and 10b5-1 context;
5. acceptance/first-seen chronology and conservative executable entry;
6. complete survivorship-aware total-return prices and costs.

No event is admitted from this baseline.

## 6. Other source lines and operational status

- Phase 403 SEC Form 144: latest scheduled run remains [44302697069](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44302697069). Offline regression failed; live-capture was skipped and no artifact was produced. PR #140 passed 40 offline tests, but no post-fix scheduled success is yet visible at this cutoff. Issue [#136](https://github.com/jafelix81/NuevaEstrategia/issues/136) remains open; the next existing minute-47 UTC slot after this cutoff is 20:47 UTC. Do not dispatch manually or create a replacement.
- FINRA Reg SHO: first scheduled windows remain 22:30 and 23:30 UTC; no live first-seen observation is admitted at this cutoff.
- CFTC TFF: the current prospective history is still only one report cycle, not a 52-week warm-up.
- Options: OCC Phase 24B endpoint coverage remains insufficient for contract-level historical flow/OI; OptionMetrics/ThetaData and Cboe/Nasdaq NOTO/PHOTO remain conditional on licensed sample coverage, stable identifiers and first-receipt timestamps. No purchase or vendor contact.
- SEC 13D/G: keep the historical panel quarantined under the Phase 484/485 issuer-vs-filer identity findings; reuse the existing Phase 84/87 and PR #37 parent-retrieval chain after its SEC contact prerequisite. Do not create another crawler.
- FINRA Phase 20A/B/C: follow Phase 487 disposition. Phase 20B and 20C rules are rejected for promotion; Phase 20A residual IC remains exploratory only. No FINRA signal is admitted.

## 7. Strategy controls

No backtest, return study, OOS, bootstrap, LOO, or holdout test was run in Phase 488.

F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, production, or signal eligibility changed.
