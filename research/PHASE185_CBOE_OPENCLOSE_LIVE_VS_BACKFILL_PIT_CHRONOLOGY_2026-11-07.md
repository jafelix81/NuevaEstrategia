# Phase 185 — Cboe Open-Close live-product versus historical-backfill PIT chronology

**Date:** 2026-11-07  
**Status:** **MATERIAL PIT CORRECTION.** Cboe Open-Close remains a top-tier conditional participant-capacity/open-close source, but its advertised historical archive dates must not be treated as dates when the corresponding intraday product was live. No historical row is admitted as strict PIT.  
**Scope:** Official Cboe product pages/release notes and SEC exchange rule filings; no raw data download, vendor contact, data purchase, return test, holdout use or production change.

## 1. Repository preflight

- Repository: `jafelix81/NuevaEstrategia`; branch: `phase99-broad-pit-universe-charter`.
- Preflight head: `90b6eff170e6160b928add3b6e647bc6a574aefc`; PR #13 open, unmerged and mergeable.
- The current head's associated Actions runs were inspected before any write. All were completed; Phase 174 was the only expected sample-admission failure. Phase 149 OpenFIGI had completed (553 CUSIPs: 437 primary, 7 fallback, 109 unresolved; zero API errors). Phase 183 and Phase 184 passed their hosted checks.
- Branch search was paginated through all 130 branches. No workflow was duplicated.
- Existing Phase 138/139/167/168 reports, Phase 183 source matrix, workflow jobs, logs and artifacts were inspected before this phase.

## 2. Main correction: historical archive start is not live-product start

The current Cboe DataShop page advertises historical Open-Close archives from:
- C1: EOD 2005-01-03, 10-minute 2011-01-03, 1-minute 2019-10-07.
- BZX/C2/EDGX: EOD 2018-01-02, 10-minute and 1-minute 2019-03-01.

These are **current archive availability claims**, not evidence that the corresponding intraday product was being delivered to subscribers on those dates. The same page describes EOD as overnight and intraday feeds as minutes after interval close; it does not provide per-file historical first-receipt logs.

### 10-minute product

Cboe DataShop announced on **2020-08-03** that 10-minute interval Open-Close summaries had launched across C1, C2, BZX and EDGX. The launch announcement said the then-available historical intervals began in October 2019 for C1 and January 2020 for C2/BZX/EDGX. The current page now advertises earlier archive dates (C1 2011; other venues 2019-03), so the archive has been extended or its coverage description has changed since launch.

**PIT ruling:** 10-minute data before 2020-08-03 are retrospective archive/backfill, not evidence of a contemporaneously available live signal. The date 2020-08-03 is only the earliest documented product-launch floor; it is not proof of the first receipt of any particular historical file.

### 1-minute product

The current page advertises 1-minute history from 2019-10-07 for C1 and 2019-03-01 for BZX/C2/EDGX. However, the SEC filings identify the one-minute intraday report as a **new product filed on 2025-06-13** for each of C1, C2, BZX and EDGX; the SEC notices were issued 2025-06-25.

**PIT ruling:** all 1-minute archive dates before 2025-06-13 are retrospective backfill, not contemporaneous live availability. June 13 is a product-introduction lower bound, not a verified first-receipt timestamp.

| Interval | Current archive start | Earliest documented live-product floor | Pre-floor history |
|---|---|---|---|
| 10-minute C1 | 2011-01-03 | 2020-08-03 | Retrospective backfill |
| 10-minute C2/BZX/EDGX | 2019-03-01 | 2020-08-03 | Retrospective backfill |
| 1-minute C1 | 2019-10-07 | 2025-06-13 | Retrospective backfill |
| 1-minute C2/BZX/EDGX | 2019-03-01 | 2025-06-13 | Retrospective backfill |

Even for post-launch dates, **no historical row is strict-PIT admitted** until actual first-received timestamps, immutable file hashes and revision lineage are evidenced. The product-launch floor alone is not sufficient.

## 3. Intraday delivery latency and cumulative-state semantics

The SEC filings describe 10-minute snapshots as available to subscribers within five minutes after each interval closes. Their example places the first 09:30-09:40 snapshot at approximately 09:42 ET.

For one-minute reports, the filings describe the first 09:30-09:31 snapshot at approximately 09:34 ET, with expected delivery generally 2-5 minutes after the interval; delivery may vary with market activity. Later updates contain the aggregate of the current snapshot **and all prior snapshots**.

