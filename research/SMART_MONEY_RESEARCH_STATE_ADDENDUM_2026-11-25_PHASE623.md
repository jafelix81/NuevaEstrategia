# Smart Money Research — state addendum, Phase 623

**Cutoff:** 2026-11-25 19:32 UTC  
**Implementation branch:** `phase620-sec-form4-entity-aware-feed-dedup`  
**Parent PR:** [#237](https://github.com/jafelix81/NuevaEstrategia/pull/237)

## New integrity control

Phase 623 adds a transaction-linked Form 4 footnote sidecar. The legacy transaction ledger schema and transaction fingerprint remain unchanged. The sidecar preserves accession, transaction detail key, XML field/reference path, footnote ID, text, text hash, source hashes, and conservative availability metadata. It is append-only and schedule-only.

The bounded backfill targets previously parsed transaction accessions lacking a sidecar completion marker. New transaction-detail parses write their footnote sidecar from the same XML fetch. No extra fetch is required for newly parsed documents.

## Validation status

- Final offline regression: **75/75 passed** in [Run 45687169039](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45687169039).
- The initial run [45687060727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45687060727) failed one test-fixture field-name assertion; corrected in commit `907bef37`.
- Live capture was skipped as designed on PR validation; no SEC feed or filing was fetched.
- Historical sidecar backfill was not executed in this PR validation.
- Existing transaction rows were not rewritten.
- Signal eligibility remains zero.

## Cross-source feasibility checkpoint

| Source | Current evidence / blocker | Disposition |
|---|---|---|
| SEC Form 4 / 144 | Structured event data; cadence gaps and transaction/owner/footnote provenance still being hardened | Continue, daily conservative clock only |
| SEC 13D/G | 44-document bounded sample architecture; real sample still pending PR #233 integration/authorized run | Continue after identity and receipt audit |
| SEC 13F | Prospective feed capture and full-snapshot safety exist in draft PRs #231/#232; no live holdings capture or manager/security crosswalk yet | Continue metadata only; no feature |
| Cboe OPRA Trades/Quotes | Best conditional all-venue options candidate; 2012-vs-2010 advertised history conflict, T+1 receipt/corrections, 335-name coverage, pricing and rights unresolved | Highest options research priority, no purchase |
| Massive Options | Trades 2014-06; quotes 2022-03; OI/Greeks/IV 2022-09; individual plan USD 199/month but current terms are not cleared for professional/organization use or public-repo derived data | Do not use absent separate license |
| ThetaData | Individual tiers advertise 6/10/14 years; first-receipt, inactive-symbol coverage and license treatment of this workflow unresolved | Lower priority pending written rights/coverage |
| FINRA Reg SHO | 7/7 daily files rejected by overlap/duplicate controls | Quarantined |
| FINRA consolidated short interest | Historical panel incomplete; credentials and one-settlement live validation remain human prerequisites | Do not infer zeros or backfill |
| CFTC TFF | 3,043 historical rows; only two prospective vintages; preregistered minimum history not met | Accumulate vintages; no test |
| SEC N-PORT share-balance growth | Prior 5/6 ICs negative | Killed as independent signal |

No source is called smart money by label. Any candidate must first pass historical coverage, ex-ante availability, identifier and licensing gates before a return test.

## Source and strategy disposition

The UPST purchase cluster remains one issuer-level descriptive observation. Transaction-specific footnotes improve classification but do not establish open-market venue, discretion, historical F80 membership or exact public availability. No event return or alpha test is authorized.

FINRA Reg SHO remains quarantined; CFTC TFF remains awaiting additional vintages; options remain subject to the existing zero-budget constraint. Continue independent data-feasibility audits for SEC 13F/13D/G, options and consolidated short interest rather than treating any one source as the definition of smart money.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No capital, exposure, universe, cost, parameter, holdout or production changes. No paid data, quote request or vendor contact; options-data budget remains USD 0.


## Operational capture checkpoint — 2026-11-25 19:40 UTC

The schedule-filtered Actions inventory contains 67 schedule events. The newest natural SEC captures remain Form 4 [45620008946](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45620008946) at 13:05:10 UTC and Form 144 [45595957832](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45595957832) at 10:32:27 UTC. No later scheduled event is visible in the current inventory.

- Form 4's declared cron is `17 * * * 1-5`; nominal slots 14:17 through 19:17 UTC are absent.
- Form 144's declared cron is `47 * * * *`; nominal slots 10:47 through 18:47 UTC are absent (19:47 had not yet occurred at this checkpoint).
- This is an observed scheduler-delivery gap, not proof the workflows are administratively disabled.
- GitHub's available read interface cannot inspect workflow enabled-state or repository scheduled-Actions policy. Human check remains in Issue #194.
- No manual dispatch, rerun, duplicate capture, cancellation or cron change was performed.

No intraday Form 4 feature is authorized. The collector's first-seen interval remains an upper-bound metadata clock, not exact public availability.
