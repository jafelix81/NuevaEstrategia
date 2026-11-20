# Smart Money Research State Addendum — Phase 534 (2026-11-20)

- SEC MIDAS *Metrics by Individual Security* official catalog lists 59 quarterly ZIPs from 2012 Q1 through 2026 Q3, >4,800 securities, and 18 fields. Listed rounded file sizes sum to approximately 982.96 MB compressed.
- Critical semantic correction: `HiddenVol` is on-exchange execution volume against hidden/undisplayed resting orders, **not dark-pool/off-exchange volume**. The public per-security metrics generally exclude off-exchange executions, opening/closing auctions and off-hours. `TradeVolForHidden` is the eligible hidden-order denominator.
- Preserve methodology breaks at Jan 2014 (odd-lot SIP coverage), May 1 2017 (NYSE Integrated Feed and NYSE/Amex metric inclusion changes), and Nov 3 2025 (new round-lot tiers).
- Historical release PIT is not verified: daily observation dates inside quarterly ZIPs are not daily availability dates. Current page metadata is not a per-quarter first-publication timestamp.
- F80 335-name coverage, effective-dated identity, delisted/ticker-change coverage and CRSP universe refresh effects remain unverified. No sample ZIP was successfully downloaded.
- Retain only as a conditional public market-microstructure / liquidity-risk hypothesis (hidden-liquidity state, order-interaction/liquidity state, odd-lot regime). Do not call it institutional flow, dark-pool activity or signed smart money.
- No forward-return, alpha, backtest, OOS, bootstrap/LOO or holdout test. No signal admitted. F80 and production remain frozen.
- Report: [Phase 534](research/PHASE534_SEC_MIDAS_SECURITY_METRICS_SEMANTICS_AND_PIT_AUDIT_2026-11-20.md) · [summary](research/PHASE534_SEC_MIDAS_SECURITY_METRICS_SUMMARY_2026-11-20.json).
