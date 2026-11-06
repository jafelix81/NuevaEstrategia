# Phase 166 — SEC 13(f) cross-format content and PIT metadata bridge

**Date:** 2026-11-06  
**Status:** Cross-format/PIT reconciliation passed in the initial CI run; a follow-up run adds unique-CUSIP coverage to the summary.  
**Research role:** Historical Section 13(f) eligibility/identity cross-check for the SEC 13D/G sample only; not a 13F holdings signal.

## 1. Inputs and preflight

Before this phase, the latest Phase 163/164 regression runs and the completed Phase 149 OpenFIGI run had passed. The branch inventory was paginated (129 branches), PR #13 was open/mergeable/unmerged, and no workflow was duplicated.

Phase 165 produced two successful 45-quarter runs:

- [All-PDF run 42278015855](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42278015855): 45/45 snapshots, PDF content and PDF metadata.
- [TXT-first corrected run 42278657127](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42278657127): 45/45 snapshots; 25 TXT and 20 PDF content snapshots, with corrected CUSIP check-digit validation and fixed-width TXT decoding.

Both runs used the same immutable 599-filing Phase 124/127 sample. It contains 571 valid filing rows and **553 unique valid CUSIPs**. Phase 166 downloads only the compact shard artifacts and sample input. It makes no SEC network requests and does not persist raw 13(f) list rows or CUSIPs.

## 2. Cross-format sample concordance

The per-accession/per-quarter match booleans were compared across both Phase 165 runs:

| Content source in corrected run | Quarters | Sample comparisons | Concordant | Disagreements |
|---|---:|---:|---:|---:|
| TXT, compared with the all-PDF run | 25 | 14,275 | **14,275** | 0 |
| PDF, PDF run repeated | 20 | 11,420 | 11,420 | 0 |
| Total | 45 | 25,695 | **25,695** | 0 |

The 14,275 TXT-versus-PDF comparisons are the independent format cross-check. The 11,420 PDF-versus-PDF comparisons are repeatability checks, not independent format validation.

This establishes 100% **sample-level match concordance** for the 571 valid Phase 127 filing rows across all 45 quarters. It does not prove byte-for-byte or full-universe equality of the TXT and PDF files.

## 3. Critical PIT finding: TXT Last-Modified is often an archive migration date

The corrected TXT-first run initially used each TXT file's HTTP Last-Modified as its only timestamp. That is not a valid historical availability proxy for many archives:

- **22 of 25 TXT snapshots** have Last-Modified dates of 2026-09-04, more than a year after the quarter represented.
- These historical files were evidently re-hosted/re-published in a later archive migration; the header records the later file modification, not the original quarterly list's first public availability.
- Three more recent TXT files have dates closer to their quarter, but they still do not establish first-publication time.
- The all-PDF run contains **three** 1970-01-01 Last-Modified sentinels; Phase 166 ignores all three.

Using TXT Last-Modified naively yields a 5-day match rate of **67.78%** (weighted 74.72%) and 132 lookahead-only matches. Those results are materially distorted by the archive migration and are superseded.

Phase 166 instead bridges the corrected run's content match booleans to the all-PDF run's historical PDF Run Date metadata. It uses the later of PDF Run Date and a non-sentinel PDF Last-Modified, then applies +2/+6 calendar-day sensitivities. This remains a **conservative proxy, not verified first-publication time**.

## 4. Re-adjudicated historical overlap

Using the PDF timestamp bridge and the corrected TXT/PDF content matches:

| Availability sensitivity | Matches | Rate | Sample-weighted rate |
|---|---:|---:|---:|
| PDF Run Date + 2 calendar days | 478 / 571 | **83.71%** | 90.13% |
| PDF Run Date + 6 calendar days | 478 / 571 | **83.71%** | 89.94% |
| Same-quarter list (lookahead diagnostic only) | 511 / 571 | 89.49% | 93.03% |

The 1-day and 5-day sensitivities have the same aggregate match count, but **two filing rows change status** between them. The same-quarter list produces **41 lookahead-only matches** relative to the 5-day proxy. It must remain a diagnostic, never an available signal.

