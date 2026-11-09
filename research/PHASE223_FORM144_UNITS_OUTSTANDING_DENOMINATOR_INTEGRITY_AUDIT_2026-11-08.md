# Phase 223 — Form 144 units-outstanding field integrity and denominator audit

**Audit date:** 2026-11-08  
**Disposition:** SOURCE FIELD PRESERVED; NOT ADMITTED AS A UNIVERSAL SHARES-OUTSTANDING DENOMINATOR  
**Research class:** data-quality / measurement audit only; no return test

## Executive result

The Phase 69 Form 144 panel is numerically parseable, but the Form 144 field units_outstanding is not sufficiently reliable to serve as a denominator for proposed-sale pressure.

The audit reprocessed the immutable Phase 69 expanded issuer-event CSV (21,634 accession rows; 21,863 sale tranches). It found zero missing numeric values in the three parsed fields, but seven zero reported-outstanding values, four positive values below 10,000, six positive proposed sales with a zero denominator, and two finite cases where proposed units exceed the reported outstanding count.

Among 3,342 same-issuer / normalized-class / filing-date groups containing at least two accessions, **222 groups (6.64%) report conflicting outstanding counts**. These conflicts affect 669 tranches, 660 accessions and 90 issuers. Eighteen groups have at least a 90% relative spread; observed scale inconsistencies include approximately 10x, 100x and 1,000,000x.

Two official SEC primary-document checks independently confirm that the problem is not merely a parser artifact:
- A Celestica Form 144 filed 2026-03-23 reports 39,492 shares proposed for sale and zero shares outstanding.
- An Expedia Form 144 filed 2026-03-04 reports 1,775 common shares outstanding, while the issuer's latest prior 10-K, filed 2026-02-13, reports 117,011,421 common shares outstanding as of 2026-01-30 (plus 5,523,452 Class B shares).

**Decision:** preserve the field for forensic context, but never use it directly as the denominator of a Form 144 supply-pressure feature. Use an independently reconstructed, class-specific, point-in-time shares-outstanding value from the latest issuer report publicly filed before the event. Shares outstanding, public float and ADV are distinct denominators and must not be substituted for one another.

## 1. Immutable input and reproducibility

| Item | Value |
|---|---|
| Source workflow run | 41959603351 |
| Source artifact | 13385365595 |
| Artifact ZIP SHA-256 | f84644200a8925c6fc190a823ca0dcd6b40c7bee127a8d2740a5ea67cae56519 |
| CSV member | expanded_issuer_event_raw.csv |
| Expanded CSV bytes | 67,014,714 |
| Expanded CSV SHA-256 | 7a54ee09e8d4520e1ec14cf22f2c0d1c62d077798b14d3db596826e3360a3659 |
| Accession rows / unique accessions | 21,634 / 21,634 |
| Parsed sale tranches | 21,863 |

The ZIP and expanded CSV hashes were recomputed after downloading the original GitHub Actions artifact. The audit script refuses a different CSV hash or row count.

## 2. Tranche-level field diagnostics

| Diagnostic | Count |
|---|---:|
| Missing units-to-be-sold values | 0 |
| Missing aggregate-market-value values | 0 |
| Missing units-outstanding values | 0 |
| Zero units-to-be-sold | 2 |
| Zero aggregate market value | 3 |
| Zero units outstanding | 7 |
| Positive units outstanding below 10,000 | 4 |
| Positive sale with zero outstanding denominator | 6 |
| Finite sale/outstanding ratios above 100% | 2 |
| Raw ratios above 1% (including zero-denominator infinities) | 105 |
| Raw ratios above 10% (including zero-denominator infinities) | 19 |
| Raw ratios above 100% (including zero-denominator infinities) | 8 |

The eight raw ratios above 100% comprise six undefined/infinite ratios caused by a zero denominator and two finite ratios using positive but implausibly small denominators. They must not be interpreted as actual economic percentages.

## 3. Same-day cross-filer consistency

The audit groups tranche rows by exact issuer CIK, normalized security-class text and SEC filing date. It does not merge different issuers or different class labels.

| Diagnostic | Result |
|---|---:|
| Groups with at least two accessions | 3,342 |
| Groups with conflicting outstanding values | 222 |
| Conflict rate | 6.64% |
| Tranches in conflict groups | 669 |
| Unique accessions affected | 660 |
| Unique issuers affected | 90 |
| Conflict groups with relative spread above 1% | 84 |
| Conflict groups with relative spread above 10% | 56 |
| Conflict groups with relative spread at least 90% | 18 |
| Approximate 10x / 100x / 1,000,000x scale conflicts | 8 / 2 / 1 |

