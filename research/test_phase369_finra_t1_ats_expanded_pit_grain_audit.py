import unittest

from research.phase369_finra_t1_ats_expanded_pit_grain_audit import (
    GapStats,
    analyze_partition,
    audit_ats_bridge,
    build_query,
    parse_date,
    parse_integer,
    parse_rows,
)


class Phase369Tests(unittest.TestCase):
    def test_query_pins_historical_week_and_t1(self):
        q=build_query("2025-10-20",5000,10000)
        f={x["fieldName"]:x["fieldValue"] for x in q["compareFilters"]}
        self.assertEqual(f["historicalWeek"],"2025-10-20")
        self.assertEqual(f["tierIdentifier"],"T1")
        self.assertEqual(q["offset"],10000)

    def test_date_and_integer_parsers(self):
        self.assertEqual(str(parse_date("2025-10-20")),"2025-10-20")
        self.assertIsNone(parse_date("bad"))
        self.assertEqual(parse_integer("1,234"),1234)
        self.assertIsNone(parse_integer("-1"))
        self.assertIsNone(parse_integer("1.5"))

    def test_gap_stats_distinguish_post_initial_update(self):
        g=GapStats()
        g.add("2025-11-10","2025-11-10")
        g.add("2025-11-10","2026-01-01")
        g.add("2025-11-10","2025-11-01")
        s=g.summary()
        self.assertEqual(s["positive_gap_rows"],1)
        self.assertEqual(s["zero_gap_rows"],1)
        self.assertEqual(s["negative_gap_rows"],1)
        self.assertEqual(s["maximum_days"],52)

    def _rows(self):
        return [
            {"summaryTypeCode":"ATS_W_SMBL","issueSymbolIdentifier":"AAA","productTypeCode":"CTS","totalWeeklyShareQuantity":300,"totalWeeklyTradeCount":30},
            {"summaryTypeCode":"ATS_W_SMBL_FIRM","issueSymbolIdentifier":"AAA","MPID":"M1","firmCRDNumber":None,"marketParticipantName":"Firm 1","totalWeeklyShareQuantity":100,"totalWeeklyTradeCount":10},
            {"summaryTypeCode":"ATS_W_SMBL_FIRM","issueSymbolIdentifier":"AAA","MPID":"M2","firmCRDNumber":None,"marketParticipantName":"Firm 2","totalWeeklyShareQuantity":200,"totalWeeklyTradeCount":20},
        ]

    def test_symbol_firm_bridge_exact(self):
        result=audit_ats_bridge(self._rows())
        self.assertEqual(result["unambiguous_bridges"],1)
        self.assertEqual(result["both_exact_matches"],1)
        self.assertEqual(result["share_total_delta"],0)
        self.assertEqual(result["trade_total_delta"],0)
        self.assertEqual(result["bridge_gate"],"PASS")

    def test_duplicate_aggregate_symbol_is_ambiguous(self):
        rows=self._rows()+[
            {"summaryTypeCode":"ATS_W_SMBL","issueSymbolIdentifier":"AAA","productTypeCode":"UTP","totalWeeklyShareQuantity":300,"totalWeeklyTradeCount":30}
        ]
        result=audit_ats_bridge(rows)
        self.assertEqual(result["ambiguous_symbols"],1)
        self.assertEqual(result["bridge_gate"],"FAIL_OR_REVIEW")

    def test_numeric_mismatch_fails_bridge(self):
        rows=self._rows()
        rows[-1]["totalWeeklyShareQuantity"]=199
        result=audit_ats_bridge(rows)
        self.assertEqual(result["both_exact_matches"],0)
        self.assertEqual(result["bridge_gate"],"FAIL_OR_REVIEW")

    def test_missing_participant_identity_fails_bridge(self):
        rows=self._rows()
        rows[1]["MPID"]=None
        rows[1]["firmCRDNumber"]=None
        rows[1]["marketParticipantName"]=None
        result=audit_ats_bridge(rows)
        self.assertEqual(result["participant_rows_missing_mpid_crd_excluding_de_minimis"],1)
        self.assertEqual(result["bridge_gate"],"FAIL_OR_REVIEW")

    def test_de_minimis_is_not_silently_treated_as_named_participant(self):
        rows=self._rows()
        rows[1]["firmCRDNumber"]="0"
        rows[1]["MPID"]=None
        rows[1]["marketParticipantName"]="De Minimis Firms"
        result=audit_ats_bridge(rows)
        self.assertEqual(result["de_minimis_rows"],1)
        self.assertEqual(result["bridge_gate"],"FAIL_OR_REVIEW")

    def test_analyze_partition_flags_ats_post_initial_update(self):
        rows=[
            {"summaryTypeCode":"ATS_W_SMBL","issueSymbolIdentifier":"AAA","productTypeCode":"CTS","weekStartDate":"2025-10-20","initialPublishedDate":"2025-11-10","lastUpdateDate":"2025-11-10","lastReportedDate":"2025-10-24"},
            {"summaryTypeCode":"ATS_W_SMBL_FIRM","issueSymbolIdentifier":"AAA","MPID":"M1","totalWeeklyShareQuantity":1,"totalWeeklyTradeCount":1,"weekStartDate":"2025-10-20","initialPublishedDate":"2025-11-10","lastUpdateDate":"2025-12-01","lastReportedDate":"2025-11-20"},
        ]
        result=analyze_partition(rows,"2025-10-20",2,1)
        self.assertEqual(result["ats_rows_with_post_initial_update"],1)
        self.assertFalse(result["ats_date_pit_candidate"])
        self.assertFalse(result["raw_identifiers_retained"])

    def test_parse_rows_accepts_list_and_wrapped_payload(self):
        self.assertEqual(parse_rows([{"x":1}]),[{"x":1}])
        self.assertEqual(parse_rows({"data":[{"x":1}]}),[{"x":1}])


if __name__=="__main__":
    unittest.main()
