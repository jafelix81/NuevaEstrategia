# Phase 306 — SEC Latest Filings RSS contiguous overlapping scan

**Date:** 2026-11-12  
**Status:** protocol committed; hosted scan pending.  
**Branch:** \`phase306-sec-rss-contiguous-overlap-scan\`

## Research question

Phase 305 established that the SEC Atom \`start\` parameter offsets entity rows, not unique accessions; \`count=100\` is the effective page size; and \`type=4\` is a prefix filter that includes non-target forms. This phase tests whether a contiguous, overlapping scan can reconstruct the current Form 4 and Form 4/A feed snapshot without losing multi-owner rows or silently claiming completeness when the feed changes during pagination.

## Protocol

- Query both Form 4 (\`type=4\`, exact title-token filter required) and Form 4/A (\`type=4/A\`).
- Use \`count=100\`, \`start=0,80,160,...\`, and a 20-entity-row overlap between adjacent pages.
- Scan at most 25 pages per form (2,020 raw row positions maximum); stop at the first page with fewer than 100 raw entity rows.
- Preserve each raw Atom page, response headers, poll-start/completion UTC timestamps, and SHA-256.
- Retain all raw entity rows; build a separate exact-form target ledger.
- Deduplicate by accession/entity-role/entity-CIK/filing-link while preserving arbitrary reporting-owner multiplicity.
- Verify every adjacent page overlap against the expected 20 raw rows, re-fetch page zero after the scan, and compare ordered row fingerprints to detect feed drift.
- Flag accessions whose entity rows span page windows; do not collapse multiple owners.
- Treat a capped scan, failed page, unexpected overlap, changed page-zero snapshot, row conflict, or structural mismatch as incomplete/unstable coverage.

## Interpretation limits

- A complete result means only that the observed current feed snapshot was scanned to a short tail with stable overlaps and a stable page-zero recheck. It is not a historical archive or proof of long-term feed retention.
- Atom \`updated\` remains an acceptance-time proxy in the cross-checked samples, not an independent first-public timestamp.
- No exact first-public timestamp, strict PIT admission, PAC event capture, security-class identity, or transaction-line-to-individual-owner attribution is established by this phase.
- The \`type=4\` endpoint remains a prefix query; non-target forms are retained in raw pages and counted separately.

## Frozen controls

\`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen. No production, universe, capital, parameter, vendor, licensing, or holdout changes. No return/alpha, bootstrap/LOO, or chronological OOS test is authorized by this source-coverage audit.

## Hosted result

Pending.
