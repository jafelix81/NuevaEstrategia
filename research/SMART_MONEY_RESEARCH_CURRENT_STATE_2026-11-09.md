# Smart Money Research — Current State

**Updated:** 2026-11-09  
**Research branch:** \`phase99-broad-pit-universe-charter\`  
**Frozen production baseline:** \`F80_TOP20_PARTIAL50_BASELINE_C20\` — unchanged

## Latest material updates

### Phase 231 — Cboe Option Quotes full-row reparse
- Public sample hash pinned and reverified: \`7645a6cc94f1a984e98264a4b494f748e373c30ecde85de25ceadb83a5c56782\`.
- 115,617 populated row instances across five data members.
- 3,304 ambiguous expiration rows quarantined; no locale guessing.
- 112,313 unambiguous rows passed the full row-level contract/numeric/duplicate/OI checks.
- 0 invalid quote timestamps, 0 numeric errors, 0 duplicate contract/interval keys, 0 inconsistent start-of-day OI contract-days, 0 bid-above-ask rows.
- Independent Phase 175 all-row date diagnostics reconciled on all five members.
- Current-head GitHub Actions run \`42568771468\` succeeded; 9/9 regression tests; artifact \`13651429847\`.
- Sample remains too narrow (two quote dates and only one or two underlyings per file) for historical coverage. Source is not PIT- or alpha-admitted.

### Phase 232 — Cboe Option Sentiment feasibility
- Public spec v1.4 (05/25) documents 80 daily fields and a historical start of January 2012.
- Rich candidate fields: directional net option delta and premium/volume, OI, customer/firm/market-maker clearing categories, size/DTX buckets, IV/skew/borrow, and exchange volumes.
- Cboe documents preliminary/complete subscription delivery targets, but historical first-receipt timestamps and immutable correction vintages are not established.
- Universe is documented broadly for U.S. stock, ETF, and index options disseminated over OPRA; delisted-symbol continuity and daily historical symbol coverage remain unverified.
- No raw sample or paid history obtained. Candidate only; strict PIT and alpha gates remain closed.
- 10/10 local documentation-audit tests passed. No hosted CI was run for this static feasibility audit.

### Phase 233 — Cboe Option Sentiment field dimensionality and directional semantics
- Audited the official DataShop specification v1.4 (05/25), its footnotes, and Cboe's early-exercise research.
- Found three inconsistent footnote references: net_option_delta, calls_sold, and puts_sold point to note 2, although note 2 is the blank-field list and note 3 contains the midpoint direction rule.
- The 80-field schema does not expose direction by trade size, OCC participant category, DTX, or moneyness. The proposed large-size-directional and customer-net-directional hypotheses are therefore unimplementable with this file and are killed as measurement designs, not empirically falsified.
- Non-ITM put/call volume is retained only as a non-directional activity/composition control. Customer/firm/market-maker totals are context only; they do not identify beneficial owners.
- net_option_delta units, sign, multiplier/deliverable treatment, and complete field-specific rules are unspecified. Its feature definition and normalization by underlying volume are suspended pending written provider clarification.
- Historical orders are delivered at order-processing completion; original historical first-receipt and immutable correction vintages remain unverified. Strict PIT remains blocked.
- 12/12 local regression tests passed. No hosted Phase 233 workflow was run; files use skip-ci commits.
- [Phase 233 report](PHASE233_CBOE_OPTION_SENTIMENT_FIELD_DIMENSION_AND_DIRECTIONAL_SEMANTICS_AUDIT_2026-11-09.md)

## Source decisions

| Source | Current decision | Main blocker |
|---|---|---|
| FINRA 20C / short flow | Not promoted | Historical coverage and incremental value not established |
| Form 4 | Standalone implementation discarded | Must distinguish transaction semantics and filing availability |
| Form 144 | Conditional event candidate | Independent shares/float/ADV denominators and identity mapping |
| SEC 13D/G | Separate 13D and 13G research tracks | Reporting-person economic identity and amendment chains |
| N-PORT | Conditional short-side hypothesis | Original XML retrieval blocked by missing authorized \`SEC_CONTACT_EMAIL\` |
| Cboe Option Quotes | Sample parser gate passes on unambiguous rows only | PIT receipt/vintage, broad history/universe, licensing |
| Cboe Option Sentiment | Conditional candidate; no PIT/alpha admission | net_option_delta units/sign/multiplier and field semantics; no directional size/participant cross-tabs; historical receipts/vintages, delisted coverage, sample, price/license |
| SEC MIDAS | Microstructure context only | Historical publication vintages and PIT identity |
| Cboe Open-Close | Not admitted to daily PIT | First-receipt/vintage and venue coverage controls |

## Non-negotiable controls
- No forced CAGR target; optimize return relative to risk and robustness.
- No minimum or maximum holding period.
- \`F80_TOP20_PARTIAL50_BASELINE_C20\` remains frozen.
- \`CONSUMED_NOT_PRISTINE\` is not used as a final holdout.
- No signal promotion without chronological OOS, identical exposure/costs, bootstrap/time-block inference, and LOO diagnostics.
- Explicitly control for prior returns to distinguish predictive flow from return-chasing.
- Missing data remain UNKNOWN, not zero.
- No purchases, production changes, or universe changes without explicit gates.

## Human/technical blockers
1. Set an authorized \`SEC_CONTACT_EMAIL\` in GitHub Actions to enable SEC N-PORT original-document retrieval.
2. Before any Cboe paid historical order, obtain written answers on first-receipt logs, correction/revision policy, historical delisted coverage, licensing, and price. No order has been placed.

## Next research steps
1. Keep Phase 231 parser and artifact metadata as the accepted sample diagnostic; do not generalize it to the full product.
2. For Option Sentiment, obtain written clarification of net_option_delta units/sign/multiplier, footnote mappings, cancellation scope, and any directional cross-tabs; require a representative sample, historical backfill completeness, correction vintages, and delivery logs before any paid data.
3. If a sample becomes available, validate the 80-field schema, null semantics, per-day symbol coverage, corporate-action handling, and cross-field invariants.
4. Only then preregister one primary directional-flow hypothesis (\`net_option_delta\` scaled by underlying volume) with prior-return controls and secondary size/non-ITM tests.
5. Compare incremental information to frozen LTM/F80 under identical exposure and costs; do not use the consumed holdout.
