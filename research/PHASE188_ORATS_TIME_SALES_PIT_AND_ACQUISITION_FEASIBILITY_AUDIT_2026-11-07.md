# Phase 188 — ORATS Option Time & Sales: PIT, measurement and acquisition feasibility audit

**Audit date:** 2026-11-07  
**Disposition:** high-priority conditional microstructure candidate; not admitted to PIT or alpha testing.

## 1. Why this source matters

ORATS documents a tick-level U.S. equity-options Time & Sales API with historical prints beginning 2022-09-09 and a live session tape. Each historical row includes trade price, size, exchange code, sale conditions, contemporaneous NBBO bid/ask, inferred `aggressorSide`, spread-leg and validity flags, and a parsed option contract. This is materially closer to trade-level order flow than the Near-EOD chain snapshot and can support tests of continuation versus temporary dealer-hedging pressure.

It does **not** identify the beneficial owner, participant capacity, institutional/retail status, or whether a trade opens/closes a position. `aggressorSide` is inferred and can be blank; it is not an identity label.

## 2. Historical coverage is not historical live availability

The documented backfill starts on 2022-09-09. The current product page marks Time & Sales as a new Tools API, but no historical date establishing when this product was first available live is published. Therefore:
- historical rows may support retrospective measurement research;
- the backfill start date does not establish that a live subscriber could have received the same rows in 2022;
- no historical first-receipt ledger or immutable correction-vintage history has been demonstrated;
- strict PIT admission remains false.

A prospective capture could establish a real availability ledger, but requires a paid token and the applicable live data agreements. No subscription, token, vendor contact or data purchase was authorized or used.

## 3. Event and measurement semantics that must be preserved

- Each row is one option print. Preserve `eventTime` in epoch milliseconds and `eventEstTime` as the documented Eastern-time representation.
- `eventIndex` is unique per contract, not per chain. Preserve it as a **string**: the documented example exceeds JavaScript's exact-integer range.
- `eventSequence` advances by two. A `CANCEL` row shares `eventIndex` and `eventSequence` with the `NEW` row it cancels. Key events by `symbol + eventIndex + type`; follow the vendor's rule to sum `NEW` prints only and never count a cancellation as new volume.
- Preserve blank `aggressorSide` as unknown. Do not coerce it to BUY or SELL.
- Separate `spreadLeg=true` from single-leg prints; retain `validTick`, `extendedTradingHours`, `exchangeSaleConditions` and exchange code.
- Historical `stockPrice`, delta, gamma and IV are joined from a one-minute Greeks snapshot, not measured at the exact print time. `stockPrice` is an option-implied reference value, not an independent equity price. `smvValue` is null on dates before that field became available.
- For same-day expiry, Greeks are null for snapshots at 09:30–09:32 ET and resume at 09:33.
- Historical backfilled days end at 15:59 ET (12:59 on half-days), while live capture ends near 16:15 ET. The last 16 minutes are therefore not historically comparable.
- Share-class ticker prints are only present from 2026-08-26 onward; earlier history is not complete for those symbols.

## 4. Operational and commercial feasibility

The endpoint is limited to 10 requests per minute per token. It accepts one ticker or one contract per request, returns JSON capped at 250,000 rows, and has an uncapped CSV form; large responses redirect to presigned gzip files. ORATS states that a full-day SPY chain is approximately 1.3 million rows / 700 MB of JSON.

For scale only, using the project's **reference** 335-name universe (not a closed universe), 252 sessions/year and the documented 2022-09-09 to 2026-11-07 window:
- 335 whole-chain requests per day: approximately 33.5 minutes at the 10/minute cap;
- approximately 84,420 requests/year and 351,324 requests over the documented history window;
- approximately 585.5 hours / 24.4 continuous days at the rate limit for the full backfill, before retries, downloads or processing.

Current public individual pricing shows the Time & Sales add-on at $299/month, attached to a data plan. Estimated plan costs for this illustrative backfill, based on monthly request quotas and full billing months:
| Plan | Combined monthly price | Monthly request cap | Billing months | Subscription cost estimate |
|---|---:|---:|---:|---:|
| Delayed + Time & Sales | $498 | 20,000 | 18 | $8,964 |
| Live + Time & Sales | $598 | 100,000 | 4 | $2,392 |
| Live Intraday + Time & Sales | $898 | 1,000,000 | 1 | $898 |
| All-In | $899 | 1,000,000 | 1 | $899 |

These are individual public prices and rough request-budget estimates only; they exclude storage/transfer, taxes, institutional licensing, retries and actual coverage gaps. The 10/minute endpoint rate remains a separate throughput constraint. There is no public free trial. A full-universe live polling sweep of 335 symbols cannot fit a 30-second refresh bucket at 10 requests/minute.

## 5. Historical/live mismatch and source independence

Historical prints include minute-snapshot Greeks and underlying reference values; live prints do not include those enrichment fields. Historical capture ends earlier than the live tape. A backtest using historical Greeks therefore cannot simply be deployed with the same feature set in live trading without a separate live join and a parity test.

ORATS Time & Sales and IvyDB TradeFlow may both derive from the options tape/OPRA ecosystem. The exact upstream lineage and side-inference methodology are not proven independent. Treat Time & Sales as an alternative measurement implementation, not independent raw-source replication, until provenance is established.

## 6. Preregistered hypotheses and falsification

1. Net single-leg signed flow adds information after controlling for underlying momentum, option volume/OI, IV changes, liquidity, earnings and market regime.
2. Signed flow is temporary price pressure from dealer hedging and reverses rather than producing persistent continuation.
3. Large- and small-print signed flow differ; size bands must be fixed ex ante.
4. Spread legs, sale conditions, exchange and invalid ticks explain apparent flow effects; multi-leg activity must not be double-counted.
5. Signed flow combined with IV/skew changes adds information beyond either component and beyond frozen LTM/F80.
6. Signed execution price relative to NBBO/SMV measures execution urgency or trade quality, not participant identity.

Kill the hypothesis if the effect disappears after momentum/volume/IV controls, is driven by a few issuers, relies on spread legs or cancellation rows, fails net costs, or does not survive chronological OOS, block bootstrap, issuer LOO and multiple-testing control. Do not use same-session returns before the first verifiable receipt/next executable price.

## 7. Admission decision

Keep as a high-priority conditional microstructure candidate for prospective capture and feasibility. Before any alpha test require:
- authorized token/license and a representative public or licensed sample;
- documented first live availability and prospective first-receipt ledger;
- 335-plus/open-universe symbol coverage including inactive/delisted names;
- aggressor-side blank/error rates and independent NBBO-side validation;
- event/cancel reconciliation and sale-condition mapping;
- historical/live feature parity and separate point-in-time equity prices;
- storage and request-budget proof.

No data purchase, vendor contact, API token, raw data download, holdout use, alpha test or production change. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
