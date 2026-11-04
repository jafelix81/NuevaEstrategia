# Phase 70 — Point-in-time U.S. equity security-master feasibility audit

**Date:** 2026-11-04  
**Branch:** `phase70-pit-equity-security-master-feasibility`  
**Scope:** identity, listing lifecycle, historical-universe and delisting-data feasibility only. No returns or alpha test.

## Executive decision

The next hard blocker is not the SEC CIK map. It is the historical security universe and security identity layer.

The repository's current Phase 6/8 implementation embeds a fixed `DEFAULT_UNIVERSE` of 335 current ticker strings and downloads a 10-year price history for those strings. The repository does not contain an effective-dated, historical all-security eligibility panel for that 335-name set or the broader cross-section from which the top-20 ranking was selected. This is not proof that the frozen strategy's observed results are wrong, but it means they cannot yet be described as a survivorship-bias-free historical-universe test.

Phase 68's 335/335 ticker-to-registrant-CIK result closes a current SEC lookup gap only. A CIK identifies a registrant/issuer, not a unique tradable listing or share class. Shared fund registrants, multiple share classes, ADRs, ETFs/ETPs, ticker changes/reuse and delisted securities still require security-level identifiers and effective dates.

**Decision:** prioritize a small historical security-master sample from Databento and/or AlgoSeek before any further Form 144 forward-return work. CRSP is the preferred research-grade benchmark if accessible. Sharadar and Norgate are useful lower-cost or cross-check candidates, but neither is yet proven to provide the two-clock point-in-time history required here.

## 1. What the current repository establishes — and does not establish

- Phase 6 and Phase 8 code contain a hard-coded 335-symbol `DEFAULT_UNIVERSE`; the price loader requests `period="10y"` by ticker. No date-effective universe inclusion/exclusion file was found in the inspected repository tree.
- The list mixes operating companies with ETFs/ETPs, ADRs and multiple share classes. Phase 6's simple asset classifier only identifies a subset of known ETFs; it is not a complete security-type master.
- Phase 68 mapped 335/335 current ticker strings to 319 candidate registrant CIKs. Six registrants are shared across multiple tickers. This is a current candidate mapping, not a historical listing master.
- The SEC mutual-fund file's `seriesId` and `classId` are necessary for fund security resolution. A trust-level CIK match must not be fanned out to every ETF under that registrant.
- A ticker is not a permanent identifier. A symbol can change, be reused, represent another class, or refer to a different security in another effective period.

**Critical implication:** even a perfect historical mapping for the 335 current symbols cannot restore delisted or acquired names that were omitted when the 335-name list was assembled. To validate a cross-sectional top-20 strategy as a general strategy, we must recover the original universe-selection rule and reconstruct the eligible security pool as it existed on each formation date. If that rule cannot be recovered, results using only the fixed 335 names must be explicitly labelled conditional on the present-day curated survivor set; they cannot be promoted as a general survivorship-free edge.

## 2. Vendor/source comparison

| Source | Documented history and identity | PIT evidence | Main limitation | Decision |
|---|---|---|---|---|
| Databento Security Master | Product advertises 18 years of PIT reference history across listed/delisted securities and many venues. Fields include listing/security/issuer IDs, symbol, CIK, CUSIP, FIGI, listing/delisting dates and status. | Strongest documented two-clock model: `ts_record` (record last changed) and `ts_effective` (when attributes become effective). API supports PIT range retrieval. | Confirm U.S. venue coverage, historical retention by symbol, correction semantics, reference-data license and exact pricing. Public pages show differing symbol-plan language; do not budget from marketing snippets. | **Priority 1 — request/sample first.** |
| AlgoSeek Equity Security Master + ASID Lookup | Listed and delisted U.S. equities from 2007; includes common stocks, ETFs/ETNs, ADRs, preferreds, warrants and related instruments. Stable `SecId`, cross-lifecycle `ASID`, ticker effective ranges, FIGI/ISIN and corporate-action support. | Effective-date ranges are documented; a vendor record-known/publication timestamp for each historical correction is not established by the public ASID schema inspected. | Need confirm `created/changed/recorded` history and whether the ASID/lookup table is versioned PIT. ASID may join related SecIds across restructurings; retain SecId for distinct tradable share classes. | **Priority 1A — parallel sample/quote.** |
| CRSP US Stock Database | 32,000+ active and inactive U.S. securities; daily/monthly history from 1926/1965; PERMNO/PERMCO permanent identifiers and corporate actions. | Strong effective-dated security history and survivor-bias-free research conventions; verify precise vintage/availability fields for any non-price attributes. | Institutional/WRDS access and pricing not confirmed; coverage/identifier crosswalk for all 335 mixed security types must be tested. | **Preferred benchmark if access exists.** |
| Sharadar Tickers + Corporate Actions + Stocks/Funds | Tickers master covers active/delisted instruments; permanent ticker per security/share class, CUSIPs, FIGI, category and delisted flag. Prices reach Dec-1997; corporate actions reach Jan-1998 and include ticker changes, listing/delisting dates/reasons, mergers and related securities. | Tickers table is documented as a current snapshot; corporate actions have event dates, but public docs inspected do not establish archived as-known vintages for each change. | Good retrospective lifecycle crosswalk, but current snapshot/lastupdated is not proof of historical first availability. Delisting returns and fund-series completeness need validation. | **Secondary / cost-sensitive candidate; not PIT PASS.** |
| Norgate Data | Active and delisted U.S. stocks; Platinum/Diamond adds delisted history and daily major-exchange-listing indicator back to Jan-1990 for equities and ETPs. Historical constituents for major indices (e.g. Nasdaq-100 from 1990; Russell broad universes from 2000) are available at Platinum/Diamond. | Effective historical time series for listing and index membership are documented. | Not a bespoke historical membership file for this custom 335-name universe; delisted database is described as extensive but not complete, and OTC continuation handling differs. Windows/proprietary database/export workflow may complicate GitHub Actions ingestion. | **Secondary cross-check, especially listing status.** |

