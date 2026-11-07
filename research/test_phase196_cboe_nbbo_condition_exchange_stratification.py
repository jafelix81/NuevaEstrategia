import csv
import io
import json
import unittest
import zipfile

from research.phase194_cboe_option_trades_daily_flow_sample_audit import BASE_FIELDS, CALCS_FIELDS
from research.phase196_cboe_nbbo_condition_exchange_stratification import stratify_archive


def make_row(sequence, condition, exchange, size, price, bid="1.20", ask="1.25"):
    return {
        "underlying_symbol": "RAWXYZ",
        "market_date": "1/7/2026",
        "quote_datetime": "97:88.7",
        "sequence_number": str(sequence),
        "root": "RAWXYZ",
        "expiration": "1/16/2026",
        "strike": "25",
        "option_type": "C",
        "exchange_id": str(exchange),
        "trade_size": str(size),
        "trade_price": str(price),
        "trade_condition_id": str(condition),
        "canceled_trade_condition_id": "0",
        "best_bid_size": "20",
        "best_bid": bid,
        "best_ask": ask,
        "best_ask_size": "30",
        "underlying_bid": "24.99",
        "underlying_ask": "25.01",
    }


def csv_payload(rows, fields):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def make_archive(rows):
    base = csv_payload(rows, BASE_FIELDS)
    calc_rows = []
    for row in rows:
        calc = dict(row)
        for field in CALCS_FIELDS:
            calc[field] = "0"
        calc_rows.append(calc)
    calcs = csv_payload(calc_rows, list(BASE_FIELDS) + list(CALCS_FIELDS))
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("UnderlyingOptionsTrades_2026-01-07.csv", base)
        archive.writestr("UnderlyingOptionsTradesCalcs_2026-01-07.csv", calcs)
    return buff.getvalue()


def mappings():
    conditions = {
        "row_count": 3,
        "headers": ["id", "name", "security_type"],
        "effective_date_fields": [],
        "mapping_by_id": {
            18: {"id": 18, "name": "AutoExecution", "message_type": None, "security_types": "option", "fields": {}},
            114: {"id": 114, "name": "SingLegAuctNonISO", "message_type": None, "security_types": "option", "fields": {}},
            119: {"id": 119, "name": "MultLegAutoEx", "message_type": None, "security_types": "option", "fields": {}},
        },
    }
    exchanges = {
        "row_count": 2,
        "headers": ["id", "display_name", "full_name", "security_type"],
        "mapping_by_id": {
            5: {"id": 5, "name": "CBOE", "code": None, "fields": {}},
            7: {"id": 7, "name": "ARCA", "code": None, "fields": {}},
        },
    }
    return conditions, exchanges


