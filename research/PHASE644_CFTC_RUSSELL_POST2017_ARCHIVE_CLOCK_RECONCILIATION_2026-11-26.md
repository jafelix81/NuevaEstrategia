# Phase 644 — CFTC Russell TFF post-2017 archive-clock reconciliation

**Audit cutoff:** 2026-11-26 16:48 UTC  
**Main HEAD at cutoff:** `4dc7765855af1e81990dd8d2cb2285c450682646`  
**Disposition:** retain one narrow Russell E-mini TFF historical subpanel as a conditional macro-positioning candidate; do not promote the broad CFTC archive to strict PIT and do not admit a signal.

## 1. Why this reconciliation is necessary

Phase 640 correctly concluded that the broad CFTC TFF historical archive cannot be treated as if every Tuesday position report were public on the usual Friday. The 2025 shutdown backlog, 2023 ION-related delays, holiday shifts and older archive migration anomalies invalidate a blanket Friday timestamp.

That global rejection must not erase a narrower, separately audited candidate already documented in the CFTC research chain:

- PR [#58 — Phase 383, Russell E-mini post-2017 archive availability panel](https://github.com/jafelix81/NuevaEstrategia/pull/58).
- PR [#55 — Phase 380, full post-launch archive timestamp census](https://github.com/jafelix81/NuevaEstrategia/pull/55).
- PR [#56 — Phase 382, targeted anomaly repair](https://github.com/jafelix81/NuevaEstrategia/pull/56).
- PR [#60 — Phase 384, clean mainline prospective-capture activation](https://github.com/jafelix81/NuevaEstrategia/pull/60), merged on 2026-11-14.

PR #58 is still Draft and stacked on the Phase 382 branch. Its historical panel is not part of main. PR #60 separately activated prospective capture on main; it does not certify the historical archive.

## 2. Russell E-mini subpanel evidence

The Phase 383 audit isolated CFTC TFF contract code `239742` for the post-2017 CME E-mini Russell 2000 era. It kept the earlier 2006–2008 Russell Mini x$100 contract separate.

Reported Phase 383 results:

| Audit item | Result |
|---|---:|
| API report-date/code rows reconciled | 482 |
| Archive pages valid | 480 / 482 |
| Archive page coverage | 99.5851% |
| Exact exceptions | 2 |
| Median archive Updated lag | 3 days |
| 90th-percentile lag | 6 days |
| Maximum observed lag | 50 days |
| Official schedule cross-checks not earlier than publication | 23 / 23 |

The two excluded observations are:
- **2018-09-25:** the nominal archive page heading identifies positions as of 2018-09-18; do not substitute or forward-fill.
- **2019-12-24:** archive page returned 404; do not impute.

For the 480 valid pages, Phase 383 proposed the first regular XNYS session strictly after the page's archive `Updated` date as a conservative availability proxy. This is **not** an exact first-publication timestamp. The 23 official schedule cross-checks support the direction of the bound but do not certify every historical page.

## 3. Reconcile with the global CFTC failure

Phase 380 audited 851 post-launch report dates across the broader TFF archive:

- 846/851 pages retrieved.
- Five missing/unparseable pages.
- One heading/date mismatch.
- Two older pages had `Updated` dates earlier than their report dates (2011 and 2012 migration anomalies).
- Recent official schedule checks were 23/23 not earlier than publication, but those checks do not establish every historical release time.
- Across that broader census, archive lag reached 70 days.

Therefore:

1. **Global CFTC TFF:** remains ineligible for blanket historical PIT use.
2. **Russell 239742 post-2017:** remains a conditional subpanel candidate under its own page-level validation and exclusions.
3. **Prospective Phase 384 collector:** remains the strictest receipt clock for genuinely new reports observed after activation.

The narrow subpanel does not override the global archive exceptions and must not be merged with the 2006–2008 Russell Mini era, other Russell contracts, or the full four-index dataset.

## 4. Permitted interpretation and proposed research role

TFF categories are self-reported business-purpose classifications, not verified identities of informed investors or proof of trade intent. The Russell series is an aggregate futures-positioning measure, not a stock-level flow feed.

If the archive-clock gate is strengthened, the only permitted initial hypothesis is:

> Changes in Leveraged Money, Asset Manager and Dealer positioning in Russell E-mini futures may contain incremental information about small-cap market regime, crowding or risk appetite.

Candidate features, to be evaluated separately:
- Net position divided by open interest for each category.
- Week-over-week changes in those normalized positions.
- Leveraged Money versus Asset Manager divergence.
- Dealer positioning as a separate liquidity/intermediation descriptor.

Do not infer that any category is inherently “smart money.” The feature set must also detect cadence changes; the Phase 384 collector already suppresses weekly rolling features when observed gaps are not within its weekly cadence gate, which matters as CFTC moves toward semiweekly publication.

## 5. Gates before a return test

The 480-page panel is promising enough to retain, but not yet sufficient for a strict historical alpha test. Required next steps:

1. Reproduce the 482-row report-date/code manifest from the exact Phase 383 artifact and preserve the two exclusions.
2. Reconcile every valid archive page's heading, report date, contract code and `Updated` field; retain page hash and retrieval provenance.
3. Expand independent publication-date cross-checks beyond the existing 23 cases. Where exact historical release dates cannot be established, keep the row as a conservative proxy only and do not call it certified PIT.
4. Use the first full XNYS session strictly after the conservative availability date; never use report Tuesday or the customary Friday by assumption.
5. Separate the post-2017 $50 E-mini contract from the old $100 Russell Mini and from other Russell futures.
6. Keep missing weeks missing. No zero fill, forward fill, report-date interpolation or cadence-based backdating.
7. Only after these gates, test market-regime outcomes at pre-registered horizons and compare any portfolio overlay with frozen LTM/F80 at identical exposure and costs. Use chronological OOS, block bootstrap and leave-one-time-block-out checks.

This is a macro-regime candidate, not a direct ticker-ranking signal. It cannot enter the F80 stock-selection model until incremental value against LTM/F80 is demonstrated.

## 6. Current prospective capture and operational preflight

- Mainline Phase 384 prospective capture last observed in Actions run [45753716471](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45753716471), successful. Its log reports `NO_NEW_REPORTS_OR_REVISIONS_NO_STATE_CHANGE`, 3,043 total rows and zero signal-eligible historical rows.
- Phase 643 state records eight prospective observations across two report-date clusters; this is not enough for a positioning model test.
- Phase 384 mainline workflow remains scheduled for weekday post-release polling; no manual dispatch or duplicate poll was launched.
- FINRA T1 ATS PRs #50/#61 remain Draft and stacked on old branches. Their 209-week panel is venue/reporting-participant concentration, not beneficial-owner or directional flow. Effective-dated security identity, historical F80 membership and inactive-security price coverage remain unpassed.
- Latest Actions inventory at cutoff: 8,350 total runs; latest 100 = 71 success / 17 failure / 12 cancelled; zero in-progress or queued.

## 7. Quantitative disposition

- CFTC Russell 239742 post-2017: **conditional macro-positioning research candidate; no alpha test authorized yet**.
- Broad CFTC historical archive: **not globally PIT-certified**.
- Prospective CFTC observations: **research monitoring only; insufficient sample**.
- Signals admitted: **0**.
- New OOS / bootstrap / LOO: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- No universe, capital, exposure, cost, parameter or holding-period change.
- No options data purchase, vendor contact or quote request; authorized options-data budget remains USD 0.

The next CFTC step is a reproducible, page-level Russell subpanel recheck—not an assumed-Friday backtest.
