from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from research import phase525_form4_reporting_owner_identity as p

XML = b"""<ownershipDocument>
<issuer><issuerCik><value>0001593899</value></issuerCik><issuerName><value>Atea Pharmaceuticals, Inc.</value></issuerName></issuer>
<reportingOwner><reportingOwnerId><rptOwnerCik><value>0001508458</value></rptOwnerCik><rptOwnerName><value>Bruce Polsky</value></rptOwnerName></reportingOwnerId><reportingOwnerRelationship><isDirector><value>1</value></isDirector></reportingOwnerRelationship></reportingOwner>
<remarks>Sale transactions were executed to pay the exercise price of options for tax planning purposes.</remarks>
</ownershipDocument>"""
MULTI = b"""<ownershipDocument><issuer/><reportingOwner><reportingOwnerId><rptOwnerCik><value>0001508458</value></rptOwnerCik><rptOwnerName><value>Bruce Polsky</value></rptOwnerName></reportingOwnerId></reportingOwner><reportingOwner><reportingOwnerId><rptOwnerCik><value>0001829622</value></rptOwnerCik><rptOwnerName><value>Bruno Lucidi</value></rptOwnerName></reportingOwnerId></reportingOwner></ownershipDocument>"""

class Phase525OwnerIdentityTests(unittest.TestCase):
    def test_single_owner_is_filing_grain_only(self):
        parsed = p.parse_owner_identity(XML)
        self.assertEqual(parsed["reporting_owner_count"], 1)
        self.assertEqual(parsed["owners"][0]["owner_cik"], "0001508458")
        self.assertEqual(parsed["owners"][0]["owner_name"], "Bruce Polsky")
        self.assertTrue(parsed["remarks_flags"]["exercise_price_payment_mention"])
        self.assertTrue(parsed["remarks_flags"]["tax_planning_mention"])

    def test_multi_owner_never_gets_transaction_line_link(self):
        parsed = p.parse_owner_identity(MULTI)
        rows = p.build_owner_rows({"accession":"0000123456-26-000001","form":"4"}, {}, parsed)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(x["line_owner_link_status"] == "MULTI_OWNER_FILING_GRAIN_ONLY_NO_LINE_LINK" for x in rows))
        self.assertTrue(all(x["transaction_line_attribution_verified"] is False for x in rows))

    def test_manual_mode_does_not_fetch_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = p.run_backfill("manual", 10, Path(tmp) / "out", Path(tmp) / "events.csv", Path(tmp) / "details.csv", Path(tmp) / "owners.csv")
            self.assertEqual(summary["disposition"], "MANUAL_MODE_NO_FETCH_NO_PERSISTENCE")
            self.assertFalse((Path(tmp) / "owners.csv").exists())

if __name__ == "__main__":
    unittest.main()
