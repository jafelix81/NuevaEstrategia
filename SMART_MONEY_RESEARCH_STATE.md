# Smart Money Research State

Updated: 2026-11-04 (Phase 35 cross-quarter lineage audit; Phase 50 review)

## Frozen control
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
- MOM120 is a validated control candidate but not promoted: realized portfolio metrics slightly exceeded LTM, but incremental daily excess was small and the block-bootstrap CI included zero.

## Phase 31 — FINRA short-flow × short-interest divergence
- Status: KILLED as independent alpha.
- Valid OOS run: 40164323397.
- PIT: short flow through signal close; short interest only after conservative knowledge date.
- Result: horizon-dependent sign reversal; economic spreads' bootstrap intervals included zero. Do not tune horizons to rescue.

## Phase 21C — SEC Form 4 insider transactions
- Status: KILLED as a standalone signal in the current frozen-universe diagnostic.
- Run 39369692938 completed successfully with 24 training signal dates and 6 untouched final OOS dates (2025-02-25 through 2026-09-29).
- Official SEC dataset coverage is strong from 2016Q1 through 2026Q3; 301/335 universe CIKs mapped in the current implementation. KnowledgeDate uses filing date and downstream requires KnowledgeDate < SignalDate; same-day filings are excluded.
- Training-selected features were BUY_DAYS20 (H5), BUY_EVENTS60 (H10), and BUY_ADTV20 (H20). Final OOS mean top-minus-bottom was -0.12% (H5), +0.65% (H10), and -0.46% (H20); all bootstrap 95% CIs included zero. Residualized Spearman means were negative at all three horizons (-6.33%, -2.54%, -2.99%).
- Decision: do not tune insider features/horizons to rescue this implementation. Reuse only for a materially different, pre-registered mechanism.

## Phase 22C — SEC 13F feasibility
- Status: NOT PRODUCTION-READY; identity-resolution research only if it materially improves worst-period coverage without lookahead.
- Latest run 41652405078 (2026-11-03) succeeded. Coverage remains 70.43% (2016Q1), 81.73% (2020Q1), and 93.02% (2024Q1); ambiguous candidates remain 51, 37, and 19 respectively. Conclusion: `INSUFFICIENT_COVERAGE_FOR_PRODUCTION`.
- Earlier PIT issuer/CUSIP audit produced minimum 54.8% coverage in 2016Q1. Direct PIT CUSIP is preferable to name fuzzy matching but still has class/ADR/legacy-CUSIP ambiguity.
- This is a data-identity feasibility result, not evidence against 13F economically. Park unless a deterministic security identity method materially improves the worst-quarter coverage.

## Phase 23C — CFTC COT positioning
- Status: KILLED for the tested equity-index positioning hypothesis.
- Run 39375172026 completed with 12 walk-forward test dates for NASDAQ and S&P 500 families.
- NASDAQ mean strategy return was +0.192% at H5 versus +0.890% unconditional and -0.460% at H20 versus -3.370% unconditional. S&P 500 mean strategy return was -0.049% at H5 versus +1.024% unconditional and -3.058% at H20 versus -1.443% unconditional; H20 hit rate was 16.7% for S&P 500.
- Decision: no robust incremental equity-selection edge; archive rather than optimize.

## Phase 24B — public listed-options historical feasibility
- Status: public OCC endpoint path is insufficient for event-level historical option-flow research.
- Run 39398787569 tested 11 historical sample dates. Contract-volume, DLP HTTP, and trade-volume endpoints returned effectively empty payloads; daily volume statistics were substantive, while volume-by-account-type was substantive on only 2/11 samples.
- Decision: do not infer historical options flow/OI/IV/skew from these endpoints.

