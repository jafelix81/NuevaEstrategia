import unittest
from research.phase276_pr14_action_reference_immutability_audit import WRITE_WORKFLOW, WORKFLOW_PATHS, inspect_workflow

CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"

class Phase276WorkflowAuditTests(unittest.TestCase):
    def read_only(self, extra=""):
        return (
            "name: test\non:\n  pull_request:\n    branches: [main]\n"
            "permissions:\n  contents: read\njobs:\n  test:\n    steps:\n"
            f"      - uses: {CHECKOUT}\n      - uses: {SETUP}\n" + extra
        )

    def test_verified_full_sha_refs_pass(self):
        result = inspect_workflow(".github/workflows/test.yml", self.read_only())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["action_ref_count"], 2)

    def test_major_tag_is_rejected(self):
        text = self.read_only().replace(CHECKOUT, "actions/checkout@v4")
        self.assertIn("UNPINNED_ACTION_REF", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_wrong_full_sha_is_rejected(self):
        text = self.read_only().replace(CHECKOUT, "actions/checkout@" + "0" * 40)
        self.assertIn("ACTION_SHA_NOT_IN_VERIFIED_PIN_SET", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_unknown_action_source_is_rejected(self):
        text = self.read_only().replace(CHECKOUT, "third-party/action@" + "1" * 40)
        self.assertIn("UNREVIEWED_ACTION_SOURCE", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_missing_permissions_is_rejected(self):
        text = self.read_only().replace("permissions:\n  contents: read\n", "")
        self.assertIn("MISSING_EXPLICIT_PERMISSIONS", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_pull_request_target_is_rejected(self):
        text = self.read_only().replace("on:\n  pull_request:", "on:\n  pull_request_target:")
        self.assertIn("PULL_REQUEST_TARGET_PRESENT", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_write_permission_on_non_cftc_workflow_is_rejected(self):
        text = self.read_only().replace("contents: read", "contents: write")
        self.assertIn("UNEXPECTED_WRITE_CAPABLE_WORKFLOW", inspect_workflow(".github/workflows/test.yml", text)["errors"])

    def test_cftc_write_path_requires_all_guards(self):
        text = self.read_only().replace("contents: read", "contents: write")
        self.assertIn("CFTC_WRITE_GUARD_MISSING", inspect_workflow(WRITE_WORKFLOW, text)["errors"])

    def test_cftc_guarded_write_path_is_recognized(self):
        text = (
            "name: cftc\non:\n  schedule:\n    - cron: '0 0 * * 1-5'\n"
            "permissions:\n  contents: write\n"
            "jobs:\n  capture:\n    if: github.ref == 'refs/heads/main'\n"
            "    steps:\n      - uses: " + CHECKOUT + "\n"
            "        with:\n          persist-credentials: false\n"
            "      - env:\n          GH_TOKEN: $" + "{{ github.token }}\n"
            "        run: |\n"
            "          git diff --cached --name-status | grep -Ev '^A[[:space:]]'\n"
            '          git -c http.extraheader="AUTHORIZATION: basic $AUTH_HEADER" push origin\n'
        )
        self.assertEqual(inspect_workflow(WRITE_WORKFLOW, text)["errors"], [])

    def test_workflow_without_action_refs_is_rejected(self):
        result = inspect_workflow(".github/workflows/test.yml", "permissions:\n  contents: read\n")
        self.assertIn("NO_ACTION_REFERENCES", result["errors"])

    def test_phase277_and_phase278_are_in_audit_inventory(self):
        self.assertIn(".github/workflows/phase277_finra_ats_stratified_coverage_audit.yml", WORKFLOW_PATHS)
        self.assertIn(".github/workflows/phase278_finra_ats_duplicate_grain_followup.yml", WORKFLOW_PATHS)
        self.assertEqual(len(WORKFLOW_PATHS), 30)

if __name__ == "__main__":
    unittest.main()
