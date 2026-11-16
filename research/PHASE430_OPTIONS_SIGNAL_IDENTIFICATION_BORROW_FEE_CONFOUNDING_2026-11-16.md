# Phase 430 — Options signal identification and stock-borrow-fee confounding audit

**Audit date:** 2026-11-16 UTC  
**Disposition:** demote unconditioned IV spread/skew from a Smart Money hypothesis; retain Cboe Open-Close opening-position flow as a conditional prospective candidate; no source or signal admitted.  
**Relationship to prior work:** interpretive and preregistration update to Phases 352, 407 and 429. No data acquisition or return test.

## Executive finding

Options data expose several different objects that are often incorrectly collapsed into “smart money”:

1. **Option-side position:** which account capacity bought or sold the option.
2. **Aggressor side:** which side initiated the trade against the prevailing quote.
3. **Position lifecycle:** whether the trade opened or closed exposure.
4. **Exchange capacity:** customer, professional customer, firm, broker-dealer or market maker.
5. **Beneficial owner / information status:** who ultimately controls the account and whether the trader is informed.

No single public dataset in our current candidate set identifies all five. A trade-size threshold, a call purchase, a put purchase, a customer code, a high volume/OI ratio or a quote-rule sign is not proof of informed institutional positioning.

The most consequential literature update is that implied-volatility spread/skew predictability is substantially explained by stock-borrow fees. Separately, the classic options-volume result depends on buyer-initiated **opening** trades, not generic option volume. This changes the order in which we should evaluate options features.

## 1. Literature reconciliation

### 1.1 Opening buyer-initiated option volume is a specific construct

Pan and Poteshman (2006), *The Information in Option Volume for Future Stock Prices*, construct put/call ratios from option volume initiated by buyers to open new positions. They report that low-ratio stocks outperform high-ratio stocks by more than 40 bps the next day and more than 1% over the next week in their historical sample.

That result does **not** establish that any public put/call ratio, raw option volume, or trade/quote sign reproduces the signal. The defining measurement is the conjunction of buyer initiation and opening status. Their unique CBOE data are richer than consolidated OPRA prints.

Our current candidates provide different subsets:
- ThetaData OPRA trade_quote pairs trades with NBBO and supports a strict prior-quote constraint, but does not identify participant capacity or opening/closing status.
- Cboe Open-Close identifies participant capacity and opening/closing buy/sell position buckets, but those buy/sell fields are account-side classifications, not necessarily aggressor initiation.
- Cboe TBT may contain actual buyer/seller side and lifecycle fields, but Phase 351's public sample is a non-random 3% C1 one-day sample with unresolved row/side/session issues; it is not a population calibration panel.

Therefore, do not describe a Cboe Open-Close net-opening feature as a replication of Pan–Poteshman. It is a related but distinct position-acquisition hypothesis.

### 1.2 IV spread and skew are materially confounded by stock-borrow fees

Muravyev, Pearson and Pollet (2025), *Why does options market information predict stock returns?*, Journal of Financial Economics 172, article 104153, show that implied-volatility spread and skew predictability is consistent with those measures reflecting stock-borrow fees. Their analysis reports that predictability falls by at least two-thirds when high-borrow-fee stocks are excluded. After borrow-fee adjustments, the reported spread/skew portfolio abnormal returns are economically small and statistically insignificant.

The paper's matched sample uses OptionMetrics implied-volatility data and Markit indicative borrow fees over July 2006–December 2020. It contains 4,933 unique stocks after filters. This is a relevant warning for our design: an IV spread/skew association with subsequent returns need not be informed option demand; it can be a stock-lending scarcity/friction proxy, with short-sale costs eroding the apparent trade.

**Decision:** do not admit raw IV spread, IV skew or close variants as Smart Money directional signals. Keep them as candidate risk/friction controls. Any future predictive test must either obtain point-in-time borrow-fee/utilization data or explicitly demonstrate robustness in a pre-defined low-fee sample. FINRA short interest and short volume are not substitutes for borrow fees: they measure different objects and do not identify the marginal cost or availability of stock borrow.

### 1.3 Participant labels and lifecycle remain essential

Phase 407 already records Amaya et al. (2025) evidence that 42.4% of Cboe SLIM trades / 42.6% of volume in their Cboe subset were closing, and that quote-rule trade-direction estimates were materially misclassified in that subset. The paper also notes that the public-customer category includes hedge funds, mutual funds and other institutional public customers.