## Phase 27O — SEC N-PORT institutional holdings dose-response
- Status: KILLED in the tested dose-response form.
- Run 39503800069 covered six annual formation periods (2020Q4–2025Q4) using the PIT 27N2 share-accumulation signal and fixed 63-trading-day forward return.
- Top-minus-bottom decile returns were -11.77%, -5.56%, +12.03%, +6.12%, -4.78%, and -1.74%; sign is not stable and no monotonic institutional-flow effect is established.
- Decision: do not optimize dose threshold or horizon.

## Phase 32 / 42B — market microstructure and SEC MIDAS
- Event-level historical order/quote data remain commercially licensed; do not synthesize them from inadequate aggregates.
- SEC MIDAS Metrics by Individual Security has quarterly history from 2012Q1 through 2026Q2 and useful daily security-level fields. However, no per-quarter first-publication timestamp was verified. Uniform 2/3/4-month lag sensitivity is exploratory only, not proof of PIT. Alpha authorization remains FALSE pending archived index snapshots or timestamped official publication evidence.

## Phases 43–45 — SEC fails-to-deliver (FTD)
- Phase 43 actual-file parser gate passed (runs 40800732551 and 40809120246): representative 2018/2026 files contained 43,567 and 66,693 records; SEC trailer counts/quantities reconciled, with no exact duplicate rows or missing CUSIPs.
- Phase 44 representative universe coverage was 253/335 (75.52%) in 2018 and 316/335 (94.33%) in 2026; 332/335 were observed in at least one sample.
- Phase 45 PIT identity gate (run 40973633206) found only 207/335 names observed in all five samples (61.79%); 21 of those 207 had changed/unresolved 2018–2026 CUSIP continuity. Crucially, absence from an FTD file cannot distinguish an active security with zero fails from an inactive/unlisted security.
- Decision: PARK FOR PUBLIC-DATA ALPHA. Restricting to always-observed names would create survivorship/selection bias. Reopen only with a deterministic historical security master/listing-status panel with PIT-effective dates. FTD is an aggregate balance, not a daily flow and not proof of naked short selling.

## Phase 46 / 52 — Cboe options data
- Public monthly symbol-level equity-option volume actual-file audit (run 40841944879) parsed successfully, but minimum frozen-universe coverage was 64.48%, below the predeclared 70% gate; representative 2019 samples were 69.55% and 71.04%. Historical release timestamps were also not available. Decision: KILL the public aggregate-volume candidate for this frozen-universe line.
- Cboe Trade-by-Trade (TBT) is materially richer: participant origin, side, open/close, contract, price, size and NBBO context; historical availability begins 2019-10-07. But the documented proposed price is $12,000/month, with $8,000/month ad-hoc historical access. Decision: PARK — commercial access required; no alpha test until licensed reproducible data is available.

