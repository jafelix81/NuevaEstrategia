# Smart Money Research state addendum — Phase 499 (2026-11-19)

## Completed
- Recovered and hash-verified the immutable Phase 29 and corrected Phase 30 artifacts.
- Re-adjudicated the later bounded Top-20 state-machine implementation, not the earlier invalid residual-book run.
- Phase 29 selected MOM120 after 2017–2020 discovery and 2021–2023 validation.
- Phase 30's 2024-01-02 to 2026-10-23 temporal OOS contains 706 daily observations but only eight observed trade/rebalance dates.
- All six candidate/baseline ledgers passed date alignment, return/equity chain, cash/equity balance, non-negative cash, gross <=100%, and max-20-position checks.
- Mean daily excess MOM120 minus LTM was approximately 0.70–0.73 bps across 10/20/50 bps per-side cost scenarios.
- Block-bootstrap 95% intervals include zero at 20-, 80- and 160-session blocks for every cost scenario. C20 sign-test p=0.214; naive paired daily t-test p=0.750. LOO means are positive but do not establish statistical significance.
- The C20 relative final-multiple difference was +4.34%, with only small descriptive Sharpe and drawdown differences.
- Strict PIT is not established: the experiment uses a static 335-name universe and Yahoo Finance history without an effective-dated security master or delisted-security return coverage.

## Decision
- Reject the tested MOM120 standalone replacement for promotion: no statistically reliable incremental portfolio edge over LTM was demonstrated.
- Do not kill the general momentum hypothesis; LTM already contains overlapping long-term momentum information.
- Do not repeat the same MOM120 replacement test with altered parameters. A new test requires a genuinely complementary hypothesis and a pre-registered protocol.
- No Smart Money signal was promoted by this phase.

## Other source gates unchanged
- Phase 20A/B/C short-flow implementations remain rejected for promotion under Phase 487.
- FINRA Reg SHO Phase 495 still requires a post-fix live capture.
- SEC Form 4 remains metadata-only pending historical identity, first-seen timing and effective-dated universe membership.
- CFTC TFF remains a prospective positioning source pending more history and PIT checks.
- Options candidates remain conditional on historical PIT/vintage, coverage, licensing and independent validation.
- SEC 13D/G parent retrieval remains blocked on the repository Actions secret SEC_USER_AGENT.

## Frozen controls
F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen. No universe, parameter, holding-period, capital, exposure, cost, holdout or production changes. No new signal admitted.
