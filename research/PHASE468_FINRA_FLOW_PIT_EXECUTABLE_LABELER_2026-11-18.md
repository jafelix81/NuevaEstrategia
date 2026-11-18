# Phase 468 — FINRA flow executable-label PIT guard

**Audit date:** 2026-11-18 UTC  
**Disposition:** **STRICT FIRST-RECEIPT LABELER IMPLEMENTED; NO HISTORICAL TIMESTAMPS IMPUTED; NO ALPHA ADMISSION.**  
**Scope:** implement a reusable label constructor following the Phase 467 finding that Phase 31 starts labels at the signal-date close even though FINRA daily short-sale volume is published after regular trading hours. Synthetic regression tests only; no market-data download or return test.

## 1. Repository preflight

- Main HEAD at the Phase 467 audit cutoff: \`bc4a2ccecd32962340831eea54563743dadfe6c6\`.
- PR #129 remains a draft/open PR based on main. Its two existing Actions checks, runs [44209207223](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44209207223) and [44209207126](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44209207126), completed successfully. Each had one \`offline-regression\` job; neither produced artifacts.
- Latest Actions inventory: 7,730 total runs; zero in-progress and zero queued.
- Branches: 300 across three 100-item pages. Open PRs: 57.
- No scheduled SEC or CFTC capture is present after the expected slots described below. No capture was manually dispatched.

## 2. Scheduled delivery recheck

**SEC Form 144**
- Existing workflow: \`.github/workflows/phase403_sec_form144_first_seen_capture.yml\`, cron \`47 * * * *\` UTC.
- Latest scheduled run remains [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367), created 2026-11-17 21:23:10 UTC.
- The expected 2026-11-18 00:47 UTC slot does not appear in the scheduled-run inventory through 01:13 UTC.
- Phase 465 pagination remains unvalidated in a scheduled production run.

**CFTC TFF**
- Existing workflow: \`.github/workflows/phase384_cftc_tff_prospective_capture.yml\`, cron \`25 22 * * 1-5\` UTC.
- Latest verified run remains bootstrap/push [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200), 2026-11-13.
- The expected 2026-11-17 22:25 UTC slot does not appear in the scheduled-run inventory.
- The read connector does not expose the administrative enabled/disabled state. Human check remains required for the two existing workflows; do not create replacements or alter crons.

## 3. Label contract

The new \`research/phase468_finra_flow_pit_labeler.py\` module constructs labels only. It does not compute a signal, optimize features, run a portfolio, or admit alpha.

Each flow observation must have:
- \`symbol\`, \`trade_date\`;
- timezone-aware \`poll_start_utc\`, \`first_seen_utc\`, and \`poll_end_utc\`;
- HTTP status 200;
- raw response SHA-256;
- positive integer row count;
- schema version;
- \`observation_kind="first_seen"\`.

The local first-receipt timestamp is a conservative upper bound on when our process knew the file, not proof of the exact public publication instant. Historical rows without this timestamp are rejected; no lag is guessed or imputed.

Timing rules:
1. \`poll_start_utc <= first_seen_utc <= poll_end_utc\`.
2. \`first_seen_utc\` must be strictly later than the XNYS close on the file's trade date.
3. Entry is the first supplied XNYS session open strictly later than first receipt. If first receipt is at or after an opening timestamp, that opening price is skipped.
4. Horizon H exits at the close of the H-th session counting the entry session as session 1.
5. The signal-date close is never used as entry.
6. Missing intermediate daily bars invalidate that horizon; missing entry prices invalidate the event. Duplicate symbol/trade-date first-seen events are rejected.

The caller must provide a verified XNYS schedule including early closes and a consistent adjusted OHLC panel. Only \`split_adjusted_ohlc\` and \`total_return_adjusted_ohlc\` are accepted. Split-adjusted labels omit cash dividends; a final economic test must use total-return data, delisting/terminal returns, corporate actions, realistic costs, and the frozen universe's effective-dated identity coverage.

## 4. Validation

- 30 synthetic unit tests passed locally.
- The branch-only Actions workflow runs Python compilation and the 30 tests on push to the Phase 467 branch.
- The test suite covers post-close entry, exact/after-open receipt, timezone normalization, missing/naive timestamps, poll bounds, non-200 responses, invalid hashes/row counts, revisions, duplicates, missing entry/intermediate bars, incomplete horizon tails, unsupported price bases, and calendar-clock errors.
- No FINRA request, price download, historical label generation, backtest, OOS, bootstrap, or LOO was run.

## 5. Research disposition

| Item | Decision |
|---|---|
| Phase 31 same-close labels | Invalid for strict PIT; retain as diagnostics only |
| Historical daily flow without first-seen ledger | Not admitted to this labeler |
| Prospective first-seen flow | Conditional candidate after capture and price/universe gates |
| New signal / alpha | None |
| Production change | None |

The next research gate is to connect this labeler to a prospective raw-file first-seen ledger and a verified adjusted OHLC/security-master panel. Only after coverage, delisting, corporate-action and execution-cost gates pass should flow-only features be compared with frozen LTM/F80 on identical exposure and chronological OOS.

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