## Phase 35/49 — initial submissions-by-CIK sample (superseded)
- Status: **INVALID FOR SUBJECT-ISSUER COVERAGE; no economic test authorized.** The 20,266-row submissions-by-CIK artifact is a filer-side retrieval sample, not a global subject-issuer census. Its issuer counts, ticker coverage, reporting-person coverage, and first-event diagnostics must not be used. The corrected subject-side discovery route is the global master-index + primary XML pilot documented below.
- Latest workflow run 41652405132 completed successfully (job 125973726145; artifact 13256930771). It retrieved 20,266 rows, but the artifact issuer_cik field is not consistently the subject issuer CIK. The reported 303 "issuers" are not validated subject-issuer counts.
- Root cause: submissions_for_cik() stores the ticker-mapped query CIK as issuer_cik; extract_fields() only searches the legacy text label CENTRAL INDEX KEY and falls back to that query CIK. Schedule 13G XML uses issuerCik, so the fallback can assign a reporting-person CIK as the subject issuer.
- Concrete artifact defect: accession 0000092230-25-000015 is assigned to TFC / CIK 0000092230, but its SEC XML identifies subject issuer Federated Hermes ETF Trust / CIK 0001849998 and reporting person Truist Financial Corp. The XML also contains exact previousAccessionNumber=0000092230-25-000001.
- There are 7,858 XML 13G rows (2024–2026) at risk pending subject-CIK re-extraction. All 7,858 have null reporting_person in the old artifact because its parser does not handle the 13G-specific coverPageHeaderReportingPersonDetails schema. The 437 XML 13D rows and legacy HTML/TXT rows also require a subject-CIK consistency audit; do not assume them correct.
- Consequently, current ticker coverage, unique-issuer counts, 13G ownership field coverage, and the earlier accession-prefix sequence counts are not valid issuer-level or economic-group statistics. The previous 3,115 sequences / 58.5% amendment-first diagnostic is superseded.
- The latest artifact still contains two future event_date values (MS filings 2024-02-09 and 2024-02-12 with event date 2024-12-31); event_date is not PIT-certified. Use filing_date only as KnowledgeDate after subject attribution is validated.
- A schema-aware parser prototype and five local unit tests are in branch phase35-13dg-issuer-attribution-repair; all five tests pass on synthetic fixtures modeled on SEC XML/index structures. It is not yet integrated or run against the full artifact.
- Next gate: reparse every XML 13G row for issuerCik; validate all XML 13D and stratified legacy rows; preserve query_cik, archive_path_cik, filed_by_cik, subject_issuer_cik, reporting-person IDs/names, and submission_cik as separate fields; deduplicate by accession; follow exact previousAccessionNumber links; rebuild historical issuer-universe coverage; then normalize events. No forward returns before these gates pass.
- Decision: **retrieval complete, issuer attribution failed, event normalization blocked, no alpha claim.** No change to F80_TOP20_PARTIAL50_BASELINE_C20.

## Current priority
- Keep `F80_TOP20_PARTIAL50_BASELINE_C20` frozen.
- Do not spend further cycles rescuing killed FINRA, Form 4 standalone, CFTC COT, N-PORT dose-response, public aggregate options volume, or public FTD without a historical security master.
- Continue 13D/13G only through corrected reporting-group identity and complete historical predecessor chains. MIDAS remains a conditional public-data candidate only if PIT publication dates can be verified. Cboe TBT remains conditional on commercial licensing.
- No source has earned alpha promotion in this cycle.

## Research principle
“Smart money” is a hypothesis, not an assumption. Every candidate must pass historical coverage, ex-ante availability, PIT timestamps, universe overlap, incremental-information, chronological OOS, bootstrap and LOO tests before portfolio promotion.


## Phase 35 source-census redesign — 2026-11-03
- **New structural finding:** the old pipeline queried the SEC submissions endpoint using the 307 ticker-mapped CIKs. That endpoint returns submissions made by the queried CIK (the filer/submitting entity), not a census of filings whose subject issuer is that CIK. Thus the old 20,266-row artifact is a filer-side sample, not an issuer-side 13D/13G universe. Parsing issuerCik fixes row attribution but cannot recover target-issuer filings that were never in the queried filer submissions.
- SEC filing detail pages expose distinct Filed-by and Subject entities. The reproducible Truist/Federated example shows Filed by CIK 0000092230 and Subject CIK 0001849998; the same separation appears in the SEC FMR/Sandisk filing detail page.
- Correct discovery path: scan each quarter's global EDGAR master.idx for SC 13D, SC 13D/A, SC 13G and SC 13G/A; fetch each filing detail index page; parse Filed-by and Subject CIK/name separately; filter on Subject CIK. Cross-check structured XML issuerCik/issuerCIK where available.
- The global index's CIK column is still the filer. It must never be treated as the subject issuer. The filing index page's Subject CIK is the primary legacy-compatible identity source; XML issuerInfo is an independent cross-check.
- Parser v3 corrects 13G field names and nesting: reportingCik (not reportingPersonCIK), memberGroup (not memberOfGroup), issuerInfo/issuerCik, and issuerCusips/issuerCusipNumber. A CIK-set fingerprint is only a reporting-person-set checksum, not an economic-group key.
- Parser v3 has six local unit tests covering 13D, 13G, SEC filing-index Filed-by/Subject metadata, master.idx filtering, and conservative person-set hashing. These are synthetic/schema fixtures, not full-artifact validation.
- New pilot: 2025Q1 global master-index census. It must parse at least 95% of Subject CIKs, pass the known Truist/Federated accession fixture, and report target-subject counts separately from target-filer counts. No forward returns.
- The pilot's 335-name CIK list uses current SEC ticker mapping plus fallback mapping only as a candidate set. It is not historical active-universe membership. Historical ticker/CIK continuity, delistings, predecessor chains, and reporting-group identity remain separate gates.
- The previous 20,266-row artifact, its 303 purported issuers, and ticker/form coverage statistics remain uncertified and must not be used for event counts, first-event claims, or alpha tests.
- Full census must extend back to the earliest usable EDGAR full-index history (1993 archive onward where available) to reduce left-censoring. If complete predecessor history cannot be established for a filer/subject pair, classify as left-censored; do not call it a true first event.
- Current state: parser prototype and global-census pilot are on this isolated branch; no main-branch workflow has been launched. F80 remains frozen.


