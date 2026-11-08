# Phase 224 — SEC Companyfacts vs. accession-specific XBRL for PIT shares outstanding

**Date:** 2026-11-08  
**Disposition:** COMPANYFACTS IS A PARTIAL PIT SOURCE; RAW AS-FILED XBRL IS REQUIRED FOR CLASS-SPECIFIC COVERAGE  
**Research class:** source feasibility / measurement audit only. No forward returns or alpha test.

## Executive decision

The SEC Companyfacts API is a credible, free, low-latency source for historical shares-outstanding observations **only when the relevant fact applies to the filing entity as a whole**. It is not a universal solution for Form 144 denominators.

The SEC says its XBRL APIs aggregate standard-taxonomy facts that apply to the entire filing entity. The EDGAR Filer Manual separately requires a DEI shares-outstanding fact for each class in periodic filings; when an issuer has multiple classes, those facts must use explicit class dimensions. Those dimensioned facts do not satisfy the Companyfacts API's entity-wide scope. Therefore:

1. Use Companyfacts as a discovery and entity-wide baseline for verified single-class issuers.
2. For multi-class issuers, retrieve the exact accession-specific 10-K/10-Q/20-F/40-F instance and parse the class-dimensioned DEI fact.
3. Map the Form 144 security description to the exact XBRL class member. If that mapping is not deterministic, the denominator is UNKNOWN.
4. Never treat a missing Companyfacts observation as zero or as proof that no class-specific fact exists.

This is a useful path forward for Form 144, but it does **not** yet pass historical coverage or class-identity gates. No API sample was downloaded in this phase.

## 1. Immutable Form 144 panel inspected

Source: Phase 69, run 41959603351, artifact 13385365595.

- Artifact ZIP SHA-256: **f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519**
- Expanded issuer-event CSV SHA-256: **7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659**
- 21,634 unique accessions; 21,863 sale tranches.
- 289 issuer CIKs and 4,162 distinct seller-name strings.
- 170 exact security-class text labels and 915 issuer-CIK / exact-class-text pairs.
- 233 issuers have more than one exact class-text label. This is a **text-normalization diagnostic**, not a count of actual multi-class issuers; spelling, punctuation and filer wording create false splits.
- The panel includes ADR/ADS, ordinary-share and subordinate-voting descriptions. Those must not be silently equated with a US common-share class.

The class-description burden is material: a CIK-only join is insufficient for a class-specific shares denominator.

## 2. Official SEC source contract

The SEC EDGAR API documentation states:

- data.sec.gov submissions and XBRL APIs do not require authentication or API keys.
- XBRL APIs include standard taxonomies such as DEI and aggregate facts that apply to the entire filing entity.
- API JSON is updated as filings are disseminated; the SEC reports typical XBRL API processing under one minute, with possible longer delays during peak periods.
- Bulk Companyfacts ZIP files are republished nightly, approximately 3:00 a.m. ET.

Source: https://www.sec.gov/search-filings/edgar-application-programming-interfaces

The current EDGAR Filer Manual, Volume II, §6.5.26, requires a non-empty DEI EntityCommonStockSharesOutstanding fact for each class in the specified periodic filing types. For issuers with multiple common-stock classes, the fact must be in a distinct context with a stock-class axis member; a dimensionless entity-wide fact is not the compliant representation for that multi-class case.

Source: https://www.sec.gov/files/edgar/filermanual/archive/efmvol2-v68.pdf

The XBRL instant is the **measurement date**. The filing date/accession is the **public-availability provenance**. They are different clocks and both must be retained.

## 3. Direct filing evidence: multi-class Expedia

The SEC's 2024 Expedia 10-K XBRL instance contains two DEI EntityCommonStockSharesOutstanding facts: 123,333,622 and 5,523,452. The same instance reports EntityPublicFloat in USD (15,649,026,000), not shares.

Source: https://www.sec.gov/Archives/edgar/data/1324424/000132442425000008/expe-20241231_htm.xml

This is consistent with the Phase 223 cross-document control: Expedia's 2026-03-04 Form 144 reported 1,775 shares outstanding, while the latest prior 10-K filed 2026-02-13 reported 117,011,421 common shares plus 5,523,452 Class B shares. The original Form 144 field is not a safe denominator.

Phase 223 source documents:
- Form 144: https://www.sec.gov/Archives/edgar/data/1324424/000162828026014565/xsl144X01/primary_doc.xml
- Prior 10-K: https://www.sec.gov/Archives/edgar/data/1324424/000132442426000008/expe-20251231_htm.xml

