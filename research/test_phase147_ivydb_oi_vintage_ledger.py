import unittest
from research.phase147_ivydb_oi_vintage_ledger import build_oi_features_asof, select_vintages_asof

def vrow(session, previous, oi, volume, received, version_id, source_hash,
         kind="initial", supersedes="", operation="upsert", **overrides):
    item = {
        "security_id": "1001", "option_id": "90001", "session_date": session,
        "previous_session_date": previous, "open_interest": oi, "volume": volume,
        "expiration_date": "2027-01-15",
        "contract_terms_key": "deliverable=100shares|multiplier=100|adj=1",
        "first_received_at": received, "source_file_hash": source_hash,
        "source_version": "ivydb-open-interest-v5", "version_id": version_id,
        "version_kind": kind, "supersedes_version_id": supersedes, "operation": operation,
    }
    item.update(overrides)
    return item

def two_sessions(prior_oi=100, current_oi=125):
    return [
        vrow("2026-11-04", "", prior_oi, 400, "2026-11-05T08:50:00-05:00", "p0", "sha:p0"),
        vrow("2026-11-05", "2026-11-04", current_oi, 500, "2026-11-06T08:30:00-05:00", "c0", "sha:c0"),
    ]

class Phase147Tests(unittest.TestCase):
    def test_initial_vintage_selected_before_correction(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0")]
        cur = [x for x in select_vintages_asof(rows,"2026-11-06T09:00:00-05:00") if x["session_date"].isoformat()=="2026-11-05"][0]
        self.assertEqual((cur["open_interest"],cur["version_id"],cur["correction_count"]),(125,"c0",0))

    def test_correction_selected_after_receipt(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0")]
        cur = [x for x in select_vintages_asof(rows,"2026-11-06T10:00:01-05:00") if x["session_date"].isoformat()=="2026-11-05"][0]
        self.assertEqual((cur["open_interest"],cur["version_id"],cur["correction_count"]),(118,"c1",1))

    def test_exact_correction_timestamp_excludes_correction(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0")]
        cur = [x for x in select_vintages_asof(rows,"2026-11-06T10:00:00-05:00") if x["session_date"].isoformat()=="2026-11-05"][0]
        self.assertEqual(cur["version_id"],"c0")

    def test_later_correction_does_not_rewrite_earlier_asof_result(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0")]
        early = build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")
        late = build_oi_features_asof(rows,"2026-11-06T10:00:01-05:00")
        self.assertEqual((early[1]["delta_open_interest"],late[1]["delta_open_interest"]),(25,18))
        self.assertEqual((early[1]["current_version_id"],late[1]["current_version_id"]),("c0","c1"))

    def test_prior_session_correction_delays_feature_knowledge_time(self):
        rows = [
            vrow("2026-11-04","",100,400,"2026-11-05T08:50:00-05:00","p0","sha:p0"),
            vrow("2026-11-05","2026-11-04",125,500,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
            vrow("2026-11-04","",110,400,"2026-11-06T08:45:00-05:00","p1","sha:p1",kind="correction",supersedes="p0"),
        ]
        before = build_oi_features_asof(rows,"2026-11-06T08:40:00-05:00")[1]
        after = build_oi_features_asof(rows,"2026-11-06T08:50:00-05:00")[1]
        self.assertEqual((before["delta_open_interest"],before["knowledge_time"]),(25,"2026-11-06T08:30:00-05:00"))
        self.assertEqual((after["delta_open_interest"],after["knowledge_time"],after["prior_version_id"]),(15,"2026-11-06T08:45:00-05:00","p1"))

    def test_prior_correction_exact_time_is_not_used(self):
        rows = [
            vrow("2026-11-04","",100,400,"2026-11-05T08:50:00-05:00","p0","sha:p0"),
            vrow("2026-11-05","2026-11-04",125,500,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
            vrow("2026-11-04","",110,400,"2026-11-06T08:45:00-05:00","p1","sha:p1",kind="correction",supersedes="p0"),
        ]
        current = build_oi_features_asof(rows,"2026-11-06T08:45:00-05:00")[1]
        self.assertEqual((current["delta_open_interest"],current["prior_version_id"]),(25,"p0"))

    def test_correction_chain_requires_immediate_predecessor(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="wrong")]
        with self.assertRaisesRegex(ValueError,"correction_chain_mismatch"):
            select_vintages_asof(rows,"2026-11-06T11:00:00-05:00")

    def test_correction_before_initial_is_rejected(self):
        rows = [
            vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T08:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0"),
            vrow("2026-11-05","2026-11-04",125,500,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
        ]
        with self.assertRaisesRegex(ValueError,"vintage_chain_missing_initial"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_equal_receipt_timestamps_are_ambiguous(self):
        rows = two_sessions() + [vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T08:30:00-05:00","c1","sha:c1",kind="correction",supersedes="c0")]
        with self.assertRaisesRegex(ValueError,"ambiguous_or_nonmonotonic"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_duplicate_version_id_is_rejected(self):
        rows=two_sessions(); rows.append(dict(rows[1]))
        with self.assertRaisesRegex(ValueError,"duplicate_version_id"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_duplicate_source_hash_in_chain_is_rejected(self):
        rows=two_sessions()+[vrow("2026-11-05","2026-11-04",118,500,"2026-11-06T10:00:00-05:00","c1","sha:c0",kind="correction",supersedes="c0")]
        with self.assertRaisesRegex(ValueError,"duplicate_source_hash"):
            select_vintages_asof(rows,"2026-11-06T11:00:00-05:00")

    def test_tombstone_applies_only_after_receipt(self):
        rows=two_sessions()+[vrow("2026-11-05","2026-11-04",None,None,"2026-11-06T10:00:00-05:00","c1","sha:c1",kind="correction",supersedes="c0",operation="delete")]
        before=select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")
        after=select_vintages_asof(rows,"2026-11-06T10:00:01-05:00")
        self.assertEqual([x for x in before if x["session_date"].isoformat()=="2026-11-05"][0]["status"],"OK")
        self.assertEqual([x for x in after if x["session_date"].isoformat()=="2026-11-05"][0]["status"],"WITHDRAWN")

    def test_initial_delete_is_rejected(self):
        rows=[vrow("2026-11-05","2026-11-04",None,None,"2026-11-06T08:30:00-05:00","c0","sha:c0",operation="delete")]
        with self.assertRaisesRegex(ValueError,"initial_version_cannot_be_delete"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_missing_provenance_is_rejected(self):
        rows=two_sessions(); rows[1]["source_file_hash"]=""
        with self.assertRaisesRegex(ValueError,"source_or_version_provenance_missing"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_naive_receipt_timestamp_is_rejected(self):
        rows=two_sessions(); rows[1]["first_received_at"]="2026-11-06T08:30:00"
        with self.assertRaisesRegex(ValueError,"timezone_aware"):
            select_vintages_asof(rows,"2026-11-06T09:00:00-05:00")

    def test_naive_decision_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"timezone_aware"):
            select_vintages_asof(two_sessions(),"2026-11-06T09:00:00")

    def test_future_initial_is_not_visible(self):
        rows=[vrow("2026-11-05","2026-11-04",125,500,"2026-11-06T10:00:00-05:00","c0","sha:c0")]
        self.assertEqual(select_vintages_asof(rows,"2026-11-06T09:00:00-05:00"),[])

    def test_prior_not_yet_known_is_not_bridged(self):
        rows=[
            vrow("2026-11-04","",100,400,"2026-11-06T10:00:00-05:00","p0","sha:p0"),
            vrow("2026-11-05","2026-11-04",125,500,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
        ]
        current=[x for x in build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00") if x["session_date"]=="2026-11-05"][0]
        self.assertEqual(current["status"],"PRIOR_NOT_YET_KNOWN")
        self.assertIsNone(current["delta_open_interest"])

    def test_nonadjacent_previous_session_is_blocked(self):
        rows=[
            vrow("2026-11-03","",90,100,"2026-11-04T08:50:00-05:00","p0","sha:p0"),
            vrow("2026-11-04","2026-11-03",100,150,"2026-11-05T08:50:00-05:00","m0","sha:m0"),
            vrow("2026-11-05","2026-11-03",125,500,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
        ]
        current=[x for x in build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00") if x["session_date"]=="2026-11-05"][0]
        self.assertEqual(current["status"],"NON_ADJACENT_PREVIOUS_SESSION")
        self.assertIsNone(current["delta_open_interest"])

    def test_expiry_session_precedes_expiration_break(self):
        rows=two_sessions(); rows[1]["expiration_date"]="2026-11-05"
        current=build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")[1]
        self.assertEqual(current["status"],"EXPIRY_OR_EXERCISE_AFFECTED")

    def test_expiration_change_blocks_delta(self):
        rows=two_sessions(); rows[1]["expiration_date"]="2027-01-22"
        current=build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")[1]
        self.assertEqual(current["status"],"EXPIRATION_DATE_BREAK")
        self.assertIsNone(current["delta_open_interest"])

    def test_source_version_break_blocks_delta(self):
        rows=two_sessions(); rows[1]["source_version"]="ivydb-open-interest-v6"
        current=build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")[1]
        self.assertEqual(current["status"],"SOURCE_VERSION_BREAK")
        self.assertIsNone(current["delta_open_interest"])

    def test_negative_delta_is_preserved_and_not_directional(self):
        current=build_oi_features_asof(two_sessions(100,80),"2026-11-06T09:00:00-05:00")[1]
        self.assertEqual(current["delta_open_interest"],-20)
        self.assertFalse(current["directional_buyer_signal"])

    def test_zero_denominators_are_null(self):
        rows=[
            vrow("2026-11-04","",0,0,"2026-11-05T08:50:00-05:00","p0","sha:p0"),
            vrow("2026-11-05","2026-11-04",10,0,"2026-11-06T08:30:00-05:00","c0","sha:c0"),
        ]
        current=build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")[1]
        self.assertIsNone(current["delta_oi_to_volume"])
        self.assertIsNone(current["delta_oi_fraction_prior"])
        self.assertIsNone(current["volume_to_prior_oi"])

    def test_contract_terms_change_blocks_delta(self):
        rows=two_sessions(); rows[1]["contract_terms_key"]="deliverable=101shares|multiplier=100|adj=1"
        current=build_oi_features_asof(rows,"2026-11-06T09:00:00-05:00")[1]
        self.assertEqual(current["status"],"CONTRACT_TERMS_BREAK")
        self.assertIsNone(current["delta_open_interest"])

if __name__ == "__main__":
    unittest.main()
