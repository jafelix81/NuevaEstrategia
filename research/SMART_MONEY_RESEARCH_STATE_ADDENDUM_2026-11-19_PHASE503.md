# Smart Money Research state addendum — Phase 503 (2026-11-19)

- Phase 503 supplements PR #157 / Phases 501–502; no new workflow was started.
- Fresh review of Cboe's official Option Sentiment specification v1.4 (0525) found an 80-field daily underlying-level aggregate built from trade-level information. Fields include midpoint-based directional call/put premiums and volume, net option delta, IV30/IV90, 25-delta 30-day skew, implied borrow, OI/OTM OI, DTE/size buckets and OCC customer/firm/market-maker volume aggregates.
- Cboe FAQ lists Option Sentiment history from January 2012. However, the dedicated product URL could not be verified and redirects to the DataShop home page; active orderability and current product terms remain unconfirmed.
- Spec says preliminary subscription files target 8–9 PM ET same trade date and complete files 5–6 AM ET next day. Historical order files are delivered at end of day on fulfillment; no historical first-delivery/vintage ledger was found. Strict historical PIT remains uncertified.
- Direction is midpoint-based (above midpoint buy, below midpoint sell); spreads, late and tied trades are excluded from net delta. This is a proxy, not beneficial-owner intent. Cancelled trades are stated to be backed out.
- OCC customer/firm/market-maker volumes are unsigned participant-composition aggregates, not participant-by-side flow. Do not label customer as retail or firm as informed.
- OI timing and net-delta units require product-specific confirmation. General Cboe FAQ says options OI is prior-night OCC EOD OI at SOD and static intraday. Vendor 20-day average cutoff is unspecified; recompute prior-only baselines.
- TBT is a C1-only trade-by-trade cross-check (side/open-close/capacity; history from 2019-10-07; T+1). Open-Close provides participant type, buy/sell and open/close for Cboe venues only, with historical convention breaks. Neither is a full OPRA-wide substitute.
- No sample, purchase, vendor contact, parser, feature, alpha/event study/OOS/bootstrap/LOO or signal admission. F80 unchanged.
- Next gate: confirm Option Sentiment orderability, current spec, price/firm-use/retention rights, 335-name/delisted coverage, units and preliminary/complete correction lineage; then lawful sample and prospective actual-receipt ledger.

- Integration: PR #157 merged by squash at `190211d58fcd6519abef7acf9c475fef267e6ad0` on 2026-11-19 16:56:23 UTC. Main HEAD after merge: same SHA. PR was documentation-only; no CI workflow was triggered and no production/code changes were included.
