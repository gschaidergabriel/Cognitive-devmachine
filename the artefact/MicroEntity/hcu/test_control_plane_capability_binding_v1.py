import sqlite3
import unittest

from control_plane_capability_binding_v1 import (
    CapabilityBindingError,
    admit_entry_with_control_plane,
    snapshot_capability_authority,
)
from xeno_entry_fabric_v1 import EntryFabricError


class CanonicalDBFixture:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            "CREATE TABLE sessions (session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, generation INTEGER NOT NULL)"
        )
        self.db.executemany(
            "INSERT INTO sessions(session_id,user_id,generation) VALUES(?,?,?)",
            (("session:a", "user:a", 7), ("session:b", "user:b", 7)),
        )
        self.live = {"session:a": 7, "session:b": 7}

    def assert_live_generation(self, session_id, generation):
        if self.live.get(session_id) != generation:
            raise RuntimeError("stale generation")


class EffectGateFixture:
    def __init__(self, db, capabilities=("state.noop",)):
        self.db = db
        self._capabilities = tuple(capabilities)

    def available_capabilities(self):
        return self._capabilities


def base_entry(binding, *, capabilities=("memory.read", "hcu.route")):
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:test:1",
        "causal_id": "causal:test:1",
        "entity_generation": 7,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:a",
        "modality": "TEXT",
        "observed_time": "2026-08-24T01:45:00+07:00",
        "received_time": "2026-08-24T01:45:01+07:00",
        "provenance_ref": "canonical:source:test:1",
        "provenance_sha256": "a" * 64,
        "capabilities": list(capabilities),
        "capability_binding_sha256": binding,
        "parent_id": None,
        "stream_id": "stream:test",
        "budget": {"max_model_calls": 1, "max_tokens": 512, "max_wall_ms": 1000},
        "payload_ref": "canonical:payload:test:1",
        "payload_sha256": "c" * 64,
    }


ADMITTED_BUDGET = {"max_model_calls": 2, "max_tokens": 1024, "max_wall_ms": 2500}


def admit_with_fixture(entry, db, gate):
    return admit_entry_with_control_plane(
        entry,
        canonical_db=db,
        effect_gate=gate,
        user_id="user:a",
        session_id="session:a",
        trusted_source_kind="HUMAN_PROMPT",
        trusted_source_id="user:a",
        admitted_budget=ADMITTED_BUDGET,
    )


class ControlPlaneCapabilityBindingTests(unittest.TestCase):
    def setUp(self):
        self.db = CanonicalDBFixture()
        self.gate = EffectGateFixture(self.db)

    def test_cross_session_same_rights_same_generation_do_not_alias(self):
        a = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        b = snapshot_capability_authority(
            self.db, self.gate, user_id="user:b", session_id="session:b"
        )
        self.assertEqual(a.entity_generation, b.entity_generation)
        self.assertEqual(a.admitted_capabilities, b.admitted_capabilities)
        self.assertNotEqual(a.binding_sha256, b.binding_sha256)

    def test_valid_entry_uses_canonical_control_plane_binding(self):
        view = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        packet = admit_with_fixture(base_entry(view.binding_sha256), self.db, self.gate)
        self.assertEqual(packet.capability_binding_sha256, view.binding_sha256)
        self.assertEqual(packet.capabilities, ("hcu.route", "memory.read"))

    def test_other_session_binding_is_rejected(self):
        b = snapshot_capability_authority(
            self.db, self.gate, user_id="user:b", session_id="session:b"
        )
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_BINDING_MISMATCH"):
            admit_with_fixture(base_entry(b.binding_sha256), self.db, self.gate)

    def test_trusted_ingress_source_kind_cannot_be_relabelled(self):
        view = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        entry = base_entry(view.binding_sha256)
        entry["source_kind"] = "EXTERNAL_EVENT"
        with self.assertRaisesRegex(CapabilityBindingError, "TRUSTED_SOURCE_KIND_MISMATCH"):
            admit_with_fixture(entry, self.db, self.gate)

    def test_trusted_ingress_source_id_cannot_be_relabelled(self):
        view = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        entry = base_entry(view.binding_sha256)
        entry["source_id"] = "user:b"
        with self.assertRaisesRegex(CapabilityBindingError, "TRUSTED_SOURCE_ID_MISMATCH"):
            admit_with_fixture(entry, self.db, self.gate)

    def test_entry_cannot_self_grant_effect_capability(self):
        view = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        entry = base_entry(
            view.binding_sha256,
            capabilities=("memory.read", "hcu.route", "entityos.exec"),
        )
        with self.assertRaisesRegex(EntryFabricError, "CAPABILITY_NOT_ADMITTED:entityos.exec"):
            admit_with_fixture(entry, self.db, self.gate)

    def test_effect_gate_change_rebinds_context_but_never_grants_entry_effect_right(self):
        before = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        enabled_gate = EffectGateFixture(self.db, ("state.noop", "entityos.exec"))
        after = snapshot_capability_authority(
            self.db, enabled_gate, user_id="user:a", session_id="session:a"
        )
        self.assertNotEqual(before.binding_sha256, after.binding_sha256)
        self.assertEqual(before.admitted_capabilities, after.admitted_capabilities)
        self.assertNotIn("entityos.exec", after.admitted_capabilities)
        self.assertIn("entityos.exec", after.effect_capabilities)

    def test_effect_gate_must_share_canonical_db(self):
        other_db = CanonicalDBFixture()
        with self.assertRaisesRegex(CapabilityBindingError, "EFFECT_GATE_CANONICAL_DB_MISMATCH"):
            snapshot_capability_authority(
                self.db,
                EffectGateFixture(other_db),
                user_id="user:a",
                session_id="session:a",
            )

    def test_generic_process_exec_exposure_fails_closed(self):
        bad_gate = EffectGateFixture(self.db, ("state.noop", "process.exec"))
        with self.assertRaisesRegex(CapabilityBindingError, "FORBIDDEN_EFFECT_CAPABILITY_EXPOSED:process.exec"):
            snapshot_capability_authority(
                self.db, bad_gate, user_id="user:a", session_id="session:a"
            )

    def test_generation_change_rebinds_capability_view(self):
        before = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        self.db.db.execute("UPDATE sessions SET generation=8 WHERE session_id='session:a'")
        self.db.live["session:a"] = 8
        after = snapshot_capability_authority(
            self.db, self.gate, user_id="user:a", session_id="session:a"
        )
        self.assertNotEqual(before.binding_sha256, after.binding_sha256)
        self.assertEqual(after.entity_generation, 8)


if __name__ == "__main__":
    unittest.main()
