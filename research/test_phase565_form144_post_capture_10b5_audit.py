from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/phase403_sec_form144_first_seen_capture.yml")


class Phase565PostCapture10b5WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_classifier_runs_after_post_capture_quality_and_before_commit(self):
        quality = self.text.index("- name: Run post-capture Form 144 ledger quality audit")
        classifier = self.text.index("- name: Run post-capture Form 144 10b5-1 audit")
        commit = self.text.index("- name: Commit append-only first-seen ledger and poll state")
        self.assertLess(quality, classifier)
        self.assertLess(classifier, commit)
        self.assertIn("if: steps.post_capture_quality.outcome == 'success'", self.text)

    def test_classifier_reconciles_accession_and_detail_counts(self):
        self.assertIn("f['accessions'] == q['filing_count']", self.text)
        self.assertIn("f['detail_rows'] == q['row_count']", self.text)
        self.assertIn("d['controls']['signal_admitted'] is False", self.text)

    def test_post_capture_artifact_is_separate_and_success_gated(self):
        self.assertIn("name: phase565-form144-10b5-post-capture", self.text)
        self.assertIn("path: phase403_output/phase549_post_capture_summary.json", self.text)
        self.assertIn("if: always() && steps.post_capture_10b5.outcome == 'success'", self.text)

    def test_live_job_compiles_the_classifier(self):
        live_compile = self.text.split("- name: Compile capture and migration clients", 1)[1].split(
            "- name: Migrate append-only event ledger schema", 1
        )[0]
        self.assertIn("research/phase549_form144_10b5_plan_polarity_audit.py", live_compile)


if __name__ == "__main__":
    unittest.main()