## Pilot execution status
- The first hosted global-census run, 41707588968, completed with a validation failure after both test suites passed. Job 126166891297 fetched 1,306 filing-detail pages with zero HTTP errors, but the HTML parser extracted zero Subject CIKs and zero Filed-by CIKs, including the fixed Truist/Federated fixture. Artifact 13267337601 is preserved; its summary correctly reports FAILED_VALIDATION.
- The failure is a page-parser representation mismatch, not missing SEC filings. The master.idx census and candidate selection succeeded: 16,629 13D/G rows, 8,318 accessions, 1,100 target-relevant accessions, and 206 non-target validation accessions.
- A second pilot now uses each accession's candidate archive paths to fetch structured primary_doc.xml directly. It parses subject issuer CIK separately from the XML submission-filer CIK and retains reporting persons and previousAccessionNumber. The new script and tests are on this isolated branch.
- The branch-only workflow is being updated to run the XML pilot; its concurrency group has cancel-in-progress=false so a queued run will not overlap/replace an active run. No main-branch workflow or F80 code is changed.


## 2026-11-03 — 2025Q1 global master-index feasibility result
- The first pilot attempts exposed two implementation errors, not missing SEC data: raw master.idx uses SCHEDULE 13D/G and SCHEDULE 13D/G/A labels as well as SC variants; and filing-detail archive URLs require the accession-number subdirectory. The parser and URL construction are corrected in the isolated branch.
- The saved 2025Q1 master.idx is 30,623,221 bytes / 340,137 lines. It contains 16,629 13D/G rows after form normalization: 4,460 13G, 9,230 13G/A, 538 13D, 2,394 13D/A, and 7 SC 13D/A.
- Grouping by accession produces 8,318 unique accessions: 8,311 have two associated CIK/name rows and 7 have one. Known pairs: 0000092230-25-000015 maps to Federated Hermes ETF Trust (0001849998) and Truist Financial Corp (0000092230); 0000315066-25-000987 maps to Sandisk Corp (0002023554) and FMR LLC (0000315066).
- The master-index CIK pairs are not role-labelled. The pilot must verify Subject and Filed-by from the filing-detail page; row order is not used. The revised pilot fetches all accessions associated with a current candidate CIK plus a deterministic stratified non-target sample.
- Current candidate CIK mapping now includes SEC company_tickers.json, company_tickers_exchange.json, company_tickers_mf.json and a fallback mapper. Multiple CIKs and fund series/class IDs are retained. This is still not a PIT historical security master.
- No forward returns, no group inference, no alpha test. F80 remains frozen.


## 2026-11-03 — SEC ticker-map JSON schema correction
The corrected global-census pilot passed both parser test suites but stopped before the master-index download because company_tickers_exchange.json encodes rows as arrays under top-level fields and data, not as dictionaries. The SEC mutual-fund ticker file may use the same shape. The mapping reader now converts fields/data arrays into named records before extracting CIK, ticker, exchange, series and class. This is an ingestion-format fix, not evidence against SEC coverage; no returns or alpha test.


