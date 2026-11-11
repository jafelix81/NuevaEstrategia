import unittest
from phase301_form4a_intermediate_validation import classify, sample_cases


def filing(acc, doc, issuer="0000000001", filed="2023-05-01", orig="", owners=(), period="2023Q2"):
    return {"accession": acc, "doc": doc, "issuer": issuer, "filing_date": filed,
            "orig_date": orig, "owners": set(owners), "period": period,
            "ticker": "TEST", "nd": [], "dv": []}


class Phase301Tests(unittest.TestCase):
    def periods(self, parents, children):
        result = {"2022Q4": {"filings": {}}, "2023Q1": {"filings": {}}, "2023Q2": {"filings": {}}}
        for row in parents + children:
            result[row["period"]]["filings"][row["accession"]] = row
        return result

    def test_unique_parent_across_quarters(self):
        parent = filing("0000000001-22-000001", "4", filed="2022-12-20", owners={"0000000002"}, period="2022Q4")
        child = filing("0000000001-23-000002", "4/A", filed="2023-05-01", orig="2022-12-20", owners={"0000000002"})
        row = classify(self.periods([parent], [child]))[0]
        self.assertEqual(row["status"], "unique_owner_overlap")
        self.assertEqual(row["parent"]["accession"], parent["accession"])

    def test_ambiguous_multiple_owner_overlaps(self):
        p1 = filing("0000000001-23-000001", "4", filed="2023-04-20", owners={"0000000002"})
        p2 = filing("0000000001-23-000003", "4", filed="2023-04-20", owners={"0000000002"})
        child = filing("0000000001-23-000002", "4/A", filed="2023-05-01", orig="2023-04-20", owners={"0000000002"})
        row = classify(self.periods([p1, p2], [child]))[0]
        self.assertEqual(row["status"], "ambiguous_multiple_owner_overlaps")
        self.assertEqual(len(row["owner_candidates"]), 2)

    def test_same_issuer_date_without_owner_overlap(self):
        parent = filing("0000000001-23-000001", "4", filed="2023-04-20", owners={"0000000003"})
        child = filing("0000000001-23-000002", "4/A", filed="2023-05-01", orig="2023-04-20", owners={"0000000002"})
        row = classify(self.periods([parent], [child]))[0]
        self.assertEqual(row["status"], "same_issuer_date_no_owner_overlap")

    def test_no_parent_in_loaded_archives(self):
        child = filing("0000000001-23-000002", "4/A", filed="2023-05-01", orig="2022-06-20", owners={"0000000002"})
        row = classify(self.periods([], [child]))[0]
        self.assertEqual(row["status"], "no_parent_in_loaded_archives")

    def test_future_parent_excluded(self):
        parent = filing("0000000001-23-000001", "4", filed="2023-05-02", owners={"0000000002"})
        child = filing("0000000001-23-000002", "4/A", filed="2023-05-01", orig="2023-05-02", owners={"0000000002"})
        row = classify(self.periods([parent], [child]))[0]
        self.assertEqual(row["status"], "no_parent_in_loaded_archives")

    def test_sample_selection_is_deterministic(self):
        parent = filing("0000000001-23-000001", "4", filed="2023-04-20", owners={"0000000002"})
        children = [filing(f"0000000001-23-{i:06d}", "4/A", filed="2023-05-01", orig="2023-04-20", owners={"0000000002"}) for i in range(2, 10)]
        rows = classify(self.periods([parent], children))
        self.assertEqual(sample_cases(rows), sample_cases(list(reversed(rows))))


if __name__ == "__main__":
    unittest.main()
