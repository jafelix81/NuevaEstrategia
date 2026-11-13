# Phase 378 — CFTC TFF Russell contract-era and classification-regime audit

**Status:** implementation and deterministic tests added; hosted subset retrieval pending.  
**Parent:** Phase 377 full TFF coverage/contract-key audit.  
**Scope:** source feasibility and series identity only; no feature or return test.

## Why this phase is necessary

Phase 377 found that CFTC code 239742 (Russell) contains 601 observations across a 20-year date range, but only 56.43% coverage under a weekly anchor count and a maximum gap of 3,255 days. The prior report treated 239742 as one candidate contract series from 2006 through 2026. That is not safe.

Official CFTC historical reports show that code 239742 referred to different Russell contract specifications in different eras:

- 2006-10-24: Russell 2000 Stock Index (Mini), $100 multiplier, CFTC code 239742.
- 2017-10-03: E-mini Russell 2000 Index, $50 multiplier, CFTC code 239742.

This is a contract-specification break, not a continuous, interchangeable position series. Official archive examples:
- https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2006/futures/deacmelf102406.htm
- https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2017/futures/financial_lf100317.htm

The same 2017 CFTC TFF report lists ICE Russell 2000 Mini code 23977A separately from CME E-mini Russell code 239742. Code 23977A is a separate exchange/contract series, not an extension to merge with CME 239742. CFTC archive:
- https://www.cftc.gov/sites/default/files/files/dea/cotarchives/2017/options/financial_lof101017.htm

Code 239741 is also a separate Russell 2000 Stock Index Future contract (historical multiplier $500) and must not be merged with either mini contract.

## Second issue: TFF category history is backcast before launch

CFTC announced the TFF report on 2010-07-22. Its own explanatory notes state that historical TFF data back to 2006-06-13 were classified using recent trader classifications because CFTC did not maintain historical classification vintages; the agency warns that the backcast becomes less accurate further back in time.

Therefore:
- Pre-launch TFF rows are historical backcast classifications, not contemporaneously published TFF categories.
- Exclude pre-2010-07-22 observations from the primary TFF feature research.
- They may be retained only as a clearly labelled sensitivity/history diagnostic.
- Even post-launch report dates are not exact knowledge dates. CFTC's historical report index says its dates are report dates, not release dates. Actual historical release dates beyond the verified recent window remain unavailable, so strict historical PIT is not established.

Official references:
- TFF launch announcement: https://www.cftc.gov/PressRoom/PressReleases/5857-10
- TFF explanatory notes, Historical Data section: https://www.cftc.gov/sites/default/files/idc/groups/public/%40commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf
- Historical Viewable report-date disclaimer: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm

## Method

The hosted audit queries only CFTC TFF Futures Only rows for codes 239742, 239741 and 23977A, retrieving the selected date/code/name/exchange/open-interest fields. It reconciles the filtered row count and metadata update stamp before/after retrieval, tests (report date, code) uniqueness, and segments each code into separate episodes whenever the gap between observed report dates exceeds 365 days.

Within an episode, 6–8 day intervals are treated as ordinary weekly intervals to allow holiday-shifted report dates. Larger gaps are counted as absent observations; missing contract-weeks are never converted to zero or forward-filled. The output retains only anonymized aggregate counts and date ranges, not raw rows, IDs or positions.

## Competing interpretations

1. The 239742 Russell observations before and after the multi-year gap are separate contract eras with different multipliers; the later E-mini series is the only candidate for a current Russell TFF positioning feature.
2. The ICE 23977A and CME 239742 series reflect separate venues and participant populations; any combined feature would need a predeclared economic rationale and cannot be created by concatenating codes.
3. Russell report gaps may also reflect the CFTC's reportable-trader threshold. Missing weeks are not zero and can create selection bias.
4. Even a clean post-2017 series may be a return-chasing/crowding proxy rather than an informed signal.

## Decision rules

- Do not use 239742 as one uninterrupted 2006–2026 series.
- Do not merge 239741, 239742 and 23977A.
- Do not use pre-2010-07-22 TFF category observations in primary tests.
- Do not claim strict historical PIT from report dates or generic Friday schedule proxies.
- No alpha test is authorized in this phase. A future study must first freeze the post-launch contract era, define a verified/explicitly proxy availability rule, compare against prior index returns, volatility, QQQ Risk ON/OFF and frozen LTM/F80, and use chronological validation with identical exposure/costs.
- The consumed legacy holdout remains unavailable.

## Controls

No raw data retention, forward returns, feature selection, alpha, OOS, bootstrap, LOO or holdout use. No changes to F80_TOP20_PARTIAL50_BASELINE_C20, production, universe, capital, parameters or exposure.