## 2026-11-03 — XML-based subject-census repair
- Run 41707588968 (job 126166891297; artifact 13267337601) completed as FAILED_VALIDATION. The 2025Q1 master.idx discovery was successful and 1,306 index pages were fetched without HTTP errors, but the HTML text parser returned zero role CIKs. The known Truist/Federated accession also failed its role check. No forward returns were used.
- The repair bypasses the failed HTML role parser for 2025Q1 and fetches `primary_doc.xml` through each CIK archive path associated with the accession in master.idx. Subject issuer CIK comes only from XML `issuerInfo/issuerCik`/`issuerCIK`; submission filer CIK comes separately from `filerCredentials/cik`. These are not reporting-group identifiers.
- Structured XML is a suitable Q1 2025 feasibility route because the SEC's Modernization of Beneficial Ownership Reporting rule required structured Schedule 13D/13G data beginning 2024-12-18 (official rule: https://www.sec.gov/files/rules/final/2023/33-11253.pdf).
- New code: `research/phase35_global_subject_census_pilot_xml.py`; tests: `research/test_phase35_global_subject_census_pilot_xml.py`; failure/repair audit: `research/PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_FAILURE_2026-11-03.md`.
- Predeclared gates remain >=95% subject and submission-filer CIK coverage, >=95% role-to-master-index-pair consistency, >=95% form agreement, <=5% XML fetch errors, and exact Truist/Federated identity. Current ticker CIKs are still candidate mappings only; 27 tickers remain unresolved in the pilot mapping.
- KnowledgeDate remains the SEC filing date from master.idx, with signal date strictly later. No same-day signal assumption, no forward returns, no economic-group inference, and no alpha claim. F80 remains frozen.


## 2026-11-03 — XML pilot retry: test-fixture robustness fix
- Latest run 41714047979 completed with failure before any SEC census requests. The parser-v3 suite (6 tests) and master-index suite (4 tests) passed; the XML pilot suite had 2 passes and 1 error.
- The failing negative test intentionally used `https://example.invalid/primary_doc.xml` to verify that a missing reporting-person CIK does not invent a group. `identity_row()` unconditionally split the URL on `/data/` to derive archive_path_cik, causing IndexError. This is a local robustness defect, not a source-coverage or SEC HTTP failure.
- Replaced the unconditional split with a guarded SEC archive-path parser; non-archive URLs now yield null. Added assertions for both a real SEC archive URL and the negative URL.
- Latest run produced no artifact because the pilot step was skipped after the unit-test failure. No SEC census, forward returns, or economic test ran. The corrected branch push will trigger one new pilot run; no overlapping run was active at the time of the fix.
- F80 remains frozen; 13D/13G remains a data-feasibility project only.


## 2026-11-03 — XML pilot retry: regex escaping correction
- Run 41724302967 again stopped before the SEC census. The 6 parser-v3 tests and 4 master-index tests passed; the XML identity suite had 2 passes and one assertion failure.
- The first guarded archive-path patch was itself over-escaped: its regex matched a literal backslash-d rather than numeric path digits, so a valid SEC URL returned null. This was a patch-generation defect, not a data/source failure.
- Corrected the regex to match the numeric CIK segment in `/Archives/edgar/data/{cik}/`; the negative non-archive URL still returns null. The existing test asserts both behaviors.
- No census requests, artifact, forward returns, or economic test occurred in run 41724302967. A single corrected push will rerun the branch-only workflow.


