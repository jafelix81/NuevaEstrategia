# Phase 620 — SEC Form 4 entity-aware feed occurrence audit and canonical selection

## Audit cutoff

2026-11-25 15:21 UTC. Main HEAD reviewed: `074e3596b6982308889ed33e614ec4e169005ee5`.

Source run: [Phase 476 / run 45620008946](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45620008946). Both jobs completed successfully. The 4,107-byte artifact 15023279430 contains the compact poll summary and downstream Phase 510/525 summaries, but not the accession-occurrence ledger. The latter was therefore read directly from the main-branch Git blob (SHA `06ec9509fb4aba6c1f37d1aeea17d259fbaaea94`).

## Finding: the 38 repeated accessions are entity-level feed rows, not pagination duplicates

The 74 candidate occurrences in the Form 4 feed reconcile as follows:

| Measure | Result |
|---|---:|
| Candidate accession occurrences | 74 |
| Unique candidate accessions | 36 |
| Repeated same-feed occurrences | 38 |
| Accession groups with 2 entity rows | 35 |
| Accession groups with 4 entity rows | 1 |
| Groups spanning more than one page offset | 0 |
| Groups with multiple archive-path CIKs | 36 |

All 36 groups have the same accession-level form, filing date and Atom `updated` value within the group. The rows differ by archive-path CIK and filing URL. All repeated rows occur within a single page hash/offset; there is no evidence of a page-boundary overlap or a repeated-page pagination failure in this run.

The four-row example is accession `0000947871-26-001051`. Its four path CIKs are:

- `0001739410` — Avenzo Therapeutics, Inc. (issuer)
- `0001055951` — ORBIMED ADVISORS LLC (reporting owner)
- `0001808744` — OrbiMed Genesis GP LLC (reporting owner)
- `0001920574` — OrbiMed Capital GP IX LLC (reporting owner)

Public filing metadata independently identifies that issuer and the three reporting owners ([filing cross-check](https://disclosery.com/filings/0000947871-26-001051); [entity-level detail](https://bakercapitalstrategies.com/filings/1920574/0000947871-26-001051/orbimed-capital-gp-ix-llc-4)). SEC's ownership XML specification permits multiple reporting owners in one submission ([SEC technical specification](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf)). SEC also explains that the first ten digits of an accession are the login CIK, which may belong to a filer or a filing agent and is not necessarily the issuer ([SEC login CIK guidance](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/understand-select-set-default-login-cik)).

This is consistent with the EDGAR `owner=include` feed returning an entity-level row for the issuer and each reporting owner. The accession is the filing-level key; the path CIK is an entity-level locator. The old collector correctly deduplicated the accession for event count, but incorrectly treated repeated entity rows as generic duplicates and selected the first path CIK. That first row is not guaranteed to be the issuer.

**Scope limitation:** the role/name mapping above is independently checked for the four-row example, not for all 36 accessions. The historical ledger did not preserve Atom titles, so the remaining 70 entity occurrences cannot be retrospectively role-labelled from the stored rows alone.

## Phase 620 implementation

The collector now parses the Atom title into:

- feed entity name;
- feed entity CIK;
- feed entity role (`ISSUER` or `REPORTING`);
- title-parse status.

It separately preserves the accession-prefix/login CIK and the archive-path CIK. A path/entity-CIK match is required before the occurrence can support canonical entity selection.

### Canonical event rules

1. Keep every issuer/reporting occurrence in the new append-only `entity_observations.csv` sidecar.
2. Deduplicate the underlying filing on accession, not on title or entity CIK.
3. If one issuer CIK is present and every parsed path CIK matches its title CIK, select the issuer occurrence as the canonical event locator.
4. If no issuer row is present, retain the accession-level metadata event but blank the URL/path locator; never substitute a reporting-owner URL as the issuer URL.
5. If any parsed path CIK conflicts with its title CIK, or multiple distinct issuer CIKs appear for one accession, quarantine the accession and emit no canonical event.
6. Preserve existing `accession_observations.csv` unchanged. The new entity sidecar avoids rewriting its append-only schema.

The sidecar records the entity name/CIK/role, accession submitter CIK, path-CIK match, page hash/offset, poll and interval metadata, repeat-occurrence marker, canonical selection status and quarantine status. The compact `entity_summary.json` is included in the normal workflow artifact.

The workflow continues to store metadata only. No Form 4 XML, transaction rows or non-public information is fetched or added by this phase.

## Regression coverage

Six new tests cover:

- feed entity parsing and separation of accession-prefix CIK from entity CIK;
- one issuer plus three reporting owners, with issuer selected as canonical;
- path/entity-CIK mismatch quarantine;
- conflicting issuer CIK quarantine;
- missing issuer row with locator omitted;
- persistence of all entity occurrences and issuer-canonical marking in the sidecar.

The existing same-feed repeat counter remains for backward compatibility, but it is now interpreted as repeated accession/entity occurrences, not as evidence of a pagination defect. The first PR run exposed one test-fixture mistake (the initial-baseline fixture included a supposed watermark without a prior state); the fixture was corrected. Final PR validations [45644057878](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45644057878) and [45644162986](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45644162986) passed `py_compile` and all 69 offline tests. The live-capture job was skipped.

## Separate cadence issue

This phase does not fix the independently observed capture cadence. The current mainline ledger still shows 14 successful Form 4 poll windows and 13 gaps: median 8.676 hours, p90 12.490 hours, maximum 54.964 hours. The latest gap was 10.519 hours. No cron change or manual dispatch was made.

## Research disposition

- Phase 619 duplicate-occurrence hypothesis: **reclassified**. The observed repeats are expected multi-entity rows; no pagination defect was established.
- Historical role reconstruction for the 74 occurrences from run 45620008946: **unresolved**, because titles were not persisted.
- Future entity-level capture: **implemented, live prospective validation pending**.
- Research-observation eligible rows: 0.
- Signal-eligible rows: 0.
- No event study, OOS, bootstrap or LOO run is justified by this metadata audit.

`F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen. No capital, exposure, universe, cost, parameter or production changes. No paid data was purchased or requested; options-data budget remains USD 0.
