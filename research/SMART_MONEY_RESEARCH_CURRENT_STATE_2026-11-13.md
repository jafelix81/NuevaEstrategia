# Smart Money Research — current state (2026-11-13 UTC)

## Latest update — Phase 360 completed: FINRA symbol bridge and arithmetic reconciliation pass with exclusions

**Frozen baseline:** `F80_TOP20_PARTIAL50_BASELINE_C20`. No new signal admitted; no return/alpha test; no holdout reuse; F80 unchanged.  
**Legacy holdout:** `CONSUMED_NOT_PRISTINE`; do not reuse.  
**Economic status:** no new Smart Money feature has demonstrated incremental, cost-adjusted OOS edge. No CAGR target or holding-period constraint is imposed.

### Phase 359 — product-type key diagnostic

Hosted run [43413334750](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43413334750) passed 8/8 offline tests and retrieved four historical partitions: 409,225 rows across 84 pages, with exact API Record-Total matches. The zero exact joins from Phase 358 were explained by a row-grain difference: `productTypeCode` was blank on all **363,241** symbol-firm rows but populated on symbol aggregates. Ignoring product type, symbol sets aligned. A unique symbol-only bridge was possible for 45,212 of 45,222 shared symbols (99.9779%); ten multi-product symbols and two missing-symbol rows require exclusion.

### Phase 360 — bridge and arithmetic reconciliation (completed)

Corrected hosted run [43426428636](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636) passed 12/12 offline tests and retrieved all four partitions: **409,225 rows / 84 pages**, all API Record-Total counts matched. Retrieval gate PASS; data gate PASS_WITH_EXCLUSIONS. Metadata-only artifact [14037407295](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636/artifacts/14037407295).

For all **45,212 unambiguous symbol-family-period mappings**, firm-level share quantity and trade count both reconciled exactly to the symbol aggregate. No invalid numeric cells, duplicate aggregate symbol/product keys, duplicate participant-symbol keys or missing MPID/CRD identities among non-de-minimis participant rows were found. Ten multi-product symbol cases were excluded; one aggregate and one firm row in 2022-01-03/T2 lacked a symbol.

- ATS T1 samples (2022 and 2025): bridge 100% and no exclusions; ATS-level intermediary concentration is technically measurable on these samples, but no HHI was calculated. This is venue/routing structure, not beneficial-owner identity or informed direction.
- ATS T2 samples: 8,871/8,874 and 8,621/8,622 mapped; 3 and 1 ambiguous symbols excluded.
- OTC non-ATS: exact arithmetic reconciliation also passed, but every mapped symbol has a De Minimis Firms aggregate row. De-minimis share of volume was 33.13%, 31.06%, 22.95% and 12.11% by partition (19.71% weighted across the four sampled partitions). Complete firm concentration is therefore censored.

[Phase 360 report](PHASE360_FINRA_SYMBOL_BRIDGE_RECONCILIATION_2026-11-13.md) · [run](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636) · [artifact](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43426428636/artifacts/14037407295).

**Decision:** FINRA's symbol-only bridge and arithmetic reconciliation pass with explicit exclusions in the four Phase 360 partitions. Keep ATS as a conditional venue-level market-structure candidate; do not interpret it as Smart Money. OTC non-ATS concentration remains censored by de-minimis aggregation. A separate Phase 107 sample found two conflicting LND aggregate-key groups in 2025-01-06/T2 (one ATS and one OTC); Phase 361 is now running on [GitHub Actions 43427833220](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43427833220), extending the reconciliation to all five Phase 107 sample weeks (10 partitions). The combined Phase 360 + Phase 361 offline regression suite passed; the five-week live retrieval is still in progress. Do not start another copy. Historical final snapshots do not establish interim-vintage PIT, and FINRA data is published with two-week Tier 1 and four-week Tier 2/OTC delays. No returns, alpha, OOS, bootstrap, LOO or holdout test is authorized yet.

### Next gate

1. Audit broader weekly coverage over the available historical window, including inactive/delisted securities and the frozen 335-symbol panel as a comparison denominator only.
2. Determine whether prospective first-receipt and correction capture is feasible without excessive retrieval/storage burden.
3. If coverage and PIT pass, consider descriptive ATS concentration features; only then test incremental value versus frozen LTM/F80 using strict chronological validation and a new untouched holdout.
4. Continue Cboe Open-Close EOD/Option EOD feasibility in parallel; its historical first-receipt/correction archive, inactive-underlying coverage, session alignment and licensing remain unresolved.

## Latest completed phase — Phase 355: Cboe EOD participant-volume accounting reconciliation

The public C1 20% EOD sample for 2025-03-28 passed the participant accounting gate. The 34 participant-side volume fields sum exactly to `total_exchange_vol` on **23,179/23,179 rows**; all **556,296** Customer/Professional-Customer size-bucket aggregate checks passed; there were zero duplicate series keys, missing/invalid numeric cells or width errors.

A unit correction was necessary: Cboe defines `total_exchange_vol` as counting both sides of a trade, while the OCC industry field is a contract count. A raw comparison falsely flags 7,576 rows (32.68%); after comparing `total_exchange_vol/2` with industry contracts, zero of 23,179 rows exceed the industry total. The sample's normalized C1/industry ratio has p50 0.25 and p90/p95/max 1.00. This is an accounting result for one selected C1 sample, not a representative market-share or alpha result.