## 2026-11-03 — Phase 35 global subject census: 2025Q1 XML pilot result
- Run [41724414979](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41724414979) succeeded; job 126225315601; artifact `phase35-global-subject-census-xml-2025q1` ID 13274405289 (SHA-256 `9cbcb2b7c9f19d008e56bbbd882ce7009f9628d0ed9a3f7c28930827feadd591`).
- **PASS is limited to 2025Q1 structured-XML subject/filer identity feasibility.** 16,629 master-index rows; 8,318 unique 13D/G accessions; 1,100 candidate-relevant accessions plus 206 non-target validation accessions; 1,299/1,306 XMLs parsed; seven 404s, all in non-target validation. Subject and submission-filer CIK coverage were 100% in the target-relevant sample and 96.60% in the non-target sample; XML form match 99.46%; fixed Truist/Federated fixture passed.
- Current candidate mapping: 307 CIKs for 335 tickers; 27 tickers unresolved. This is not a historical security master.
- Crucial distinction: 242 filings have a subject issuer CIK in the candidate universe (142 distinct subject CIKs: 16 with 13D-family filings and 130 with 13G-family filings, four overlapping). 904 filings have a candidate submission-filer CIK; 858 are filer-only cross-issuer records. The 1,100 discovery union is not the target-subject count.
- Target-subject filings: 4 SC 13D, 25 SC 13D/A, 49 SC 13G, 164 SC 13G/A. The 13D sample is sparse (29 filings, 16 subjects) for one quarter.
- The 13G schema makes `reportingCik` optional; all 474 target-subject 13G reporting-person records in this pilot lack an explicit CIK. This is not a parser failure and does not authorize substituting the submission-filer CIK. A deterministic type-aware name crosswalk uniquely matched the filer to one reporting person in 203/213 target-subject 13G filings (95.3%) and 91/100 non-target validation filings (91.0%); two cases in each sample were ambiguous. These are candidate-link coverage rates, not measured precision. Freeze and validate on separate quarters before use; do not infer a complete group from one matched person.
- 13D explicit reporting-person CIK coverage: 7/8 persons in originals (87.5%) and 37/73 in amendments (50.7%); explicit no-CIK flags account for many missing identifiers.
- Amendment lineage remains blocked: previousAccessionNumber exists in 19/25 13D/A and 126/164 13G/A records; six 13D/A and 38 13G/A are unresolved. The 13G/A field may be optional, and a pointer is not necessarily the immediately preceding amendment. The parser also needs to emit amendmentNo.
- Historical active-universe membership, the 27 unresolved tickers, legacy HTML/TXT subject attribution before structured XML, and economic-group normalization remain unpassed. No forward returns were used. Full audit: [PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_RESULTS_2026-11-03.md](research/PHASE35_GLOBAL_SUBJECT_CENSUS_XML_PILOT_RESULTS_2026-11-03.md).
- Next: validate the frozen name crosswalk on 2025Q2/Q3; add amendmentNo and lineage diagnostics; extend quarter-by-quarter global discovery; then solve historical F80 membership and legacy filings. No economic test until all event/group gates pass.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen.


## 2026-11-03 — Cross-quarter identity validation launch history
- Canonical research branch commit: `a73e60621fbe9abb76a2b98cc600c82fabc637ef`.
- Added `amendmentNo` extraction to parser v3, deterministic filer-to-reporting-person candidate crosswalk code/tests, and a Q2/Q3 validation workflow. The crosswalk never overwrites source CIKs and never infers an economic group.
- Runs [41729360514](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729360514) (canonical branch) and [41729228829](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729228829) (prototype branch) both completed successfully. They covered the same Q2/Q3 workload because the run list was delayed after the prototype branch push. The canonical-branch artifact is the reference result; the duplicate artifact is not pooled as an independent sample.
- The completed Q2/Q3 findings are recorded in `research/PHASE35_CROSS_QUARTER_13DG_IDENTITY_VALIDATION_2025Q2_Q3_2026-11-03.md`.