class Phase196Tests(unittest.TestCase):
    def test_condition_exchange_decomposition_reconciles_phase194_totals(self):
        rows = [
            make_row(1001, 18, 5, 10, "1.25"),
            make_row(1002, 114, 7, 5, "1.20"),
            make_row(1003, 119, 5, 7, "1.22"),
        ]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        self.assertEqual(result["status"], "STRATIFIED_SAMPLE_DIAGNOSTIC_PASS")
        self.assertEqual(result["totals"]["rows"], 3)
        self.assertEqual(result["totals"]["contract_volume"], 22)
        self.assertEqual(result["totals"]["at_ask_contract_volume"], 10)
        self.assertEqual(result["totals"]["at_bid_contract_volume"], 5)
        self.assertEqual(result["totals"]["candidate_signed_contract_volume_at_ask_minus_bid"], 5)
        self.assertTrue(all(result["reconciliation"].values()))

    def test_condition_level_net_is_separate_for_each_execution_label(self):
        rows = [
            make_row(1001, 18, 5, 10, "1.25"),
            make_row(1002, 114, 7, 5, "1.20"),
            make_row(1003, 119, 5, 7, "1.22"),
        ]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        by_id = {x["id"]: x for x in result["condition_groups"]}
        self.assertEqual(by_id[18]["candidate_signed_contract_volume_at_ask_minus_bid"], 10)
        self.assertEqual(by_id[114]["candidate_signed_contract_volume_at_ask_minus_bid"], -5)
        self.assertEqual(by_id[119]["candidate_signed_contract_volume_at_ask_minus_bid"], 0)

    def test_exchange_and_condition_exchange_cross_tabs_reconcile(self):
        rows = [
            make_row(1001, 18, 5, 10, "1.25"),
            make_row(1002, 114, 7, 5, "1.20"),
            make_row(1003, 119, 5, 7, "1.22"),
        ]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        by_exchange = {x["id"]: x for x in result["exchange_groups"]}
        self.assertEqual(by_exchange[5]["candidate_signed_contract_volume_at_ask_minus_bid"], 10)
        self.assertEqual(by_exchange[7]["candidate_signed_contract_volume_at_ask_minus_bid"], -5)
        self.assertEqual(len(result["condition_exchange_cells"]), 3)
        self.assertEqual(sum(x["rows"] for x in result["condition_exchange_cells"]), 3)

    def test_missing_mapping_fails_closed(self):
        rows = [make_row(1001, 18, 5, 10, "1.25")]
        conditions, exchanges = mappings()
        del conditions["mapping_by_id"][18]
        with self.assertRaisesRegex(ValueError, "invalid_or_unmapped_sample_rows"):
            stratify_archive(make_archive(rows), conditions, exchanges)

    def test_sample_member_pair_mismatch_fails_closed(self):
        rows = [make_row(1001, 18, 5, 10, "1.25")]
        changed = [make_row(1001, 18, 5, 11, "1.25")]
        buff = io.BytesIO()
        with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("UnderlyingOptionsTrades_2026-01-07.csv", csv_payload(rows, BASE_FIELDS))
            calc_rows = []
            for row in changed:
                calc = dict(row)
                for field in CALCS_FIELDS:
                    calc[field] = "0"
                calc_rows.append(calc)
            archive.writestr("UnderlyingOptionsTradesCalcs_2026-01-07.csv", csv_payload(calc_rows, list(BASE_FIELDS) + list(CALCS_FIELDS)))
        conditions, exchanges = mappings()
        with self.assertRaisesRegex(ValueError, "phase194_daily_sample_gate_failed"):
            stratify_archive(buff.getvalue(), conditions, exchanges)

    def test_opaque_quote_time_is_not_used_or_persisted(self):
        rows = [make_row(1001, 18, 5, 10, "1.25")]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn("RAWXYZ", rendered)
        self.assertNotIn("97:88.7", rendered)
        self.assertFalse(result["interpretation"]["quote_datetime_used"])
        self.assertFalse(result["interpretation"]["quote_datetime_semantics_assigned"])

    def test_condition_buckets_keep_auction_and_multileg_separate(self):
        rows = [
            make_row(1001, 18, 5, 10, "1.25"),
            make_row(1002, 114, 7, 5, "1.20"),
            make_row(1003, 119, 5, 7, "1.22"),
        ]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        buckets = {x["bucket"]: x for x in result["condition_bucket_groups"]}
        self.assertIn("auto_execution", buckets)
        self.assertIn("single_leg_auction_or_cross", buckets)
        self.assertIn("multi_leg", buckets)

    def test_no_feature_pit_or_alpha_admission(self):
        rows = [make_row(1001, 18, 5, 10, "1.25")]
        conditions, exchanges = mappings()
        result = stratify_archive(make_archive(rows), conditions, exchanges)
        self.assertFalse(result["interpretation"]["strict_pit_admitted"])
        self.assertFalse(result["interpretation"]["signed_flow_feature_admitted"])
        self.assertFalse(result["interpretation"]["alpha_admission"])
        self.assertFalse(result["interpretation"]["holdout_used"])
        self.assertTrue(result["interpretation"]["f80_frozen"])


if __name__ == "__main__":
    unittest.main()
