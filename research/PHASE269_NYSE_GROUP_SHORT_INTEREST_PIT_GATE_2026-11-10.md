# Phase 269 — NYSE Group Short Interest: early-release, historical coverage and PIT gate

**Audit date:** 2026-11-10 UTC  
**Repository:** `jafelix81/NuevaEstrategia`  
**Scope:** NYSE Group Short Interest product, its release calendar and specification, and relationship to FINRA Rule 4560 short-interest data.

## Executive decision

**A potentially useful earlier distribution channel, not a new independent smart-money source. Keep it conditional; do not purchase or contact NYSE.**

The NYSE Group Short Interest file is a semi-monthly subscription product. NYSE advertises historical data from January 1988 to present for NYSE, NYSE Arca and NYSE American listings. The current technical specification (v1.7, 2025-04-10) says delivery is at **2:00 p.m. ET on the NYSE Group Release Date**. FINRA's current developer documentation says its consolidated short-interest dataset is available by **4:40 p.m. ET on the same publication date**. For the same report date, that is a **160-minute earlier distribution window**.

That timing could make a same-day closing-price entry eligible for NYSE Group securities, whereas the FINRA API release at 4:40 p.m. is after the regular close. This is a timing/access advantage, not incremental underlying information: the SEC explains that FINRA aggregates Rule 4560 short-interest submissions and provides them to the appropriate listing exchange for publication. The NYSE file should therefore be treated as another distribution of the FINRA reporting pipeline, not an independent institutional-flow dataset.

The full historical product is subscription-based, its public price is not shown, and original as-published vintages, revision history, delisted-security coverage and exact universe overlap are not verified. No purchase, vendor contact, download, backtest or alpha test was performed.

## 1. Historical coverage and scope

NYSE's product page advertises a semi-monthly file with historical data from **January 1988 to present**. The product page lists NYSE, NYSE Arca and NYSE American securities. The current v1.7 technical specification also lists NYSE Texas and defines market code `M` for it. This product-page/specification scope discrepancy should be confirmed before coverage claims are made.

The public sample directory contains two sample settlement-date files (2026-07-15 and 2026-07-31); it is not the full 1988-present history. Full historical access is through a subscription. The product is delivered through SFTP or AWS S3. SFTP access requires a dedicated source IP and SSH key. Pricing and the detailed license terms were not publicly verified.

The source is not a full U.S. equity universe: it does not purport to cover Nasdaq-listed or OTC issues. The repository does not currently contain an immutable point-in-time universe/security list, so exact overlap with the research universe cannot be calculated. Do not infer coverage from the historical-start claim alone.

## 2. Publication timing: material potential advantage

The NYSE specification states that the file is delivered every two weeks at **2:00 p.m. ET** on the NYSE Group Release Date.

The 2026 NYSE calendar gives:
- settlement 2026-07-15 → release 2026-07-24;
- settlement 2026-07-31 → release 2026-08-11.

FINRA's official 2026 calendar lists the same release dates for those settlement dates. FINRA's developer documentation states that the Consolidated Short Interest dataset is available by **4:40 p.m. ET** on the publication date.

The scheduled difference is 160 minutes. For an end-of-day strategy, a report actually received at 2:00 p.m. could potentially be used with that day's closing price. This is eligible only if the file is truly received and validated before the actual XNYS close on that date. On an early-close session (for example, a 1:00 p.m. close), a 2:00 p.m. delivery is already post-close and entry must move to the next session. The scheduled time is not a substitute for an immutable first-receipt timestamp. Late or missing deliveries must move entry to the next eligible session; never backdate availability.

## 3. Relationship to FINRA: same underlying reports, not independent information

The SEC's short-sale reporting proposal describes the existing pipeline: FINRA collects and aggregates broker-dealer short-interest data by security twice each month, then provides the aggregate to the appropriate listing exchange for publication; some exchanges charge for access. FINRA itself publishes the OTC aggregate.

Accordingly, NYSE Group Short Interest should be treated as a **listing-exchange distribution of FINRA Rule 4560 data**. Its potential advantage is earlier delivery, historical archive access and CUSIP-rich file layout—not a separate set of short sellers or an independent measure of institutional conviction.

FINRA Rule 4560 data are not beneficial-owner or account-level positions. FINRA's FAQ says reportable short interest can arise from short sales and certain transactions marked long at the aggregation-unit level; it excludes some stock-loan, fail-to-receive and RVP positions. The NYSE file's word “uncovered” must not be interpreted as proof of naked short selling.

## 4. File semantics and controls

