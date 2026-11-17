import csv
import tempfile
import unittest
from pathlib import Path

from research import phase403_sec_form144_first_seen_capture as p403
from research.phase454_form144_event_ledger_schema_migration import migrate_event_ledger

NEW_FIELDS={"cross_feed_provenance_complete","capture_poll_status"}
LEGACY_FIELDS=[x for x in p403.EVENT_FIELDS if x not in NEW_FIELDS]

class Phase454MigrationTests(unittest.TestCase):
    def write_csv(self,path,fields,rows):
        with path.open("w",newline="",encoding="utf-8") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_legacy_header_migrates_and_preserves_rows_then_new_append_aligns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.csv"
            old={
                "accession":"0001517413-26-000361","form":"144","feed_name":"144",
                "feed_names":"[\"144\"]","feed_title":"old title",
                "feed_link":"https://www.sec.gov/Archives/edgar/data/1769490/x",
                "feed_updated_raw":"2026-11-13T16:24:50-05:00",
                "feed_updated_utc":"2026-11-13T21:24:50Z","feed_path_cik":"0001769490",
                "first_seen_at_utc":"2026-11-14T20:45:08Z"
            }
            self.write_csv(path,LEGACY_FIELDS,[old])
            result=migrate_event_ledger(path)
            self.assertTrue(result["changed"])
            self.assertEqual(result["rows_migrated"],1)
            with path.open("r",newline="",encoding="utf-8") as handle:
                reader=csv.DictReader(handle)
                self.assertEqual(reader.fieldnames,p403.EVENT_FIELDS)
                prior=next(reader)
            self.assertEqual(prior["feed_path_cik"],"0001769490")
            self.assertEqual(prior["feed_updated_raw"],"2026-11-13T16:24:50-05:00")
            self.assertEqual(prior["cross_feed_provenance_complete"],"")
            self.assertEqual(prior["capture_poll_status"],"")
            new={field:"" for field in p403.EVENT_FIELDS}
            new.update({"accession":"0001950047-26-011078","form":"144","feed_path_cik":"0001833508",
                        "feed_updated_raw":"2026-11-16T16:55:39-05:00",
                        "cross_feed_provenance_complete":"False","capture_poll_status":"partial"})
            p403.append_events(path,[new])
            with path.open("r",newline="",encoding="utf-8") as handle:
                rows=list(csv.DictReader(handle))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[1]["feed_path_cik"],"0001833508")
            self.assertEqual(rows[1]["feed_updated_raw"],"2026-11-16T16:55:39-05:00")
            self.assertEqual(rows[1]["capture_poll_status"],"partial")

    def test_migration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.csv"
            self.write_csv(path,LEGACY_FIELDS,[{"accession":"A"}])
            first=migrate_event_ledger(path)
            self.assertTrue(first["changed"])
            after_first=path.read_bytes()
            second=migrate_event_ledger(path)
            self.assertFalse(second["changed"])
            self.assertEqual(second["reason"],"already_current")
            self.assertEqual(path.read_bytes(),after_first)

    def test_unknown_column_fails_closed_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.csv"
            self.write_csv(path,LEGACY_FIELDS+["unrecognized"],[{"accession":"A","unrecognized":"keep"}])
            before=path.read_bytes()
            with self.assertRaisesRegex(ValueError,"unknown columns"):
                migrate_event_ledger(path)
            self.assertEqual(path.read_bytes(),before)

    def test_duplicate_header_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.csv"
            path.write_text("accession,accession\nA,B\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"duplicate header"):
                migrate_event_ledger(path)

    def test_extra_row_values_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"events.csv"
            path.write_text("accession,form\nA,144,unexpected\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"extra columns"):
                migrate_event_ledger(path)

    def test_missing_or_empty_file_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"missing.csv"
            self.assertFalse(migrate_event_ledger(path)["changed"])
            path.write_text("",encoding="utf-8")
            self.assertFalse(migrate_event_ledger(path)["changed"])

if __name__=="__main__": unittest.main()
