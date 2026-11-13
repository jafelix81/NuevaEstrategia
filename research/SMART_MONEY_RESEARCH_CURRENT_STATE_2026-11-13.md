# Smart Money Research — current state (2026-11-13 UTC)

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; do not reuse.  
**Economic status:** no new Smart Money feature has demonstrated incremental, cost-adjusted OOS edge. No CAGR target or holding-period constraint is imposed.

## Latest completed phase — Phase 351: Cboe TBT public sample

The public Cboe TBT 3% sample for 2025-03-28 was downloaded and parsed against the 22-field v1.1 schema. Hosted workflow passed **16/16 regression tests** and the metadata-only sample gate.

- 113,018 rows; 1,250 underlyings; 25,015 complete option-series identities.
- 111,333 `EXEC_ID` groups: 109,648 singleton and 1,685 two-row Buy/Sell groups.
- 46,350 `COMPLEX_EXEC_ID` groups; 2,111 span multiple complete option series.
- `OPEN_CLOSE` blank on 20,180 rows (17.86%); 507 rows (0.45%) lack OSI root and call/put identity; 69 side codes are unmapped.
- All 113,018 rows show `TRADING_SEGMENT=1`, including 111,240 RTH rows. This conflicts with the v1.1 specification's 1=prior-evening/overnight and 2=daytime example. Do not use segment labels pending clarification.
- 306 rows have a calendar date mismatch between `TRANSACT_TIME` and `TRADING_DT`; all timestamps are timezone-naive in the sample. Use `TRADING_DT` for market date; do not invent timezone.
- NBBO/BBO are present on all rows; 12 crossed NBBO, 2 crossed BBO, 1,646 trades outside NBBO. `FLOOR_ACTION_TS` is blank on 99.45% of rows.

This validates the sample parser and execution-linkage diagnostics only. The sample is one date and a 3% subset; it is not assumed random or representative. The 2025 archive sample is retrospective backfill, not PIT. C1 is not all-OPRA. No returns or alpha were tested.

