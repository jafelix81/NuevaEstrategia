"""Phase 234: CFTC Bank Participation Report feasibility audit.

This module parses a small, source-linked transcription of the November 2026
CFTC BPR futures report. It is a schema/semantics diagnostic, not a historical
data downloader, backtest, or alpha model.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

INTEGER = re.compile(r"^\d[\d,]*$")
NUMBER = re.compile(r"^\d[\d,]*(?:\.\d+)?$")

@dataclass(frozen=True)
class BankRow:
    category: str
    bank_count: Optional[int]
    long_positions: Optional[int]
    long_pct_oi: Optional[float]
    short_positions: Optional[int]
    short_pct_oi: Optional[float]
    open_interest: Optional[int]

def _clean(value: str) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").strip().split())

def _int_or_none(value) -> Optional[int]:
    value = _clean(value)
    if not value:
        return None
    if not INTEGER.match(value):
        raise ValueError(f"invalid integer field: {value!r}")
    return int(value.replace(",", ""))

def _float_or_none(value) -> Optional[float]:
    value = _clean(value)
    if not value:
        return None
    if not NUMBER.match(value):
        raise ValueError(f"invalid numeric field: {value!r}")
    return float(value.replace(",", ""))

def _nonnegative_optional(value, field: str) -> Optional[int]:
    parsed = _int_or_none(value)
    if parsed is not None and parsed < 0:
        raise ValueError(f"negative {field}")
    return parsed

def _nonnegative_float_or_none(value, field: str) -> Optional[float]:
    parsed = _float_or_none(value)
    if parsed is not None and parsed < 0:
        raise ValueError(f"negative {field}")
    return parsed

def parse_bank_row(line: str, category: str) -> BankRow:
    """Parse a pipe-delimited audit row, preserving every blank as UNKNOWN."""
    cells = [_clean(x) for x in line.split("|")]
    if len(cells) < 7:
        raise ValueError("BPR row has fewer than seven cells")
    if category == "US":
        bank_type = cells[1].upper()
        offset = 2
        if bank_type not in {"U.S.", "US"}:
            raise ValueError("US row category mismatch")
    elif category == "NON_US":
        bank_type = cells[0].upper()
        offset = 1
        if bank_type not in {"NON U.S.", "NON-US", "NON US"}:
            raise ValueError("NON_US row category mismatch")
    else:
        raise ValueError("category must be US or NON_US")
    fields = cells[offset:offset + 6]
    if len(fields) != 6:
        raise ValueError("BPR row has incomplete fields")
    count, long_pos, long_pct, short_pos, short_pct, oi = fields
    return BankRow(
        category=category,
        bank_count=_nonnegative_optional(count, "bank_count"),
        long_positions=_nonnegative_optional(long_pos, "long_positions"),
        long_pct_oi=_nonnegative_float_or_none(long_pct, "long_pct_oi"),
        short_positions=_nonnegative_optional(short_pos, "short_positions"),
        short_pct_oi=_nonnegative_float_or_none(short_pct, "short_pct_oi"),
        open_interest=_nonnegative_optional(oi, "open_interest"),
    )

def aggregate_contract(us: BankRow, non_us: BankRow, total_row: dict) -> dict:
    """Use observed total-row/category values; never coerce blanks to zero."""
    if us.category != "US" or non_us.category != "NON_US":
        raise ValueError("category order/identity mismatch")
    if us.open_interest is None or us.open_interest <= 0:
        raise ValueError("US row must carry a positive market open-interest denominator")
    total_long = _nonnegative_optional(total_row.get("long_positions"), "total_long_positions")
    total_short = _nonnegative_optional(total_row.get("short_positions"), "total_short_positions")
    category_values = (us.long_positions, us.short_positions,
                       non_us.long_positions, non_us.short_positions)
    category_complete = all(value is not None for value in category_values)
    category_sum_reconciled = None
    if category_complete:
        category_long = us.long_positions + non_us.long_positions
        category_short = us.short_positions + non_us.short_positions
        if total_long is not None and category_long != total_long:
            raise ValueError("total long positions do not reconcile")
        if total_short is not None and category_short != total_short:
            raise ValueError("total short positions do not reconcile")
        effective_total_long = category_long
        effective_total_short = category_short
        category_sum_reconciled = (
            True if total_long is not None and total_short is not None else None
        )
    else:
        effective_total_long = total_long
        effective_total_short = total_short
    if effective_total_long is not None and effective_total_short is not None:
        net = effective_total_long - effective_total_short
        coverage = "OBSERVED_FULL_CATEGORY_BREAKDOWN" if category_complete else "OBSERVED_TOTAL_ONLY"
        net_to_oi = net / us.open_interest
    else:
        net = None
        coverage = "UNKNOWN_TOTAL_POSITION"
        net_to_oi = None
    us_net = (us.long_positions - us.short_positions
              if us.long_positions is not None and us.short_positions is not None else None)
    non_us_net = (non_us.long_positions - non_us.short_positions
                  if non_us.long_positions is not None and non_us.short_positions is not None else None)
    return {
        "us_bank_count": us.bank_count,
        "non_us_bank_count": non_us.bank_count,
        "total_bank_count": _nonnegative_optional(total_row.get("bank_count"), "total_bank_count"),
        "us_long": us.long_positions,
        "us_short": us.short_positions,
        "us_net_long_minus_short": us_net,
        "non_us_long": non_us.long_positions,
        "non_us_short": non_us.short_positions,
        "non_us_net_long_minus_short": non_us_net,
        "total_long": effective_total_long,
        "total_short": effective_total_short,
        "net_long_minus_short": net,
        "open_interest": us.open_interest,
        "net_to_open_interest": net_to_oi,
        "category_breakdown_complete": category_complete,
        "category_sum_reconciled": category_sum_reconciled,
        "coverage_status": coverage,
    }


def build_audit() -> dict:
    """Return the reproducible source-feasibility decision and sample checks."""
    sample = {
        "report_month": "2026-11",
        "report_date": "2026-11-03",
        "scheduled_release_date": "2026-11-06",
        "scheduled_release_time_et": "after 15:30 ET",
        "first_receipt_timestamp": None,
        "contracts": {
            "CME E-MINI S&P 500": {
                "us": "CME E-MINI S&P 500 | U.S. | 7 | 39,925 | 2.0 | 71,568 | 3.6 | 1,986,532",
                "non_us": "NON U.S. | 19 | 15,383 | 0.8 | 273,885 | 13.8 |",
                "total": {"bank_count": 26, "long_positions": 55_308, "short_positions": 345_453},
            },
            "CME NASDAQ MINI": {
                "us": "CME NASDAQ MINI | U.S. | 6 | 19,891 | 6.8 | 5,310 | 1.8 | 292,587",
                "non_us": "NON U.S. | 15 | 6,753 | 2.3 | 18,858 | 6.4 |",
                "total": {"bank_count": 21, "long_positions": 26_644, "short_positions": 24_168},
            },
            "CME RUSSELL E-MINI": {
                "us": "CME RUSSELL E-MINI | U.S. | 8 | 15,033 | 3.3 | 7,130 | 1.6 | 449,399",
                "non_us": "NON U.S. | 14 | 25,910 | 5.8 | 13,945 | 3.1 |",
                "total": {"bank_count": 22, "long_positions": 40_943, "short_positions": 21_075},
            },
            "CBT DJIA x $5": {
                "us": "CBT DJIA x $5 | U.S. | 4 | 0 | 0.0 | 1,865 | 2.1 | 87,410",
                "non_us": "NON U.S. | 7 | 6,719 | 7.7 | 20,335 | 23.3 |",
                "total": {"bank_count": 11, "long_positions": 6_719, "short_positions": 22_200},
            },
        },
    }
    parsed = {}
    for name, rows in sample["contracts"].items():
        us = parse_bank_row(rows["us"], "US")
        non_us = parse_bank_row(rows["non_us"], "NON_US")
        parsed[name] = aggregate_contract(us, non_us, rows["total"])

    return {
        "phase": 234,
        "source": "CFTC Bank Participation Report (BPR), futures-in-contract",
        "source_url": "https://www.cftc.gov/MarketReports/BankParticipationReports/index.htm",
        "explanatory_notes_url": "https://www.cftc.gov/MarketReports/BankParticipationReports/ExplanatoryNotes/index.htm",
        "release_schedule_url": "https://www.cftc.gov/MarketReports/BankParticipationReports/ReleaseSchedule/index.htm",
        "report_month": sample["report_month"],
        "report_date": sample["report_date"],
        "scheduled_release_date": sample["scheduled_release_date"],
        "scheduled_release_time_et": sample["scheduled_release_time_et"],
        "first_receipt_timestamp": sample["first_receipt_timestamp"],
        "archive_retention_months": 25,
        "archive_long_history_gate": False,
        "prospective_capture_candidate": True,
        "prospective_capture_started": False,
        "historical_pit_admission": False,
        "alpha_admission": False,
        "stock_level_universe_coverage": False,
        "market_regime_candidate_only": True,
        "bpr_release_cadence": "monthly",
        "bpr_schedule_change_confirmed": False,
        "reported_equity_index_futures": list(parsed),
        "sample_contracts": parsed,
        "semantics": {
            "reported_population": "U.S. and Non-U.S. commercial banks classified from CFTC Form 40 responses and staff approval",
            "not_all_institutions": True,
            "not_beneficial_owner_identity": True,
            "positions_are_aggregate_gross_long_and_short": True,
            "bank_classification_applies_across_commodities": True,
            "markets_require_at_least_five_banks": True,
            "category_count_suppressed_when_category_has_fewer_than_four_banks": True,
            "blank_bank_count_is_unknown_not_zero": True,
            "blank_position_or_percentage_is_unknown_not_zero": True,
            "missing_market_is_unknown_not_zero": True,
            "options_report_is_separate_and_gross_not_delta_adjusted": True,
            "open_interest_denominator_is_market_total": True,
        },
        "limitations": [
            "Only the most recent 25 months are retained on the CFTC site.",
            "Monthly frequency is too sparse and the public archive too short for a credible standalone stock-selection backtest.",
            "The data cover index futures, not the user's individual-stock universe; at most they can be tested as a market-regime overlay.",
            "Report date is the first Tuesday (or following Tuesday after a federal holiday), while publication is the first Friday after 15:30 ET; scheduled date is not an immutable first-receipt timestamp.",
            "The 2025 lapse of appropriations interrupted publication from October 1 through November 12 and required chronological catch-up, proving that the nominal schedule can fail.",
            "Bank categories are not a pure directional-smart-money label; banks may hedge, intermediate, or carry offsetting exposures.",
            "The options BPR is gross and not delta-adjusted; it must not be combined with futures positions as if units were comparable.",
            "The October 27 2026 COT twice-weekly modernization announcement is not treated as a BPR schedule change; the current BPR index still describes monthly publication."
        ],
        "feature_candidates_if_prospective_panel_becomes_adequate": [
            "US-bank net futures positions divided by total market OI",
            "Non-US-bank net futures positions divided by total market OI",
            "Combined bank net positions divided by total market OI",
            "Month-over-month changes in each ratio",
            "US versus Non-US net-position divergence"
        ],
        "required_controls": [
            "QQQ/SPY trend and realized volatility",
            "VIX level/term structure",
            "prior market and stock returns",
            "interest-rate regime",
            "month-end and release-week effects"
        ],
        "pit_rule": "Use the pipeline receipt, never report date; initial scheduled observation is a baseline state only (not a release event); later new report URLs/revisions may qualify from receipt onward.",
        "decision": "CONDITIONAL_PROSPECTIVE_REGIME_RESEARCH_ONLY",
    }

def main(output_path: Optional[str] = None) -> dict:
    result = build_audit()
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return result

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    print(json.dumps(main(args.output), indent=2, sort_keys=True))
