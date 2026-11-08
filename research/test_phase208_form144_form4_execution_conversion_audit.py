import unittest
from datetime import date
from decimal import Decimal

from research.phase208_form144_form4_execution_conversion_audit import (
    cik, name, cls, family, flag, match
)

class Phase208Tests(unittest.TestCase):
    def test_cik_padding(self):
        self.assertEqual(cik("0000012345"), "12345")

    def test_name_normalization_is_strict(self):
        self.assertEqual(name("Jane A. Doe, Jr."), "JANEADOEJR")
        self.assertNotEqual(name("Jane Doe"), name("Doe Jane"))

    def test_class_families(self):
        self.assertEqual(family("Class A Common Stock"), "CLASS_A")
        self.assertEqual(family("Common Stock, $0.01 par value"), "COMMON")
        self.assertEqual(family("Ordinary Shares"), "ORDINARY")
        self.assertEqual(family("Series A Preferred"), "SERIES_A")

    def test_10b5_flag(self):
        self.assertIs(flag("1"), True)
        self.assertIs(flag("true"), True)
        self.assertIs(flag("0"), False)
        self.assertIs(flag("false"), False)
        self.assertIsNone(flag(""))

    def test_one_to_one_exact_match(self):
        t = {"accession":"144a","idx":"1","issuer":"123","seller":"JANEDOE",
             "date":date(2026,7,1),"units":Decimal("100"),
             "class_norm":"COMMON","class_family":"COMMON","plan":False}
        b = {"accession":"4a","issuer":"123","owner":"JANEDOE",
             "date":date(2026,7,2),"shares":Decimal("100"),
             "class_norm":"COMMONSTOCK","class_family":"COMMON","lag":2,"flag":"false"}
        candidates, unique = match([t],[b],0,2)
        self.assertEqual(len(candidates),1)
        self.assertEqual(len(unique),1)
        self.assertTrue(unique[0]["exact_qty"])

    def test_pre_notice_is_not_post_notice(self):
        t = {"accession":"144a","idx":"1","issuer":"123","seller":"JANEDOE",
             "date":date(2026,7,2),"units":Decimal("100"),
             "class_norm":"COMMON","class_family":"COMMON","plan":False}
        b = {"accession":"4a","issuer":"123","owner":"JANEDOE",
             "date":date(2026,7,1),"shares":Decimal("100"),
             "class_norm":"COMMONSTOCK","class_family":"COMMON","lag":2,"flag":"false"}
        self.assertEqual(len(match([t],[b],0,2)[1]),0)
        self.assertEqual(len(match([t],[b],-2,-1)[1]),1)

    def test_collision_rejected(self):
        base = {"issuer":"123","seller":"JANEDOE","date":date(2026,7,1),
                "units":Decimal("100"),"class_norm":"COMMON","class_family":"COMMON","plan":False}
        t1 = dict(base,accession="144a",idx="1")
        t2 = dict(base,accession="144b",idx="1")
        b = {"accession":"4a","issuer":"123","owner":"JANEDOE",
             "date":date(2026,7,1),"shares":Decimal("100"),
             "class_norm":"COMMONSTOCK","class_family":"COMMON","lag":1,"flag":"false"}
        candidates, unique = match([t1,t2],[b],0,2)
        self.assertEqual(len(candidates),2)
        self.assertEqual(len(unique),0)

if __name__ == "__main__":
    unittest.main()