## 2026-11-03 — Phase 35 cross-quarter identity validation completed (2025Q2–Q3)
- Canonical run [41729360514](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41729360514) completed successfully (job 126242359519; artifact 13277920675; SHA-256 3ab744ca033ec1af94c7586004bbe3ce9dd0bed9b5d8677cfd5e27a41c06c5b4). Duplicate prototype-branch run 41729228829 also completed; use the canonical artifact as the reference. No workflow remains active.
- Q2/Q3 global XML subject/filer identity gates passed in the tested samples: target-relevant subject/filer CIK coverage 100% in both quarters; non-target validation coverage 98.52%/99.50%; form agreement 99.83%/99.92%. Target-subject counts were 289 (Q2) and 252 (Q3), not the larger filer/subject discovery unions. XML fetch errors (3 and 1) were confined to non-target validation samples.
- Frozen exact-name filer-to-reporting-person candidate crosswalk coverage: target 13G 252/264 (95.45%) Q2 and 209/216 (96.76%) Q3; non-target 13G 95/100 and 96/100. These are coverage rates only; 13G explicit reporting CIK was absent in all tested records, so do not claim measured 13G precision or infer a group.
- Independent label check: for unique 13D name matches, candidate filer CIK equaled the explicit XML reporting-person CIK in 57/57 target-subject matches and 180/180 non-target validation matches (237/237, zero mismatches; 197 distinct CIKs). This validates the exact-name link in the tested 13D subset, not all 13G records or group identity.
- Target-subject 13G group markers were mostly unavailable (337/480 all missing; 134 all “b”; 9 all “a”). Target-subject amendments totalled 406; amendmentNo was present in all 406, but previousAccessionNumber only in 197/406 (48.52%). Missing lineage remains unresolved; amendmentNo alone does not identify the immediately prior filing.
- Added reproducible validator and tests: `research/phase35_13dg_crosswalk_precision_validation.py` and `research/test_phase35_13dg_crosswalk_precision_validation.py` (5 tests pass). Full report: `research/PHASE35_CROSS_QUARTER_13DG_IDENTITY_VALIDATION_2025Q2_Q3_2026-11-03.md`.
- Current ticker map remains 307/335 with 27 unresolved ETF-like symbols; this is not historical F80 membership. No forward returns, economic-group inference, or alpha test. Keep F80 frozen.
- Next: keep the crosswalk rule frozen and test 2025Q4/2026Q1; retain unmatched names as unresolved; then tackle amendment chains, historical ticker/CIK/CUSIP/listing-status continuity, and pre-structured-XML legacy filings before any economic test.


## 2026-11-03 — Next frozen-rule validation queued
- Added manual/push-scoped workflow `.github/workflows/phase35_q4q1_crossquarter_validation.yml` to validate the unchanged crosswalk on 2025Q4 and 2026Q1 and run the explicit-13D-CIK precision check. It is isolated to this research branch and uses a distinct concurrency group.
- Run [41742690656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41742690656) completed successfully on commit `fd7bf942634801fac9f4430e75e34ea81dc38f7f` (artifact 13282921575). No further Q4/Q1 run is needed.
- The Q2/Q3 crosswalk and precision rule are frozen; no aliases or fuzzy matching will be added after seeing those results.


