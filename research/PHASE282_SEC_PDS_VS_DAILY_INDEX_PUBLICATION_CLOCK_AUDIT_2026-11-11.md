# Phase 282 — SEC PDS versus daily-index public-availability clock

**Date:** 2026-11-11 UTC  
**Status:** `PDS_NOT_A_PUBLIC_FIRST_RECEIPT_CLOCK_DAILY_INDEX_REMAINS_PRIMARY`  
**Control:** `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.  
**Scope:** official SEC PDS system notice, historical PDS technical specification, EDGAR access guidance and Webmaster FAQ. No PDS subscription, vendor contact, SEC download, automated SEC request, raw archive inspection or return test.

## Executive decision

Phase 281 identified historical SEC daily `form.YYYYMMDD.idx` files as a conditional, conservative public-availability bridge for Form 4 accessions. This phase tested whether the EDGAR Public Dissemination Service (PDS) could provide a better clock.

**It cannot replace the daily-index route as the public first-availability clock.** The SEC's PDS page says the service is paid and that the current PDS configuration was changed so filings are available on the SEC public website before they are made available to PDS subscribers. The historical PDS specification describes acceptance/build metadata and a daily list of disseminated filenames, but not a per-submission first-public timestamp in the ordinary `.dissem` file.

PDS may be a secondary source for acceptance/build diagnostics and post-acceptance-correction (PAC) audit, subject to historical-format and archive-availability validation. It is not a prerequisite for Phase 281 and no paid access is justified by the present evidence.

## 1. Current PDS service: paid and downstream of SEC public posting

The SEC's PDS system page, last reviewed 2025-08-01, states:

- PDS is a privatized dissemination service and subscribers must enter a paid subscription agreement.
- PDS offers delivery tracking, retransmission and access to archives of recently accepted/transmitted filings.
- The PDS New Subscriber Document and technical specification were updated to reflect changes ensuring filings are available to the public on sec.gov **before** they are made available through PDS.
- The technical-specification update is dated 2025-05-19; the subscriber document is dated 2025-08-01.

Consequently, a PDS subscriber receipt timestamp after this change is not the first public availability time. It is a later service-delivery timestamp. It could be useful for independent delivery diagnostics, but cannot make the SEC public knowledge date earlier.

## 2. What the historical PDS specification actually records

The inspected 2014 PDS technical specification is historical, not the current 2025 specification. It describes the following:

| PDS object | Documented contents | PIT implication |
|---|---|---|
| `.dissem` | 256-byte control block, SGML submission header and public documents | Control block includes accession, form, receipt date, acceptance date/time and EDGAR build time; it does not define a per-file first-public timestamp |
| `.pc` | Post-acceptance correction header, correction timestamp, optional deletion or metadata changes | Can help identify correction events; old specification says document text is not updated by a PAC |
| `.pr` | Public-ready/private-to-public dissemination with a timestamp | Separate dissemination class; not the ordinary Form 4 live-submission path |
| Daily `dissem*.EOD` | List of `.dissem` and `.pc` filenames sent that day | Day-level audit of the PDS stream, not an exact per-submission public timestamp |

The old specification's statement that acceptance/dissemination usually completes within about two minutes describes the EDGAR processing sequence. It is not a measured first-public timestamp for each accession and cannot override the SEC Webmaster FAQ, which says no timestamp is published for when filing content first becomes available on sec.gov.

**Version caveat:** the SEC now links a 2025 technical-specification ZIP. That current ZIP was not inspected in this phase; the 2014 PDF is used only to understand the historical PDS record model. No assumption is made that every 2014 field layout is unchanged in 2025.

## 3. Comparison with the Phase 281 daily-index route

The SEC's public EDGAR guidance states that daily indexes are available from 1994Q3, contain form type, CIK, filing date and filing path, and are updated nightly. It also distinguishes daily indexes from weekly-rebuilt full/quarterly indexes: later-business-day PAC changes do not rewrite prior daily indexes, while full and quarterly indexes are rebuilt to incorporate PAC changes.

For the Form 4 research panel, the preferred conservative procedure therefore remains:

1. Preserve each Phase 279 quarterly bulk archive and every Form 4/Form 4/A accession as a separate as-filed version.
2. Join each accession to every historical daily `form`-index sighting.
3. Use the earliest verified daily-index date as the conservative daily public-dissemination date; preserve the index bytes, retrieval timestamp and SHA-256.
4. Do not fall back to `FILING_DATE`, acceptance time or a PDS receipt when the daily-index join is missing.
5. For a daily end-of-day strategy, first eligible execution remains no earlier than the close of the next full XNYS session after that index date.
6. Keep missing-index, same-day PAC, later PAC, missing-content and conflicting joins explicitly quarantined.

The daily-index date is still not an exact first-public timestamp. Same-day PAC behavior and raw accession/path parsing remain untested until the Phase 281 sample gate is run.

## 4. Source decision

| Question | Decision |
|---|---|
| Does PDS provide EDGAR acceptance/build metadata? | Yes, in the inspected historical specification |
| Does ordinary `.dissem` expose exact first-public time? | Not documented in the inspected historical specification |
| Does the daily PDS audit file provide a per-filing timestamp? | No; it lists filenames |
| Is PDS first public after the 2025 system change? | No; SEC says sec.gov publication precedes PDS |
| Is PDS free? | No; subscriber agreement is paid |
| Should the project procure/contact PDS now? | No |
| Does PDS replace Phase 281? | No |
| Can PDS remain an optional PAC/acceptance cross-check? | Yes, only if existing lawful archive access and current format are verified |

**Decision:** retain Phase 281 daily-index reconstruction as the primary public-knowledge clock candidate. Do not pursue a PDS subscription or vendor contact. A later, narrowly scoped PDS check is justified only if public Feed archives already accessible to the project can be inspected lawfully and shown to contain the relevant historical records; their contents were not sampled here.

## 5. Research boundary and next gate

- No PDS subscription, vendor contact, purchase, trial or terms acceptance.
- No SEC raw bytes or filing bodies downloaded; no automated SEC request sent.
- No strict PIT admission, return test, alpha test, bootstrap/LOO, OOS or holdout use.
- No production, universe, capital or parameter changes.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen; legacy holdout remains `CONSUMED_NOT_PRISTINE`.

Next step remains the six-quarter Phase 281 sample gate after the authorized `SEC_CONTACT_EMAIL` repository secret is configured. PDS is not required to begin that gate.

## Official sources

1. SEC, [EDGAR Public Dissemination Service (PDS) System](https://www.sec.gov/oit/announcement/public-dissemination-service-system-contact.html), last reviewed 2025-08-01.
2. SEC, [EDGAR PDS Technical Specification (historical 2014 PDF)](https://www.sec.gov/info/edgar/specifications/pds-dissemination-spec030314.pdf).
3. SEC, [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data), daily-index coverage, nightly build and PAC behavior.
4. SEC, [Webmaster Frequently Asked Questions](https://www.sec.gov/about/webmaster-frequently-asked-questions), acceptance-to-public-availability caveat.
5. Repository, [Phase 281 daily-index feasibility report](PHASE281_SEC_DAILY_INDEX_FIRST_PUBLICATION_PIT_FEASIBILITY_2026-11-11.md).
