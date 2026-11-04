# Phase 61 — ORATS Near-EOD public sample feasibility

## Purpose

Inspect the public ORATS Near-EOD sample before any paid archive purchase. This is a schema and one-date universe-coverage audit only.

Official product page: https://orats.com/near-eod-data  
Public sample: https://s3.amazonaws.com/assets.orats.com/ORATS_SMV_Strikes_20240103.zip

## Documented product claims to verify where possible

- Daily US equity-options chain snapshot around 3:46 p.m. ET.
- Every strike and expiration for 5,000+ symbols.
- History from 2007.
- Bid/ask, call/put volume, previous-night OCC OI, SMV IV and Greeks.
- Delisted tickers retained from 2007-01-01.
- Historical archive delivered through S3; one-time individual price shown as $599, approximately 500 GB; recurring daily files shown as $99/month. Professional/institutional licensing is quoted separately.

## Audit outputs

- SHA256 and byte size of the downloaded public sample.
- ZIP member names and CSV schema.
- Row count, unique underlyings and coverage of the frozen 335-name candidate list.
- Non-null, numeric, positive and zero rates for volume, OI, bid/ask, IV and Greeks.
- Presence/absence of contract multiplier or deliverable fields.
- Presence/absence of independent underlying stock-price fields.
- Explicit PIT limitations: a historical file archive does not prove when each historical file first became available. Default KnowledgeDate is next trading session; volume is a 3:46 p.m. cumulative snapshot and OI is prior-night OCC.

## Acceptance and limits

A one-date public sample cannot prove 2007+ historical coverage, delisted retention, expired-contract continuity, stable PIT identifiers or correction-file timing. Those require additional date samples and vendor documentation. The workflow must not calculate forward returns or alpha. No purchase is authorized.
