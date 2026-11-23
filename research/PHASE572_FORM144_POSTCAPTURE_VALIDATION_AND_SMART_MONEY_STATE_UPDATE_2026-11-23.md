# Phase 572 — First natural post-Phase-565 Form 144 validation and ledger refresh

**Audit cutoff:** 2026-11-23 08:20 UTC. **Main HEAD before this report:** `c1e44314a3eb93a723306a3e988b5dc9837f56f6`.

## Executive decision

The first natural scheduled Form 144 run after Phase 565's merge completed successfully and produced the dedicated post-capture Phase 549 artifact. This closes the specific integration-validation gate left open in Phases 565–571. It does **not** admit a signal: the capture had no new accessions, and the 10b5-1 audit is descriptive only.

## Actions / repository preflight

- Latest Actions inventory: **8,074 total**; latest 100: **96 success / 4 failure**; **0 queued or in progress**.
- Branch inventory: **373** (four REST pages); open PRs: **72**.
- Latest natural runs:
  - Form 144: [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123), schedule event, 2026-11-23 08:18:38–08:19:04 UTC, both `offline-regression` and `live-capture` succeeded.
  - Form 4: [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578), schedule event, 2026-11-23 07:48:40–07:49:00 UTC, both jobs succeeded.
- No active workflow was duplicated or dispatched.
- The latest Form 144 run's automatic append-only commit is [c1e44314](https://github.com/jafelix81/NuevaEstrategia/commit/c1e44314a3eb93a723306a3e988b5dc9837f56f6).

## Form 144: natural post-merge validation

Run [45137579123](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123) exercised the merged workflow on `main`. Both jobs succeeded. In `live-capture`, the following steps all completed successfully:

1. event-ledger schema migration;
2. SEC Latest Filings capture;
3. post-capture Phase 516 ledger-quality audit;
4. post-capture Phase 549 10b5-1 audit;
5. explicit count/control reconciliation;
6. dedicated artifact upload;
7. append-only ledger/poll-state persistence.

The poll disposition was `POLL_COMPLETE_NO_NEW_ACCESSIONS`. It observed 51 unique Form 144 feed accessions and 2 Form 144/A feed accessions, but both feeds returned no new accessions. The successful poll interval is bounded by successive successful poll starts; first-seen timestamps remain receipt upper bounds, not exact SEC public-release timestamps.

Bounded backfill parsed 10 existing accessions, with 0 parse errors; 258 bounded accessions remain. The persisted ledger now contains **305 accessions and 2,244 detail rows**, up from 295 / 2,196 at the previous snapshot. Phase 516 reconciled the same 305 / 2,244 counts, reported 0 parse-error rows, 2,244 source-hash matches, 0 mismatches and 0 non-comparable rows. Its disposition is descriptive ledger-quality pass with a semantic-review queue; `no_signal_admitted=true`.

Artifacts:
- [Phase 565 post-capture 10b5-1 summary — 14800277734](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800277734), ZIP SHA-256 `7d8d62289b21ce28de22ebf408fd461534d1cea0b95034f00379b0e51e741c58`.
- [Phase 403 first-seen poll audit — 14799993648](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14799993648), ZIP SHA-256 `3ec04baa014f21361478ea2110f2601278dd7122cdb9bfbb9a09c7eabde9f821`.
- [Phase 560 current descriptive refresh — 14800551409](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45137579123/artifacts/14800551409), ZIP SHA-256 `97a317d501a908ae2340e6f900bc3fdf241c7a6e1755bfd50a45338802770047`.

## Phase 549 descriptive findings (305 Form 144 accessions / 2,244 detail rows)

- Formal plan-adoption date present in **118/305 accessions (38.69%)**, spanning **70 distinct dates**.
- All 118 formal dates precede the notice date; none is after or equal to the notice date.
- Plan-date-to-notice lag: median **183 days**, P25 **96**, P75 **264**, range **72–546** days.
- Remarks polarity: **10 positive explicit**, **4 negative explicit**, **1 ambiguous**, **290 no mention**.
- Cross-tab: 10 formal-date/positive, 1 formal-date/ambiguous, 107 formal-date/no-mention; 4 no-formal-date/negative and 183 no-formal-date/no-mention.
- Eleven accessions contain sell-to-cover/tax-withholding context. Four explicit negative Fermi notices form one cluster totaling **2,253,270 proposed units**. These are proposed-sale notices, not confirmed executions or discretionary bearish sales.
- One plan-termination accession is present.

The audit explicitly keeps formal plan date separate from signal-availability time, treats remarks presence separately from polarity, and treats Form 144 as a proposed-sale notice rather than execution confirmation.

The post-capture artifact's controls confirm: no alpha test, no OOS test, no bootstrap, no LOO, no signal admission, no production change, and F80 frozen.

## Form 4 cross-check

Latest natural Form 4 run [45133809578](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578) succeeded with both jobs. Artifact [14798359037](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45133809578/artifacts/14798359037), ZIP SHA-256 `55a7d8fa26c06b523318c5b7e829d396a7afbcfadcdf181904ad834c18297033`.

- The bounded structured-detail backfill parsed 10 accessions with 0 parse errors; 1,776 remain in that queue.
- Owner enrichment parsed 10 accessions and appended 10 filing-level owner rows; 20 bounded owner accessions remain.
- Crosswalk remains 3 descriptive rows, 2 matched Form 4 accessions, 2 multi-owner accessions quarantined, 9 accessions without single-owner identity, and **0 signal-eligible matches**.
- Filing-level owner identity is not transaction-line attribution. The ATEA exercise/tax-planning examples remain negative controls, not discretionary insider-sale alpha.

## Scheduling interpretation

Form 144's cron remains `47 * * * *`; the 08:18:38 UTC run was about 31m38s after the nominal 07:47 slot. Form 4's 07:48:40 UTC run was about 31m40s after its 07:17 slot. These are successful natural recoveries with material dispatch delay, not proof of uninterrupted hourly delivery. Do not change cron or manually poll solely from this observation. Issue [#194](https://github.com/jafelix81/NuevaEstrategia/issues/194) is updated with the new evidence and the remaining continuity caveat.

## Other research gates unchanged

- FINRA Short Interest: next scheduled publication 2026-11-24 for settlement 2026-11-13. Use existing Phase 447 single-settlement workflow only after permitted-use terms and authorized credentials are confirmed; set `settlement_date=2026-11-13`. No request or dispatch in this phase.
- FINRA Weekly Summary remains a candidate with a conservative final-snapshot PIT proxy, not strict-PIT admitted.
- FINRA Reg SHO still needs natural post-Phase-539 parser validation.
- SEC FTD PR #204 remains Draft and credential-gated; no SEC FTD request.
- Cboe/OPRA options remain license/PIT-gated; MIDAS remains market-structure/liquidity context only; CFTC TFF remains prospectively under-sampled.
- Phase 20C remains 328/335 histories, with seven inactive/acquired/renamed histories requiring terminal/successor-return reconciliation.

## Quantitative decision

- New signals admitted: **0**.
- Incremental alpha demonstrated: **none**.
- New return/OOS/bootstrap/LOO tests: **0**.
- Universe, costs, exposure, holding period, holdout and production: unchanged.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: **frozen**.

This phase closes a workflow-validation milestone and improves the Form 144 descriptive ledger. It does not establish predictive value or economic edge.