### Official documentation reviewed

- Databento Security Master: https://databento.com/security-master
- Databento schema and timestamp fields: https://databento.com/docs/schemas/security-master
- Databento reference service / quickstart: https://databento.com/docs/quickstart
- AlgoSeek Security Master and lookup datasets: https://algoseek.com/docs/rest-api/reference/us-equity-ref-sec-master-lookups
- AlgoSeek ASID effective-range schema: https://algoseek.com/docs/rest-api/reference/endpoint-v-1-data-us-equity-ref-secid-chains-lookup-get
- AlgoSeek identifier model and ticker-reuse example: https://algoseek.com/docs/rest-api/intro/data-schema
- AlgoSeek research sample catalog: https://console.algoseek.com/marketplace/datasets/eq_secid_chains_lookup
- CRSP US Stock Databases: https://www.crsp.org/research/crsp-us-stock-databases-2025-layout/
- CRSP permanent identifiers: https://www.crsp.org/research/
- Sharadar Tickers/Metadata: https://sharadar.com/docs/tickers
- Sharadar Stock Prices: https://sharadar.com/docs/stocks
- Sharadar Corporate Actions: https://sharadar.com/docs/actions
- Norgate data coverage: https://norgatedata.com/data-content-tables.php
- Norgate delisted/listing FAQ: https://norgatedata.com/data-package-faq.php

## 3. Required identifier model

Do not collapse all identifiers into CIK or ticker.

The canonical security panel should preserve at least:

- `listing_id` / exchange-specific listing identifier;
- `security_id` or `SecId` / tradable security or share-class identity;
- `issuer_id` / `ASID` / PERMCO only as issuer/economic-lifecycle grouping where appropriate;
- permanent crosswalk identifier (e.g. PERMNO, FIGI, ISIN, CUSIP) with effective dates;
- raw ticker, exchange/MIC, security type, primary-listing flag;
- SEC CIK as issuer/registrant cross-check only;
- fund registrant CIK, `seriesId`, `classId` and fund ticker separately;
- `effective_from`, `effective_to`, `ts_record` / vendor-known timestamp, source and version.

For a multi-class issuer, separate security IDs must remain separate. An issuer-level ASID/PERMCO/CIK is not a substitute for a share-class/listing identifier.

## 4. Acceptance gates before any historical F80/alpha work

### Gate A — identity coverage
1. Map every current one of the 335 symbols to one or more dated security/listing records, retaining exchange and share class.
2. Resolve ticker reuse and simultaneous same-symbol listings by date + exchange; no ticker-only joins.
3. Preserve multiple valid classes/listings as separate securities; document which listing is primary for price/volume.
4. Reconcile CIK/FIGI/CUSIP where present, but do not require a CIK for non-filers or funds if another stable security ID exists.
5. Resolve fund series/class to the exact tradable ETF; unresolved trust-level events stay registrant-level and are excluded from ticker-level tests.

### Gate B — lifecycle and coverage
1. At least 99.5% of expected security-days in the selected 2016–2026 sample must map to a security ID; report per-symbol and per-year coverage, not just pooled coverage.
2. Include inactive, acquired, bankrupt and delisted securities; report missing/delisted records separately.
3. Reconcile listing, ticker-change, merger, spin-off, liquidation and delisting effective dates against a second source for a stratified sample.
4. Confirm delisting/merger terminal returns or cash/stock consideration; do not silently drop terminal observations.
5. Separate common shares, ADRs, ETFs/ETNs, preferreds, warrants and other instruments. Do not rank them together unless the frozen strategy explicitly did so.

