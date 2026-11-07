# Phase 115 — Cboe TBT vs Open-Close EOD cross-sample consistency audit

**Date:** 2026-11-05  
**Scope:** same-date public-sample cross-check only; no forward returns, alpha test, purchase or vendor contact.

## Inputs and provenance

Two independently downloaded public sample packages were compared for the same C1 trade date, 2025-03-28:

| Input | Workflow artifact | Sample | Sample SHA-256 |
|---|---|---|---|
| Cboe Enhanced Options TBT | [Run 42023896730, artifact 13413280759](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42023896730/artifacts/13413280759) | C1 TBT 3% sample | 6c99e69e43d259e81bc31334574579cf9c623f5e77ff596cacf268712cd3262c |
| Cboe Open-Close EOD | [Run 42027724358, artifact 13415230222](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42027724358/artifacts/13415230222) | C1 EOD 20% sample | 445cd9d658dc06028c286e09d4ac4818bd5884d7da8addd7509f3a0fa4840552 |

The TBT sample contains 113,018 trade rows, 1,250 underlyings and 25,179 option-series keys. The EOD sample contains 23,179 option-series rows, 1,553 underlyings and all 86 post-2011 fields. These are different sampling fractions and populations; they must not be treated as full-market extracts or combined as if they were additive.

## Series overlap and accounting

- Exact option-series overlap: 3,971 keys.
- TBT rows belonging to those overlapping series: 10,452.
- Underlyings with at least one overlapping option series: 654.
- EOD total_exchange_vol across the 3,971 overlapping series: 1,813,434 contracts.
- EOD participant buy/sell bucket sum across those same series: 1,813,434 (exact).
- TBT sampled size on the overlapping series after mapping the observed side/capacity/open-close fields: 68,273 contracts, or 3.765% of EOD volume.

The Phase 114 full EOD sample independently reconciles participant side buckets to total_exchange_vol on all 23,179 rows. No unexplained EOD volume-accounting exception was observed.

## Capacity-level sample ratios

The TBT sample-to-EOD-volume ratios on overlapping series were:

| Capacity | TBT sample volume / EOD volume |
|---|---:|
| Customer | 3.185% |
| Pro-Customer | 3.776% |
| Market Maker | 4.442% |
| Firm | 1.749% |
| Broker-Dealer | 5.421% |

The variation is too large to apply one global expansion factor to TBT sample rows. Broker-Dealer is particularly sparse. These ratios are descriptive of the two public sample packages, not population sampling weights.

## Underlying-level rank concordance

For the 654 underlyings with overlapping series, TBT sample volume aggregated by capacity was compared with the EOD capacity volume on the same common series. Spearman rank correlations were:

| Capacity | EOD underlyings with positive volume | TBT sample underlyings with positive volume | Spearman |
|---|---:|---:|---:|
| Market Maker | 651 | 502 | 0.760 |
| Customer | 632 | 464 | 0.741 |
| Pro-Customer | 139 | 54 | 0.611 |
| Firm | 114 | 56 | 0.704 |
| Broker-Dealer | 23 | 9 | 0.624 |

The Broker-Dealer statistic is based on very few nonzero names and is not reliable as a standalone conclusion. Pro-Customer and Firm have much thinner coverage than Customer and Market Maker.

The correlations support broad consistency between the participant-volume classifications in the two samples, particularly for Customer and Market Maker. They do **not** constitute independent validation: Cboe states that TBT is the transaction-level data used to derive the Open-Close summary. The sample fractions also differ (3% vs 20%).

## TBT convention exceptions remain real

The full TBT sample contains 69 SIDE=T rows, all with blank OPEN_CLOSE, and 20,180 rows with blank OPEN_CLOSE. Blank OPEN_CLOSE is concentrated in Market Maker but also occurs for Customer (197), Firm (56), Pro-Customer (17) and Broker-Dealer (3) rows. Do not infer buy/sell from SIDE=T or impute open/close for blank rows.

Within the 3,971 overlapping series, the 10,452 TBT rows were mappable to the EOD bucket definitions, but this selected overlap does not prove that all TBT rows are classifiable. The EOD summary is preferable for daily open/close features because it already supplies the classified aggregate buckets and its sample passed exact volume accounting.

## Decision

1. Promote Cboe C1 Open-Close EOD to the **highest-priority conditional options-flow data candidate**.
2. Retain C1 TBT as a secondary raw-data/validation source, not as the first production feature source until SIDE=T and blank OPEN_CLOSE conventions are resolved.
3. Do not use the public samples to estimate market-wide weights, full-market coverage or predictive returns.
4. Before any economic test, verify the actual historical file boundary and missing dates (especially 2005-01-03 and the 2011 format break), quantify broad PIT underlying coverage including inactive/delisted issuers, establish T+1 final-file knowledge time and revisions, and obtain a license-cost estimate only if authorized.
5. Split pre-2011 and post-2011 histories or preregister a post-2011-only design. Respect the C1 2019 volume/OI convention break and the 2023-12-11 GTH start.
6. No purchase, vendor contact, terms acceptance, forward-return analysis or alpha test is authorized by this phase. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