- Hosted run [43385780546](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43385780546): **9/9** regression tests passed; accounting diagnostic passed.
- Metadata-only artifact [14019160327](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43385780546/artifacts/14019160327).
- [Phase 355 report](PHASE355_CBOE_EOD_PARTICIPANT_ACCOUNTING_AUDIT_2026-11-13.md)
- [Draft PR #42](https://github.com/jafelix81/NuevaEstrategia/pull/42), stacked on Phase 354, open and unmerged.

**Decision:** pass the one-sample participant-volume accounting gate. Keep Cboe Open-Close EOD conditional. Broad/inactive historical coverage, exact first-receipt PIT/correction vintages, C1 session alignment, S/N/F crosswalk and licensing remain unresolved. No returns/alpha/OOS/bootstrap/LOO/holdout test; no vendor contact or purchase. F80 remains frozen.

## Previous completed phase — Phase 354: Cboe EOD OSI reconstruction and OCC OI endpoint kill

The corrected Phase 354 parser reconstructs full OSI from Cboe's `option_symbol` root, expiration, strike and call/put fields. The C1 20% EOD sample for 2025-03-28 contained **23,179 rows, 1,553 underlyings, 23,080 S / 11 N / 88 F series, zero invalid reconstructed OSI keys and zero duplicate OSI rows**.

The OCC public Daily Open Interest endpoint was tested with `reportDate` and `dailyDate` parameter variants. `reportDate` returned the same 2,878-byte, 23-row March 2025 aggregate table (Equity, Index/Other, Debt, Futures and OCC Total) for each requested date; it contains no option-symbol/per-series OI field. `dailyDate` returned HTTP 500. **Kill this public OCC endpoint as a contract-level OI validator.** This is a granularity incompatibility, not evidence of an OI mismatch in Cboe.

- Corrected run [43383418385](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43383418385): 18/18 offline tests passed; metadata artifact [14017970948](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43383418385/artifacts/14017970948). The initial hosted gate rejected the aggregate-only schema; the workflow gate was updated to treat this as an expected source kill.
- [Phase 354 report](PHASE354_CBOE_OCC_OI_CROSSCHECK_AND_ENDPOINT_KILL_2026-11-13.md)
- [Draft PR #41](https://github.com/jafelix81/NuevaEstrategia/pull/41), stacked on Phase 353, not merged.

The Cboe EOD sample remains a conditional candidate only. This one-day 20% sample is not representative full-market or historical/inactive-symbol coverage. First-receipt PIT, corrections, licensing and alpha remain closed.

**Universe rule:** the frozen 335-symbol panel is a comparison denominator, not a hard research-universe limit. Expand beyond it when source identity and historical price coverage permit; report both broad-universe and frozen-panel coverage.

## Previous completed phase — Phase 351: Cboe TBT public sample

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
| Cboe Open-Close | EOD sample schema passes; Phase 354 reconstructs 23,179 unique OSI keys in one C1 20% sample. Public OCC Daily Open Interest endpoint is aggregate-only and killed as a per-series validator. EOD/1m remain conditional candidates; historical first-receipt, corrections, broad/inactive coverage, session alignment and licensing unresolved; no alpha |
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

- PR #42: Phase 355 Cboe EOD participant-volume accounting, Draft/Open, stacked on Phase 354, not merged.\n- PR #41: Phase 354 Cboe EOD OSI/OCC OI endpoint audit, Draft/Open, stacked on Phase 353, not merged.\n- PR #40: Phase 353 daily EOD flow + OPRA context feasibility, Draft/Open, stacked on Phase 352, not merged.
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


## Previous completed research line — Phase 353: Cboe daily EOD flow + OPRA option context

**Status:** PASS_SAMPLE_SCHEMA_AND_SPEC_SEMANTICS_NO_PIT_NO_ALPHA

- Hosted run [43373927474](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474) passed 11/11 offline tests, both official specification audits, both public EOD sample schema audits, product-page checks and the no-alpha gates. Metadata-only artifact [14014015757](https://github.com/jafelix81/NuevaEstrategia/actions/runs/43373927474/artifacts/14014015757).
- Open-Close EOD sample: one C1 EOD member from the 2025-03-28 20% sample bundle; 23,179 option-series rows, 1,553 underlyings, 86 columns, no duplicate series keys or missing required cells, all 34 participant-volume fields. Series types: S 23,080, N 11, F 88. The bundle also contained 1m/10m samples, which were excluded from the EOD audit.
- Option EOD Summary sample: two variants for 2023-08-25, each 32,672 rows across 4 underlyings, 34 columns, all seven calc fields, no duplicate series keys or missing required cells. IV was zero on 7.25%/8.74% of rows in the two variants; zero IV is invalid/unavailable model output, not zero volatility. SOD OI was zero on 22.80%; trade volume was zero on 59.65%. The two variants are not separate dates.
- Linked 1m sample: 123,022 rows, 88 lowercase columns, trading_dt and trading_segment present. Its filename date is 2026-09-30, before the 2026-11-08 v1.8 cutover. It shows the new headers but does not verify post-cutover live correction/removal behavior.
- Open-Close EOD v1.3 has preliminary/final files, typically delivered 00:30–01:00 ET next morning; final total-industry volume and OI are sourced from OCC. Option EOD Summary v1.1 supplies OPRA 15:45 IV/Greeks and SOD OCC OI. The full four-venue pair starts no earlier than 2018-01-02.
- C1 RTH/GTH versus Option EOD RTH alignment, S/N/F contract-class crosswalk, broad historical universe coverage, exact first-receipt PIT, licensing and prospective capture remain open. No returns or alpha test was performed.

**Decision:** daily EOD pair is the highest-priority next options-flow feasibility candidate; no source or signal is admitted. F80 remains frozen. PR #40 is Draft/Open, stacked on Phase 352, unmerged.
