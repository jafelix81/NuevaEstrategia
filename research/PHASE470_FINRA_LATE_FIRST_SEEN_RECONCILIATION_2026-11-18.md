# Phase 470 — FINRA delayed first-seen recovery and label-clock audit

**Audit date:** 2026-11-18 UTC  
**Disposition:** **ALLOW DELAYED FIRST LOCAL RECEIPT ONLY WITH PRIOR SCHEDULED NON-AVAILABILITY EVIDENCE; NO SIGNAL OR ALPHA ADMISSION.**

## 1. Preflight and current execution evidence

- Main HEAD: `843dcf2601ab04e0a7901f9b988c99252ed68115`; PR #129 (Phases 467–469) is merged.
- Final PR run [44224662699](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44224662699): `offline-regression` completed successfully; 20/20 Phase 469 tests passed. `live-capture` was skipped as designed on a pull request. No artifacts were produced.
- The Phase 469 schedule is `30 22,23 * * 1-5` UTC. Since PR #129 merged at 2026-11-18 02:39:32 UTC, its first post-merge scheduled slot is 2026-11-18 22:30 UTC. No live capture is claimed in this phase.
- The connected GitHub interface exposes repository files, selected run jobs/logs/artifacts, commit-associated PR runs and PR history, but not a complete current workflow-run listing or workflow enabled/disabled state. Therefore this report does not claim a global active-run count or administrative enablement state.
- The latest known SEC Phase 403 production run inspected directly was [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367): both offline and live-capture jobs succeeded; artifact [14371301851](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367/artifacts/14371301851) exists (2,239 bytes). It predates Phase 465 pagination and does not validate the newer paginated capture.
- The latest known CFTC Phase 384 run inspected directly was [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200): the bootstrap job succeeded; artifact [14084802705](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200/artifacts/14084802705) exists (1,068 bytes). It was a branch-push bootstrap, not a scheduled prospective observation.

## 2. Problem found in the Phase 469 eligibility rule

Phase 469 correctly treated an old-date file first encountered during initial activation as bootstrap. However, its same-New-York-date-only rule also classified a file as bootstrap if:

1. A scheduled poll for trade date D returned HTTP 403/404 and persisted `poll_status=not_available`.
2. A later scheduled poll (for example, on D+1) rechecked the ten-day lookback and received the first valid HTTP 200 file for D.
3. The collector had never previously received a valid version of D.

That later response is a real first receipt for this collector. The strategy cannot use the file before that later receipt, but it can use it prospectively after receipt. Permanently classifying it as bootstrap unnecessarily discards valid delayed observations. The correction must not infer that FINRA first published the file at the later receipt; it records only when this collector first received a valid file.

## 3. Phase 470 rule

A non-empty valid file can be research-observation eligible as either:

- `first_seen`: first valid scheduled receipt on the same New York trade date, after 16:00 ET; or
- `late_first_seen`: first valid scheduled receipt for an earlier trade date, only if the existing append-only `polls.csv` contains an earlier scheduled `not_available` poll for that exact date, with prior poll end strictly before the current poll start and the prior poll occurring at/after 16:00 ET.

Otherwise an old-date first capture remains `bootstrap`.

Additional controls:

- The prior evidence must be from a different run and `mode=schedule`; manual diagnostic runs do not qualify.
- Only `not_available` (HTTP 403/404) qualifies. HTTP errors, malformed HTTP-200 files and revisions do not establish a delayed first receipt.
- A prior poll timestamp must be timezone-aware and precede the current poll start. A malformed prior ledger fails closed.
- First-seen UTC remains the current complete-response receipt time. It is never replaced with the old trade date, file timestamp, acceptance timestamp or prior failed-poll time.
- The original first-seen hash/time is immutable. Later changed hashes remain revisions and are never new first-seen observations.
- All records retain `signal_eligible=false`.

## 4. Phase 468 executable-label behavior

The labeler accepts `late_first_seen` only with the same provenance requirements as `first_seen`. It still requires:

- first receipt strictly after the original trade-date regular-session close;
- the entry price to be the first XNYS open strictly after the actual first receipt;
- complete, consistent price paths and supported split-adjusted or total-return-adjusted OHLC;
- explicit signal age in sessions.

For example, if a file for D is first received after the close on D+1, the entry is not the D+1 open; it is the next session open strictly after the D+1 receipt. The labeler records the additional signal age rather than backdating the trade. No maximum holding period is imposed; the existing label horizons are merely diagnostic conventions.

## 5. Validation and limits

Phase 470 extends the existing offline regression workflow to run both Phase 468 and Phase 469 suites. New regressions cover:

- an earlier scheduled 403/404 followed by a later valid first receipt;
- rejection of old-date bootstrap without prior scheduled non-availability evidence;
- expansion of a hash-matched delayed event into Phase 468 inputs;
- entry only after the later actual receipt and correct signal-age accounting;
- continued rejection of manual, malformed, revision and signal-eligible shortcuts.

No live FINRA request, price download, raw-data persistence, historical backfill, forward-return test, alpha, OOS, bootstrap, LOO or signal admission is performed by this phase. The first live scheduled capture after PR #129 merge remains the next operational validation.

## 6. Official source interpretation

FINRA's May 10, 2019 notice explains that daily short-sale files include only publicly disseminated transactions, are not consolidated with exchange data, and can omit offsetting customer purchase activity in certain riskless-principal facilitation examples. FINRA Regulatory Notice 21-19 distinguishes daily transaction-volume files from twice-monthly short-interest position reports.

Official sources:

- https://www.finra.org/rules-guidance/notices/information-notice-051019
- https://www.finra.org/sites/default/files/2021-06/Regulatory-Notice-21-19.pdf
- https://www.finra.org/sites/default/files/DailyShortSaleVolumeFileLayout.pdf

Accordingly, the ratio remains a share of publicly disseminated FINRA-facility reported volume, not total U.S. market volume, net short positioning, beneficial ownership or verified institutional activity. The source remains a conditional market-microstructure hypothesis, not a “smart money” label.

## 7. Frozen strategy

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameters, holding period, capital, exposure, costs, holdout, production, or signal eligibility changed.
