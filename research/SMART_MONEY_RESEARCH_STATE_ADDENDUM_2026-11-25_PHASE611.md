# Smart Money Research State Addendum — 2026-11-25 (Phase 611)

## Current state

- **Phase 611:** bounded SEC 13F timestamp feasibility audit PASS; 12/12 offline regression tests passed.
- 2018 Q1: 6,570 accessions with cover pages; 24/24 stratified sample checks PASS.
- 2026 Jun–Aug: 11,852 accessions with cover pages; 24/24 stratified sample checks PASS.
- 48/48 filing-detail pages reconciled across accession, filer-CIK archive path, form, filing date, period of report, Accepted timestamp and SEC legal filing-date clock.
- Timestamp mix: 6 pre-market, 32 regular-session clock, 10 after-close, zero weekend acceptances.
- Filing-date clock: 44 same-day; 4 accepted after 17:30 ET and legally deemed filed the next SEC business day; zero unresolved mismatches.
- The 5:30 p.m. rollover is now encoded and regression-tested using 17 CFR §232.13(a)(2); SEC non-business days are handled under §232.12. 13F does not appear in the enumerated 10 p.m. exceptions.
- `SEC_USER_AGENT` was absent; the existing shared project contact fallback succeeded. No human intervention required.
- Phase 611 live workflow: [45535351139](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139); artifact [14986657502](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45535351139/artifacts/14986657502).
- PR [#228](https://github.com/jafelix81/NuevaEstrategia/pull/228) remains a draft, stacked on Phase 610; no production merge.

## New methodological rule

Do not require SEC `Accepted` calendar date to equal the displayed `Filing Date` for 13F. For general filings, acceptance after 17:30 ET is deemed filed on the next SEC business day. Store both clocks, reconcile them under the legal rule, and do not substitute the legal filing date for the exact acceptance timestamp.

For a historical strategy replay, the eventual knowledge time must be conservative: combine EDGAR Accepted with any independently recorded collector first-seen timestamp, then map to the first fully completed XNYS decision bar only after the exchange calendar and dissemination assumptions are validated.

## Other active capture

- Latest scheduled Form 4 run [45533818624](https://github.com/jafelix81/NuevaEstrategia/actions/runs/45533818624): 593 new Form 4 accessions captured; 24 structured detail rows appended in the bounded detail pass; 0 research-observation-eligible rows and 0 signal-eligible rows. The run did not download raw XML. Keep these as non-signal observations pending owner/security identity and verified public-availability treatment.

## Open gates

1. Broaden SEC 13F timestamp sampling across more quarters and schema eras; Phase 611 is not an all-history coverage claim.
2. Join accepted timestamps to prospective first-seen observations where available.
3. Validate first fully completed XNYS bars without look-ahead.
4. Finish effective-dated CUSIP/FIGI-to-F80 mapping; current CIK discovery is not historical security identity.
5. Reconstruct 13F manager/amendment state with the Phase 48 and 605 controls before feature creation.
6. Only then test institutional ownership/persistence/accumulation incrementally versus frozen F80/LTM.

## Research discipline

- No interpretation of 13F as real-time flow or net exposure.
- No alpha or OOS claim from this feasibility audit.
- No incomplete-universe comparison.
- No changes to `F80_TOP20_PARTIAL50_BASELINE_C20`.
- No changes to capital, exposure, parameters or production.
- Options and paid data budget remain USD 0.
