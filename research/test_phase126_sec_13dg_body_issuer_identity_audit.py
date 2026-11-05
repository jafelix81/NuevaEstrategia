import unittest
from research.phase126_sec_13dg_body_issuer_identity_audit import (
    clean_issuer_candidate, extract_cover_issuer_name, normalize_cik, normalize_name
)

class Phase126Tests(unittest.TestCase):
    def test_clean_name_rejects_cover_page_boilerplate(self):
        self.assertIsNone(clean_issuer_candidate("§ 240.13d-2(a)"))
        self.assertIsNone(clean_issuer_candidate("Formerly United Mobile Homes, Inc."))
        self.assertEqual(clean_issuer_candidate("01)* StoneCastle Financial Corp."), "StoneCastle Financial Corp.")

    def test_normalize_cik(self):
        self.assertEqual(normalize_cik("0001628063"), "1628063")
        self.assertEqual(normalize_cik("1628063"), "1628063")
        self.assertIsNone(normalize_cik(""))

    def test_normalize_name(self):
        self.assertEqual(normalize_name("Seritage Growth Properties"), "SERITAGE GROWTH PROPERTIES")

    def test_cover_issuer_name_from_preceding_label(self):
        raw = """<DOCUMENT><TYPE>SC 13G</TYPE><TEXT>
        <p>SCHEDULE 13G</p><p>(Amendment No. 2)</p>
        <p>StoneCastle Financial Corp.</p><p>(Name of Issuer)</p>
        <p>Common Stock</p><p>(Title of Class of Securities)</p>
        </TEXT></DOCUMENT>"""
        self.assertEqual(extract_cover_issuer_name(raw), "StoneCastle Financial Corp.")

    def test_cover_issuer_name_from_inline_label(self):
        raw = """<DOCUMENT><TYPE>SC 13G</TYPE><TEXT>
        <p>Item 1(a) Name of Issuer: MBIA Inc</p>
        </TEXT></DOCUMENT>"""
        self.assertEqual(extract_cover_issuer_name(raw), "MBIA Inc")

    def test_cover_issuer_name_joins_wrapped_lines(self):
        raw = """<DOCUMENT><TYPE>SC 13D</TYPE><TEXT>
        <p>(Amendment No. 14)</p><p>Seritage</p><p>Growth Properties</p>
        <p>(Name of Issuer)</p>
        </TEXT></DOCUMENT>"""
        self.assertEqual(extract_cover_issuer_name(raw), "Seritage Growth Properties")

if __name__ == "__main__":
    unittest.main()
