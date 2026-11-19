# Phase 505 — FINRA Consolidated Short Interest historical coverage and PIT feasibility

**Audit date:** 2026-11-19 UTC  
**Branch:** `phase505-finra-consolidated-short-interest-pit-audit`  
**Base main:** `cbbaaf886b7aac27b0eb0276e5cf24087a4c73f0`  
**Disposition:** **CONDITIONAL SOURCE ONLY PENDING COMPLETE ASYNC RE-INGESTION; THE EXISTING PHASE 31 PANEL REMAINS UNUSABLE AS RETRIEVED. NOT STRICT-PIT CERTIFIED, NOT ALPHA-ADMITTED.** FINRA's consolidated short-interest dataset is a useful complement to daily Reg SHO short-sale volume, but it is a twice-monthly snapshot with a material publication lag. All-exchange coverage is documented from June 2022; exact current per-symbol coverage, historical vintages, and business-use rights remain unverified.

## 1. Repository and Actions preflight

- Main HEAD at preflight: `cbbaaf886b7aac27b0eb0276e5cf24087a4c73f0`.
- Actions inventory: 7,894 total runs; latest 100 inspected; no queued, in-progress, waiting, requested, or pending run was present at final preflight.
- Branch inventory: first 100 branches inspected; targeted search confirmed no existing Phase 505 branch.
- Open PRs: 56. PR #158 (Phase 504) merged at 2026-11-19 17:51:55 UTC into main at the current HEAD. No existing Phase 505 PR was found.
- Latest Phase 500 offline run [44534689780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44534689780) passed 46 tests; its live-capture job was skipped and it produced no artifact. The preceding run [44534585085](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44534585085) failed one fixture assertion because the test expected an `errors["144"]` entry that the response classifier did not return; the corrected run passed.
- Latest scheduled Form 144 run [44521745535](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44521745535) was partial: zero new events; the 144 feed returned a parse error; 144/A returned an empty 29-byte response and no prior watermark; a possible feed-window gap remains. Artifact: [14528790385](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44521745535/artifacts/14528790385).
- Latest scheduled Form 4 run [44505739718](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718) succeeded, recording 18 new metadata event rows, but zero research-observation-eligible and zero signal-eligible rows. Artifact: [14519048458](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44505739718/artifacts/14519048458).
- Latest scheduled FINRA Reg SHO run [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) predates the Phase 495 facility-grain parser. It returned HTTP 200 for eight dates, but all eight files were rejected by the old duplicate-symbol rule; zero valid files and zero eligible observations were persisted. Artifact: [14495893727](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570/artifacts/14495893727).
- Phase 495's later PR validation [44456658463](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44456658463) passed offline regression; its live-capture job was skipped and it produced no artifact. The corrected parser accepts the expected `(symbol, reporting facility)` grain and aggregates facility rows by symbol. A post-Phase-495 scheduled capture is still required for live validation.
- Latest inspected CFTC TFF run [44453066854](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854) passed 17 tests, retained 3,039 historical rows, and found no new report or revision. Artifact: [14497030662](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453066854/artifacts/14497030662).

No workflow was dispatched, rerun, cancelled, or duplicated. The existing CFTC and FINRA schedule windows later on 2026-11-19 were not yet due at this audit.

## 2. New source: FINRA Consolidated Short Interest

Official dataset:
- FINRA Developer Center: https://developer.finra.org/docs
- Dataset group/name: `otcMarket / consolidatedShortInterest`
- API metadata: https://api.finra.org/metadata/group/otcmarket/name/consolidatedShortInterest
- API data endpoint: https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest
- FINRA reporting calendar: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest

FINRA describes Consolidated Short Interest as a single aggregate view of short-interest submissions across exchange-listed and OTC equity securities. The Developer Center says the dataset is available through the API by **4:40 PM Eastern Time on the publication date**.

Documented fields include:
- `settlementDate` and `accountingYearMonthNumber`;
- `symbolCode`, `issueName`, `marketClassCode`, and `issuerServicesGroupExchangeCode`;
- `currentShortPositionQuantity` and `previousShortPositionQuantity`;
- `changePreviousNumber` and `changePercent`;
- `averageDailyVolumeQuantity` and `daysToCoverQuantity`;
- `stockSplitFlag` and `revisionFlag`.

This is a security-level aggregate snapshot. It does not identify the beneficial owner, the broker, the short seller's strategy, the entry timestamp, or whether the position is directional rather than hedged. It is a positioning/crowding input, not a participant-identity feed.

### Important field semantics and controls

