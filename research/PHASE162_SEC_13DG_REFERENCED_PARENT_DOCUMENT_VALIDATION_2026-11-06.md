# Phase 162 — SEC 13D/G referenced-parent document validation

**Date:** 2026-11-06  
**Status:** COMPLETED — referenced document inspected; no issuer/security parent relationship survives the targeted comparison  
**Scope:** Inspect accession 0001445546-21-002430 and compare its actual SEC filer, subject issuer, security class and CUSIP with the eight Phase 161 child filings that repeat it.

## Executive finding

The referenced accession is a real **initial SC 13G** filed on **2021-05-10 at 09:06:41 ET** by **First Trust Portfolios L.P. (CIK 0001184765)**. The SEC filing-detail page identifies the subject as **First Trust Exchange-Traded Fund VIII (CIK 0001667919)**. The primary document identifies the reported security as **FT Cboe Vest U.S. Equity Deep Buffer ETF - August**, common stock, **CUSIP 33740F854**, with event date 2021-04-30.

The eight Phase 161 child filings all repeat this accession and have the same filer CIK, 0001184765. But:
- Four children have a different issuer CIK.
- Four children share the parent issuer CIK 0001667919 but report four different CUSIPs.
- **Zero of the eight children match the parent's CUSIP.**
- **Zero of the eight children match both parent issuer CIK and parent CUSIP.**

Thus the referenced filing is not a demonstrated issuer/security predecessor for any of the eight child ownership states. The pattern is consistent with a stale or template-level filer reference being reused, but this audit does not prove the software/workflow cause.

## Parent document inspected

Official SEC filing-detail index:
- https://www.sec.gov/Archives/edgar/data/1184765/000144554621002430/0001445546-21-002430-index.html

Official SEC primary document:
- https://www.sec.gov/Archives/edgar/data/1184765/000144554621002430/sc13g_3.txt

The filing-detail index records:
- Accession: 0001445546-21-002430
- Form: SC 13G (not an amendment)
- Filing date: 2021-05-10
- Acceptance: 2021-05-10 09:06:41 ET
- Filed by: First Trust Portfolios LP, CIK 0001184765
- Subject: First Trust Exchange-Traded Fund VIII, CIK 0001667919
- File number: 005-90766

The primary document states:
- Issuer/security: FT Cboe Vest U.S. Equity Deep Buffer ETF - August
- Class: Common
- CUSIP: 33740F854
- Event date: 2021-04-30
- Aggregate amount beneficially owned: 489,449
- Percent of class: 15.06%
- Reporting persons: First Trust Portfolios L.P., First Trust Advisors L.P. and The Charger Corporation
- The filing certifies ordinary-course holding and no control purpose/effect.

## Child comparison

The eight official SEC XML child URLs are retained in the Phase 161 fixture and are reproduced in the Phase 162 CSV. The targeted set includes:
- First Trust Exchange-Traded Fund VIII series with CUSIPs 33740F342, 33740F466, 33740F680 and 33740U687;
- Morgan Stanley Emerging Markets Domestic Debt Fund (617477104);
- abrdn Australia Equity Fund (003011111);
- Winmark Corporation (974250102);
- BNY Mellon Strategic Municipal Bond Fund (09662E109).

All child XMLs use filer CIK 0001184765 and repeat previousAccessionNumber 0001445546-21-002430. The parent CUSIP 33740F854 is absent from all eight children.

| Comparison | Count |
|---|---:|
| Children with same previous accession | 8/8 |
| Children with same filer CIK | 8/8 |
| Children with same issuer CIK | 4/8 |
| Children with different issuer CIK | 4/8 |
| Children with same CUSIP | 0/8 |
| Exact issuer-CIK + CUSIP match | 0/8 |

The four same-CIK cases are not treated as security continuity: the parent and child security identifiers differ, and no effective-dated corporate-action or series/CUSIP bridge was supplied. A shared registered-fund CIK does not make different ETF series the same security.

## Decision and state-machine consequence

For this targeted group:
1. Keep previousAccessionNumber as raw filing provenance.
2. Do not create parent-child ownership-state edges from this field.
3. Do not backdate any child disclosure to 2021.
4. Require issuer identity and effective-dated security identity (CUSIP/class, including documented corporate-action bridges) before accepting a parent link.
5. A same filer, same form family, earlier filing date or same issuer CIK alone is insufficient.

This supersedes Phase 161's unresolved statement that the exact cause of the reused pointer was unknown: the referenced document is now known. It does **not** establish why the filer software reused the value, nor does it establish the prevalence of this issue outside the targeted eight-child set.

## Reproducibility and limitations

- Parent SEC filing-detail index and primary text were inspected through official SEC archive pages.
- Child rows and source URLs are inherited from the Phase 161 targeted official-SEC XML fixture.
- The fixture is manually transcribed; raw parent/child response bodies and per-document SHA-256 hashes are not embedded. CI validates the recorded facts and deterministic comparison, not live SEC source integrity.
- Targeted, non-random sample; no population prevalence estimate.
- No broad SEC download, forward returns, feature panel, bootstrap/LOO, OOS test, final holdout, vendor contact/purchase or production change.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.

## Next gate

Validate all 32 Phase 160 previous-accession references against their actual parent submissions and effective-dated security identities. Do not extrapolate this one targeted counterexample to all filers or all 13D/G amendments. For the 27 structured amendments without an explicit previous accession and legacy HTML amendments, keep parent reconstruction unresolved until an independent document-level method is validated.