Consequences:
1. A snapshot is a cumulative published state, not a standalone interval-volume file.
2. First differences are changes in the published aggregate since the previous received file. They can include late-processed trades and subsequent breaks/busts/cancellations; they are not necessarily volume executed during the clock interval.
3. Preserve every received raw file, source/schema version, hash and actual first-received timestamp. Never overwrite earlier vintages.
4. Do not backdate a late-reported change to its trade time.
5. A modeled 2-5 minute delivery envelope is not a substitute for actual receipt logs in a strict historical PIT test.

## 4. EOD delivery is a separate regime

The current product page describes EOD files as overnight after midnight ET. Cboe's FAQ says daily files for a trade date are typically uploaded the next day between 00:05 and 03:00 ET, but a delay can push delivery until after the market opens.

This is a typical schedule, not a guaranteed historical first-receipt time. A same-day close price cannot be used as an executable entry when the signal depends on that day's EOD file. Actual receipt logs and next-session execution are mandatory.

## 5. Schema sample does not establish historical production vintage

The public 1-minute sample audited in Phase 167 carries trade date 2026-09-30, while the v1.8 schema enhancements are announced effective **2026-11-08**. The sample is useful for parser/schema validation, but it is not proof that v1.8 was the production schema or first-received version on 2026-09-30.

Do not use the public sample's date as a schema-vintage boundary or historical receipt timestamp.

## 6. Measurement scope and economic interpretation

Open-Close reports classify activity by Cboe venue, participant capacity (customer, professional customer, broker/dealer, market maker), buy/sell and opening/closing position buckets. They are not all-OPRA coverage and do not identify beneficial owners. A capacity bucket is not proof of informed trading; professional customer is not synonymous with institutional investor.

Cboe states that raw data are licensed for internal use only; external distribution of derived data requires additional licensing and approval. No terms were accepted and no provider was contacted.

## 7. Decision and next gate

- Keep Cboe Open-Close as a **conditional top-tier position/open-close-flow candidate**.
- Treat 10-minute pre-2020-08-03 and 1-minute pre-2025-06-13 archives as retrospective-only for live-PIT research.
- Do not admit any post-launch historical row until per-file first-receipt logs, immutable vintages, correction lineage, effective-dated contract/underlying identity, inactive/delisted coverage and licensing are verified.
- A prospective shadow-capture pilot may be considered only after authorized subscription and licensing review; every file must be captured at first receipt, timestamped, hashed and preserved append-only. No purchase or contact is part of this phase.
- No feature construction, forward returns, bootstrap/LOO, OOS, or final-holdout test is authorized by this phase.

**Controls:** F80 remains frozen; no holdout used; no raw sample downloaded; no vendor contact; no data purchase; no production change.

## Official sources

- [Cboe Open-Close product page and current archive start dates](https://datashop.cboe.com/cboe-options-open-close-volume-summary)
- [Cboe 2020-08-03 announcement launching 10-minute Open-Close across C1/C2/BZX/EDGX](https://datashop.cboe.com/product-enhancement-10-minute-interval-open-close-data-now-available-for-c1-c2-bzx-edgx)
- [SEC SR-CBOE-2020-070 — C1 10-minute product](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboe-2020-070)
- [SEC SR-C2-2020-010 — C2 10-minute product](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-c2-2020-010)
- [SEC SR-CboeBZX-2020-059 — BZX 10-minute product](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboebzx-2020-059)
- [SEC SR-CboeEDGX-2020-036 — EDGX 10-minute product](https://www.sec.gov/rules-regulations/self-regulatory-organization-rulemaking/sr-cboeedgx-2020-036)
- [SEC 34-103323 — C1 one-minute product](https://www.sec.gov/files/rules/sro/cboe/2025/34-103323.pdf)
- [SEC 34-103324 — C2 one-minute product](https://www.sec.gov/files/rules/sro/c2/2025/34-103324.pdf)
- [SEC 34-103322 — BZX one-minute product](https://www.sec.gov/files/rules/sro/cboebzx/2025/34-103322.pdf)
- [SEC 34-103321 — EDGX one-minute product](https://www.sec.gov/files/rules/sro/cboeedgx/2025/34-103321.pdf)
- [SEC 34-103760 — one-minute delivery example and 2-5 minute expected latency](https://www.sec.gov/files/rules/sro/cboebzx/2025/34-103760.pdf)
- [Cboe DataShop FAQ — SFTP and daily-file delivery timing](https://datashop.cboe.com/faqs)

