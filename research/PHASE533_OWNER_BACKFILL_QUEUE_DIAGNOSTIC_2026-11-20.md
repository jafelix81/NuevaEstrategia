# Phase 533 follow-up — Atea owner-backfill queue diagnostic (2026-11-20)

## Finding

The zero-row crosswalk from scheduled Form 4 run 44794670480 is explained by bounded owner-enrichment coverage, not by a failed match rule.

I reproduced the exact candidate-selection logic in `research/phase525_form4_reporting_owner_identity.py`:
- `read_structured_accessions` reads parsed `filing_header` accessions in the existing transaction-ledger order.
- Completed owner accessions are excluded.
- Candidates must have a corresponding validated first-seen Form 4 event.
- Candidates are stably sorted by ascending `first_seen_at_utc`.
- The scheduled workflow processes the first 10 candidates.

At the post-run snapshot there were 30 structured accessions, 10 completed owner accessions, and 20 pending owner candidates. The two Atea Form 4 accessions previously reviewed manually are ranked **2 and 3** in the exact next batch:

1. `0001841761-26-000127`
2. `0001193125-26-469038` — Atea Pharmaceuticals / Bruno Lucidi
3. `0001193125-26-469037` — Atea Pharmaceuticals / Bruce Polsky
4. `0002052022-26-000011`
5. `0001193125-26-469031`
6. `0000919574-26-008202`
7. `0001493152-26-053331`
8. `0001493152-26-053329`
9. `0001193125-26-469022`
10. `0001193125-26-469021`

Both Atea accessions already exist in `transaction_details.csv`; the corresponding Form 144 accessions `0001950047-26-011348` and `0001950047-26-011363` exist in `sale_details.csv`. The Atea Form 4 accessions were absent from `reporting_owners.csv` only because the first scheduled owner backfill processed the ten older candidates.

## Next natural validation

The next existing weekday Form 4 cron slot after this audit is 2026-11-20 20:17 UTC. Do not dispatch or rerun it manually. If the scheduled run succeeds, inspect whether both Atea accessions are appended to the owner sidecar and whether the strict crosswalk produces the expected exact matches.

A match is still descriptive only. Do not relax issuer/owner/date/share/class matching, infer line-owner attribution, or authorize a signal. Public availability remains uncertified and no forward-return or alpha test is authorized.

## Disposition

- The operational blocker in Issue #185 remains resolved and the issue remains closed.
- This queue diagnostic is not a new signal or alpha result.
- No code, data, workflow, universe, model, cost, exposure, holdout or production changes.
- `F80_TOP20_PARTIAL50_BASELINE_C20` remains frozen.