- `revisionFlag = R` indicates that the prior cycle's short position was revised. A current row may therefore incorporate a revision to the previous-cycle comparator.
- `stockSplitFlag = S` indicates a split in the current short-interest cycle. Do not interpret raw share changes or percent changes across split-affected cycles without a split-aware adjustment.
- The provider's `averageDailyVolumeQuantity` and `daysToCoverQuantity` are provider-defined fields. Preserve null, zero, and sentinel values distinctly; do not silently replace them with zero or treat extreme sentinel values as ordinary days-to-cover observations.
- `changePercent` is based on the previous unadjusted short position. If the previous position is absent or zero, the documented value may be 100; this is not a conventional percentage-growth observation and must be flagged.
- No float or shares-outstanding field is supplied. Short-interest-to-float requires a separate point-in-time shares-outstanding source and must not use today's float retroactively.

## 3. Historical coverage: promising, but not yet a complete panel

FINRA's January 24, 2023 API launch note says Consolidated Short Interest initially provided five years of history and that, as of June 2022, the dataset would include short-interest data from all exchanges.

Implications:
- June 2022 is the conservative beginning of the documented **all-exchange coverage regime**.
- The launch note's five-year backfill statement is not a guarantee that every current symbol, inactive security, historical share class, or every settlement date is present today.
- The public documentation does not provide a 335-name coverage matrix, an inactive/delisted-symbol census, or a complete per-symbol gap map.
- Pre-June-2022 observations must be treated as a separate, potentially incomplete coverage regime until a row-level audit proves otherwise.
- Do not infer complete historical coverage from the dataset's name or from a small documentation sample.

Before any return test, query every frozen-universe security by effective-dated identity, count expected settlement cycles, classify missing rows versus true zero positions, and reconcile ticker changes, share classes, splits, acquisitions, and delistings. Use CUSIP/other stable security identifiers where available; ticker alone is not a permanent identity.

## 4. Current reporting cadence and the 2026 rulemaking correction

The current FINRA reporting page continues to require short-interest reporting **twice per month**. Firms must submit by 6:00 PM ET on the second business day after the designated settlement date.

The API documentation states that consolidated data is available by 4:40 PM ET on the publication date. For the November 2026 cycle, FINRA's current calendar lists:
- Settlement date: **Friday, November 13, 2026**.
- Firm due date: **Tuesday, November 17, 2026, 6:00 PM ET**.
- Public publication date: **Tuesday, November 24, 2026**.

Thus, the November 13 position snapshot is not a public feature on November 13 or November 17. Its nominal publication date is November 24; actual file receipt must be recorded and controls the usable timestamp.

### Withdrawn weekly-reporting proposal

FINRA filed SR-FINRA-2026-012 in May 2026 proposing, among other things:
- weekly rather than twice-monthly short-interest reporting;
- inclusion of certain arranged-financing loan obligations;
- a final short-interest report for a security before its symbol is deleted.

The SEC's current rulemaking record marks the proposal **WITHDRAWN on August 5, 2026**. Do not model weekly short interest, arranged-financing coverage, or the proposed deleted-symbol final report as if they became effective. The current twice-monthly schedule remains the operative public calendar in this audit.

## 5. Short interest is not daily short-sale volume

FINRA explicitly distinguishes the two datasets:
- Short interest is a snapshot of open short positions on two designated settlement dates each month.
- Daily Short Sale Volume is a count of short-sale transactions executed and reported to FINRA facilities on individual trade dates.
- A short sale opened and closed on the same day can appear in daily short-sale volume without remaining in short interest.
- A short position can remain in short interest for days or weeks even though its opening short-sale transaction appeared in daily volume only once.

Therefore:
- Never sum daily Reg SHO short volume into short interest.
- Never label a high daily short-volume ratio as a growing outstanding short position.
- Never call a large short-interest position “smart money” or assume it is bearish alpha; it may be hedging, market making, financing, or directional positioning.
- The two sources can be tested as separate but complementary hypotheses: daily short-sale activity may relate to later changes in outstanding short interest, but that relationship must be measured rather than assumed.

## 6. Point-in-time availability ruling

The settlement date is the **measurement date**, not the date the public could trade on the information.

Conservative clock:
1. Capture the settlement date and the official publication date from FINRA's calendar.
2. Use 4:40 PM ET on the publication date only as FINRA's documented API availability target/bound, not as a substitute for our own receipt timestamp.
3. Record actual first receipt UTC, response status, filename/metadata, byte count, SHA-256, schema version, and any later revision.
4. The first eligible decision time is after the file is actually received and validated.
5. Execute no earlier than the first regular-session open strictly after actual receipt. Never backdate the feature to the settlement date or publication date if the file arrived later.

