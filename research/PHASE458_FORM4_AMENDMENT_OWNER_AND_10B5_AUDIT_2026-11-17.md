# Phase 458 — Form 4 amendment-state, reporting-owner grain and 10b5-1 flag audit

**Audit date:** 2026-11-17  
**Disposition:** Form 4 remains a conditional source, but the bulk tables alone are not sufficient to construct transaction-level insider breadth or purchase signals. A verified 2026Q3 Form 4/A corrected two original P-coded rows from disposition (D) to acquisition (A). Amendments must be modeled as later information-state updates, not new trades or backdated corrections.

## 1. Immutable input and reproducibility

- Source artifact: [Phase 39 run 40606706518](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518), [artifact 12781850078](https://github.com/jafelix81/NuevaEstrategia/actions/runs/40606706518/artifacts/12781850078).
- Artifact SHA-256: 203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66.
- Nested archives: 2012Q1 SHA-256 0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357; 2026Q3 SHA-256 a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3.
- Only SUBMISSION.tsv, REPORTINGOWNER.tsv and NONDERIV_TRANS.tsv were parsed. No raw SEC data or transaction rows are committed. The auditor fails closed on hash, required-header, primary-key or duplicate-key errors.

## 2. Reporting-owner grain: material limitation for clustered-insider hypotheses

The bulk REPORTINGOWNER table is keyed by accession and reporting-owner CIK. NONDERIV_TRANS is keyed by accession and transaction surrogate key and has no reporting-owner CIK. Therefore, in a joint filing, the bulk tables do not establish which reporting owner executed each transaction line.

| Measure | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Form 4 / 4-A accessions | 63,678 | 34,148 |
| Accessions with multiple reporting owners | 1,134 (1.781%) | 854 (2.501%) |
| P-coded accessions | 4,136 | 3,211 |
| P-coded accessions with multiple owners | 380 (9.188%) | 238 (7.412%) |
| P-coded rows inside multi-owner accessions | 1,134 / 7,180 (15.794%) | 694 / 5,183 (13.390%) |

This is not a negligible edge case for an insider-clustering signal. Counting every owner on a joint filing as a buyer would fabricate breadth; assigning every transaction row to every owner would multiply the same trade. Until original XML/exhibits provide a deterministic owner-to-transaction attribution, multi-owner accessions must be quarantined from owner-breadth and clustered-buy features. The issuer-level transaction may remain descriptive.

## 3. Verified amendment correction: P/D became P/A

The 2026Q3 archive contains this original/amendment pair for CytoMed Therapeutics (GDTC, issuer CIK 0001873093):

- Original Form 4: accession 0001493152-26-034516, accepted by EDGAR on 2026-07-24 at 12:33:42 ET.
- Form 4/A: accession 0001493152-26-034654, accepted on 2026-07-24 at 21:01:08 ET.
- The original contains two non-derivative rows with TRANS_CODE=P and TRANS_ACQUIRED_DISP_CD=D (100,000 shares on 2026-07-14 and 100,000 on 2026-07-20).
- The amendment contains the same two rows with TRANS_CODE=P and TRANS_ACQUIRED_DISP_CD=A.
- The amendment's own footnote states that it corrects Column 4 of Table I from D to A and makes no other changes.

Official SEC source documents: [original submission text](https://www.sec.gov/Archives/edgar/data/1873093/000149315226034516/0001493152-26-034516.txt) and [amendment submission text](https://www.sec.gov/Archives/edgar/data/1873093/000149315226034654/0001493152-26-034654.txt). The original XML and amendment XML are both included in those SEC submissions. The original disclosure should not be treated as a confirmed purchase while its A/D field says D; the amendment later corrects the acquisition/disposition indicator.

Across the two audited archives:

| Measure | 2012Q1 | 2026Q3 |
|---|---:|---:|
| P-coded non-derivative rows | 7,180 | 5,183 |
| P-coded rows with A/D=D | 57 | 6 |
| Same-quarter unique heuristic amendment links | 1,046 | 291 |
| Ambiguous same-quarter candidate links | 26 | 3 |
| No in-quarter original candidate | 790 | 333 |
| P/D to P/A corrections found in linked sample | 0 | 2 |

The amendment join is deliberately labelled heuristic, not authoritative: same issuer CIK, original filing date, period of report and at least one shared reporting-owner CIK. The bulk archive does not provide an explicit parent accession ID. “No in-quarter candidate” can mean that the original is in another quarterly archive; it is not proof that no original exists. The two 2026Q3 corrections were independently verified against the actual SEC submission text.

**Point-in-time consequence:** the original P/D state is what was public at the original acceptance time. The corrected P/A state becomes known only when the Form 4/A is accepted. Do not backdate the corrected A to the original filing or count the amendment as two new trades. The conservative tradable event must use the amendment's own knowledge time (and the project's next-full-session rule), not the transaction date or original filing time.

## 4. AFF10B5ONE: submission-level flag and schema-era break

The 2012Q1 archive has no AFF10B5ONE column. All 4,136 P-coded accessions are therefore unknown, not false.

The 2026Q3 archive has the field. It serializes both 0/1 and false/true; the auditor normalizes these without treating missing/unsupported values as false. Among 3,211 P-coded accessions, 82 are flagged yes (2.552%) and 3,129 no. This is a filing-level field, not a transaction-row owner/plan join. Use it as filing context or a stratification, not as proof that every row in a multi-transaction filing has independently resolved plan status. Preserve the documented pre-coverage period as unknown.

## 5. Transaction-form type is not the submission document type

TRANS_FORM_TYPE is a transaction-line field. The 2026Q3 sample contains 25 P-coded rows with TRANS_FORM_TYPE=5 inside Form 4 submissions; the 2012Q1 sample contains 205. A SEC Form 4 submission can therefore contain a line whose transaction-form-type field is 5. For example, the original NCT filing 0001493152-26-044229 has documentType=4 and a P-coded transaction with transactionFormType=5 in the same SEC submission ([official SEC submission text](https://www.sec.gov/Archives/edgar/data/2018529/000149315226044229/0001493152-26-044229.txt)). Do not use TRANS_FORM_TYPE as a substitute for SUBMISSION.DOCUMENT_TYPE, and do not drop those rows without a separate semantic rule. The official data dictionary describes the field as “Transaction form type”; it does not justify collapsing the two grains.

## 6. Signal-construction rules implied by this audit

1. Preserve each accession as a separate disclosure-arrival event.
2. Maintain an amendment lineage/state table. Apply corrected transaction fields at the amendment's acceptance/first-seen time; never rewrite the historical original state or create duplicate economic trades.
3. TRANS_CODE=P alone is not enough for a purchase label. Require a coherent TRANS_ACQUIRED_DISP_CD=A state, retain conflicts as unresolved pending amendment/footnote review, and still distinguish open-market from private purchase using the full filing/footnotes.
4. Exclude multi-owner accessions from insider-breadth/cluster counts unless XML-level owner-to-line attribution is deterministic. Never assign one transaction to every owner by default.
5. Treat AFF10B5ONE as filing-level context; pre-field history is unknown. Do not infer absence of a plan from a missing historical column.
6. Keep TRANS_FORM_TYPE separate from submission DOCUMENT_TYPE.
7. Do not run returns until historical security/class identity, historical universe membership, acceptance/first-seen timing and survivorship-aware prices pass.

## 7. Research decision

This is a data-integrity and event-sourcing result, not alpha. It materially changes how Form 4 events must be represented, but does not justify an event study on the two endpoint quarters or the current 335-symbol snapshot. The next useful gate is to expand amendment reconciliation across all 83 quarterly archives with authoritative accession lineage from original EDGAR submissions, then resolve transaction-owner attribution and effective-dated security identity.

No forward-return, alpha, OOS, bootstrap, LOO or holdout test was run. No signal was admitted. No vendor data were purchased. F80_TOP20_PARTIAL50_BASELINE_C20, universe, parameters, capital, exposure, holding rules, holdout and production remain frozen.

## 8. Reproduction

    python -m unittest -v research.test_phase458_form4_amendment_owner_audit
    python -m research.phase458_form4_amendment_owner_audit --artifact phase39_form345_actual_file_audit.zip --output phase458_result.json
