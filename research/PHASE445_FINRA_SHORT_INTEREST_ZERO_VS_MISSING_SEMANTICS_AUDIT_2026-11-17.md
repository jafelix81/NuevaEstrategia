# Phase 445 — FINRA short-interest zero-vs-missing semantics re-audit

Date: 2026-11-17

## Decision

**REOPEN FOR DATA-SEMANTICS / COVERAGE RECONSTRUCTION ONLY. NO ALPHA RE-ADMISSION.**

Phase 37 classified the 98 unique symbols in the Phase 31 consolidated short-interest artifact as roughly 29% coverage of the frozen 335-name universe and killed the joint flow + position candidate on that basis. That inference is not established. FINRA's own reporting instructions say firms are not required to submit a zero position when a previously reported issue has no short position in the current cycle. The public consolidated dataset is an aggregate of reported short positions, not necessarily a dense panel containing one row for every eligible listed security.

Consequently, the Phase 31 counts (9,420 rows; 98 unique tickers; 84–96 positive-row symbols per settlement in the audited requests) measure **positive reported-position incidence in the retrieved data**, not automatically data coverage. A missing row can be a structural zero, but only after the full settlement snapshot, symbol eligibility, and source scope are verified. It must not be blindly zero-filled.

This supersedes Phase 37's *coverage interpretation* only. It does not supersede Phase 31's unstable horizon directions or bootstrap intervals that included zero, and it does not admit any signal or return test.

## New primary-source evidence

1. FINRA's Regulatory Notice 16-32 states that firms are not required to report a zero position for issue symbols that had a prior-cycle short position but no short position in the current cycle. This establishes that zero positions can legitimately disappear from the row set. [FINRA Regulatory Notice 16-32](https://www.finra.org/sites/default/files/notice_doc_file_ref/Regulatory-Notice-16-32.pdf).
2. FINRA's API documentation describes Consolidated Short Interest as an aggregate view across exchange-listed and OTC equity securities, with public credentials available, and says the dataset is available by 4:40 p.m. ET on the publication date. [FINRA Developer Center](https://developer.finra.org/docs).
3. FINRA's January 2023 release notes say the consolidated dataset provides five years of history and, from June 2022, includes short-interest data from all exchanges. [January 2023 release notes](https://developer.finra.org/release-notes/january-2023-release-notes).
4. The current FINRA calendar remains twice monthly. For the November 13, 2026 settlement, reports are due November 17 at 6:00 p.m. ET and publication is November 24. [FINRA 2026 reporting calendar](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest).
5. FINRA's FAQ confirms that the reported measure is scoped to positions on FINRA member firms' books and to positions meeting Rule 4560's reportability conditions. It excludes, among other things, certain stock-loan positions, fails-to-receive, and RVP positions. Short positions in the same account are not netted against longs. [FINRA Short Interest FAQ](https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest/faq).
6. FINRA's May 2026 proposal SR-FINRA-2026-012, which would have expanded reporting and changed the cadence, is marked **withdrawn on August 5, 2026** on the SEC rulemaking page. Do not model the proposed weekly regime as if it were effective. [SEC FINRA rulemaking status](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/finra).

## Reclassification of the Phase 31 / Phase 37 evidence

| Quantity previously treated as coverage | Observed value | Correct interpretation |
|---|---:|---|
| Phase 31 consolidated SI rows | 9,420 | Retrieved report rows, not universe coverage |
| Unique symbols with positive rows | 98 | Positive-position incidence in the artifact |
| Per-settlement symbols with rows | 84–96 | Positive-position incidence, conditional on successful request |
| Frozen universe | 335 | Denominator for the future effective-dated panel audit |

The earlier 98/335 ratio is **not a valid missing-data rate** unless FINRA's dataset contract guarantees a row for every in-scope security, including zero positions. The official 2016 instruction demonstrates the opposite for zero positions. Failed or partial settlement-date requests in the old audit remain genuine missing snapshots and cannot be converted to zeros.

## Safe row-state rules for the next audit

A row may be treated as a **structural zero** only when all of the following hold:

- The complete consolidated settlement-date snapshot was retrieved and independently reconciled (record totals / pagination complete, no API or transport errors).
- The security is proven active and in scope on that settlement date using an effective-dated security identity map, not a current ticker-only join.
- The security's market / listing classification is within the dataset's documented scope for that date.
- No row for the effective security key exists in that complete snapshot.

Otherwise classify the observation as **unknown / missing**, not zero.

Required row-state fields:

