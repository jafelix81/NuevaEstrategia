# Phase 493 — SEC Form 4/4-A accession-level feed provenance

**Audit cutoff:** 2026-11-19 01:46 UTC  
**Pre-change main:** `3ae5a3d27659ce0f1b806e3b1076ac4754600444`  
**Merged PR:** [#149](https://github.com/jafelix81/NuevaEstrategia/pull/149)  
**Merge commit:** `1adc01aeef5e8bf951e40b7e469af2b51aaf948e`  
**Disposition:** preserve every parsed accession occurrence before canonical deduplication; keep Form 4/4-A metadata-only and signal-ineligible.

## 1. Preflight

- GitHub Actions inventory: 7,865 total runs; latest 100 contained 72 successes, 26 failures and 2 cancellations; 0 active or queued at the audit.
- Branches: 318. Open PRs after opening Phase 493: 57.
- Latest scheduled SEC Form 4 run: [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679), 2026-11-18 19:25 UTC.
- Latest scheduled SEC Form 144 run: [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680), 2026-11-18 20:55 UTC.
- Latest recorded scheduled CFTC TFF capture: [44232546204](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44232546204), 2026-11-18 03:44:57 UTC.
- No FINRA Reg SHO scheduled capture appears in the current 100-run inventory.
- No live workflow was dispatched, rerun or duplicated.

## 2. Form 4 baseline reconciliation

The initial scheduled Form 4/4-A capture [44380395679](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44380395679) recorded two page-level feed observations:

| Feed | Raw Atom entries | Parsed accession occurrences |
|---|---:|---:|
| Form 4 feed | 100 | 20 |
| Form 4/A feed | 50 | 50 |
| **Total** | **150** | **70** |

The canonical event ledger contains **35 unique accession numbers**: 10 Form 4 and 25 Form 4/A. Thus 35 of the 70 parsed accession occurrences were repeated occurrences of accessions already represented in the canonical ledger.

The initial `feed_observations.csv` retained page counts and hashes, but not each accession occurrence. The canonical ledger retained only one feed/path observation per accession. The exact split between same-feed and cross-feed duplicates, and any additional feed-path CIK variants, therefore cannot be reconstructed from the committed baseline. This is an auditability limitation, not proof of a parser defect or of 35 separate economic events.

All 35 canonical rows remain `INITIAL_BASELINE_NO_LOWER_BOUND`; 0 are research-eligible, 0 have certified public availability, and 0 are signal-eligible.

## 3. Phase 493 change

The collector now appends an additional file:

`research/data/sec_form4_first_seen/accession_observations.csv`

It records every parsed accession occurrence up to and including the prior-watermark boundary, with:

- poll/run and feed identity;
- accession, form, filing date and filing URL;
- feed-path CIK explicitly marked unverified;
- Atom updated value and local page-response receipt;
- page offset and exact response SHA-256;
- prior-watermark status and poll completeness;
- event interval classification;
- same-feed and cross-feed duplicate flags;
- whether the accession already existed in the canonical ledger;
- whether this occurrence emitted the canonical first-seen event; and
- whether a candidate was suppressed by an incomplete poll.

The sidecar is append-only. It does not store raw Atom payloads, filing XML/text, transaction rows or owner semantics. Incomplete-poll candidates may be retained in the observation sidecar for audit, but they cannot create canonical events or advance the successful watermark.

**The initial baseline is not backfilled.** Its raw Atom payloads were not retained, so accession-level duplicate/path provenance for that poll is irrecoverable. The new sidecar begins with the first scheduled poll after the Phase 493 merge.

## 4. Cross-source status at cutoff

### SEC Form 144

The current ledger has 247 accession rows:
- 142 initial-baseline rows without a lower bound;
- 50 rows quarantined as `POSSIBLE_FEED_WINDOW_GAP`;
- 55 bounded metadata observations, comprising 51 from the latest successful capture and 4 earlier bounded observations.

The latest capture [44396134680](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44396134680) added 51 accessions (50 Form 144 and 1 Form 144/A). Six matched a candidate CIK manifest, but none has verified historical F80 membership or certified public availability. All 247 rows remain signal-ineligible.

### CFTC TFF

The prospective state contains 3,039 row hashes, with the latest report date 2026-11-10 for four contract codes. The only recorded prospective capture remains 2026-11-18 03:44:57 UTC. This is not 52 independent weekly observations; the preregistered warm-up remains unmet and no positioning signal is eligible.

### FINRA and options

FINRA Phase 20B/20C remain unpromoted after Phase 487. The prospective Reg SHO ledger is still absent. Cboe/OptionMetrics/ThetaData remain conditional on historical coverage, timestamp integrity and licensing; no data purchase or new crawler was initiated.

SEC 13D/G remains quarantined for issuer-versus-filer identity. The earlier N-PORT ownership-growth hypothesis remains rejected.

## 5. Validation and merge

- PR [#149](https://github.com/jafelix81/NuevaEstrategia/pull/149) merged to main.
- [GitHub Actions run 44439202893](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44439202893): **39/39 offline tests passed**.
- The `live-capture` job was skipped as designed for a pull-request event.
- No live SEC request or artifact was produced by CI.

## 6. Schedule delivery

The main-branch schedules remain:
- Form 4/4-A: `17 * * * 1-5` UTC;
- Form 144: `47 * * * *` UTC;
- CFTC TFF: `25 22 * * 1-5` UTC;
- FINRA Reg SHO: `30 22,23 * * 1-5` UTC.

No scheduled event appears after the 2026-11-18 20:55 UTC Form 144 run in the current Actions inventory. The 2026-11-18 22:25 CFTC and 22:30/23:30 FINRA slots are not present; the 2026-11-19 00:47 Form 144 and 01:17 Form 4 slots are also not present. At cutoff, the next Form 144 slot (01:47 UTC) and Form 4 slot (02:17 UTC) had not yet occurred.

The read interface does not expose the repository's administrative workflow-enabled state. Missing schedule events are not proof that a workflow is disabled. No cron was changed and no manual capture was used.

## 7. Next gate

1. Let the next existing scheduled Form 4 poll run; do not dispatch a duplicate.
2. Confirm both feed watermarks are found and the new accession-observation sidecar is appended.
3. Reconcile same-feed/cross-feed duplicates and all path CIK variants from the sidecar.
4. Only after at least two successful bounded polls, validate issuer/security identity, owner attribution, transaction semantics and public-availability timing on a stratified filing sample.
5. Do not run an insider event study until those gates and historical universe membership are satisfied.

No backtest, event study, alpha, OOS, bootstrap, LOO or holdout test was run. `F80_TOP20_PARTIAL50_BASELINE_C20` and production remain frozen.
