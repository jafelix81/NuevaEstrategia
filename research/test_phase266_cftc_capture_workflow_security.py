"""Static safety contract for the CFTC scheduled/manual capture workflow.

These tests do not run the live capture. They guard deployment policy and ensure
that the write-capable workflow is restricted to the default branch, keeps the
checkout token out of parser steps, validates both parsers before capture, and
refuses non-additive changes to the raw PIT archive.
"""
from pathlib import Path
import unittest

WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "phase234_cftc_bpr_prospective_capture.yml"
)


class Phase266CftcWorkflowSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_exists_and_is_schedule_or_manual_only(self):
        self.assertIn("on:\n  schedule:", self.text)
        self.assertIn("  workflow_dispatch:", self.text)
        self.assertNotIn("pull_request:", self.text)
        self.assertNotIn("pull_request_target:", self.text)

    def test_write_capable_job_is_restricted_to_main(self):
        self.assertIn("if: github.ref == 'refs/heads/main'", self.text)
        self.assertIn("permissions:\n  contents: write", self.text)

    def test_checkout_does_not_persist_write_credentials(self):
        self.assertIn("persist-credentials: false", self.text)

    def test_token_is_exposed_only_in_commit_step(self):
        self.assertEqual(self.text.count("GH_TOKEN: ${{ github.token }}"), 1)
        self.assertIn('git -c http.extraheader="AUTHORIZATION: basic $AUTH_HEADER" push origin "HEAD:${GITHUB_REF_NAME}"', self.text)

    def test_both_capture_test_suites_run_before_network_capture(self):
        bpr_test = self.text.index("python -m unittest -v research.test_phase234_cftc_bpr_capture")
        tff_test = self.text.index("python -m unittest -v research.test_phase239_cftc_tff_prospective_capture")
        bpr_capture = self.text.index("- name: Capture latest CFTC BPR futures report")
        tff_capture = self.text.index("- name: Capture latest CFTC TFF futures-only and combined reports")
        self.assertLess(bpr_test, bpr_capture)
        self.assertLess(tff_test, bpr_capture)
        self.assertLess(bpr_capture, tff_capture)

    def test_raw_archive_commit_is_additive_only(self):
        self.assertIn("git diff --cached --name-status | grep -Ev '^A[[:space:]]'", self.text)
        self.assertIn("Refusing to commit a modification, rename, or deletion", self.text)
        self.assertIn("git add -A -- data/cftc_bpr", self.text)
        self.assertIn("git add -A -- data/cftc_tff", self.text)

    def test_timeout_allows_retained_bpr_polling(self):
        self.assertIn("timeout-minutes: 20", self.text)


if __name__ == "__main__":
    unittest.main()