Historical archive rows do not provide a complete immutable first-publication/vintage ledger in the reviewed material. The `revisionFlag` identifies a revised prior-cycle comparator but does not reconstruct the exact earlier file contents or first receipt. Therefore:
- **Historical PIT is publication-calendar-bounded, not fully vintage-certified.**
- A prospective first-receipt ledger is required before the source can be used in strict PIT tests.
- Preserve original and revised files separately; never overwrite the original first-seen version.
- If an old vintage cannot be reconstructed or hash-verified, exclude that observation from primary PIT results.

## 7. Preregistered research hypotheses if coverage and PIT gates pass

These are hypotheses, not assumptions about informed trading:

1. **Outstanding-position change:** test `changePreviousNumber` and `changePercent` as predictors of next-session-to-multiweek returns and forward risk, after controlling for same-period price performance, momentum, realized volatility, liquidity, and events.
2. **Crowding / days to cover:** test current short position relative to provider ADV and, separately, relative to point-in-time float once a valid float history exists. Do not use a present-day denominator for historical dates.
3. **Daily-flow-to-position conversion:** test whether prior-only aggregates of FINRA daily short volume and short-exempt volume between settlement dates explain the next published change in short interest. This is a linkage hypothesis, not an assumption that daily short volume accumulates into open positions.
4. **Persistence versus acceleration:** distinguish a high but stable short position from a newly accelerating position; test level, change, and persistence separately.
5. **Crowding and squeeze-risk interaction:** test whether high short interest/days-to-cover combined with price stabilization, liquidity, and borrow-cost conditions predicts asymmetric upside or downside risk. Treat both directions as plausible.
6. **Revision sensitivity:** measure how often `revisionFlag` appears and how much it changes the prior-cycle comparator. Do not use revised values as though they were known at the original publication.

Feature controls:
- Use only observations whose actual receipt precedes the decision timestamp.
- Keep missing, zero, and sentinel values distinct.
- Recompute prior-only rolling baselines; do not use future rows or a vendor average whose lookback cutoff is unclear.
- Control for LTM/F80, momentum, realized volatility, liquidity/size, corporate actions, borrow conditions where available, earnings/events, sector and market regime.
- Do not interpret participant identity: this dataset is aggregate and does not expose the short holder.

## 8. Access and licensing gate

FINRA's API fee page currently lists Public credentials at $0/month with a 10 GB monthly data limit. FINRA's documentation says individual-user API accounts are intended for individual research and are not intended for commercial purposes. Organization credentials are listed at $1,650/month; the exact credential and license needed for this project's use must be confirmed before business use.

No API credential was created, no paid credential was activated, no purchase was made, and no data was downloaded or committed for this phase. Do not incur fees or treat a personal public credential as permission for firm/commercial use.

## 9. Decision and next gates

**Promote to conditional historical positioning research; do not admit as a signal.**

Required next gates:
1. Confirm the appropriate API credential and usage rights for the intended research/business context without incurring a paid subscription automatically.
2. Obtain a lawful sample and audit the actual current earliest date, per-settlement row counts, missing cycles, revisions, and exact 335-name coverage.
3. Reconcile effective-dated issuer/security identity, share classes, ticker changes, splits, acquisitions, and delistings.
4. Build a prospective first-receipt ledger around the next scheduled publication, **November 24, 2026**, retaining original and revised vintages.
5. Validate the Phase 495 Reg SHO parser with the next naturally scheduled live capture; the prior eight-file capture used the old parser.
6. Only after coverage, license, and PIT gates pass, test incremental information versus frozen LTM/F80 with identical exposure, turnover, execution timing, and costs; use chronological discovery/validation/OOS, block bootstrap, LOO, and multiplicity controls.

No alpha test, event study, backtest, OOS, bootstrap, LOO, or signal admission was performed in Phase 505.

## 10. Frozen controls

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No universe, parameter, holding-period, exposure, cost, holdout, or production change. New signals admitted: **0**.

## Official sources

- FINRA Short Interest Reporting and 2026 calendar: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
- FINRA Developer Center — Consolidated Short Interest dataset and 4:40 PM ET publication availability: https://developer.finra.org/docs
- FINRA Consolidated Short Interest API metadata: https://api.finra.org/metadata/group/otcmarket/name/consolidatedShortInterest
- FINRA Consolidated Short Interest API data: https://api.finra.org/data/group/otcmarket/name/consolidatedShortInterest
- FINRA January 2023 API release note (five-year launch backfill; all-exchange data from June 2022): https://developer.finra.org/release-notes/january-2023-release-notes
- FINRA — “Short Interest: What It Is, What It Is Not”: https://syndication.finra.org/content/short-interest-what-it-what-it-not
- SEC rulemaking record for SR-FINRA-2026-012 (withdrawn August 5, 2026): https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-finra-2026-012
- FINRA API fees: https://developer.finra.org/fees
- FINRA API public credential terms/fees: https://developer.finra.org/fees/public
- FINRA API organization credential fees: https://developer.finra.org/fees/organizations