- [Phase 351 report](PHASE351_CBOE_TBT_PUBLIC_SAMPLE_ROW_GRAIN_AUDIT_2026-11-13.md)
- [Hosted run 43357411197](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357411197)
- [Metadata-only artifact 14006931596](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43357411197/artifacts/14006931596)
- [Draft PR #38](https://github.com/jafelix81/NuevaEstrategia/pull/38)


## Latest completed phase — Phase 352: Cboe Open-Close 1-minute v1.8

The official v1.8 PDF (effective 2026-11-08) was downloaded and hash-pinned. Hosted run [43365537803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43365537803) passed **12/12 regression tests and all 14 specification-semantic checks**; metadata-only artifact [14010665042](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43365537803/artifacts/14010665042). PDF SHA-256: \`49bbab63392f9282ad772fc5460bf19575178476f7b0e3ec2653fd8f1ed2c439\`.

- 1-minute files are cumulative day-to-date snapshots, not interval-only bars. Late trades may appear later; subsequent snapshots remove trades later broken/cancelled. Preserve every first-received snapshot and hash; negative differences may be correction events and must not be clipped or called sell flow.
- Product page documents 1-minute history from 2019-10-07 for C1 and 2019-03-01 for BZX/C2/EDGX. C1 has GTH/RTH; BZX/C2/EDGX are RTH-only. This is four Cboe venues, not all OPRA. C1 GTH begins 2023-12-11.
- The 1-minute schema leaves fields 10–17 empty, including EOD prices, total exchange/industry volume and OI. IV/Greeks require a separately timestamped companion source.
- Participant labels are exchange capacity buckets, not beneficial-owner identities. No category is assumed to be informed.
- The 1-minute product's C1 segment convention is product-specific and is not used to reinterpret the separate TBT v1.1 discrepancy from Phase 351.
- The surfaced sample file has a 2026-09-30 market-date filename, before the 2026-11-08 cutover; its binary header was not inspected. Historical first-receipt/correction vintages are not established.

**Decision:** high-priority conditional prospective participant-flow candidate; historical PIT and alpha remain closed. Prospective PIT would require append-only first-receipt capture. No sample purchase, vendor contact, subscription, returns test, OOS, bootstrap, LOO or holdout test was made.

- [Phase 352 report](PHASE352_CBOE_OPEN_CLOSE_1M_V18_SPEC_PIT_AUDIT_2026-11-13.md)
- [Draft PR #39](https://github.com/jafelix81/NuevaEstrategia/pull/39)

## Source dispositions

| Source / line | Current disposition |
|---|---|
| Cboe TBT | High-priority conditional C1 measurement candidate; sample parser passes, but row-grain/sampling, 17.86% open-close missingness, side-code mapping, session/segment discrepancy, licensing, first receipt, corrections and inactive-underlying coverage remain open |
| Cboe Open-Close | EOD sample schema/coverage 288/335 in a 20% C1 sample; v1.8 1m specification verified, but snapshots are cumulative/corrected and historical first-receipt vintages are unproven; high-priority conditional prospective candidate, no alpha |
| Cboe Option Sentiment | Historical start advertised at 2012; field cross-tabs and net-delta units/sign remain insufficient for a directional participant hypothesis |
| Cboe Option Quotes | Conditional option risk/context source; sample parser corrections do not establish PIT, all-symbol history or inactive names |
| CFTC TFF/COT | Historical strict PIT rejected: CFTC lacks complete historical release-date ledger; 2023 ION outage and 2025 funding lapse invalidate synthetic availability proxies. Legacy Phase 23C walk-forward quarantined; no reuse |
| CFTC BPR | Monthly broad equity-index regime context only; public retention 25 months, no historical first-receipt ledger; prospective capture staged but not active on default branch |
| FINRA short flow / short interest | Weak/incomplete or timing/pagination defects; no promotion |
| FINRA ATS / OTC | Context-only; later revisions and unresolved duplicate-grain conflicts; do not sum/choose arbitrarily |
| SEC Form 4 | Bulk history and daily-index PIT route are feasible candidates, but raw retrieval, owner attribution and effective-dated security identity remain blocked/incomplete |
| SEC 13D/G | CUSIP and explicit predecessor audits improved identity integrity; broad event/security panel still not admitted |
| SEC 13F / N-PORT | Delayed context only; acceptance/amendment timing and security mapping remain open |
| Form 144 | Filing/role and document-linkage work only; no market-execution or return edge established |

## SEC retrieval blocker

Phase 350's latest hosted attempt [43344689909](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43344689909) stopped before SEC requests because the repository secret `SEC_USER_AGENT` was not configured. No request was sent by that guarded run and no document was retrieved. The earlier HTTP 403 attempt remains quarantined. Do not retry until the secret contains a monitored contact address in the User-Agent. Do not expose the address in code, logs or chat.

## Active GitHub work

- PR #40: Phase 353 daily EOD flow + OPRA context feasibility, Draft/Open, stacked on Phase 352, not merged.
- PR #39: Phase 352 Open-Close 1m v1.8 spec/PIT audit, Draft/Open, not merged.
- PR #38: Phase 351 TBT sample audit, Draft/Open, not merged.
- PR #37: Phase 350 SEC 13D/G parent retrieval, Draft/Open, blocked on `SEC_USER_AGENT`.
- PR #14 and PR #13: broader stacked research work remains open/unmerged. Do not merge any PR without explicit authorization.
- No active workflow was duplicated; each Phase 351 run was checked before a subsequent update.

## Next gates

1. Obtain a verifiably post-2026-11-08 Open-Close 1m sample to validate live correction/removal behavior; the linked 2026-09-30 sample has the new headers but predates the cutover.
2. For the daily EOD pair, establish exact per-file first-receipt UTC, preliminary/final lineage and an append-only correction archive before any prospective PIT feature is admitted.
3. Quantify four-venue per-symbol/per-date coverage against the frozen 335 universe, including inactive/delisted names, option-root changes and a separate full-OPRA denominator.
4. Resolve the TBT sample's 3% selection rule, row grain, missing `OPEN_CLOSE`, 69 unmapped side codes and `TRADING_SEGMENT` discrepancy before any TBT feature construction.
5. Continue SEC 13D/G and Form 4 retrieval only after the required monitored-contact secret is configured.
6. Any eventual economic test must use a new untouched prospective holdout, strict chronological splits, label-maturity embargoes, identical exposure/costs versus frozen LTM/F80, clustered bootstrap, LOO and multiplicity controls.

## Controls

No signal admitted. No returns, alpha, OOS, bootstrap or LOO test performed in Phase 351. No holdout used. No vendor contacted, no trial requested, no data purchased, no terms accepted, no PR merged, no production/universe/capital/parameter change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## Latest completed research line — Phase 353: Cboe daily EOD flow + OPRA option context

<badge>PASS_SAMPLE_SCHEMA_AND_SPEC_SEMANTICS_NO_PIT_NO_ALPHA</badge>

- Hosted run [43373927474](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474) passed 11/11 offline tests, both official specification audits, both public EOD sample schema audits, product-page checks and the no-alpha gates. Metadata-only artifact [14014015757](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474/artifacts/14014015757).
- Open-Close EOD sample: one C1 EOD member from the 2025-03-28 20% sample bundle; 23,179 option-series rows, 1,553 underlyings, 86 columns, no duplicate series keys or missing required cells, all 34 participant-volume fields. Series types: S 23,080, N 11, F 88. The bundle also contained 1m/10m samples, which were excluded from the EOD audit.
- Option EOD Summary sample: two variants for 2023-08-25, each 32,672 rows across 4 underlyings, 34 columns, all seven calc fields, no duplicate series keys or missing required cells. IV was zero on 7.25%/8.74% of rows in the two variants; zero IV is invalid/unavailable model output, not zero volatility. SOD OI was zero on 22.80%; trade volume was zero on 59.65%. The two variants are not separate dates.
- Linked 1m sample: 123,022 rows, 88 lowercase columns, trading_dt and trading_segment present. Its filename date is 2026-09-30, before the 2026-11-08 v1.8 cutover. It shows the new headers but does not verify post-cutover live correction/removal behavior.
- Open-Close EOD v1.3 has preliminary/final files, typically delivered 00:30–01:00 ET next morning; final total-industry volume and OI are sourced from OCC. Option EOD Summary v1.1 supplies OPRA 15:45 IV/Greeks and SOD OCC OI. The full four-venue pair starts no earlier than 2018-01-02.
- C1 RTH/GTH versus Option EOD RTH alignment, S/N/F contract-class crosswalk, broad historical universe coverage, exact first-receipt PIT, licensing and prospective capture remain open. No returns or alpha test was performed.

**Decision:** daily EOD pair is the highest-priority next options-flow feasibility candidate; no source or signal is admitted. F80 remains frozen. PR #40 is Draft/Open, stacked on Phase 352, unmerged.
