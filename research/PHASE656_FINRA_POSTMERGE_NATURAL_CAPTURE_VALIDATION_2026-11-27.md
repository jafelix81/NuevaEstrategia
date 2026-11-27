# Phase 656 — FINRA CNMS post-merge natural-capture validation

**Audit cutoff:** 2026-11-27 04:45 UTC  
**Latest observed mainline capture commit:** `ea17538125256cf3098d7a4cc3845edb92c1ecb1` (SEC Form 144, 2026-11-27 04:35:45 UTC)  
**FINRA capture commit:** `9a8f88d89530b2f003848c119f80e75b1360088c`  
**Disposition:** Phase 650's partial-symbol quarantine parser passed its first post-merge scheduled live capture. The seven available historical files parsed as partial panels, but all were correctly classified as bootstrap rather than first-seen observations. No FINRA observation became research-eligible and no signal was admitted.

## 1. Preflight and repository state

- Phase 650 PR [#247](https://github.com/jafelix81/NuevaEstrategia/pull/247) is merged as `c7379f42ffffd631e8ce1bc3b9b3261871e3480d`; its offline validation passed **62/62 tests** in [run 45895296971](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45895296971).
- First natural post-merge FINRA run [45939887443](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443): offline-regression and live-capture jobs both completed successfully. Artifact [15172510181](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45939887443/artifacts/15172510181).
- Latest observed Form 144 scheduled run [45940802895](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45940802895): offline-regression and live-capture jobs both completed successfully. Artifacts: [15172139727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45940802895/artifacts/15172139727), [15173150738](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45940802895/artifacts/15173150738), [15172114851](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45940802895/artifacts/15172114851).
- Latest observed Form 4 natural capture remains [45917890802](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45917890802); both jobs succeeded. Latest observed 13F capture [45910142871](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45910142871); both jobs succeeded.
- The branch census returned **407 branches** over five pages, including `main`, existing Phase 20C/Smart Money branches and the merged Phase 650 branch. No Phase 656 branch was created. Existing research branches were not rewritten.
- Draft PRs #199 (Form 4 overlap) and #37 (13D/G parent identity) remain unmerged. No workflow was manually dispatched, rerun, cancelled or duplicated.

## 2. FINRA live result

Run `45939887443` requested eight trade dates: 2026-11-26, 25, 24, 23, 20, 19, 18 and 17.

| Measure | Result |
|---|---:|
| HTTP 200 files | 7 |
| HTTP 403 / not available | 1 (2026-11-26) |
| Valid parsed files | 7 |
| Valid files marked partial | 7 |
| Duplicate symbol-date groups | 14 |
| Extra duplicate rows | 14 |
| Row occurrences quarantined | 28 |
| Exact byte-identical duplicate rows | 0 |
| First-seen / late-first-seen events | 0 / 0 |
| Research-eligible observations | 0 |
| Signal-eligible observations | 0 |

Each of the seven files contained two repeated symbols: **BCPC** and **TPC**. Their repeated rows had overlapping or identical facility-token sets, but were not byte-identical duplicates. The parser quarantined *all* rows for each repeated symbol and retained the other unique-symbol rows. Each file retained 12,275–12,414 symbols from 12,279–12,418 source rows. The 14 duplicate groups are two symbols repeated across seven dates, not 14 distinct issuers.

All seven successful files were recorded as **bootstrap**. This is deliberate: the prior parser had rejected the historical files and had not established an eligible first-seen clock for them. The collector did not backdate availability or promote those historical files retrospectively. The 2026-11-26 file returned HTTP 403 and was recorded as not available.

The append-only state now records seven bootstrap dates and their receipt/hash metadata. Only metadata and duplicate diagnostics were persisted; raw FINRA rows and volume values remain unpersisted. Therefore this run validates safe parsing and quarantine, **not a usable short-flow feature panel or an alpha hypothesis**.

## 3. Other live-feed checks

### SEC Form 144

Run `45940802895` appended 53 feed observations (50 Form 144 and 3 Form 144/A). No new accession was discovered. A bounded backfill enriched 10 previously known accessions with 58 structured detail rows; the ledger now contains **845 accessions and 5,595 detail rows**, with 158 backfill accessions remaining. All 807 research-observation-eligible filing headers have bounded first-seen intervals; no malformed interval or parse error was reported. Signal-eligible count remains zero.

### SEC Form 4

Run `45917890802` parsed 10 accessions and appended 13 owner rows. Its Form 144/Form 4 crosswalk contained 14 rows and 12 matched Form 4 accessions; signal-eligible matches remained zero. The Phase 655 overlap cohort still has 21 accessions, 13 with owner sidecars and eight pending; filing-level owner data does not establish transaction-line attribution or historical F80 membership.

### SEC Form 13F

Run `45910142871` completed all feed and watermark checks, observed 29 existing accession records, found zero new accessions and downloaded no holdings. No 13F signal was admitted.

## 4. Interpretation and next gates

1. Let the next **natural scheduled** FINRA poll run; do not dispatch a manual backfill. Specifically verify whether 2026-11-26, previously 403, becomes a conservatively timestamped `late_first_seen`, and whether the next trade-date file becomes `first_seen`. A daily FINRA file received after the close cannot be traded at that same close; the earliest executable session must follow the conservative receipt clock.
2. Preserve BCPC/TPC quarantine until source grain is independently resolved. Do not sum, select or infer among overlapping rows.
3. Keep the FINRA line research-ineligible until row-level volume features can be reproducibly reconstructed from a permitted source and linked to effective-dated security identity and historical F80 membership.
4. Continue the bounded Form 4 owner/footnote queue and preserve issuer/accession clustering. Do not interpret transaction code P or a blank 10b5-1 box as proof of discretionary open-market buying.
5. Maintain the existing 13D/G global-index sample as a separate manual-only gate; do not trigger legacy F80-filer-only workflows.

## 5. Strategy controls

- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.
- New signal promoted: **none**.
- Incremental alpha demonstrated: **none**.
- New forward-return/OOS/bootstrap/LOO test: **none**.
- Holdout untouched.
- No price series or forward returns inspected in this phase.
- No universe, parameters, costs, exposure, capital, production logic or holding-period constraints changed.
- No vendor contacted, quote requested or data purchased; budget remains **USD 0**.