This reinforces three controls:
- Customer is not synonymous with retail.
- Pro-customer is not a verified beneficial-owner identity.
- Opening/closing, buyer/seller position side and aggressor side must remain separate fields.

## 2. Source-by-source interpretation

| Source | What it can identify | What it cannot establish | Current disposition |
|---|---|---|---|
| Cboe Open-Close 1m v1.8 | Cboe-venue capacity, option series, buy/sell position side, open/close and size buckets | Beneficial owner, aggressor initiation, all-OPRA coverage, historical first receipt | High-priority conditional prospective candidate |
| ThetaData OPRA trade_quote | Trade print, size/price, prevailing NBBO and a prior-quote-based aggressor estimate | Capacity, open/close, beneficial owner, historical vendor first receipt/correction vintage | Conditional broad-market microstructure companion |
| Cboe TBT | Richer venue-level trade/capacity/side/lifecycle fields | Population calibration from the current 3% C1 sample; complete PIT/correction history | Conditional; existing sample gates remain open |
| Option IV spread/skew | Option-implied relative pricing and possible stock-lending friction | Informed direction without borrow-fee controls | Demoted to friction/control candidate |
| Open interest | Outstanding positions as of its reporting reference date | Which side opened, who owns the position, or same-session flow | Context only; respect prior-session reporting clock |

### Cboe Open-Close specifics

The official v1.8 specification effective 2026-11-08 provides participant-capacity buckets for Firm, Broker-Dealer, Market Maker, Customer and Professional Customer, with opening/closing buy/sell volume for non-market-maker capacities and separate size buckets for Customer/Professional Customer.

The dataset covers four Cboe exchanges, not the entire OPRA market. The 1-minute files are cumulative day-to-date snapshots, can reflect late-processed trades, and later snapshots remove trades subsequently broken/cancelled. They must be captured append-only with actual first-receipt UTC and raw hashes. A later corrected snapshot must never rewrite a feature that was available earlier. See Phase 352 for the detailed snapshot, venue, session and field audit.

The Cboe “buy” and “sell” fields should be treated as the classified participant's option-position side, not as an aggressor flag. The 1-minute schema does not provide OI, total industry volume, IV or Greeks in fields 10–17. Companion data must have its own clock and coverage audit.

### ThetaData specifics

The Phase 429 audit found that trade_quote with exclusive=true can enforce quote_timestamp < trade_timestamp. This helps avoid using a same-time/future quote to sign a print, but it does not recover opening/closing or account capacity, and it does not establish historical first-vendor receipt or complete correction/bust vintages. Do not infer “institutional” from print size.

## 3. Preregistered feature family — conditional only

If licensing, coverage and prospective PIT gates pass, the first Cboe Open-Close family should remain small and interpretable:

1. **Opening position-side flow:** opening buy volume minus opening sell volume, separately for Customer, Professional Customer, Firm and Broker-Dealer; Market Maker buy/sell activity remains a separate dealer-flow measure.
2. **Calls and puts:** calculate separately by call/put and broad, predeclared maturity/moneyness buckets only when the required contract and companion-price data are available as of the feature timestamp.
3. **Closing flow:** preserve as a distinct unwind/close hypothesis; never net it into opening flow before testing.
4. **Size buckets:** retain separately as descriptive trade-size strata; do not label the >=200-contract bucket “institutional.”
5. **Aggressor estimate:** ThetaData quote-signed flow is a separate feature family, not a substitute for opening position-side flow. Midpoint/ambiguous/stale/locked/crossed prints remain unclassified.
6. **IV spread/skew:** control variables only until a valid point-in-time borrow-fee treatment is available.

Potential normalization is by the same underlying's trailing Cboe-venue classified opening volume or a trailing within-symbol z-score. Do not divide Cboe-only flow by an all-market denominator unless a valid full-OPRA denominator is separately available. Keep missing/zero-volume states distinct.

No thresholds, signs, holding periods or model weights are selected here. No feature is admitted.

## 4. Required feasibility and PIT gates before any return test