## 2026-11-04 — Phase 35 Q4/Q1 validation and amendment-lineage audit
- Canonical run [41742690656](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41742690656) completed successfully (job 126287874908; artifact 13282921575). The Q4/Q1 XML subject/filer identity gate passed: 100% target subject/filer CIK coverage in both quarters; Q4 non-target validation 100%; Q1 non-target validation 99.01%; XML form match 100%/99.84%. Q1's two XML fetch errors were confined to the non-target validation sample.
- The Q1 pilot was the development sample. The frozen exact-name filer-to-reporting-person crosswalk then produced 237/237 exact matches against explicit 13D reporting-person CIKs in the first Q2/Q3 held-out validation and 231/231 in the second Q4/Q1 held-out validation (zero mismatches in both). The pooled two-holdout count is 468/468. This is conditional precision among unique matched 13D cases, not universal precision.
- 13G target unique-name-match coverage: Q4 219/224 (97.77%), Q1 457/463 (98.70%), Q4/Q1 held-out combined 676/687 (98.40%), and combined Q2–Q1 1,137/1,167 (97.43%). This remains coverage only; explicit reporting-person CIKs were absent in the tested 13G XMLs, so 13G precision and group identity are not established.
- The four-quarter target-subject panel contains 1,278 accessions (111 13D; 1,167 13G). Of 98 13D/A amendments, 57 contain previousAccessionNumber (58.2%); of 925 13G/A, 331 contain it (35.8%).
- In-panel explicit references: 23 13D and 94 13G. All 23 13D references match subject/family/person/CUSIP. Of 94 13G references, 92 have the same uniquely matched person name, 92 have CUSIP overlap, and 90 satisfy both. Among comparable person+CUSIP references, 19/23 13D and 75/90 13G point to the latest earlier in-panel candidate; 4/23 13D and 13/90 13G point to an older accession; 2/90 13G are same-day and cannot be ordered by filing date alone.
- **Methodology correction:** previousAccessionNumber is an explicit prior-filing reference, not a guaranteed immediate-predecessor edge. Preserve it as a chain anchor; never assume it identifies the immediately preceding amendment. A unique earlier same-subject/person/CUSIP candidate for a missing pointer remains unassigned because the four-quarter panel is left-censored.
- Missing-pointer candidate counts (not assignments): 13D/A — 11 unique, 8 multiple, 19 zero in-panel, 3 unmatched/missing CUSIP; 13G/A — 150 unique, 38 multiple, 400 zero in-panel, 6 unmatched/missing CUSIP. A zero in-panel candidate does not prove no earlier filing.
- Added reproducible audit script/tests and reports: research/phase35_13dg_lineage_feasibility_audit.py, research/test_phase35_13dg_lineage_feasibility_audit.py, research/PHASE35_13DG_LINEAGE_FEASIBILITY_AUDIT_2026-11-04.md. Four helper tests are included; the equivalent local prototype test harness passed, but the repository test file has not yet been run by GitHub Actions. Full artifact review and lineage analysis are recorded there.
- No forward returns, event-direction labels, threshold/horizon selection, or alpha test. The historical F80 universe, pre-2024 legacy filing coverage, reporting-group continuity and same-day accepted timestamps remain unpassed. F80 stays frozen.

## Phase 50 — SEC Form 144 feasibility review (2026-11-04)
- Latest run 40961563763 failed (job 123755365019; artifact 12936426126). The two Phase 50 runs are completed; no workflow is active.
- The failed artifact had 301/335 current CIK mappings, 165 issuer hits, 132 HTTP 403 query errors, and four successful no-hit queries. The 54.8% hit rate is a lower bound with 132 unresolved queries; among 169 successful queries, 165 had a hit (97.6%). Do not interpret this as a true coverage failure.
- Only 6/25 sampled XMLs downloaded. Field-presence zeros for securitiesClassTitle, noOfUnitsSold, acquiredDate, and natureOfAcquisitionTransaction are parser false negatives: the code searched incorrect tag names. The archive resolver also assumes accession-prefix CIK equals archive-path CIK, which is not reliable for Form 144.
- SEC examples show distinct accession prefix, archive-path/filer CIK, and subject issuer CIK. The XML includes explicit issuerCik, filer credentials, sale quantity/value/date, security class and acquisition fields. Form 144 remains conditional / not killed pending a corrected archive resolver, actual XML parser, rate-limited/batched discovery, 144/A lineage, and prospective-vs-retrospective classification.
- PIT caveat: Form 144 is a notice, not proof of execution. Some filings are retrospective/late and describe sales already executed before filing. Use SEC acceptance timestamp (or filing date with next-session use); never use approxSaleDate as KnowledgeDate. Exclude retrospective notices from prospective planned-supply features.
- Review: research/PHASE50_FORM144_FEASIBILITY_REVIEW_2026-11-04.md. No forward returns or alpha test.