### Gate C — point-in-time availability
1. For a decision at time (t), require the record-known timestamp (leq t) and the effective date (leq) the trading date.
2. If a vendor only supplies effective dates and no record-known history, require archived dated snapshots or a validated conservative publication lag; otherwise PIT status remains unproven.
3. Preserve every vendor correction/version. Never let a later correction rewrite what the strategy would have known historically.
4. Weekly reference updates require a weekly knowledge calendar; do not assume same-day availability.
5. Price/corporate-action adjustment factors must be applied without using future corporate-action knowledge before it was effective/known.

### Gate D — universe definition (hard gate)
1. Recover the exact rule that generated the 335-name universe and its original formation/selection date.
2. If it is a custom fixed list, document whether it was chosen using information after the historical test period.
3. For a general cross-sectional top-20 claim, reconstruct the broad eligible U.S. security universe at each formation date, including names later delisted/acquired; a historical index-constituent feed alone is not enough unless that index was the actual original universe rule.
4. If the original rule cannot be recovered, label all fixed-335 historical results as conditional/survivor-set diagnostics and prohibit alpha promotion from those results alone.

## 5. Minimum sample design

Request a sample that deliberately includes lifecycle edge cases, not only liquid survivors:

- 2016, 2019, 2022, 2024 and 2026 snapshots;
- active names and known delisted/acquired names;
- ticker change and ticker reuse (e.g. FB/META; historical AOL/TWX reuse);
- multiple share classes (e.g. Z/ZG);
- ETFs sharing a registrant (ARK family and SPDR sector funds);
- ADRs, SPACs, reverse splits, fund liquidations and OTC transitions;
- all 335 current tickers plus a broad sample of non-current/delisted securities.

Cross-check at least 50 security lifecycles against a second provider and official exchange/SEC evidence. Include at least 10 difficult cases selected before inspecting whether they match.

## 6. Cost and access decision

No data has been purchased and no vendor has been contacted.

- AlgoSeek's catalog advertises a free/sample research package containing the ASID lookup and a 2023 full-universe demo; request the sample before any paid research package. Confirm the exact license and whether the sample can be retained in the repository's private research artifacts.
- Databento advertises downloadable U.S. samples and a Standard plan, but the security-master page directs users to pricing and the public plan pages do not give a single unambiguous PIT-reference quote. Request a quote for 335 symbols first, then for the broader historical eligible universe if required.
- CRSP should be checked through any existing WRDS institutional entitlement before obtaining a new quote.
- Sharadar/Norgate remain alternatives for lifecycle cross-checks; do not treat their public documentation as proof of vendor-vintage PIT.

No purchase should be approved until the sample passes Gates A–C and the universe decision in Gate D is resolved.

## 7. Workflow coordination

At the time of this audit:
- Phase 67 run 41828139052 remains `in_progress` in the XML resolution step; all four unit-test suites have passed; no artifact is available yet.
- Phase 67 run 41828179718 is `pending` in the same concurrency group, reflecting later code/test commits. Do not dispatch another full census.
- The active job's log download returned `BlobNotFound`; this is an unavailable log object, not evidence of failure or completion.
- Phase 68 run 41828426133 completed successfully. Artifact 13321546076 reports 335/335 current ticker-to-registrant-CIK mappings and zero source errors. This does not pass historical security identity or universe PIT.
- No Phase 69 incremental fund scan should run until Phase 67 completes and the 319-CIK/series-class reconciliation plan is updated.

## 8. Decision

- Current 335 ticker-to-CIK map: **PASS for current registrant lookup only**.
- Historical security master: **NOT TESTED**.
- Historical active/delisted universe: **NOT TESTED**.
- PIT record-known timestamps: **NOT TESTED**.
- Custom 335-name universe selection process: **NOT DOCUMENTED / HARD BLOCKER FOR GENERAL ALPHA CLAIMS**.
- Forward returns and alpha: **NOT AUTHORIZED**.

The most efficient next step is a free/sample request to AlgoSeek and Databento for the same preselected edge-case list, then a field-level comparison of identity, effective dates, record timestamps, delisted coverage and terminal corporate actions. If neither supplies historical record-known timestamps, CRSP/WRDS becomes the reference alternative; Sharadar/Norgate can still validate lifecycle dates but cannot be assumed to satisfy PIT by themselves.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No production code, portfolio rules, costs, holding period or allocation logic were changed.
