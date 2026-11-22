# Phase 559 — SEC FTD credential-chain integration and offline validation

**Audit cutoff:** 2026-11-22 16:55 UTC  
**Base:** `main` at `f94f51fd82dbed8fe06a4d710da49d3cccb3abf0`  
**Disposition:** Phase 43 and Phase 44 now share one fail-closed `SEC_USER_AGENT` contract. The Phase 44 pull-request path is offline-only; SEC downloads are available only through an explicit manual dispatch after the secret is configured. This is an integration/safety improvement, not a live-access or alpha result.

## 1. Preflight

- Actions API: 8,052 total runs; latest 100 = 98 completed successes / 2 completed failures; zero active or queued.
- Branch inventory: 370 (100 + 100 + 100 + 70); open PRs: 71.
- Latest natural Form 144 run: [45012113618](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618), created 2026-11-22 10:22:19 UTC, on historical head `b830c13fa2f30c58967257086caf4008a543471c`.
- At the 16:55 UTC cutoff, no newer run appears in the latest 100. The nominal hourly :47 slots from 10:47 through 16:47 UTC are absent from the run inventory. `created_at` is run creation, not a certified cron-fire timestamp; treat this as an operational delivery/observability gap, not proof of administrative disablement.
- Run 45012113618 jobs were inspected directly: `offline-regression` and `live-capture` both succeeded. The live job's post-capture Phase 516 audit reported 275 filing headers / 2,072 rows; same-run count reconciliation passed. Artifact [14750197356](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45012113618/artifacts/14750197356) is unexpired (3,643 bytes; SHA-256 `2b7d749c4555754ff4d1ddad135ccf97c10bd0ad9e879597ad16968887bd88b6`).
- Sunday means no weekday FINRA Reg SHO or Form 4 scheduled capture was expected. No workflow was dispatched, rerun, cancelled or duplicated during preflight.

## 2. Integration defect addressed

The existing chain had three incompatible paths:

1. Canonical Phase 43 on main used a generic non-contact User-Agent.
2. PR #198 correctly proposed `secrets.SEC_USER_AGENT` for Phase 43, but was Draft, non-mergeable and based on an older main snapshot.
3. PR #5's Phase 44 script still hardcoded `research@example.com`; its workflow did not pass the secret. PR #4 added a misspelled duplicate `fase43` workflow and a second Phase 43 parser.

This branch starts from current main, updates the existing canonical Phase 43 workflow, adds only the Phase 44-specific workflow/script/input, and does not copy the duplicate `fase43` workflow or parser.

## 3. Changes

- Phase 43 now requires the `SEC_USER_AGENT` Actions secret and checks for a monitored email before any SEC request. The value is never printed.
- Phase 44 uses the same environment variable; the script fails closed before downloading if the secret is missing or has no monitored email.
- Phase 44 pull-request and branch-push validation is offline-only. The live SEC download job is gated exclusively to `workflow_dispatch`.
- The Phase 44 parser now preserves CUSIP-only records and reports exact duplicate economic rows and identity-missing rows, instead of silently dropping all ticker-less rows.
- The frozen Phase 21C input is checked as exactly 335 unique tickers.
- Five offline unit tests cover credential fail-closed behavior, User-Agent propagation, schema validation, symbol/CUSIP identity handling, and the exact 335-name universe constraint.

## 4. FTD coverage interpretation retained

The prior representative-file audit reports:

- 2018 first half: 43,567 economic rows; 253/335 fixed-snapshot symbols (75.522%).
- 2026 second half: 66,693 economic rows; 316/335 (94.328%).
- Both files: 237/335 (70.746%); either: 332/335 (99.104%).

These are fixed-snapshot feasibility diagnostics, not date-appropriate active-universe coverage. Missing ticker rows must not be treated as zero FTD. FTD is an outstanding settlement-fails balance, not daily short-sale flow or evidence of informed direction. No FTD return test is authorized until an effective-dated active-universe/CUSIP crosswalk is reproducible.

## 5. Validation and remaining human gate

This branch's push workflow runs only offline tests. A successful offline run does not validate SEC access.

The repository connector cannot inspect or set the GitHub Actions secret. Before any live sample, the repository owner must configure `SEC_USER_AGENT` with a project identifier and monitored contact email. Then:
1. manually dispatch Phase 43's existing two-file representative sample;
2. require both files to download and pass schema/type/trailer/hash checks;
3. only after Phase 43 passes, manually dispatch Phase 44's same bounded two-file coverage sample;
4. do not start historical backfill or return testing until the active-universe/CUSIP crosswalk gate passes.

No SEC request, sample download, backfill, purchase, signal test, return test, OOS, bootstrap, LOO or production change occurred in this phase.

## Frozen controls

- New signals admitted: **0**.
- `F80_TOP20_PARTIAL50_BASELINE_C20`: unchanged and frozen.
- No universe, parameters, exposure, costs, holding-period policy, holdout or production changes.
