# Smart Money Research state addendum — Phase 468 (2026-11-18)

## Phase 468 — Strict FINRA flow executable-label PIT guard

- Added \`research/phase468_finra_flow_pit_labeler.py\` and 30 synthetic regression tests.
- The labeler requires a first-seen observation with timezone-aware poll start, first receipt and poll end; HTTP 200; raw SHA-256; positive integer row count; schema version; and first-seen event kind.
- First receipt is treated as a conservative local-knowledge upper bound, not the exact public release instant. Entry is the first supplied XNYS open strictly after receipt; H-session labels exit at the close of the H-th session including entry day.
- Historical Phase 31 rows without first-receipt timestamps are rejected. Same-day close entry is never used. Missing bars, duplicate observations, revisions, invalid clocks, unsupported price bases and incomplete price paths fail closed.
- Only adjusted OHLC is accepted. Split-adjusted returns omit cash dividends; a later economic test still requires total-return data, delisting/terminal returns, corporate actions, costs and effective-dated security identity.
- 30 synthetic tests passed locally. Branch-only CI was added; it performs no market-data access and has no schedule.
- No FINRA request, price download, label generation on historical data, backtest, OOS, bootstrap, LOO, signal admission or production change.

## Operational preflight — 2026-11-18 01:13 UTC

- Actions inventory: 7,730 total runs; zero in-progress; zero queued.
- Branches: 300 (three pages of 100). Open PRs: 57.
- PR #129's existing runs [44209207223](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44209207223) and [44209207126](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44209207126) completed successfully. Each ran one offline regression job; neither produced artifacts.
- SEC Form 144: latest scheduled run remains [44179257367](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44179257367). The expected 2026-11-18 00:47 UTC slot is absent from the scheduled-run inventory through 01:13 UTC. Phase 465 pagination remains not live-validated.
- CFTC TFF: latest verified run remains bootstrap/push [43525140200](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43525140200). The expected 2026-11-17 22:25 UTC scheduled slot is absent.
- The connected read interface does not expose administrative enabled/disabled workflow state. Human check remains required for the two existing workflows. Do not create replacements or change crons before that check.
- PR #129 remains draft/open and unmerged. Main HEAD remains \`bc4a2ccecd32962340831eea54563743dadfe6c6\` at this preflight.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
