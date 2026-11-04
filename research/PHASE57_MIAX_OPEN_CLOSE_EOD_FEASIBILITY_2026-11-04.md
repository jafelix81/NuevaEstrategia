# Phase 57 — MIAX Open-Close EOD feasibility review
Date: 2026-11-04
Branch: phase57-miax-open-close-feasibility
Status: CONDITIONAL SECONDARY SOURCE; no data acquired and no return test authorized.

## Research question

Can MIAX Open-Close EOD reports provide a feasible, independently sourced participant-specific option-flow panel to replicate or complement Cboe Open-Close signals, while retaining full-OPRA context and strict point-in-time availability?

## Official product facts

### Exchange coverage and history
- MIAX Options, MIAX Pearl Options and MIAX Emerald Options introduced Open-Close reports on 2021-06-01. EOD history is available from June 2021.
- MIAX Sapphire EOD history begins 2024-08.
- The reports are separate by exchange and cover each option series traded on that exchange.
- MIAX's report page says the EOD file is available at approximately 06:00 ET on the calendar date following the trading date, after overnight processing. This is a reproducible conservative availability statement, but production should retain actual delivery timestamps.
- EOD adds first/high/low/close trade price, industry volume and open interest to the origin/buy-sell/open-close quantities.
- Origin categories must be preserved exactly as MIAX defines them: Priority Customer, Non-Priority Customer, Firm, Broker-Dealer and Market Maker. Do not force a one-to-one mapping to Cboe Customer/Pro Customer labels.

Official sources:
- 2021 launch/history and 06:00 ET availability: https://www.miaxglobal.com/alert/2021/09/02/miax-exchange-group-options-markets-introducing-availability-open-close
- Current MIAX Options report description: https://aws.miaxglobal.com/markets/us-options/miax-options/reports
- 2025 history and pricing summary: https://www.miaxglobal.com/alert/2025/12/19/miax-exchange-group-options-markets-fee-change-extend-historical-open-close
- 2026 discount extension through year-end: https://www.miaxglobal.com/alert/2026/06/30/miax-exchange-group-options-markets-july-1-2026-fee-changes-2
- Sapphire report page: https://www.miaxglobal.com/markets/us-options/sapphire-options/reports

### Historical pricing / access
- Published EOD historical price: $500 per request per month of data per exchange; EOD subscription: $600 per month per exchange. Confirm the exact current invoice and selected exchange coverage directly before any order.
- MIAX Options, Pearl and Emerald EOD history begins June 2021; Sapphire begins August 2024.
- The 2026-07-01 to 2026-12-31 historical discount is 20% on qualifying historical orders of $20,000 or more by existing subscribers; Sapphire has no minimum purchase size for that discount. Do not assume eligibility or apply the discount to a small pilot.
- The report requires a MIAX Exchange Data Agreement and Schedule B Data Feed Request; delivery is via MIAX SFTP. No public free sample or automatic entitlement was verified.
- A six-month historical pilot for the three older exchanges would be approximately $9,000 at the published $500/request/month rate, before any negotiated terms. This is an estimate, not a quote; no purchase has been made.

## Why it is useful

MIAX supplies a second exchange-group classification of options activity with origin, buy/sell and open/close, and a separate venue history. It can serve as an independent venue replication of a Cboe participant-flow hypothesis. The EOD delivery around 06:00 ET next calendar day is compatible with conservative next-session KnowledgeDate treatment.

It does not reveal the entire OPRA market, identify beneficial owners, or prove that any origin category is informed. MIAX and Cboe categories are not interchangeable. The MIAX industry-volume and OI fields require their own unit/provenance and historical-convention audit.

## Coverage and feasibility gates (not yet tested)

1. Obtain a one-month representative sample/specification for MIAX Options, Pearl and Emerald; add Sapphire only for dates on/after 2024-08.
2. Measure ticker/date coverage against the point-in-time F80 membership and a full-OPRA optionability panel, not merely the current 335 names.
3. Report both all-335 reach and coverage among historically optionable F80 members. Absence from a venue's report means no observed execution on that venue/date, not necessarily no listed option.
4. Reconcile series identifiers, adjusted roots, contract multiplier and deliverables against OCC reference data.
5. Validate participant category definitions, size buckets, units, whether quantities represent the initiating side, and totals against exchange-level volume.
6. Validate actual file delivery time, missing/corrected files, holidays, and the 06:00 ET next-calendar-day statement.
7. Confirm internal-use/derived-data licensing and exact per-exchange historical price.

## Proposed role / decision

- Role: independent cross-exchange replication and possible complementary flow feature, not primary alpha source.
- Priority: after Cboe's full-OPRA/Cboe sample gates and pricing are clarified. Avoid spending on multi-year MIAX history before a Cboe hypothesis survives an initial preregistered test.
- No return test, no feature selection, and no alpha claim until coverage, PIT, reference-data and licensing gates pass.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.


## 2026-11-04 addendum — 1-minute historical depth and current fee schedule

The earlier report described EOD history only. A later official MIAX alert identifies a deeper historical archive for the **1-minute intraday** Open-Close report:

- MIAX Options: January 2013.
- MIAX Pearl: March 2017.
- MIAX Emerald: March 2019.
- MIAX Sapphire: August 2024.

The 1-minute files are cumulative snapshots generated from 09:31 through 16:20 ET (410 files on a full session). A 1-minute subscription includes 10-minute and EOD reports. The last cumulative interval may be usable as a session aggregate, but this must be confirmed against the delivered file specification and an actual sample; do not assume it contains the EOD-only price/industry-volume/OI fields.

Official launch/history alert (2026-01-23):  
https://www.miaxglobal.com/alert/2026/01/23/miax-exchange-group-options-markets-introducing-availability-1-minute

Official fee establishment alert (2026-01-30):  
https://www.miaxglobal.com/alert/2026/01/30/miax-exchange-group-options-markets-fee-changes-establish-fees-1-minute

The current MIAX Options fee schedule as of 2026-11-01 confirms for MIAX Options:
- EOD subscription: $600/month; historical EOD: $500 per request per month of history, from June 2021.
- 10-minute subscription: $3,000/month; historical 10-minute: $1,000 per request per month of history, from January 2013.
- 1-minute subscription: $9,000/month; historical 1-minute: $4,000 per request per month of history, from January 2013.
- A 1-minute historical request includes the same date range of 10-minute and EOD historical data at no extra charge; a 10-minute request includes EOD.
- Qualifying academic historical 1-minute pricing is separately stated; eligibility is not assumed.

Current official MIAX Options fee schedule (2026-11-01):  
https://www.miaxglobal.com/sites/default/files/fee_schedule-files/MIAX_Options_Fee_Schedule_11012026.pdf

The January 30, 2026 alert lists the 1-minute subscription at $6,000/month and historical ad-hoc 1-minute data at $2,500 per request per month for Pearl, Emerald and Sapphire. Confirm each exchange's current fee schedule before any order.

### Research priority correction

For a daily end-of-day strategy, 1-minute history is not automatically worth its materially higher price. Prefer an EOD pilot first; consider 10-minute data only if the hypothesis requires intraday timing. The 1-minute archive is a valuable historical option, not a purchase recommendation. MIAX remains a secondary venue replication source, not full OPRA and not beneficial-owner identity.
