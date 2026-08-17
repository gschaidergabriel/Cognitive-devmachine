import hashlib
import json
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


class MicroClayExplicitFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="clay-explicit-feedback-")
        self.db = UnifiedDB(Path(self.tmp.name) / "unified.db")
        self.db.ensure_user("gabriel", "Gabriel")
        self.db.ensure_user("andreas", "Andreas")
        self.session_id = self.db.ensure_session("gabriel", "clayverse-gabriel")
        self.db.ensure_session("andreas", "clayverse-andreas")
        self.organ = MicroClayExplicitFeedback(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def apply(self, request, **kwargs):
        return self.organ.apply(**request, source="USER_EXPLICIT", **kwargs)

    def add_memory(
        self,
        memory_id,
        *,
        subject="topic:shared",
        value="orchid procedure",
        user_id="gabriel",
        source_turn_id=None,
        kind="fact",
        ts=None,
    ):
        self.db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                memory_id, kind, subject, value, source_turn_id, user_id,
                time.time() if ts is None else ts,
                json.dumps({"source": "explicit-feedback-test"}),
            ),
        )

    def seed_retrieval(self, *, query="codename", selected=(), shadow=()):
        turn_id = self.db.append_turn(self.session_id, "gabriel", "user", query)
        episode_id = str(uuid.uuid4())
        causal_id = str(uuid.uuid4())
        retrieval_id = str(uuid.uuid4())
        now = time.time()
        self.db.db.execute(
            "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, self.session_id, now, turn_id, 0.5, "[]", None, "OPEN"),
        )
        token_hashes = [
            MicroClayRetrieval._token_key(token)[4:]
            for token in sorted(MicroClayRetrieval._tokens(query))
        ]
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        chars_selected = 0
        for memory_id in selected:
            row = self.db.db.execute(
                "SELECT value FROM durable_memory WHERE memory_id=?", (memory_id,)
            ).fetchone()
            if row is not None:
                chars_selected += len(str(row["value"]))
        self.db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,limit_items,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                retrieval_id, turn_id, episode_id, causal_id, self.session_id, "gabriel",
                self.db.entity_generation(), MicroClayRetrieval.POLICY_VERSION, "SHADOW",
                query_hash, json.dumps(token_hashes), json.dumps(list(selected)),
                json.dumps(list(shadow)), "[]", 12000, 24, chars_selected,
                "PRESENT" if selected else "UNKNOWN", now,
            ),
        )
        return {
            "retrieval_id": retrieval_id,
            "user_id": "gabriel",
            "session_id": self.session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": self.db.entity_generation(),
            "query_sha256": query_hash,
            "budget_chars": 12000,
            "limit_items": 24,
        }

    def real_retrieval(self, query):
        turn_id = self.db.append_turn(self.session_id, "gabriel", "user", query)
        episode_id = str(uuid.uuid4())
        causal_id = str(uuid.uuid4())
        self.db.db.execute(
            "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, self.session_id, time.time(), turn_id, 0.5, "[]", None, "OPEN"),
        )
        result = MicroClayRetrieval(self.db).retrieve(
            query=query,
            user_id="gabriel",
            session_id=self.session_id,
            turn_id=turn_id,
            episode_id=episode_id,
            causal_id=causal_id,
            generation=self.db.entity_generation(),
        )
        row = self.db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        return result, json.loads(row["selected_memory_ids"]), json.loads(row["shadow_memory_ids"])

    def test_complete_miss_teaches_exact_memory_route_without_sibling_spray(self):
        self.add_memory("target", value="orchid procedure")
        self.add_memory("sibling", value="bicycle violet")
        request = self.seed_retrieval(query="codename")

        applied = self.apply(
            request, feedback_class="USER_MISS_TARGET", target_memory_id="target"
        )
        self.assertTrue(applied["applied"])
        self.assertEqual(applied["updated_entrypoints"], 1)
        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        target_key = self.organ._route_key(cue_hash, "target")
        sibling_key = self.organ._route_key(cue_hash, "sibling")
        self.assertGreater(
            self.db.db.execute(
                "SELECT capital FROM retrieval_entrypoint_policy WHERE entry_key=?", (target_key,)
            ).fetchone()[0], 0.0,
        )
        self.assertIsNone(
            self.db.db.execute(
                "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (sibling_key,)
            ).fetchone()
        )

        result, selected, shadow = self.real_retrieval("codename")
        self.assertEqual(result["receipt"]["mode"], "SHADOW")
        self.assertEqual(result["receipt"]["status"], "UNKNOWN")
        self.assertEqual(selected, [])
        self.assertEqual(shadow, ["target"])

        replay = self.apply(
            request, feedback_class="USER_MISS_TARGET", target_memory_id="target"
        )
        self.assertFalse(replay["applied"])
        self.assertEqual(replay["reason"], "duplicate_receipt")
        self.assertEqual(
            self.db.db.execute(
                "SELECT pulls FROM retrieval_entrypoint_policy WHERE entry_key=?", (target_key,)
            ).fetchone()[0], 1,
        )

    def test_identity_source_mode_and_hindsight_fail_before_mutation(self):
        self.add_memory("target")
        request = self.seed_retrieval()
        bad = dict(request)
        bad["budget_chars"] -= 1
        with self.assertRaises(StaleGeneration):
            self.apply(bad, feedback_class="USER_MISS_TARGET", target_memory_id="target")
        with self.assertRaises(PermissionError):
            self.organ.apply(
                **request,
                source="CLAUDE_INFERRED",
                feedback_class="USER_MISS_TARGET",
                target_memory_id="target",
            )

        hindsight = self.seed_retrieval(query="later-codename")
        time.sleep(0.001)
        self.add_memory("future-target", subject="topic:future")
        with self.assertRaisesRegex(PermissionError, "did not exist at retrieval time"):
            self.apply(
                hindsight,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="future-target",
            )

        self.db.db.execute("UPDATE retrieval_policy_state SET mode='ACTIVE' WHERE singleton=1")
        with self.assertRaises(PermissionError):
            self.apply(request, feedback_class="USER_MISS_TARGET", target_memory_id="target")
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0], 0)
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0], 0)

    def test_privacy_control_current_turn_and_corrupt_replay_fail_closed(self):
        base_ts = time.time() - 10.0
        self.add_memory("other-user", user_id="andreas", ts=base_ts)
        self.add_memory("control", kind="source_archive", ts=base_ts)
        self.add_memory("target", subject="topic:target", ts=base_ts)
        request = self.seed_retrieval()
        self.add_memory(
            "echo",
            subject="topic:echo",
            source_turn_id=request["turn_id"],
            ts=base_ts,
        )

        for target in ("other-user", "control", "echo"):
            with self.subTest(target=target), self.assertRaises(PermissionError):
                self.apply(
                    request,
                    feedback_class="USER_MISS_TARGET",
                    target_memory_id=target,
                )

        self.db.db.execute(
            "UPDATE retrieval_episodes SET shadow_memory_ids=? WHERE retrieval_id=?",
            (json.dumps(["other-user"]), request["retrieval_id"]),
        )
        with self.assertRaises(StaleGeneration):
            self.apply(
                request,
                feedback_class="USER_MISS_TARGET",
                target_memory_id="target",
            )
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0], 0)

    def test_no_memory_records_calibration_without_inventing_route(self):
        request = self.seed_retrieval()
        result = self.apply(request, feedback_class="USER_NO_MEMORY")
        self.assertTrue(result["applied"])
        self.assertEqual(result["updated_entrypoints"], 0)
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0], 0)
        row = self.db.db.execute("SELECT credit,signal_class FROM retrieval_feedback").fetchone()
        self.assertEqual(float(row["credit"]), 0.0)
        self.assertTrue(row["signal_class"].startswith("user_explicit:user_no_memory:"))

    def test_relevance_requires_served_target_and_irrelevance_is_negative(self):
        self.add_memory("served")
        self.add_memory("unserved", subject="topic:other", value="different memory")
        request = self.seed_retrieval(selected=("served",), shadow=("served",))
        with self.assertRaises(PermissionError):
            self.apply(
                request,
                feedback_class="USER_RELEVANT",
                target_memory_id="unserved",
            )
        result = self.apply(
            request,
            feedback_class="USER_IRRELEVANT",
            target_memory_id="served",
        )
        self.assertTrue(result["applied"])
        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        key = self.organ._route_key(cue_hash, "served")
        self.assertLess(
            self.db.db.execute(
                "SELECT capital FROM retrieval_entrypoint_policy WHERE entry_key=?", (key,)
            ).fetchone()[0], 0.0,
        )

    def test_feedback_joins_outer_transaction_and_rolls_back_atomically(self):
        self.add_memory("target")
        request = self.seed_retrieval()
        with self.assertRaisesRegex(RuntimeError, "force outer rollback"):
            with self.db.tx():
                result = self.apply(
                    request,
                    feedback_class="USER_MISS_TARGET",
                    target_memory_id="target",
                )
                self.assertTrue(result["applied"])
                self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0], 1)
                raise RuntimeError("force outer rollback")
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0], 0)
        self.assertEqual(self.db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