The v1.7 file has 16 fields, including:
- ticker and standard suffix;
- CUSIP;
- issuer and issue names;
- primary market;
- prior-period revision flag (`R`);
- current-period split flag (`S`);
- free float;
- current and previous short-interest positions and change;
- average daily volume and change;
- current days-to-cover and change.

Important controls:
- CUSIP improves matching but is not a permanent security/listing identifier; use an effective-dated security master and class-aware joins.
- `Free_Float=0` means unavailable, not zero float. NYSE says free float is maintained on a best-effort basis and may differ from other sources.
- `Revision_Indicator=R` means the previous reporting period was revised. It does not itself provide the original vintage, revision timestamp or complete revision history.
- `Split_Indicator=S` flags a split in the current period; retain raw values and adjust consistently.
- NYSE's days-to-cover and average-volume fields are source-defined. Do not substitute them for the project's independently defined ADV20 or assume identical calculation conventions without reconciliation.

## 5. Strict PIT status

The 2:00 p.m. schedule is a strong prospective availability contract, but historical PIT is **not admitted**:
- The product advertises history since 1988, but we have not verified that those files are preserved as originally published rather than restated/current snapshots.
- The revision flag proves revisions can occur; no complete as-published revision chain was established.
- Delisted/inactive security retention is not established.
- Exact universe overlap cannot be measured because no immutable universe snapshot is present in the repository.
- Full historical access is paid; no subscription, sample purchase or vendor contact was authorized.

If later authorized, the minimum evidence request is: a representative multi-year historical sample including delisted issues, original file bytes for each release, release and revision timestamps, retention/version policy, NYSE Texas scope, pricing and license/redistribution terms. Do not buy or contact the vendor until explicitly authorized.

## 6. Research disposition

| Gate | Result |
|---|---|
| Historical coverage advertised | 1988-01 to present |
| Release frequency/time | Semi-monthly, 2:00 p.m. ET |
| FINRA API availability | By 4:40 p.m. ET |
| Scheduled timing difference | 160 minutes |
| Same underlying information as FINRA | Yes, via listing-exchange distribution |
| Independent smart-money signal | No |
| CUSIP / revision / split fields | Present |
| Original historical vintages | Unverified |
| Delisted coverage | Unverified |
| Universe overlap | Not measurable yet |
| License / price | Subscription required; terms/price unverified |
| Historical PIT / alpha | Not admitted / not tested |

**Conditional hypotheses (not admitted):**
1. Does access to the same short-interest report at 2:00 p.m. enable a same-day-close execution that improves realized performance versus the 4:40 p.m. FINRA API / next-session execution?
2. Do short-interest level, change and days-to-cover add incremental risk/crowding information versus frozen LTM/F80?
3. Does the feature help with downside risk or squeeze vulnerability rather than directional return prediction?

Any test must use actual first receipt, same report values, identical exposure/costs, a point-in-time security master, revision/split handling, chronological OOS, bootstrap/LOO and independent OOS. The consumed legacy holdout remains unused. No maximum holding period is imposed.

**Decision:** `CONDITIONAL_PAID_EARLY_RELEASE_DISTRIBUTION_OF_FINRA_SHORT_INTEREST`. No alpha admitted, no purchase/contact, no capture workflow, no production or universe change, and F80 remains frozen.

## 7. Official sources

1. NYSE Group Short Interest product page: https://www.nyse.com/data-products/catalog/nyse-group-short-interest
2. NYSE Group Short Interest Client Specification v1.7 (2025-04-10): https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Client_Specification_v1.7.pdf
3. NYSE Group Short Interest Calendar (2025–2026): https://www.nyse.com/publicdocs/nyse/data/NYSE_Group_Short_Interest_Calendar.pdf
4. FINRA Developer Center documentation, Consolidated Short Interest dataset (available by 4:40 p.m. ET): https://developer.finra.org/docs
5. FINRA 2026 Short Interest Reporting calendar: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
6. SEC Release 34-94313, *Short Position and Short Activity Reporting by Institutional Investment Managers* (2022-03-16), section II.B: https://public-inspection.federalregister.gov/2022-04670.pdf
7. FINRA Short Interest Reporting FAQ (2022-10-27): https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest/faq
8. Public NYSE sample directory: https://ftp.nyse.com/Reference%20Data%20Samples/NYSE%20GROUP%20SHORT%20INTEREST/

## 8. Reproducibility

- Code: `phase269_nyse_group_short_interest_pit_gate.py`
- Tests: `test_phase269_nyse_group_short_interest_pit_gate.py`
- Hosted workflow: `.github/workflows/phase269_nyse_group_short_interest_pit_gate.yml`
- Output: deterministic metadata-only JSON artifact.

This phase is a public-specification feasibility audit only. No subscription data were downloaded, no vendor was contacted, and no return labels or alpha tests were used.
