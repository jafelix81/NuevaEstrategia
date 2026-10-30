# Phase 42B — MIDAS PIT catalog audit

Date: 2026-10-30

## Purpose
Supplement the live SEC MIDAS index audit with the federal Data.gov catalog metadata, without using the catalog as a historical knowledge-date source unless it can support that claim.

## Findings
- SEC's current Metrics by Individual Security page lists quarterly ZIPs from 2012 Q1 through 2026 Q2 and states that the dataset covers January 2012 through June 2026.
- The Data.gov catalog currently lists 58 quarterly resources, from 2012 Q1 through 2026 Q2, and identifies the publisher as the U.S. Securities and Exchange Commission.
- Data.gov reports `inventoried: 2021-12-16`, but its dataset metadata also reports `modified: 2017-10-30T17:43:20Z`. The catalog therefore does not provide a trustworthy per-resource first-publication timestamp for the quarterly ZIPs.
- The current Data.gov resource inventory is dynamic: it includes resources through 2026 Q2 even though the catalog's dataset-level `modified` field is 2017. Consequently, the catalog cannot be interpreted as evidence that every currently listed quarter was publicly downloadable on the inventory date.

## Methodological consequence
The catalog strengthens evidence that MIDAS is a long-lived public data asset and that the quarterly files are stable, named distributions, but it does NOT solve the point-in-time knowledge-date problem.

Do not assign a historical release date from the quarter label, current page review date, catalog modified date, or current catalog resource inventory.

The PIT gate remains NOT PROVEN. Alpha remains unauthorized.

## Next acceptable evidence
1. Timestamped historical snapshots of the SEC download index or equivalent official archive;
2. an official timestamped publication record for each quarterly distribution; or
3. an independently justified conservative lag convention, applied uniformly, followed by sensitivity analysis across plausible lags.

## External references checked
- SEC Metrics by Individual Security: https://www.sec.gov/data-research/sec-markets-data/marketstructuredata-security
- Data.gov Metrics by Individual Security catalog: https://catalog.data.gov/dataset/metrics-by-individual-security