## 11. Mandatory reconciliation with prior FINRA short-interest work (Phase 506 correction)

This Phase 505 audit must be read together with Phases 37 and 445–447. The source is **not newly discovered**, and Phase 505 does not re-admit the old Phase 31 panel or establish frozen-universe coverage.

### What the earlier work actually established

- **Phase 37:** initially treated the 98 observed symbols in the Phase 31 artifact as roughly 29% of the 335-name universe and killed the joint flow + position panel on apparent coverage. It also correctly recorded that Phase 31's horizon directions were unstable and bootstrap intervals included zero.
- **Phase 445:** corrected the missing-versus-zero semantics. FINRA does not require a zero-position row when a previously reported issue has no current short position. A missing row can only be inferred as a structural zero after a complete settlement snapshot and effective-dated proof that the security was active and in scope.
- **Phase 446:** established that the Phase 31 artifact cannot support either coverage or zero inference. It contained 106 requested settlement dates; 102 successful synchronous pulls all returned exactly 5,000 rows (the documented synchronous cap), and four requests failed. The filtered feature file had 9,420 rows and 98 observed symbols, all A–D. **Zero settlement snapshots were proven complete.** The 98 symbols are not a valid 98/335 coverage estimate; E–Z may have been truncated beyond the cap. No missing symbol can be assigned zero from that artifact.
- **Phase 447:** already implemented the correct asynchronous retrieval client and a manual-only, single-settlement validation workflow. The client passed 14/14 synthetic tests, but synthetic tests do not validate a live FINRA response. The workflow is `.github/workflows/phase447_finra_single_live_validation.yml`; it requires either `FINRA_ACCESS_TOKEN` or both `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET` as GitHub Actions secrets.
- The only recorded live attempt, [Run 44007662531](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44007662531), failed at the credential guard. Its log explicitly says: “Set FINRA_ACCESS_TOKEN or both FINRA_CLIENT_ID and FINRA_CLIENT_SECRET; no FINRA request was made.” The capture step was skipped. No FIP token request or FINRA data request occurred.

### Current reconciliation at 2026-11-19 18:54 UTC

- The latest 100 Actions runs were inspected; 7,894 total runs were reported. The latest run was [44534689780](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44534689780), a Phase 500 offline PR validation. No queued, in-progress, waiting, requested or pending run appeared in that returned set.
- No later Phase 447 live-validation run or successful FINRA asynchronous snapshot was found in the latest 100 runs.
- Phase 495 Reg SHO parser validation remains offline-only; the last scheduled live Reg SHO capture [44453548570](https://github.com/jafelix81/NuevaEstrategia/actions/runs/44453548570) predates Phase 495. Its eight HTTP-200 files were rejected by the old duplicate-symbol rule. A post-Phase-495 live capture is still required.
- Phase 505's twice-monthly calendar/PIT analysis remains useful, but it does not cure the incomplete Phase 31 retrieval or the missing live credential validation.

### Correct disposition

1. **Old Phase 31 short-interest panel: KILLED / INCOMPLETE AS RETRIEVED.** Do not use its 9,420 rows for coverage, zero inference, or return tests.
2. **FINRA Consolidated Short Interest source: conditional only.** Re-entry requires one successful Phase 447 asynchronous live validation with exact `Record-Total` reconciliation, then a complete historical async re-ingestion. Do not start the 106-date batch before the single-settlement validation passes.
3. **Credential/usage gate:** before the manual validation, an authorized maintainer must configure `FINRA_CLIENT_ID` and `FINRA_CLIENT_SECRET`, or `FINRA_ACCESS_TOKEN`, as repository Actions secrets. Choose credentials and terms appropriate to the intended personal/non-commercial or organization/commercial use. Never put values in code, logs, PR text or this report.
4. After complete snapshots exist, classify each security-date as positive row, structural zero, or unknown. Structural zero requires complete snapshot proof plus effective-dated security/listing scope. Preserve revisions and original vintages.
5. Only after effective-dated identity and the frozen-335 panel pass may a new, preregistered flow + position diagnostic be designed. Phase 31's prior return findings remain non-promotable and must not be repackaged as OOS evidence.

**Human action required before the existing manual live workflow can progress:** configure an authorized FINRA credential in GitHub Actions secrets and confirm the applicable usage tier. No credential values were inspected or changed in this audit.

No FINRA request, historical re-ingestion, alpha test, event study, backtest, OOS, bootstrap, LOO, signal admission, production change, or F80 change was performed in this correction.