- `snapshot_complete`
- `security_valid_at_settlement`
- `effective_security_id` (or explicit unresolved state)
- `row_present`
- `reported_short_quantity`
- `zero_inferred_from_complete_snapshot`
- `revision_flag`
- `stock_split_flag`
- `settlement_date`
- `official_publication_date`
- `official_available_at_et` (conservative 16:40 ET upper-bound clock)
- `first_seen_utc` (when captured prospectively)
- `knowledge_timestamp`

Do not collapse these states into one null/zero field. For historical backtests, use the official publication date and the conservative 16:40 ET availability bound; because that is after the 4:00 p.m. regular-session close, the earliest regular-session execution is the next trading session. For prospective capture, preserve the actual first-seen timestamp as an additional constraint; never backdate it.

## Data-quality and scope controls

- Preserve `revisionFlag = R` and do not overwrite earlier vintages. FINRA FAQ requires corrections when firms discover inaccurate or incomplete submissions; historical revisions can therefore alter prior reported positions.
- Preserve `stockSplitFlag = S`; validate share-count comparability across the cycle before computing percentage changes.
- Do not use FINRA's `changePercent` blindly when the previous short position is zero or absent; FINRA's schema defines 100 when there is no previous position or it is zero. Prefer raw current/previous quantities and explicit denominator states.
- `averageDailyVolumeQuantity` excludes non-media trades. Treat FINRA `daysToCoverQuantity` as a provider-defined derived field, not an independent borrow-market measure.
- The measure is not total economic short exposure, securities-lending utilization, or a direct institutional identity signal. FINRA FAQ excludes several non-reportable position types. It is a reported aggregate of Rule 4560 positions at member firms.
- The withdrawn 2026 proposal included a final short-interest report for deleted symbols and additional arranged-financing positions. Since it was withdrawn, do not assume either proposed enhancement exists in the current public series. Delisting / deleted-symbol terminal positions remain a separate survivorship and completeness risk.

## Re-entry sequence

1. Rebuild the Phase 31 settlement panel from complete raw snapshots; distinguish positive rows, inferred structural zeros, and unknowns.
2. Validate all 335 names against an effective-dated identity/security master for each settlement date. Ticker continuity alone is insufficient.
3. Recompute the joint flow + position panel's **effective coverage** after structural-zero handling. Report both active-universe coverage and positive-position incidence; never conflate them.
4. Reconcile row counts, revisions, split flags, exchange/OTC scope, and failed settlements. A failed snapshot invalidates the whole settlement panel for zero inference.
5. Only if the panel passes pre-specified identity and completeness gates, design a new chronological diagnostic against the frozen LTM/F80 baseline. Do not reuse Phase 31's selected transformations or choose features on the full sample.
6. Any later return test must control for prior/contemporaneous returns, liquidity, volatility and short-interest level; distinguish predictive information from return-chasing; use identical exposure/costs, bootstrap and leave-one-date-out checks, and a truly untouched OOS period.

## Current conclusion

- **Coverage kill from Phase 37 is downgraded to unresolved pending semantic-aware reconstruction.**
- **Phase 31 return evidence remains non-promotable**: horizon directions were unstable and bootstrap intervals included zero.
- No new data was downloaded in this phase; no alpha, OOS test, feature, or trading rule was admitted.
- No production workflow, F80 parameter, universe, holdout, capital, exposure, or trading code was changed.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.

## Operational preflight — 2026-11-17 01:10 UTC

- Main HEAD at preflight: `a5f4da0609d49b30a5335296f29e298a8ef3e2d6` (Phase 444 CI validation record).
- Branch enumeration completed over three pages: 279 branches. Open PR enumeration: 56.
- Latest known Phase 444 CI run `43990197952`: offline validation passed 18/18. Its log contains synthetic test fixtures (including a dummy accession); these are tests, not live SEC observations.
- SEC live capture `43970444015`: offline regression passed; live Form 144/A request timed out after retries; no output artifact. Phase 444 fixed partial-feed persistence, but no post-merge live capture was confirmed in this preflight.
- CFTC run `43525140200`: successful bootstrap/push only; 3,035 warm-up records, no prospective eligible observations; artifact `14084802705` (SHA-256 `c7a652038336f852e3c51792d1bdc96ebc1368176bdafdae0693332fb4224eef`). The next scheduled capture was not due at preflight.
- The GitHub connector available in this session exposes run/job/artifact fetches but not a current workflow-run listing endpoint. No manual workflow was dispatched or duplicated; live-run absence is not asserted beyond the runs directly inspected.
- Phase 444 report and summary are already present in the repository; this phase appends the corrected short-interest semantics and does not alter the Phase 444 implementation.