These are internal consistency diagnostics, not proof that every conflict is a filer error: class descriptions can be generic and the panel does not yet provide a deterministic effective-dated security-class key. Nevertheless, the frequency and magnitude of conflicts make the field unsuitable as an unqualified denominator.

### Illustrative same-day panel conflict

For Workday (issuer CIK 0001327811), six Form 144 accessions filed on 2023-07-05 for the normalized Common class report both 261 and 261,000,000 as units outstanding. The 1,000,000x scale discrepancy is preserved as a panel-level anomaly; the 261 entry is not silently rescaled.

## 4. Official SEC source cross-checks

### 4.1 Celestica — zero reported shares outstanding

The SEC primary Form 144 for accession 0001628280-26-020559, filed 2026-03-23, reports:
- Common Stock;
- 39,492 shares to be sold;
- aggregate market value USD 10,818,563;
- **zero** shares outstanding.

[SEC primary Form 144](https://www.sec.gov/Archives/edgar/data/1030894/000162828026020559/xsl144X01/primary_doc.xml) (source lines 33–37 in the filing rendering).

### 4.2 Expedia — irreconcilable with the latest prior issuer report

The SEC primary Form 144 for accession 0001628280-26-014565, filed 2026-03-04, reports:
- Expedia Common (EXPE);
- 8,225 shares to be sold;
- aggregate market value USD 1,815,891.63;
- **1,775** shares outstanding.

[SEC primary Form 144](https://www.sec.gov/Archives/edgar/data/1324424/000162828026014565/xsl144X01/primary_doc.xml) (source lines 32–37).

The latest prior issuer 10-K was accession 0001324424-26-000008, filed 2026-02-13. Its cover page reports 117,011,421 common shares and 5,523,452 Class B shares outstanding as of 2026-01-30. The common-share count is approximately 65,922 times the Form 144 value.

[SEC 10-K filing detail](https://www.sec.gov/Archives/edgar/data/1324424/000132442426000008/0001324424-26-000008-index.htm)  
[SEC 10-K cover page](https://www.sec.gov/Archives/edgar/data/1324424/000132442426000008/expe-20251231.htm) (source lines 71–73).

This is a direct cross-document contradiction, not a later-data comparison: the 10-K was publicly filed before the Form 144.

## 5. Regulatory meaning and interpretation

The SEC Form 144 instructions define Item 3(e) as the number of shares or other units of the class outstanding **as shown by the most recent report or statement published by the issuer**. The form does not make this a live transfer-agent count, a public-float measure, an ADV measure or a guarantee that the filer-entered value is accurate.

[SEC Form 144 and instructions](https://www.sec.gov/divisions/corpfin/forms/144.htm), Item 3(e), lines 103–109.

Therefore:
- retain the original value and accession for auditability;
- do not silently repair, scale or winsorize it;
- if independently reconstructed shares outstanding are unavailable, set the denominator to UNKNOWN;
- use the correct security class and the latest issuer report that was public before the Form 144 filing date;
- separately obtain PIT public float and PIT ADV if measuring proposed-sale pressure relative to float or trading capacity;
- never backfill a later 10-Q/10-K share count into an earlier event.

## 6. Admission decision

**Passed:** immutable source artifact and CSV hash; accession uniqueness; tranche parsing; numeric-field inventory; deterministic same-day conflict calculation; official SEC cross-checks.

**Not admitted:**
- Form 144 units_outstanding as a universal shares-outstanding denominator;
- units_to_be_sold / units_outstanding as a model feature;
- any return/alpha test based on this denominator.

The field remains available as raw source context only. Form 144 still requires historical issuer/security-class/listing identity, seller identity continuity, a broad historical active/delisted universe, independent PIT shares outstanding/float/ADV and proposed-versus-completed-sale semantics before a supply-pressure feature can be tested.

No forward returns, bootstrap/LOO, OOS or holdout test was run. No vendor was contacted or purchased. No production or universe change occurred. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; the legacy holdout remains CONSUMED_NOT_PRISTINE.

## Reproducibility

- Audit: research/phase223_form144_units_outstanding_integrity_audit.py
- Tests: research/test_phase223_form144_units_outstanding_integrity_audit.py
- Machine result: research/phase223_form144_units_outstanding_integrity_audit_result.json
- Source is downloaded from immutable Phase 69 run/artifact IDs and checked by SHA-256.
- Local regression suite: 9/9 passed.
