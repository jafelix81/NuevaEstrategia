# Smart Money Research — Phase 671 state addendum

**Cutoff:** 2026-11-27 21:04 UTC  
**Phase:** 671 — SEC 13F value-unit detector control calibration  
**Base:** \`main\` \`521cc3ff59aae222fe32c519fc024425bce6a777\`

## Preflight

- Checked the latest 100 Actions runs, jobs, logs, artifacts, branches, open PRs and current research files before work. Latest 100 run conclusions: 78 success, 18 failure, 4 cancelled; zero active/queued.
- Phase 669 Form 4 run 46057111964: successful. Logs confirm 94 new bounded metadata accessions, 201 entity observations, 21 transaction-detail rows, 30 linked footnote references plus 50 additional footnote references, 10 single-owner accessions and zero signal-eligible rows. Artifact is a compact poll summary, not raw filings.
- Phase 614 SEC 13F run 46026323554: successful. Logs confirm 15 new metadata observations, all four feeds complete and zero research/signal-eligible rows. Artifact contains only poll_summary.json, not holdings XML.
- PR #259 / Phase 670 was updated with four row-level amendment-table samples, manually JSON-validated, marked ready and squash-merged to main as 521cc3ff59aae222fe32c519fc024425bce6a777. No code or production parser changed in that PR.
- No active workflows were present after the merge. No live capture was manually dispatched.

## New calibration result

A same-quarter SEC primary negative control was added to the Canada Life anomaly evidence:

- Canada Life amendment (CIK 1046192, accession 0001046192-26-000018): four ordinary common-stock rows from the SEC-indexed information table support scale factor 1,000 within 0.11% of 2026-09-30 closes.
- Home Federal Bank of Tennessee (CIK 1665446, accession 0001665446-26-000004): five ordinary common-stock rows from its SEC primary information table support scale factor 1 (nearest-dollar) with maximum absolute price deviation below 0.00018%.
- Canada Life base filing has only two sampled rows; it deliberately remains below the detector's minimum four-unique-CUSIP threshold and is classified insufficient evidence.
- This rejects a blanket 1,000× multiplier for all post-2023 Form 13F filings.

A new fail-closed retrospective classifier is proposed in \`research/phase671_13f_value_unit_detector.py\`. It requires at least four unique ordinary common-stock CUSIPs, exact report-date reference prices, 80% consensus and median relative error ≤0.5%. It emits a scale candidate only; it never normalizes source values or creates a trading feature. These thresholds are initial engineering guardrails, not statistically optimized or production-validated.

## Controls

- Offline-only Python module and unittest suite; no external requests or secrets.
- Production parser unchanged; no normalized data written.
- No post-event returns, event study, OOS, bootstrap or LOO run.
- Holdout untouched; \`F80_TOP20_PARTIAL50_BASELINE_C20\` frozen.
- Data spend USD 0.

## Next

1. Retrieve and SHA-256 hash the full Canada Life amendment XML via the established SEC User-Agent path.
2. Parse all 806 entries and compare with the original filing.
3. Expand the detector control cohort to at least 20 independent positive and negative filings across multiple post-2023 quarters.
4. Only then consider production integration; preserve immutable as-filed values and require human approval for normalization.
5. Continue FINRA, Form 4, 13D/G and CFTC work independently. No signal is promoted from this audit.
