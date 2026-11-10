# Phase 270 — NYSE Group Short Interest: official sample scope correction and license gate

**Audit date:** 2026-11-10 UTC  
**Branch:** `phase231-cboe-option-quotes-full-row-reparse` (PR #14)  
**Scope:** Resolve whether the official NYSE Group Short Interest sample is security-level or only exchange-level aggregate data; distinguish it from a separate consolidated press-release archive; review the current ICE website-use terms.

## Executive decision

**Correction to Phase 269: the official product sample is security-level.** The product page's "Sample Data" link resolves to the directory `/Reference Data Samples/NYSE GROUP SHORT INTEREST/`. Its two TXT/XLS/XML sample sets are dated 2026-07-15 and 2026-07-31. The indexed TXT previews show issue-level rows; the official v1.7 specification defines 16 fields including ticker, suffix, CUSIP, current short interest, previous short interest, changes, ADV and days-to-cover.

This is materially different from the separate `/NYSEGroupConsolidatedShortInterest/` directory, which contains exchange-level consolidated totals/press-release reports. A third-party description of that separate aggregate path must not be applied to the product's security-level sample directory.

The correction makes NYSE Group Short Interest more interesting as a possible per-security feature source. It does **not** admit historical PIT or alpha. The sample covers only two settlement dates; the full history advertised from January 1988 is subscription-based. Original release vintages, delisted coverage, revision chain and overlap with the immutable research universe remain unverified.

## 1. Official sample directory evidence

The official product page links "Sample Data" to:

`https://ftp.nyse.com/Reference%20Data%20Samples/NYSE%20GROUP%20SHORT%20INTEREST/`

The directory listing exposes:

| Settlement date | TXT bytes | XLS bytes | XML bytes | Indexed TXT lines |
|---|---:|---:|---:|---:|
| 2026-07-15 | 750,412 | 2,130,432 | 4,301,006 | 5,877 |
| 2026-07-31 | 751,053 | 2,132,480 | 4,308,024 | 5,889 |

These are directory/index metadata and indexed text line counts, **not a full-file parse or exact unique-security counts**. The indexed previews contain one issue-level row per line with pipe delimiters and a trailing delimiter. Multiple issues may share a ticker; the file includes a suffix and CUSIP, so ticker-only joins are invalid.

The official v1.7 specification defines 16 fields:
- Stock symbol, standard suffix, CUSIP, issuer and issue name;
- primary market, revision and split indicators;
- free float;
- current/previous short-interest position and change;
- average daily volume and change;
- current days-to-cover and change.

The specification defines market codes N, A, P and M (NYSE Texas). The product page still lists NYSE, NYSE Arca and NYSE American only; retain this scope discrepancy until clarified.

## 2. Do not conflate the two NYSE directories

- Product sample: `/Reference Data Samples/NYSE GROUP SHORT INTEREST/` — security-level sample files linked from the NYSE product page.
- Separate consolidated reports: `/NYSEGroupConsolidatedShortInterest/` — exchange-level totals/press-release reporting.

The latter does not establish that the former is aggregate-only. Phase 269's conditional source classification remains, but its sample-scope description is corrected by this phase.

## 3. Legal/use restriction is now the immediate blocker

ICE's currently posted Terms of Use apply to the NYSE website and provide a limited download/use license for personal, non-commercial purposes, while expressly excluding data mining, robots or similar data-gathering/extraction methods. The permissible-use section also prohibits systematic retrieval, electronic extraction/scrubbing, compilation and derivative works without prior written permission.

Consequently, **do not automate downloads, parse the sample into a research dataset, or calculate features from it unless NYSE/ICE grants written permission or a suitable data license is obtained**. No sample was downloaded or stored, no automated extraction was run, no vendor was contacted, and no purchase or terms acceptance occurred.

This is a material change from a mere technical feasibility issue: the data are security-level, but permitted research ingestion/derived-feature use is not established.

## 4. PIT and economic disposition

- Product advertises historical data from January 1988 to present; only two sample settlement dates are visible in the public sample directory.
- Specification v1.7 says delivery at 14:00 ET on the NYSE Group Release Date; FINRA documents API availability by 16:40 ET. The scheduled 160-minute difference is a distribution-timing advantage, not independent underlying information: both reflect the FINRA Rule 4560 reporting pipeline.
- Directory server modification timestamps are not original first-receipt timestamps.
- Revision flag R indicates a previous-period revision but does not provide the original vintage or revision timestamp.
- Delisted/inactive coverage and complete historical revision chains remain unverified.
- CUSIP and suffix help identify issues but do not replace an effective-dated security/listing master.
- No universe overlap was calculated; no backtest, return test, bootstrap/LOO or OOS analysis was performed.

**Decision:** `CONDITIONAL_SECURITY_LEVEL_SOURCE_SAMPLE_CONFIRMED_BUT_LICENSE_AND_HISTORICAL_PIT_BLOCKED`. Sample scope is admitted as a metadata/specification finding only. Historical PIT and alpha remain unadmitted.

## 5. Next gates if written permission or a suitable license is obtained

1. Confirm permitted automated download, storage, parsing, derived features, backtesting, and intended personal/commercial use.
2. Obtain representative multi-year history including inactive/delisted securities and original release vintages.
3. Preserve raw bytes, SHA-256, actual first-receipt timestamp, revisions, split states and release calendar.
4. Build effective-dated CUSIP/security/listing mapping and calculate overlap against an immutable F80 universe snapshot.
5. Compare 14:00 ET NYSE distribution with 16:40 ET FINRA availability using identical underlying values and eligible execution prices.
6. Test short-interest level, change and days-to-cover as crowding/risk features versus frozen LTM/F80, with identical exposure/costs and strict chronological OOS, bootstrap/LOO and independent OOS.

## 6. Controls

No sample download, automated extraction, data purchase, vendor contact, return test, alpha admission, production change, universe change, capital change, parameter change or holdout use. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; the legacy holdout remains `CONSUMED_NOT_PRISTINE`.

## 7. Official sources

1. NYSE Group Short Interest product page: https://www.nyse.com/data-products/catalog/nyse-group-short-interest
2. Official public sample directory: https://ftp.nyse.com/Reference%20Data%20Samples/NYSE%20GROUP%20SHORT%20INTEREST/
3. NYSE Group Short Interest Client Specification v1.7 (2025-04-10): https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Client_Specification_v1.7.pdf
4. Separate consolidated report directory: https://ftp.nyse.com/NYSEGroupConsolidatedShortInterest/
5. ICE Terms of Use: https://www.ice.com/privacy-security-center/terms-of-use
6. FINRA Developer Center: https://developer.finra.org/docs

## 8. Reproducibility

- Auditor: `phase270_nyse_short_interest_public_sample_scope_audit.py`
- Tests: `test_phase270_nyse_short_interest_public_sample_scope_audit.py`
- Workflow: `.github/workflows/phase270_nyse_short_interest_public_sample_scope_audit.yml`
- Artifact: metadata-only deterministic JSON; no market data included.
