from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(payload.get("phase") == 186, "phase must equal 186")
    check(payload.get("audit_date") == "2026-11-07", "audit_date mismatch")

    nasdaq = payload.get("nasdaq_trade_outline", {})
    venues = nasdaq.get("venues", [])
    expected = {"PHLX", "ISE", "NOM", "GEMX", "MRX", "NTX"}
    actual = {row.get("venue") for row in venues}
    check(len(venues) == 6, "exactly six Nasdaq venues are required")
    check(actual == expected, "venue set must match the six documented products")

    by_venue = {row.get("venue"): row for row in venues}
    expected_archive = {
        "PHLX": ("2009-01", "2009-01"),
        "ISE": ("2009-10", "2006-01"),
        "NOM": ("2011-11", "2011-11"),
        "GEMX": ("2013-08", "2013-08"),
        "MRX": ("2017-09", "2017-09"),
        "NTX": ("2014-09", "2014-09"),
    }
    for venue, (intraday, eod) in expected_archive.items():
        row = by_venue.get(venue, {})
        check(row.get("archive_start", {}).get("intraday") == intraday,
              f"{venue} intraday archive start mismatch")
        check(row.get("archive_start", {}).get("eod") == eod,
              f"{venue} EOD archive start mismatch")
        check(row.get("strict_pit_admitted") is False,
              f"{venue} must remain outside strict PIT admission")
        check(row.get("first_receipt_verified") is False,
              f"{venue} first receipt must remain unverified")
        check(row.get("universe_coverage_verified") is False,
              f"{venue} universe coverage must remain unverified")

    check(by_venue["PHLX"]["live_product_floor"]["intraday"] == "2010-09-01",
          "PHOTO live-product floor mismatch")
    check(by_venue["ISE"]["live_product_floor"]["intraday"] == "2010-01-04",
          "ISE intraday live-product floor mismatch")
    check(by_venue["NOM"]["live_product_floor"]["intraday"] == "2011-11-11",
          "NOTO operative lower bound mismatch")
    check(by_venue["GEMX"]["live_product_floor"]["intraday"] is None,
          "GEMX exact first-live date must remain unknown")
    check(by_venue["MRX"]["live_product_floor"]["intraday"] == "2024-09-03",
          "MRX announced product floor mismatch")
    check(by_venue["NTX"]["live_product_floor"]["intraday"] == "2024-09-03",
          "NTX/BX announced product floor mismatch")

    delivery = nasdaq.get("delivery", {})
    check(delivery.get("current_interval_minutes") == 10,
          "current intraday interval must be ten minutes")
    check(delivery.get("current_sla_minutes") == 2,
          "current FAQ delivery SLA mismatch")
    check(delivery.get("historical_sec_examples_phlx_noto_sla_minutes") == 5,
          "historical PHLX/NOTO SLA evidence mismatch")
    check(delivery.get("real_time_feed") is False, "Trade Outline is not a real-time feed")
    check(delivery.get("cumulative_snapshots") is True, "snapshots must be cumulative")
    check(delivery.get("first_receipt_verified") is False,
          "first receipt logs must remain unverified")

    semantics = nasdaq.get("semantics", {})
    check(semantics.get("routed_orders_away_included") is True,
          "routed-away inclusion must be recorded")
    check(semantics.get("routed_away_flag_available") is False,
          "routed-away flag must remain unavailable")
    check(semantics.get("cross_venue_aggregation_authorized") is False,
          "cross-venue aggregation must remain blocked")
    check(semantics.get("no_trade_row_means_zero") is False,
          "missing rows must not be interpreted as zero")
    check(semantics.get("volume_can_decrease_after_corrections") is True,
          "correction/cancellation mutability must be recorded")
    check(semantics.get("rows_can_disappear_after_full_cancellation") is True,
          "all-cancelled row disappearance must be recorded")
    check(set(semantics.get("market_maker_open_close_not_required_for", [])) ==
          {"PHOTO", "NOTO", "MRX", "TEXAS"},
          "market-maker open/close limitation mismatch")
    check(semantics.get("ise_gemx_market_maker_category_start") == "2026-03-04",
          "ISE/GEMX market-maker cutover mismatch")
    check(semantics.get("ise_gemx_schema_cutover") == "2026-03-04",
          "ISE/GEMX schema cutover mismatch")
    check(semantics.get("old_ise_gemx_codes_decommissioned_after") == "2026-06-02",
          "legacy table-code retirement mismatch")
    check(semantics.get("ise_gemx_pre_cutover_total_industry_volume_double_count") is True,
          "pre-cutover denominator regime mismatch")

    ntx = payload.get("ntx_one_minute_snapshots", {})
    check(ntx.get("filing_date") == "2026-08-11", "NTX snapshot filing date mismatch")
    check(ntx.get("operative_not_before") == "2026-09-10", "NTX snapshot operative floor mismatch")
    check(ntx.get("implementation_notice_deadline") == "2026-10-10",
          "NTX implementation notice deadline mismatch")
    check(ntx.get("implementation_notice_located") is False,
          "implementation notice must remain explicitly unverified")
    check(ntx.get("actual_first_delivery_verified") is False,
          "NTX snapshot first delivery must remain unverified")
    check(ntx.get("minimum_trades") == 2, "NTX snapshot minimum trade threshold mismatch")
    check(ntx.get("minimum_origin_types") == 3,
          "NTX snapshot minimum origin-type threshold mismatch")
    check(ntx.get("trade_count_disclosed") is False,
          "NTX snapshot must not disclose actual trade counts")
    check(ntx.get("buy_sell_side_disclosed") is False,
          "NTX snapshot must not be treated as buy/sell directional flow")
    check(ntx.get("real_time_feed") is False, "NTX snapshots are not a real-time feed")

    cboe = payload.get("cboe_one_minute_operability_correction", {})
    check(cboe.get("filing_date") == "2025-06-13", "Cboe filing date mismatch")
    check(cboe.get("operative_delay_days") == 30, "Cboe operative delay mismatch")
    check(cboe.get("legal_operative_not_before") == "2025-07-13",
          "Cboe legal operative floor must be corrected to 2025-07-13")
    check(cboe.get("first_possible_regular_trading_session") == "2025-07-14",
          "Cboe first possible session mismatch")
    check(cboe.get("actual_first_delivery_verified") is False,
          "Cboe actual first delivery must remain unverified")

    costs = nasdaq.get("costs_2026_usd", {})
    check(costs.get("monthly_intraday_all_six") == 12000,
          "six-venue intraday monthly total mismatch")
    check(costs.get("monthly_eod_all_six") == 4350,
          "six-venue EOD monthly total mismatch")
    check(costs.get("monthly_both_all_six_using_ise_combined_subscription") == 12600,
          "six-venue combined monthly total mismatch")
    check(costs.get("history_36m_intraday_discount_current_subscribers") == 57000,
          "36-month intraday discount total mismatch")
    check(costs.get("history_36m_eod_discount_current_subscribers") == 33000,
          "36-month EOD discount total mismatch")
    check(costs.get("history_36m_intraday_ad_hoc_without_subscription") == 171000,
          "36-month intraday ad-hoc total mismatch")
    check(costs.get("history_36m_eod_ad_hoc_without_subscription") == 99000,
          "36-month EOD ad-hoc total mismatch")

    decisions = payload.get("decisions", {})
    check(decisions.get("strict_pit_admitted_venues") == 0,
          "no venue should be admitted to strict PIT")
    check(decisions.get("cross_venue_aggregation_authorized") is False,
          "cross-venue aggregation must remain blocked")
    check(decisions.get("alpha_test_authorized") is False,
          "alpha test must not be authorized")
    check(decisions.get("holdout_used") is False, "holdout must remain unused")
    check(decisions.get("vendor_contact") is False, "vendor contact must remain false")
    check(decisions.get("data_purchase") is False, "data purchase must remain false")
    check(decisions.get("production_changed") is False, "production must remain unchanged")
    check(decisions.get("f80_frozen") is True, "F80 must remain frozen")

    if errors:
        raise ValueError("; ".join(errors))

    return {
        "phase": 186,
        "status": "CONDITIONAL_HIGH_PRIORITY_DATA_FEASIBILITY_CANDIDATE_NOT_PIT_ADMITTED",
        "nasdaq_venues_audited": len(venues),
        "strict_pit_admitted_venues": 0,
        "cross_venue_aggregation_authorized": False,
        "ntx_one_minute_first_delivery_verified": False,
        "cboe_one_minute_legal_operative_not_before": cboe["legal_operative_not_before"],
        "cboe_one_minute_first_possible_session": cboe["first_possible_regular_trading_session"],
        "monthly_intraday_all_six_usd": costs["monthly_intraday_all_six"],
        "recent_36_month_intraday_discount_all_six_usd": costs["history_36m_intraday_discount_current_subscribers"],
        "alpha_test_authorized": False,
        "holdout_used": False,
        "f80_frozen": True,
        "validation_errors": []
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(Path(__file__).with_name(
        "phase186_nasdaq_trade_outline_pit_feasibility_audit.json")))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = audit(payload)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