By filing family under the 5-day proxy:

- SC 13D: 140/195 = 71.79%; weighted 76.48%.
- SC 13G: 338/376 = 89.89%; weighted 92.73%.

### Unique-security rather than filing-row coverage

Deduplicating the 571 valid filing rows by CUSIP gives **553 unique securities**. The first-observed filing, last-observed filing and any-observed filing views each produce **460/553 = 83.18%** with a prior 5-day-proxy list match. The 18 repeated CUSIPs have consistent 5-day match status across their repeated filings.

This avoids overstating coverage by counting repeated filings as independent securities.

## 5. CUSIP check-digit diagnostic: do not over-filter the 13(f) list

The corrected TXT parser yields 25 TXT snapshots with 303,450 unique identifiers, of which 283,581 pass the standard equity CUSIP check-digit test (93.45%). The 2020Q1–2025Q4 TXT snapshots individually conform at 100%; the two 2026 TXT snapshots have lower conformance:

- 2026Q1: 12,792 / 22,659 = 56.45%.
- 2026Q3: 13,717 / 23,719 = 57.83%.

The official [2026Q3 TXT list](https://www.sec.gov/files/investment/13flist2026q3.txt) explicitly contains CALL and PUT series rows (including CMB.TECH NV CALL/PUT entries) whose 9-character identifiers do not pass the standard equity CUSIP check-digit test. Therefore, a nonconforming identifier is not automatically a malformed row; the check-digit metric is diagnostic, not a universal exclusion rule.

The PDF parser produces a much larger candidate set and lower check-digit conformance (180,228 / 354,493 = 50.84% across 20 PDFs). That candidate count is not used as a clean full-list security count. Sample match booleans are retained only after the TXT/PDF sample concordance check.

## 6. Corrections made during Phase 165

Two defects were found and corrected before the second successful run:

1. The Phase 129 wrapper compared the boolean returned by the tested Phase 125 CUSIP validator with a string check digit, so the first Phase 165 PDF run reported zero checksum-valid list identifiers. Phase 165 now calls the Phase 125 boolean validator directly. The first run's sample match booleans were exact-string membership checks against already validated sample CUSIPs; the second run independently confirmed them.
2. SEC TXT responses were compressed when the request advertised gzip/deflate. The first parser attempt did not decode the response and fell back to PDF. Phase 165 now requests identity encoding and defensively decodes gzip/deflate before fixed-width parsing.

The first CI attempt also exposed a newline-escaping error in a test fixture; the fixture was corrected and the second run completed successfully.

## 7. Decision and limitations

- Use corrected TXT content for 2020+ where available, after the 14,275/14,275 sample concordance.
- Use PDF Run Date and non-sentinel PDF Last-Modified only as historical timestamp proxies; never use the 2026-09-04 TXT migration header as the historical release date.
- Keep +2/+6 dates as sensitivity proxies only. First-publication time remains unverified.
- Treat the 13(f) list as a Section 13(f) reportability/identity cross-check, not as evidence of holdings, informed trading or institutional intent.
- The sample is a stratified 13D/G sample, not the 335-ticker or full historical F80 universe. No general universe coverage claim follows.
- No forward-return, signal, bootstrap/LOO, OOS or final-holdout test was performed.

## Phase 166 implementation

- `research/phase166_sec13f_cross_format_pit_bridge.py`
- `research/test_phase166_sec13f_cross_format_pit_bridge.py`
- `.github/workflows/phase166_sec13f_cross_format_pit_bridge.yml`

The workflow reconciles existing Phase 165 artifacts only. It downloads no SEC list files.

## Official SEC references

- [Official List of Section 13(f) Securities and archive links](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities)
- [2015Q3 official PDF](https://www.sec.gov/divisions/investment/13f/13flist2015q3.pdf)
- [2020Q1 official TXT](https://www.sec.gov/files/investment/13flist2020q1.txt)
- [2026Q3 official TXT](https://www.sec.gov/files/investment/13flist2026q3.txt)

**Strategy decision:** no alpha demonstrated, no vendor purchase/contact, no production change, no final holdout use. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