## 4. Shares outstanding, public float and ADV are separate measures

- EntityCommonStockSharesOutstanding is a share count, measured at the XBRL instant and tied to a specific class where the filing is multi-class.
- EntityPublicFloat is a monetary value in USD, not a share count. It is not a substitute for class-specific shares outstanding. Its measurement date and age must be retained; it is not a live daily float series.
- ADV is a market-trading-capacity measure and is not supplied by the SEC cover-page share-count fact. It requires a separate historical market-data source with delisted-security coverage and PIT identity.

Do not divide public-float dollars by a later price and call the result contemporaneous float shares. Any derived estimate would need a separately specified measurement-date price, class treatment and error audit. No such estimate is admitted here.

## 5. PIT selection protocol implemented

The reproducible selector enforces:

- exact DEI concept and shares unit;
- eligible periodic filing forms (10-K, 10-Q, 20-F, 40-F, including amendments);
- non-null accession, filing date and measurement instant;
- measurement instant no later than the filing date and event date;
- filing date strictly earlier than the Form 144 filing date. Same-day ordering is unresolved and excluded;
- as-filed amendment treatment: an amendment affects only events after its own filing date;
- latest eligible measurement instant, with the latest filed vintage for that instant;
- conflicting values on the same measurement/filed date produce AMBIGUOUS, never an arbitrary selection;
- missing facts, zero values, wrong units and class mismatches never become a zero denominator.

For a multi-class issuer, the raw accession-specific XBRL parser extracts the explicit stock-class axis member. The caller must supply a deterministic Form 144 class-to-member crosswalk. The parser does not infer that mapping from ticker or issuer CIK.

## 6. Feasibility decision

| Component | Decision |
|---|---|
| Companyfacts, single-class entity-wide fact | Conditional candidate |
| Companyfacts, multi-class issuer | Insufficient alone |
| Accession-specific dimensioned XBRL | Required fallback |
| Form 144 class-text to XBRL member mapping | Unresolved gate |
| EntityPublicFloat as shares denominator | Rejected |
| ADV / trading-capacity denominator | Requires independent PIT market data |
| Full historical coverage of 289 Form 144 issuers | Not measured |
| Alpha / forward-return test | Not authorized |

The Companyfacts API is attractive because it is public, free and updated with filings. But the API's entity-wide scope means it cannot be assumed to cover all class-specific Form 144 events. The next empirical gate must measure actual coverage on a stratified issuer/class sample, including single-class, dual-class, ADR/ADS, foreign issuer and delisted controls.

## 7. Technical implementation and limits

Added:
- a Companyfacts entity-wide PIT selector;
- an accession-specific XBRL DEI shares fact extractor;
- exact class-member selection;
- separate public-float unit classification;
- 15 regression tests covering same-day exclusion, future facts, amendments, conflicting vintages, missing facts, zero values, units, class dimensions and class mismatch.

Local regression suite: **15/15 passed**.

No live SEC API request was sent and no raw Companyfacts response was downloaded. The existing Phase 193 workflow remains fail-closed because SEC_CONTACT_EMAIL is empty. Its latest inspected log confirms zero requests and zero raw filing bytes. Configure an authorized project contact email in GitHub Actions before a reproducible live coverage sample; do not invent a contact identity.

No hosted Phase 224 CI run is claimed. The Phase 224 commits use [skip ci] to avoid triggering the legacy workflow matrix.

## 8. Decision and next gate

**Retain Companyfacts as a partial PIT source; require raw as-filed XBRL for multi-class coverage. Do not admit a Form 144 supply-pressure feature yet.**

Next:
1. After the SEC contact secret is configured, sample the 289 issuer CIKs by year, class-text family and issuer type.
2. Join Companyfacts observations to the exact accession and compare them with raw filing instances.
3. Measure entity-wide fact coverage separately from class-dimensioned raw-XBRL coverage.
4. Build and audit a deterministic class crosswalk from Form 144 descriptions to XBRL members.
5. Report measurement-age distributions and unresolved class/issuer cases before considering any event-return test.
6. Obtain independent PIT ADV and, separately, any float measure; preserve delisted securities and historical listing identity.

No forward returns, feature selection, alpha test, bootstrap/LOO, OOS test or holdout test occurred. No vendor was contacted or purchased. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains CONSUMED_NOT_PRISTINE.
