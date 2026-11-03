import unittest
from phase35_13dg_parser_v2 import parse_xml, parse_legacy, parse_index, group_fingerprint


class ParserTests(unittest.TestCase):
    def test_13d_xml(self):
        x = """<edgarSubmission xmlns="urn:13d"><previousAccessionNumber>0001193125-23-304047</previousAccessionNumber>
        <issuerCIK>0000031005</issuerCIK><issuerCUSIP>123456789</issuerCUSIP>
        <reportingPersonInfo><reportingPersonCIK>0000310051</reportingPersonCIK><reportingPersonName>Alpha Fund LLC</reportingPersonName></reportingPersonInfo>
        <reportingPersonInfo><reportingPersonName>Jane Doe</reportingPersonName></reportingPersonInfo>
        <transactionPurpose>Seeking board representation.</transactionPurpose></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0000031005")
        self.assertEqual(r["previous_accession"], "0001193125-23-304047")
        self.assertEqual(len(r["reporting_persons"]), 2)
        self.assertEqual(r["purpose_text"], "Seeking board representation.")
        self.assertTrue(group_fingerprint(r["reporting_persons"]))

    def test_13g_xml_distinct_schema(self):
        x = """<edgarSubmission xmlns="urn:13g"><previousAccessionNumber>0000092230-25-000001</previousAccessionNumber>
        <issuerCik>0001849998</issuerCik><issuerName>Federated Hermes ETF Trust</issuerName><issuerCusip>31423L503</issuerCusip>
        <eventDateRequiresFilingThisStatement>01/31/2025</eventDateRequiresFilingThisStatement>
        <coverPageHeaderReportingPersonDetails><reportingPersonName>TRUIST FINANCIAL CORP</reportingPersonName>
        <reportingPersonBeneficiallyOwnedAggregateNumberOfShares>153847</reportingPersonBeneficiallyOwnedAggregateNumberOfShares>
        <classPercent>38.0</classPercent><typeOfReportingPerson>IA</typeOfReportingPerson><typeOfReportingPerson>HC</typeOfReportingPerson>
        </coverPageHeaderReportingPersonDetails><filingPersonName>Truist Financial Corporation</filingPersonName></edgarSubmission>"""
        r = parse_xml(x)
        self.assertEqual(r["subject_issuer_cik"], "0001849998")
        self.assertEqual(r["subject_issuer_name"], "Federated Hermes ETF Trust")
        self.assertEqual(r["subject_issuer_cusips"], ["31423L503"])
        self.assertEqual(r["previous_accession"], "0000092230-25-000001")
        self.assertEqual(r["reporting_persons"][0]["name"], "TRUIST FINANCIAL CORP",)
        self.assertEqual(r["reporting_persons"][0]["percent"], "38.0")
        self.assertEqual(r["reporting_persons"][0]["types"], "IA|HC")

    def test_legacy_multiple_people(self):
        t = """Item 1: Reporting Person - FMR LLC
        Item 1: Reporting Person - Abigail P. Johnson
        CUSIÿÿÀÈÔÌÌäÌÄÀÈ()=%9P%1%9I59P(ÈôÁÉÍ}±ä¡Ð¤(Í±¹ÍÍÉÑÅÕ°¡ÉlÉÁ½ÉÑ¥¹}ÁÉÍ½¹}¹µÌt°l5H11°¥¥°@¸)½¡¹Í½¸t¤(Í±¹ÍÍÉÑÅÕ°¡ÉlÕÍ¥Àt°ÈÔÌÌäÌÄÀÈ¤(Í±¹ÍÍÉÑQÉÕ¡Él©½¥¹Ñ}¥±¥¹}Éµ¹Ðt¤((ÑÍÑ}±å}½ÙÉ}Á¡Í±¤è(ÐôUM%@9¼¸ÀÈÌäÁÄÀÄ(Äð9µ½ÉÁ½ÉÑ¥¹ÁÉÍ½¸(!1TI1=LM1%4(%Ñ´Ð¸AÕÉÁ½Í½QÉ¹ÍÑ¥½¸(Q¡ÉÁ½ÉÑ¥¹ÁÉÍ½¹ÌµäÍ¬Ñ¼¥¹±Õ¹µ¹µ¹Ð¸(%Ñ´Ô¸%¹ÑÉÍÐ¥¸MÕÉ¥Ñ¥Ì(ÈôÁÉÍ}±ä¡Ð¤(Í±¹ÍÍÉÑ%¸ !1TI1=LM1%4°ÉlÉÁ½ÉÑ¥¹}ÁÉÍ½¹}¹µÌt¤(Í±¹ÍÍÉÑ%¸ ¥¹±Õ¹°ÉlÁÕÉÁ½Í}ÑáÐt¤((ÑÍÑ}¥¹á}ÍÁÉÑÍ}¥±É}¹}ÍÕ©Ð¡Í±¤è(Áôñ¥ØùÁÑð½¥Øøñ¥ØøÈÀÈÐ´ÄÈ´ÈÜÄØèÄÔèÄÈð½¥Øø(ñ¥Øù!1TI1=LM1%4¡¥±ä¤%,èÀÀÀÄÀàÀäÄÀð½¥Øø(ñ¥Øù5I%5=Y%0MX¡MÕ©Ð¤%,èÀÀÀÄÄÈäÄÌÜð½¥Øø(ÈôÁÉÍ}¥¹à¡Á¤(Í±¹ÍÍÉÑÅÕ°¡Él¥±}å}¥¬t°ÀÀÀÄÀàÀäÄÀ¤(Í±¹ÍÍÉÑÅÕ°¡ÉlÍÕ©Ñ}¥¬t°ÀÀÀÄÄÈäÄÌÜ¤(Í±¹ÍÍÉÑÅÕ°¡ÉlÁÑ}Ðt°ÈÀÈÐ´ÄÈ´ÈÜÄØèÄÔèÄÈ¤(()¥}}¹µ}|ôô}}µ¥¹}|è(Õ¹¥ÑÑÍÐ¹µ¥¸ ¤(ÿÿÿ