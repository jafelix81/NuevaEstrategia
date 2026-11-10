# Smart Money Research — current state (Phase 265, 2026-11-10 UTC)

**Updated:** 2026-11-10 UTC  
**Active branch:** phase231-cboe-option-quotes-full-row-reparse (PR #14, stacked on PR #13)  
**Frozen baseline:** F80_TOP20_PARTIAL50_BASELINE_C20  
**Legacy holdout:** CONSUMED_NOT_PRISTINE; never reused

## Latest material result — Phase 264

SEC registered-security Inline XBRL is a conditional positive identity source, not a complete crosswalk census: the April 2026 SEC XBRL Guide says no instance type requires the registered-security title facts. Company Facts is entity-wide and cannot replace dimensioned filing contexts.

The Phase 69 Form 144 panel has 21,653 original sale tranches across 289 issuer CIKs: 166 raw security-class labels (135 after case/whitespace normalization); 205/289 issuers have multiple normalized labels; 71 have explicit class-letter labels. The generic label Common occurs in 12,562 tranches, including 11,036 in multi-label issuers and 3,297 in issuers with explicit class-letter labels. These are text-heterogeneity diagnostics, not counts of legal classes.

Normalized XBRL context, exact-title join and as-filed vintage prototype: **23/23 hosted tests passed** on isolated CI run [42755137270](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42755137270); metadata-only artifact [13734524132](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42755137270/artifacts/13734524132). Raw iXBRL parsing and issuer-panel coverage remain untested.

- Phase 253 report: PHASE253_FORM144_XBRL_REGISTERED_SECURITY_CROSSWALK_AUDIT_2026-11-10.md
- Helper: phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Tests: test_phase253_form144_xbrl_registered_security_crosswalk_audit.py
- Result: phase253_form144_xbrl_registered_security_crosswalk_audit_result.json

## Next gates

1. Run a stratified 20–30 issuer raw-iXBRL and visible-cover-page pilot; preserve each filing accession, filing/acceptance time, context, axes/members, original bytes and SHA-256. Measure exact-match coverage before scaling.
2. Bulk SEC retrieval is blocked because the authorized GitHub secret SEC_CONTACT_EMAIL is absent. No request was sent and no email was guessed.
3. Obtain a survivorship-free, corporate-action-aware daily dollar-volume source before computing Form 144 ADV20. No paid source has been authorized or purchased.
4. For Cboe options, first prove multi-date coverage, immutable final/preliminary receipt vintages, effective-dated security identity and licensing. No trial/card authorization or purchase.
5. Keep CFTC BPR/TFF prospective capture and all Smart Money candidates out of production until PIT and incremental OOS evidence pass.

## Other source dispositions

- FINRA Phase 20C: not promoted; no demonstrated incremental stock-selection edge.
- CFTC BPR/TFF: prospective regime candidates only; no historical beneficial-owner identity.
- SEC FTD: context metadata only; external history contains backfills and no immutable first-receipt proof.
- N-PORT: Phase 247 fixed the UNIT/UNITS schema defect; raw PIT and security identity remain open.
- Cboe Open-Close: feature contract and one C1 20% sample validated; no PIT or alpha.
- Cboe option quotes: 115,617 rows; 112,313 unambiguous; 3,304 expiration-ambiguous rows quarantined; no PIT or alpha.
- Cboe All Access: conditional high-information candidate; no account, trial, token, API request or purchase.

## Controls

No alpha/OOS result from Phase 253. No returns, bootstrap/LOO, chronological OOS or holdout test. No production, universe, capital or parameter changes. No minimum/maximum holding period or CAGR target is imposed. Compare any future feature against frozen LTM/F80 with identical exposure and costs.


## Phase 254 — Form 144 issuer/accession-scoped XBRL class join and prior-vintage gate (2026-11-10 UTC)
- Hardened the Phase 253 normalized resolver so the selected prior filing is explicitly scoped to the Form 144 issuer CIK, accession and filing date. Phase 253's generic selector/resolver depended on caller-side prefiltering; Phase 254 makes that precondition explicit and fail-closed.
- Same-day/future filings remain excluded for a daily Form 144 event; same-date prior-filing ties require timezone-aware acceptance timestamps on the filing date. Later amendments remain separate vintages and cannot be backdated.
- A class join now requires an explicit class-axis member. EntityListingsExchangeAxis is not class identity. Multiple listings are only reported when all matching contexts have known listing scope and agree on class member/symbol; incomplete listing scope remains UNKNOWN.
- Added 24 hosted regressions covering issuer/accession/date scope, same-day/future exclusions, amendments, class-vs-listing axes, unknown listing scope, exact-title-only joins and ambiguous classes.
- Final hosted Phase 254 run [42764068968](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968) passed **24/24**; job 129656300533; metadata-only artifact [13738319528](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764068968/artifacts/13738319528), 381 bytes, SHA-256 `ae7b3269d9fa884e6fe4f0f716b427aacc9d701e9c416175038309c025a81768`. Initial run 42763927183 passed 22 tests but had a hard-coded artifact count of 21; the workflow was corrected to calculate the count dynamically before the final 24/24 run.
- Same-head Phase 231 run [42763911397](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397) passed 9/9; artifact [13738991707](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911397/artifacts/13738991707). It parsed 115,617 rows: 112,313 unambiguous, 3,304 ambiguous expirations quarantined. Phase 249 run [42763911410](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410) passed 11/11; artifact [13738418042](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42763911410/artifacts/13738418042); still one public C1 20% sample date.
- Last 30 workflow runs were successful and no workflows remain active. PR #13 and #14 remain open/unmerged; no merge was performed.
- Raw iXBRL parsing, visible cover-page fallback, 289-issuer class coverage, effective-dated inactive/delisted identity and PIT ADV20 remain unmeasured. Bulk SEC retrieval remains blocked by missing authorized `SEC_CONTACT_EMAIL`; no request was sent and no email was guessed.
- No returns, alpha, bootstrap/LOO, chronological OOS or holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe and capital are unchanged.
- [Phase 254 report](PHASE254_FORM144_ISSUER_ACCESSION_SCOPED_XBRL_CLASS_JOIN_GATE_2026-11-10.md) · [helper](phase254_form144_xbrl_scoped_class_join.py) · [tests](test_phase254_form144_xbrl_scoped_class_join.py) · [result](phase254_form144_xbrl_scoped_class_join_result.json)


## Phase 255 — ADV20 historical market-data feasibility and dollar-turnover contract (2026-11-10 UTC)
- Completed a source-feasibility audit for the Form 144 ADV20 denominator. CRSP is the preferred research-grade benchmark if authorized access exists (32k+ active/inactive securities, survivor-bias-free history, PERMNO/PERMCO). Massive is the strongest API candidate for the 2023–2026 panel, but its individual market-data terms prohibit non-display/derived investment-strategy use unless separately licensed; its date-based security master is effective-dated current vendor data, not an archived original vintage, and it has no permanent identifier. Sharadar has active/delisted EOD history to 1997 but its published license is personal-use only. Norgate's two-year trial cannot cover the earliest Form 144 events; Tiingo and Nasdaq Data Link lack sufficient documented delisted/PIT evidence in this audit.
- The best documented reported-turnover measure is daily `VWAP × volume` where both use the same share basis. Massive documents that VWAP covers the same trades as volume, including some odd-lot/average-price/contingent trades; this is reported turnover, not executable liquidity. Missing bars are UNKNOWN, never zero-filled.
- Added `phase255_adv20_source_feasibility.py` and 26 hosted regressions. The contract requires exactly 20 distinct supplied XNYS sessions strictly before the Form 144 filing date; raw/raw or split-adjusted/split-adjusted VWAP/volume; Decimal arithmetic; no missing-bar zero fill; no same-day/future bars.
- Initial run [42764563857](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764563857) failed one test-only Decimal string expectation (`19500` vs `19500.0`). Corrected the expectation and added fractional-volume and split-invariance tests. Final run [42764720861](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861) passed **26/26**; job 129658390045; artifact [13739416974](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42764720861/artifacts/13739416974), 421 bytes, SHA-256 `be975ca3108944ba6a65acafa28cc446bf8f37a81eddadfaba218ed2212b4a90`.
- No vendor data, API key, account, license or purchase was obtained. No ADV20 was calculated for Form 144 records. Raw SEC iXBRL pilot remains blocked by missing authorized `SEC_CONTACT_EMAIL`.
- No returns/alpha/bootstrap/LOO/chronological OOS/holdout test. `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; production, universe and capital unchanged.
- [Phase 255 report](PHASE255_ADV20_HISTORICAL_MARKET_DATA_FEASIBILITY_AND_TURNOVER_CONTRACT_2026-11-10.md) · [helper](phase255_adv20_source_feasibility.py) · [tests](test_phase255_adv20_source_feasibility.py) · [result](phase255_adv20_source_feasibility_result.json)


## Phase 256 — Form 144/Form 4 lag-preserving conditional-placebo correction (2026-11-10 UTC)
- Re-audited Phase 210's conditional date placebo against its own sample-selection rule. Phase 208 admits Form 4 sale blocks only when filing_date minus transaction_date is 0–4 calendar days. Phase 210 shuffled raw transaction dates while holding filing dates fixed, so its date and joint date/share nulls did not preserve the selected lag envelope.
- Reproduced the old raw-date shuffle for 1,000 deterministic replicates. On average **4,247.36/10,525 blocks per replicate (40.35%)** became ineligible: 2,127.589 negative lags and 2,119.771 lags over four days.
- Corrected the randomization by permuting the observed 0–4-day filing lag within issuer × reporting-owner groups, holding each filing date fixed and reconstructing transaction dates. This preserves each group's lag multiset and sample eligibility.
- Across 1,000 replicates per null, the observed exact-link counts remain above every simulated value: owner 475 vs null max 184; filing lag 340 vs max 238; shares 340 vs max 223; lag+shares 340 vs max 166. Each has 0/1,000 exceedances and a plus-one Monte Carlo tail frequency of 0.000999. The corrected date null mean is 210.735 (p95 225) versus 340 observed.
- The exact-first linkage graph remains 521 exact date/share links plus 49 fallback links; 481/521 exact links agree on broad class family and 40 remain unresolved/conflicted. This is document linkage only: Form 144 is proposed, Form 4 code S can include private dispositions, and the one-quarter sample is not a market-execution census.
- Added an optimized exact-link counter, lag-preserving permutation audit, raw-date invalidity diagnostic and 8 regression tests. Local and hosted tests passed **8/8**. Hosted Phase 256 run [42767357624](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42767357624) succeeded; job 129666856922; metadata artifact [13739833787](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42767357624/artifacts/13739833787), 1,729-byte ZIP. Same-head Phase 231 run [42767363695](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42767363695) also passed; 115,617 rows, 112,313 unambiguous and 3,304 ambiguous expirations quarantined.
- No returns, alpha, bootstrap/LOO, chronological OOS or holdout test. No SEC request, vendor contact or purchase. The legacy holdout remains CONSUMED_NOT_PRISTINE. F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital unchanged.
- [Phase 256 report](PHASE256_FORM144_FORM4_LAG_PRESERVING_PLACEBO_CORRECTION_2026-11-10.md) · [code](phase256_form144_form4_lag_preserving_placebo_audit.py) · [tests](test_phase256_form144_form4_lag_preserving_placebo_audit.py) · [result](phase256_form144_form4_lag_preserving_placebo_audit_result.json)


## Phase 257 — Form 144/Form 4 temporal-stratification sensitivity (2026-11-10 UTC)
- Added a reproducible sensitivity audit using the same SHA-pinned Phase 69 Form 144 and Phase 39 Q3 2026 Form 4 artifacts as Phase 256.
- The conditional filing-lag placebo is evaluated under three strata: issuer × reporting owner; issuer × reporting owner × filing month; and issuer × reporting owner × ISO week. Filing dates remain fixed and observed 0–4 calendar-day lags are permuted only within each stratum.
- Tightened the definition of a genuinely mutable group: a group must contain at least two blocks and at least two distinct observed filing lags. Groups with identical lags are not counted as mutable or as evidence for the permutation test. Sparse/no-mutable strata are reported as insufficient rather than treated as a pass or failure.
- Added Holm step-down adjustment across the available exploratory temporal-stratification tests. This adjusts linkage-placebo tails only; it does not create an alpha p-value.
- Added 14 regression tests covering month/week grouping, ISO-year boundaries, true mutability, lag-multiset preservation, deterministic permutations, invalid-lag rejection, Holm adjustment and insufficient-strata handling. A local mirror of the 14 tests passed; the dedicated hosted workflow is configured with same-branch concurrency and superseding behavior.
- Hosted Phase 257 push run [42775383915](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42775383915) succeeded; job 129692649023 passed 14/14 tests; artifact [13743028950](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42775383915/artifacts/13743028950), SHA-256 b2ec9653ab66da858bf3e7f42376176a67011413de4d543d8ff93fd74dba7c2f. Results: observed mutable exact links 241/169/139 versus null maxima 141/111/112 for issuer-owner, month and ISO-week strata; zero exceedances in 1,000 replicates per stratum; Holm-adjusted plus-one tails 0.002997. Linkage only, not alpha.
- No return test, PIT admission, bootstrap/LOO, chronological OOS or holdout use. Form 144/Form 4 remains document-linkage research only; F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; production, universe and capital unchanged.


### Latest same-head Actions regression wave (2026-11-10 UTC)
- Current PR #14 head f6157e72f6be33dbbd54b2846327b964401b1d6a completed the existing PR-triggered regression wave. Phase 246 run 42775390335 passed; artifact 13743223201 (1,909 bytes). Phase 247 run 42775390336 passed; artifact 13743846424 (1,977 bytes). Phase 248 run 42775390092 passed; artifact 13743178838 (1,460 bytes). Phase 249 run 42775390226 passed; artifact 13743911141 (1,918 bytes). Phase 250 run 42775390134 passed (no artifact). Phase 251 run 42775390471 passed (no artifact).
- The same-head Phase 231 full-row reparse run 42775390615 completed successfully; job 129692741543; artifact 13744125510 (2,422 bytes), ZIP SHA-256 f8af57f8944655c3e7a23aca736e5361e8d4473cdcd8ee58e5a94f2bffba6c17. It again processed 115,617 rows: 112,313 unambiguous rows passed the row-level gate; 3,304 ambiguous expirations remain quarantined; no invalid timestamps; sample_schema_gate_pass=false, sample_admission=false, pit_admission=false, alpha_admission=false.
- All seven listed PR-triggered runs completed successfully. Phase 231 was not duplicated while it was in progress; the existing run was allowed to finish.
- Phase 257 push run 42775383915 was inspected after completion: 14/14 tests, job logs and artifact 13743028950 verified. It is no longer pending.


## Phase 258 — Form 144/Form 4 accession-cluster-preserving conditional placebo (2026-11-10 UTC)
- Added a stricter conditional randomization that freezes all multi-block Form 4 accessions intact and permutes only accessions with exactly one selected sale block. This avoids splitting multiple sale-date blocks reported in one filing.
- Permutation groups use issuer × permanent reporting-owner CIK, narrowed separately by filing month and ISO week. Filing dates remain fixed; only observed 0–4 calendar-day lags are reassigned within eligible single-block accession strata.
- Immutable sample: 10,525 sale blocks across 8,897 accessions; 7,512 single-block accessions; 1,385 multi-block accessions (3,013 blocks) frozen. Of 521 exact date/share links, 414 are in single-block accessions and 107 in frozen multi-block accessions. 49 lower-confidence fallback links remain separate.
- Owner identity audit: 5,198 distinct reporting-owner CIKs and 5,276 issuer-owner CIK groups; zero issuer/name-to-multiple-CIK collisions and zero CIKs with multiple normalized names in this sample.
- Three 1,000-replicate tests passed. Observed mutable exact links were 127 vs null mean 58.848/max 80 (issuer-owner CIK); 56 vs 26.249/max 43 (month); and 28 vs 14.208/max 24 (ISO week). All had zero exceedances; Holm-adjusted plus-one tails were 0.002997. These are conditional document-linkage placebo results only.
- Initial run 42787340371 failed before artifact download because the workflow token expressions were escaped. The workflow was corrected; final hosted run [42787526319](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526319) passed **15/15 tests** and the full audit; job 129732394177; artifact [13749584173](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526319/artifacts/13749584173), SHA-256 e5f51d3d123f653275934f2cdfcc6e9fc491eeb09391a11dfa4533be3877602f.
- Phase 257 and 258 are nested sensitivity analyses on the same one-quarter data, not independent replications. Form 144 remains a proposed-sale notice; Form 4 code S may include private dispositions. No PIT, return, alpha, bootstrap/LOO, chronological OOS or holdout test.
- [Phase 258 report](PHASE258_FORM144_FORM4_ACCESSION_CLUSTER_PRESERVING_PLACEBO_2026-11-10.md) · [code](phase258_form144_form4_accession_cluster_preserving_placebo.py) · [tests](test_phase258_form144_form4_accession_cluster_preserving_placebo.py) · [result](phase258_form144_form4_accession_cluster_preserving_placebo_result.json)

### Latest same-head Actions regression wave — 2026-11-10 UTC
- Commit e4a6484780cc4328204d67e21d7429f1723cdfd9: Phase 231 run [42787526616](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526616), Phase 246 [42787526442](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526442), Phase 247 [42787526563](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526563), Phase 248 [42787526289](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526289), Phase 249 [42787526342](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526342), Phase 250 [42787526637](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526637), Phase 251 [42787526386](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526386) and Phase 258 [42787526319](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42787526319) all completed successfully. No workflows remain active.
- The initial Phase 258 attempt 42787340371 is a workflow-configuration failure only; its artifact token expressions were corrected before the final successful run.
- PR #13 and PR #14 remain open and unmerged. No merge was performed.


## Phase 259 — MOM120 incremental portfolio economic audit (2026-11-10 UTC)
- Recomputed the Phase 29-selected MOM120 factor against the LTM/F80-style C20 portfolio using immutable Phase 29/30 artifacts. The paired ledgers have identical daily dates and exposure paths (positions, gross, gross-value/equity and cash/equity) at 10/20/50 bps per side; accounting and trade-cost identities pass.
- Corrected Phase 30's OOS multiple boundary: the first 2024 return includes the 2023-12-29 close, so the OOS multiple must use that pre-OOS close, not the first OOS close. Published absolute multiples were overstated by 3.65% for LTM/C20 and 3.73% for MOM120/C20.
- Over 706 daily observations (2024-01-02 to 2026-10-23), MOM120's C20 relative OOS growth was +4.26%, but mean paired excess was only 0.710 bps/day. The 20-session block-bootstrap 95% CI was -3.533 to +4.811 bps/day; HAC(20) t=0.338 and CI -3.409 to +4.830. All 5/10/20/40/80-session bootstrap sensitivities and all 10/20/50 bps cost variants include zero.
- **Decision:** MOM120 incremental upgrade is not demonstrated; retain as a research hypothesis, do not promote. The historical period is consumed/not pristine, not a new independent OOS or holdout. No production, universe, capital or F80 change.
- Final hosted run [42790753655](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753655) passed 15/15; artifact [13750088994](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753655/artifacts/13750088994). Report: [PHASE259_MOM120_INCREMENTAL_PORTFOLIO_ECONOMIC_AUDIT_2026-11-10.md](PHASE259_MOM120_INCREMENTAL_PORTFOLIO_ECONOMIC_AUDIT_2026-11-10.md).

## Phase 260 — XNYS-session-valid Form 144/Form 4 placebo (2026-11-10 UTC)
- Added a stricter Phase 258 sensitivity that freezes multi-block accessions and non-session transaction dates, and permutes only single-block accessions with observed XNYS-session transaction dates. Groups preserve issuer, reporting-owner CIK, filing weekday and identical valid 0–4-day XNYS candidate-lag signatures; month and ISO-week strata are separate.
- Of 7,512 single-block accessions, 7,499 were XNYS-session eligible and 13 non-session records were frozen. The original 521 exact links and 49 fallbacks remain unchanged.
- Under 1,000 permutations per stratum: broad issuer-owner-weekday/signature 25 observed vs null mean 12.481/max 23 (0 exceedances; Holm 0.002997); monthly 9 vs 4.486/max 9 (21 exceedances; Holm 0.043956); ISO-week 1 vs 0.533/max 1 (533 exceedances; Holm 0.533467). Broad and monthly excess survives; the sparse weekly test is inconclusive.
- This is a nested sensitivity on the same one-quarter sample as Phase 258, not independent replication. It remains document-linkage only: no PIT, stock-return, alpha, bootstrap/LOO, chronological OOS or holdout admission.
- Hosted run [42790753569](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753569) passed 15/15; artifact [13750319077](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42790753569/artifacts/13750319077). Report: [PHASE260_FORM144_FORM4_XNYS_SESSION_VALID_PLACEBO_2026-11-10.md](PHASE260_FORM144_FORM4_XNYS_SESSION_VALID_PLACEBO_2026-11-10.md).

## Latest same-head validation wave — 2026-11-10 UTC
- Head 0404eacdf45adef494ec3cc7bf0bb468baa558f5; 10/10 workflows succeeded: Phase 231, 246, 247, 248, 249, 250, 251, 258, 259 and 260. No active/queued workflows remain.
- PR #13 and PR #14 remain open, mergeable and unmerged. Branch inventory: 134. No merge was performed.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; legacy holdout remains CONSUMED_NOT_PRISTINE.


## Phase 261 — Global Form 144/Form 4 placebo multiplicity audit (2026-11-10 UTC)
- Downloaded and SHA-256 verified the immutable result JSONs from Phases 256, 257, 258 and 260; all four share the same Phase 69 Form 144 and Phase 39 Q3 2026 Form 4 input hashes and the same 1,451 notices / 1,460 tranches / 10,525 Form 4 blocks / 521 exact links / 49 fallbacks.
- Combined all 13 completed, valid exact-link placebo sensitivities into one exploratory family and applied global Holm step-down correction. **12/13 remain below 0.05**: 11 zero-exceedance tests adjust to 0.012987; Phase 260 monthly adjusts to 0.043956; sparse ISO-week remains 0.533467.
- The plus-one Monte Carlo tail is (exceedances+1)/1001; zero exceedances is p=0.000999, with one-sided 95% upper bound 0.002991. Phase 210 raw-date placebos are excluded because Phase 256 invalidated their lag-envelope preservation; Phase 238 and 259 are different endpoints.
- This is a post-hoc multiplicity audit of nested sensitivities on the same selected one-quarter sample, not independent replication or proof of informed trading. Form 144 remains proposed, Form 4 code S may include private dispositions. No PIT, feature or alpha admission.
- Hosted final run [42797886745](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42797886745) passed **13/13**; job 129767610240; metadata/result artifact [13755475932](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42797886745/artifacts/13755475932). All four upstream artifacts were downloaded and their ZIP SHA-256 digests matched the pinned manifest.
- F80 remains frozen; no return test, bootstrap/LOO/OOS, holdout use, production, universe or capital change.
- [Phase 261 report](PHASE261_FORM144_FORM4_GLOBAL_PLACEBO_MULTIPLICITY_AUDIT_2026-11-10.md) · [code](phase261_global_form144_form4_placebo_multiplicity_audit.py) · [tests](test_phase261_global_form144_form4_placebo_multiplicity_audit.py) · [result](phase261_global_form144_form4_placebo_multiplicity_audit_result.json)


## Phase 262 — Databento Security Master temporal-availability and identity gate (2026-11-10 UTC)
- Re-audited Databento Security Master against its current official dataset specification, API reference, field schema and product/licensing page. The source advertises history from 2005-01-01, 860,000+ listed/delisted securities, 220+ exchanges and listing-level PIT records; these are global product claims, not measured coverage of our frozen universe or U.S. EQS panel.
- Critical PIT finding: `ts_effective` is validity start, `ts_record` is last change, and `ts_created` is database ingestion. The official AAPL example has 2004 effective/record dates but `ts_created=2024-11-11`; effective/record history therefore cannot prove customer availability in 2005. Strict PIT now requires our own immutable first-observed receipt time, raw SHA-256 and an authorized license scope in addition to vendor clocks.
- Identity hierarchy is explicit: `listing_id` for listing, `security_id` for security across listings, `issuer_id` for issuer. Ticker-only joins are prohibited; ISIN/US CUSIP/FIGI are preferred external crosswalks. Class-share suffix normalization, symbol recycling, spin-offs and never-relisted delistings remain explicit traps.
- Documentation discrepancy: dataset specification says weekly updates; product page says four updates per day. Cadence is unresolved and is not used as a PIT clock. Public page licensing language permits internal personal/commercial use but prohibits external redistribution; exact scope for our public GitHub Actions/artifacts is unverified.
- Added a fail-closed temporal/identity contract and **35 tests**. Local tests passed 35/35. Hosted workflow will repeat the suite and upload only the deterministic metadata result; no vendor API call, account, trial, purchase or contact occurred.
- Decision: retain as a conditional identity-reference candidate, but no strict PIT, universe, ADV20, feature or alpha admission. U.S. EQS coverage, frozen-universe coverage, and delisted/relisted sample coverage remain unmeasured.
- [Phase 262 report](PHASE262_DATABENTO_SECURITY_MASTER_TEMPORAL_IDENTITY_GATE_2026-11-10.md) · [code](phase262_databento_security_master_pit_identity_gate.py) · [tests](test_phase262_databento_security_master_pit_identity_gate.py) · [result](phase262_databento_security_master_pit_identity_gate_result.json) · [workflow](../.github/workflows/phase262_databento_security_master_pit_identity_gate.yml)
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; no returns, alpha, bootstrap/LOO, OOS, holdout, production, universe or capital changes.


### Latest same-head Actions regression wave — Phase 262 commit f5394f6fd6f087296b21116012cd656de676c319
- Phase 262 push run [42808287557](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42808287557) completed **SUCCESS**, 35/35 tests; job 129802970038; metadata-only artifact [13761975456](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42808287557/artifacts/13761975456), 1,394 bytes, ZIP SHA-256 `b9aaa29287434e4fb1bffcb421d1e1e744d4efa8b5309b15acda71eda4c56249`.
- The same-commit PR regression wave completed **10/10 SUCCESS**: Phase 231 run 42808294360 (9/9; artifact 13760586643; 115,617 rows, 112,313 unambiguous, 3,304 ambiguous expirations quarantined); Phase 246 run 42808294444 (7/7; artifact 13761485590); Phase 247 run 42808294378 (11/11; artifact 13760191901); Phase 248 run 42808294535 (29/29; artifact 13762185370); Phase 249 run 42808294605 (11/11; artifact 13760186865; one-day 20% sample remains diagnostic only); Phase 250 run 42808294532 (17/17); Phase 251 run 42808294874 (42/42); Phase 258 run 42808294371 (15/15; artifact 13762230570); Phase 259 run 42808294430 (15/15; artifact 13761525609; MOM120 not promoted); Phase 260 run 42808294468 (15/15; artifact 13762305560).
- Jobs, step logs and available artifacts were inspected after completion. No workflows remain active or queued in this validation wave.
- PR #13 remains open/mergeable/unmerged (580 commits, 506 files). PR #14 remains open/mergeable/unmerged (218 commits, 129 files) with title updated through Phase 262. Branch inventory remains 134. No merge was performed.
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no production, universe, capital, parameter, return-alpha, OOS or holdout change.


## Phase 263 — CFTC TFF semiweekly-scope adjudication (2026-11-10 UTC)
- Rechecked the CFTC 2026-10-27 semiweekly COT announcement against the current COT index, current release schedule, and both live TFF file links on 2026-11-10.
- The announcement plans Monday-position/Wednesday-publication and Wednesday-position/Friday-publication by year-end, but frames the change around agricultural-market feedback and does not explicitly include TFF. The current COT index still describes weekly Tuesday/Friday reporting and its FAQ still says once weekly; the current TFF futures-only and combined files both show report date 2026-11-03. No official TFF Wednesday/Friday schedule or two-distinct-report-date TFF week was observed.
- **Decision:** retain the weekly TFF interpretation pending TFF-specific confirmation. Keep Phase 239's existing weekday 20:35 UTC capture poll and concurrency group; no duplicate workflow or cadence change.
- TFF remains broad futures-market context, not a stock-level feed. CFTC categories are self-reported business-purpose classifications, not beneficial-owner identities or verified informed traders; missing markets below the 20-reportable-trader threshold are not zero.
- Added a fail-closed cadence-scope gate, 17 deterministic tests, metadata-only result and isolated workflow. No raw files persisted, no prospective capture executed, no historical PIT/alpha admission.
- [Phase 263 report](PHASE263_CFTC_TFF_SEMIWEEKLY_SCOPE_ADJUDICATION_2026-11-10.md) · [code](phase263_cftc_tff_semiweekly_scope_gate.py) · [tests](test_phase263_cftc_tff_semiweekly_scope_gate.py) · [result](phase263_cftc_tff_semiweekly_scope_gate_result.json) · [workflow](../.github/workflows/phase263_cftc_tff_semiweekly_scope_gate.yml)
- F80_TOP20_PARTIAL50_BASELINE_C20 remains frozen; no returns, alpha, bootstrap/LOO, OOS, holdout, production, universe or capital changes.


## Phase 264 — FINRA ATS final live-artifact adjudication (2026-11-10 UTC)
- Closed the Phase 100 corrected live run previously described as still in progress in the preliminary Phase 107 note. Run [41978867803](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803) completed successfully; job 127084556636; artifact [13394110956](https://github.com/jafelix81/NuevaEstrategia/actions/runs/41978867803/artifacts/13394110956). Downloaded ZIP SHA-256 independently verified as `803c58a5301df8b505b487c5367a449696c6bc467cab39121c50eda762d1f3e9`.
- Ten of ten partitions completed: 968,139 rows (T1 269,163; T2 698,976), 199 page hashes/unique request IDs, all API Record-Total counts reconciled, zero invalid/negative quantity fields. 108,444 symbol aggregate rows had 100% non-null initialPublishedDate; 1,882 (1.735%) had lastUpdateDate later than initialPublishedDate. Median observed publication lag: T1 21 days, T2 35 days.
- Two symbol-bearing rows in 2022-01-03 T2 lack issueSymbolIdentifier (one OTC_W_SMBL_FIRM, one OTC_W_SMBL); two conflicting LND/T2/2025-01-06 duplicate groups remain in ATS_W_SMBL and OTC_W_SMBL. Adding lastReportedDate mechanically separates the pairs, but FINRA does not document it as a natural key; no selection, summation or deduplication is allowed.
- The combined exact-week/tier gate is marked false because the Phase 100 implementation folds row-level symbol validation into its no-partition-errors boolean; the two recorded examples are missing-symbol errors, not observed wrong week/tier values.
- The workflow completed with FINRA_API_TOKEN absent using synchronous public-endpoint requests. This specific run does not establish access/licensing for every FINRA endpoint. SEC_CONTACT_EMAIL remains a separate SEC bulk-retrieval requirement, not a blocker for this FINRA sample.
- **Disposition:** coverage/schema is promising, but row integrity and aggregate integrity fail/review; current revised values lack immutable first-publication vintages; strict PIT, feature and alpha admission remain closed. FINRA weekly ATS/OTC is context only, not proof of informed trading. No returns, alpha, bootstrap/LOO/OOS, holdout, production, universe, capital or F80 changes.
- [Phase 264 report](PHASE264_FINRA_ATS_FINAL_ARTIFACT_ADJUDICATION_2026-11-10.md) · [result JSON](phase264_finra_ats_final_artifact_adjudication_result.json)


### Operational deployment gate — CFTC prospective capture (2026-11-10 UTC)
- Re-inspected the actual default-branch workflow inventory and the feature-branch workflow. The research branch contains `.github/workflows/phase234_cftc_bpr_prospective_capture.yml`, with a weekday `20:35 UTC` schedule and a `workflow_dispatch` option; the default branch `main` has 53 workflows and does not contain this CFTC capture workflow.
- GitHub scheduled workflows run from the default branch only. A manual dispatch is not a safe substitute: both capture implementations explicitly classify `workflow_dispatch` as manual/non-PIT and do not advance the scheduled baseline. The first scheduled run after activation is baseline-only; only a later newly indexed report observed by a scheduled run can become an event candidate.
- The workflow also requests `contents: write` and commits append-only raw BPR/TFF snapshots into `data/cftc_bpr` and `data/cftc_tff`. This is a repository-write/data-retention change and must be reviewed as part of activation.
- No `data/` directory or CFTC raw snapshot exists on the research branch at this check. Phase 240/243 results independently state that no prospective capture has run and the workflow is not active on `main`.
- Latest live GitHub checks: Phase 231 run [42813734395](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42813734395) completed successfully (job 129821575614; metadata artifact 13764207248); Phase 263 run [42813725617](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42813725617) completed successfully (job 129821373917; artifact 13763672338). Their job steps and logs were inspected. The 10-run same-head PR regression wave is complete; no active or queued run was observed in the latest run page.
- PR #13 remains open on `main`; PR #14 remains open and is stacked on PR #13. No PR was merged. Activation therefore remains blocked until the stacked change is reviewed and reaches `main`, or an explicitly reviewed equivalent default-branch deployment is made.
- This is an operational capture-readiness issue, not evidence of a CFTC signal. No raw capture, return/alpha test, bootstrap/LOO/OOS, holdout use, production, universe, capital or F80 change occurred.


## Phase 265 — FINRA short-flow PIT, calendar and execution audit (2026-11-10 UTC)
- Re-inspected the original Phase 20C source, run [40098425254](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254), job 120885427795, artifact [12562171831](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40098425254/artifacts/12562171831); artifact ZIP SHA-256 `c15f75340bdedfbb37c82f79bb563a450dd1da11989d09e18bb745d93b7d3a5c`.
- Corrected the 2026-10-24 audit's PIT characterization: Phase 20C selects the FINRA row for the signal trade date and uses that same date's close as the forward-return denominator. Its download audit stores only Date and Status; no per-file first receipt, raw hash or immutable correction vintage exists. Chronological selection is not strict PIT.
- Corrected the coverage interpretation: Phase 20C requests every calendar date from D−100 through D inclusive for each signal. 1,382/2,020 = 68.416% is not XNYS-session coverage; weekends/holidays are in the denominator. Actual expected-session coverage remains NOT MEASURED pending an explicit XNYS calendar.
- The 12 pseudo-OOS dates show mean replacement-minus-blocked deltas of +0.141% (H5; median -0.049%), -1.686% (H10) and -0.858% (H20). Factor selection migrated across three features. This is diagnostic evidence only; no incremental alpha or PIT admission.
- Decision: quarantine Phase 20C as chronological but non-PIT diagnostic; do not rerun/retune the same dates; do not use the legacy holdout. New strict-PIT work requires first-receipt UTC, immutable raw hashes/vintages, XNYS-session coverage and next-session execution.
- Hosted validation: [run 42865680262](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42865680262), job 130003254392, 21/21 tests PASS; metadata artifact [13787227070](https://github.com/jafelix81/NuevaEstrategia/actions/runs/42865680262/artifacts/13787227070), ZIP SHA-256 `430c9344619d5af2060d81b4532e531766ecc419fa81acac6d881fb3ec9a1208`.
- [Phase 265 report](PHASE265_FINRA_SHORTFLOW_PIT_CALENDAR_AND_EXECUTION_AUDIT_2026-11-10.md) · [code](phase265_finra_shortflow_pit_calendar_execution_audit.py) · [tests](test_phase265_finra_shortflow_pit_calendar_execution_audit.py) · [result](phase265_finra_shortflow_pit_calendar_execution_audit_result.json) · [workflow](../.github/workflows/phase265_finra_shortflow_pit_calendar_execution_audit.yml)
- F80 remains frozen; no return test, bootstrap/LOO/OOS, holdout use, production, universe or capital change.


## Phase 266 — CFTC capture workflow security hardening (2026-11-10 UTC)
- Static review of the 18 workflow files in PR #14 found the CFTC capture workflow was the only write-capable workflow. Before hardening, workflow_dispatch could be selected on a non-main branch while the job had contents:write, checkout persisted credentials through the parser/network steps, the live workflow did not run the BPR test suite immediately before capture, and git add -A did not reject non-additive archive changes.
- Hardened .github/workflows/phase234_cftc_bpr_prospective_capture.yml: job restricted to refs/heads/main; checkout persist-credentials=false; GH_TOKEN available only in the commit/push step; staged non-additions/renames/deletions fail closed; BPR and TFF test suites run before capture; timeout increased to 20 minutes.
- Added research/test_phase266_cftc_capture_workflow_security.py (7 static contract tests), a dedicated Phase 266 read-only workflow, and Phase 266 report. Phase 240 was also extended to include this contract on its next applicable push.
- The earlier Phase 240 run 42878203544 predates the final CFTC workflow hardening and is not claimed as validation of the hardened workflow. Dedicated Phase 266 hosted validation is pending.
- No live CFTC capture, manual dispatch, data commit, PR merge, production/universe/capital/F80 change, or holdout use.

## Phase 267 — FINRA short-interest pagination, publication-time and vintage audit (2026-11-10 UTC)
- Downloaded and SHA-verified archived Phase 25B run 39389135458/artifact 12248259525 and Phase 25C run 40088483325/artifact 12558485136. Their feature file SHA-256 is identical, so they are not independent replications.
- Both legacy fetchers request limit=10000 but break when len(batch)<10000. FINRA's current API docs cap synchronous requests at 5,000 records; all 55 successful historical responses contained exactly 5,000 rows, and the old artifacts recorded only offset 0 and no Record-Total headers. Completeness is unverified (not an invented exact truncation count).
- The weekend-only settlement calendar queried two XNYS holidays: 2024-01-15 instead of 2024-01-12 and 2024-03-29 instead of 2024-03-28.
- Reconstructing the seventh XNYS session after settlement shows the old pandas BDay(7) knowledge date was one XNYS session early on 19/55 successful cycles. FINRA documents consolidated short-interest availability by 4:40 p.m. ET on publication date; all 55 old training price anchors used a close before the data was available. The Phase 25C 2022-11-25 signal also admitted the 2022-11-15 report one day early: 89 ticker-level latest rows change after correcting availability.
- Phase 25B raw data contains 102 revisionFlag='R' rows across 63 tickers and 9 settlement dates; original as-published values/receipt vintages are not preserved.
- Decision: Phase 25B/25C return summaries are invalid for PIT/OOS inference; no historical alpha or coverage admitted. FINRA short interest remains a prospective candidate only, with first-receipt capture, revisions, complete pagination, and next-session execution required.
- Current FINRA Developer Center docs require OAuth 2.0 Bearer authorization and list Public/Firm/Organization credential types. The old Phase 25B/C client sends no Authorization header. No credential was created, no API terms were accepted, and no live query was attempted. If we choose to deploy FINRA capture, public-credential setup will require user authorization.
- Hosted deterministic audit: push run 42880053761 and PR run 42880064173; 8/8 tests passed; metadata-only artifact 13794580187 (push) / 13794320354 (PR). Push artifact ZIP SHA-256 8923aeb7fe05d1cd5b8df3c0fd4d8f984b79eb40d23e2d3ed0c827a33c589f50; result JSON SHA-256 16a925246e0a1c9d3d2159fa1f77971fecb59b5d74a1911e2f101ea018d1712a.
- [Phase 266 report](PHASE266_CFTC_CAPTURE_WORKFLOW_SECURITY_AUDIT_2026-11-10.md) · [Phase 267 report](PHASE267_FINRA_SHORT_INTEREST_PIT_PAGINATION_AUDIT_2026-11-10.md) · [Phase 267 code](phase267_finra_short_interest_pit_pagination_audit.py) · [tests](test_phase267_finra_short_interest_pit_pagination_audit.py) · [result fixture](phase267_finra_short_interest_audit_input.json).
- F80 remains frozen; no production, universe, capital, parameter, or holdout change.
