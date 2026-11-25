# Smart Money Research state addendum — Phase 610 (2026-11-25 UTC)

- Phase 610 audits SEC filing-detail Accepted timestamps for six 13F accessions across 2018 and 2026.
- The script parses Accepted, Filing Date and Period of Report from EDGAR filing-detail HTML, records page hashes, and tests whether the Accepted calendar date matches Filing Date.
- A conservative fallback date is one calendar day after Filing Date; first subsequent XNYS session mapping remains a separate validated-calendar gate.
- Live result pending. No full-history acceptance-time coverage or backtest is claimed.
- Baseline remains frozen; no data purchase or options quote; options budget USD 0.
