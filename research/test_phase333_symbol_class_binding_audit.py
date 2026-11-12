import unittest

from research.phase333_symbol_class_binding_audit import (
    build_context_associations,
    classify_document_binding,
    extract_symbol_fact_rows,
    extract_title_fact_rows,
)


class Phase333Tests(unittest.TestCase):
    def test_symbol_fact_keeps_its_own_class_and_listing_dimensions(self):
        facts = [{
            "name": "TradingSymbol", "value": "str", "context_ref": "C1",
            "dimensions": [
                {"dimension": "us-gaap:StatementClassOfStockAxis", "member": "us-gaap:CommonStockMember"},
                {"dimension": "dei:EntityListingsExchangeAxis", "member": "dei:NasdaqMember"},
            ],
        }]
        rows = extract_symbol_fact_rows(facts)
        self.assertEqual(rows[0]["symbol"], "STR")
        self.assertEqual(rows[0]["class_axis_members"], [
            "us-gaap:StatementClassOfStockAxis=us-gaap:CommonStockMember"
        ])
        self.assertEqual(rows[0]["listing_axis_members"], [
            "dei:EntityListingsExchangeAxis=dei:NasdaqMember"
        ])

    def test_symbol_fact_without_dimensions_is_not_linked_by_document_cooccurrence(self):
        facts = [
            {"name": "TradingSymbol", "value": "STR", "context_ref": "C1", "dimensions": []},
            {"name": "Security12bTitle", "value": "Class A common stock", "context_ref": "C2",
             "dimensions": [{"dimension": "us-gaap:StatementClassOfStockAxis", "member": "us-gaap:CommonStockMember"}]},
        ]
        symbols = extract_symbol_fact_rows(facts)
        titles = extract_title_fact_rows(facts)
        members = ["us-gaap:StatementClassOfStockAxis=us-gaap:CommonStockMember"]
        self.assertEqual(classify_document_binding(symbols, members, True),
                         "SINGLE_SYMBOL_AND_CLASS_AXES_UNLINKED")
        associations = build_context_associations(symbols, titles)
        self.assertFalse(associations[0]["direct_class_binding"])
        self.assertEqual(associations[0]["same_context_security_titles"], [])

    def test_same_context_title_is_recorded_but_not_promoted_without_class_axis_on_symbol(self):
        facts = [
            {"name": "TradingSymbol", "value": "ABC", "context_ref": "C1", "dimensions": []},
            {"name": "Security12bTitle", "value": "Common stock", "context_ref": "C1", "dimensions": []},
        ]
        associations = build_context_associations(
            extract_symbol_fact_rows(facts), extract_title_fact_rows(facts)
        )
        self.assertEqual(associations[0]["same_context_security_titles"], ["Common stock"])
        self.assertFalse(associations[0]["direct_class_binding"])

    def test_all_symbol_facts_with_class_axis_are_direct(self):
        symbols = [
            {"symbol": "STR", "class_axis_members": ["axis=Common"]},
            {"symbol": "STRWS", "class_axis_members": ["axis=Warrant"]},
        ]
        self.assertEqual(classify_document_binding(symbols, ["axis=Common", "axis=Warrant"], True),
                         "DIRECT_CLASS_AXIS_ON_ALL_SYMBOL_FACTS")

    def test_partial_class_binding_is_not_overstated(self):
        symbols = [
            {"symbol": "STR", "class_axis_members": ["axis=Common"]},
            {"symbol": "STRWS", "class_axis_members": []},
        ]
        self.assertEqual(classify_document_binding(symbols, ["axis=Common", "axis=Warrant"], True),
                         "PARTIAL_DIRECT_CLASS_AXIS_BINDING")

    def test_multiple_symbols_and_class_axes_without_direct_binding_are_unlinked(self):
        symbols = [
            {"symbol": "PCG", "class_axis_members": []},
            {"symbol": "PCG-PA", "class_axis_members": []},
        ]
        self.assertEqual(classify_document_binding(symbols, ["axis=Common", "axis=Preferred"], True),
                         "MULTI_SYMBOLS_AND_CLASS_AXES_UNLINKED")

    def test_multiple_symbols_without_class_axis_are_unlinked(self):
        symbols = [
            {"symbol": "DLR", "class_axis_members": []},
            {"symbol": "DLRPRJ", "class_axis_members": []},
        ]
        self.assertEqual(classify_document_binding(symbols, [], True),
                         "MULTI_SYMBOLS_NO_CLASS_AXIS_BINDING")

    def test_single_symbol_without_class_axis_is_issuer_level_only(self):
        symbols = [{"symbol": "LFCR", "class_axis_members": []}]
        self.assertEqual(classify_document_binding(symbols, [], True),
                         "SINGLE_ISSUER_SYMBOL_NO_CLASS_BINDING")

    def test_hash_mismatch_blocks_even_direct_class_facts(self):
        symbols = [{"symbol": "STR", "class_axis_members": ["axis=Common"]}]
        self.assertEqual(classify_document_binding(symbols, ["axis=Common"], False),
                         "HASH_MISMATCH_NOT_ADMITTED")

    def test_no_symbol_fact_remains_unknown(self):
        self.assertEqual(classify_document_binding([], ["axis=Common"], True),
                         "NO_TRADING_SYMBOL_FACT")


if __name__ == "__main__":
    unittest.main()