1. Obtain a lawful, representative sample with explicit license/use rights; no vendor contact, trial or purchase was made.
2. Verify post-v1.8 headers and cumulative/correction behavior against actual bytes, not documentation alone.
3. Measure per-symbol/per-date coverage against the full frozen 335-name universe, including inactive/delisted underlyings, ticker changes and option-root adjustments. Do not shrink the denominator.
4. Reconcile Cboe venue coverage with a separately validated full-OPRA volume denominator; never treat Cboe venue activity as total-market flow.
5. Capture every first-received snapshot append-only with receipt UTC, exchange, market date, interval, trading_dt, trading_segment, schema version, raw hash and correction lineage.
6. Establish the exact daily decision cutoff. Use only the last snapshot actually received by that cutoff; if missing or late, defer the feature rather than backfill it.
7. Validate companion underlying prices, IV/Greeks and borrow-fee data independently, each with its own point-in-time availability.
8. Only after all gates pass, preregister one fixed feature family and compare it incrementally against frozen LTM/F80 using identical universe, exposure, rebalance/execution, costs and liquidity constraints; use chronological discovery/validation/fresh OOS, block bootstrap, LOO, ticker/sector clustering and multiplicity control. The consumed legacy holdout remains unavailable.

## 5. Decision

- **IV spread/skew as Smart Money alpha:** DEMOTED; no unconditioned directional test. Borrow-fee confounding is a first-order alternative explanation.
- **Generic put/call ratio or raw option volume:** NOT ADMITTED; the classic evidence depends on buyer initiation plus opening status.
- **Cboe Open-Close opening flow by capacity:** retain as the leading conditional prospective candidate, but it is not a Pan–Poteshman replication and is not proof of institutional identity.
- **ThetaData raw OPRA flow:** retain as a separate broad-market aggressor-estimation companion; it cannot supply opening status or capacity.
- **Alpha/OOS/holdout:** not authorized or run.
- **F80_TOP20_PARTIAL50_BASELINE_C20:** frozen; no universe, parameter, capital, exposure or production changes.

## References

- Pan, J. & Poteshman, A. (2006), “The Information in Option Volume for Future Stock Prices,” *Review of Financial Studies* 19(3), 871–908. https://doi.org/10.1093/rfs/hhj024 ; NBER working paper: https://www.nber.org/papers/w10925
- Muravyev, D., Pearson, N. & Pollet, J. (2025), “Why does options market information predict stock returns?”, *Journal of Financial Economics* 172, 104153. https://doi.org/10.1016/j.jfineco.2025.104153 ; replication package: https://data.mendeley.com/datasets/n73cyx89gs
- Cboe Open-Close product page: https://datashop.cboe.com/cboe-options-open-close-volume-summary
- Cboe Open-Close 1-minute v1.8 specification: https://datashop.cboe.com/documents/Open_Close_1m_Spec_v1.8.pdf
- ThetaData trade_quote documentation: https://www.thetadata.net/docs/operations/option_history_trade_quote.html
- Internal prior audits: Phase 352, Phase 407 and Phase 429.

## Operational preflight — 2026-11-16 05:35 UTC

- Main HEAD before this branch: ba0e40dea5f7eff9a6f7f5c93ece38c82b6e3488 (Phase 429 merged).
- Latest 100 Actions runs: 7,666 total reported; returned-page outcomes 62 success, 37 failure, 1 cancelled. Explicit in-progress, queued, waiting and requested queries returned zero. Inspected 264 branches (100 + 100 + 64), all 56 open PRs and all 64 workflow files. No workflow was dispatched, rerun or duplicated.
- SEC Form 144 run [43795660996](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43795660996): both jobs succeeded; offline regression 15/15; 55 feed observations appended; zero new accessions/events/candidate matches; zero eligible observations; artifact [14194203412](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43795660996/artifacts/14194203412), SHA-256 40211212baf071dcc5eb232c923bebbcc4d65708b95eaa26264002363a782cb9. Last receipt 2026-11-16 03:02:04 UTC. The prior receipt was 23:08:38 UTC, a 3h53m26s gap; hourly delivery remains irregular.
- SEC poll counters reconciled: workflow run_number=12 is the Actions workflow's run sequence; persisted state poll_count=7 is a separate capture counter. State history contains seven capture commits; the append-only feed-observation ledger contains 275 rows across five scheduled run IDs because it was initialized after the two bootstrap captures. Do not treat run_number 12 as poll_count 12.
- CFTC TFF remains bootstrap-only (3,035 historical warm-up rows, zero signal-eligible observations). Next expected weekday capture is 2026-11-16 22:15 UTC after the 20:30 UTC release; no early/manual capture.
- SEC 13D/G remains gated on repository owner setting Actions secret SEC_USER_AGENT with a project identifier and monitored contact email. FINRA Phase 20C remains at 328/329 valid price histories. No new source admitted.
- No alpha/return/OOS/bootstrap/LOO/holdout test, vendor data acquisition, workflow change or production change. F80 remains frozen.
