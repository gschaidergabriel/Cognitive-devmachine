from __future__ import annotations
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from .entity_copy_birth import EntityBirthRegistry, StateRekeyRequired, MANIFEST_REL, BIRTH_EVENTS_REL


class EntityCopyBirthTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.registry = EntityBirthRegistry(self.root / "HOST_REGISTRY.json")

    def tearDown(self):
        self.td.cleanup()

    @staticmethod
    def rekey(root, new_id, parent_id, namespace):
        marker = root / "state" / "ENTITY_STATE_NAMESPACE.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({
            "entity_id": new_id,
            "parent_entity_id": parent_id,
            "state_namespace": namespace,
        }, sort_keys=True), encoding="utf-8")

    def test_fresh_birth_restart_provider_change_semantics(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        self.assertTrue(born.new_birth)
        self.assertEqual(born.pulse_index, 1)
        again = self.registry.preflight(a)
        self.assertFalse(again.new_birth)
        self.assertEqual(again.entity_id, born.entity_id)
        self.assertEqual(again.classification, "SAME_ENTITY_RESTART")
        self.assertEqual(again.pulse_index, 2)

    def test_copy_births_distinct_child_and_parent_lineage(self):
        a = self.root / "Alpha"
        parent = self.registry.preflight(a, entity_name="Alpha")
        b = self.root / "Beta"
        shutil.copytree(a, b)
        child = self.registry.preflight(b, entity_name="Beta", state_rekey=self.rekey)
        self.assertTrue(child.new_birth)
        self.assertNotEqual(child.entity_id, parent.entity_id)
        self.assertEqual(child.parent_entity_id, parent.entity_id)
        self.assertEqual(child.pulse_index, 1)
        self.assertNotEqual(child.state_namespace, parent.state_namespace)

    def test_copy_fails_closed_without_state_rekey(self):
        a = self.root / "Alpha"
        parent = self.registry.preflight(a, entity_name="Alpha")
        b = self.root / "Beta"
        shutil.copytree(a, b)
        with self.assertRaises(StateRekeyRequired):
            self.registry.preflight(b, entity_name="Beta")
        self.assertFalse(any(
            row.get("parent_entity_id") == parent.entity_id
            for row in self.registry._data["entities"].values()
            if row["entity_id"] != parent.entity_id
        ))

    def test_same_name_copy_still_births_unique_entity(self):
        a = self.root / "A" / "Alpha"
        parent = self.registry.preflight(a, entity_name="Alpha")
        b = self.root / "B" / "Alpha"
        b.parent.mkdir(parents=True)
        shutil.copytree(a, b)
        child = self.registry.preflight(b, state_rekey=self.rekey)
        self.assertNotEqual(child.entity_id, parent.entity_id)
        self.assertEqual(child.entity_name, "Alpha")

    def test_two_concurrent_style_copies_are_distinct(self):
        a = self.root / "Alpha"
        parent = self.registry.preflight(a, entity_name="Alpha")
        ids = set()
        for name in ("Child1", "Child2"):
            p = self.root / name
            shutil.copytree(a, p)
            child = self.registry.preflight(p, entity_name=name, state_rekey=self.rekey)
            self.assertEqual(child.parent_entity_id, parent.entity_id)
            ids.add(child.entity_id)
        self.assertEqual(len(ids), 2)

    def test_move_preserves_entity_if_old_location_gone(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        moved = self.root / "MovedAlpha"
        shutil.move(a, moved)
        out = self.registry.preflight(moved)
        self.assertEqual(out.classification, "SAME_ENTITY_MOVED")
        self.assertEqual(out.entity_id, born.entity_id)

    def test_rename_after_birth_is_alias_change_not_fork(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        old = born.entity_id
        self.assertEqual(self.registry.rename_after_birth(old, "Zeta"), old)
        again = self.registry.preflight(a)
        self.assertEqual(again.entity_id, old)
        self.assertEqual(again.entity_name, "Zeta")

    def test_explicit_replica_attach_keeps_identity_and_emits_no_birth_in_replica(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        replica = self.root / "Replica"
        replica.mkdir()
        out = self.registry.preflight(replica, replica_ticket={
            "authorization": "REPLICA_ATTACH", "entity_id": born.entity_id
        })
        self.assertEqual(out.classification, "REPLICA_ATTACHED")
        self.assertEqual(out.entity_id, born.entity_id)
        self.assertFalse(out.new_birth)
        self.assertFalse((replica / BIRTH_EVENTS_REL).exists())

    def test_copied_manifest_without_registry_binding_cannot_continue_identity(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        orphan = self.root / "Orphan"
        shutil.copytree(a, orphan)
        fresh_registry = EntityBirthRegistry(self.root / "OTHER_HOST_REGISTRY.json")
        out = fresh_registry.preflight(orphan, state_rekey=self.rekey)
        self.assertNotEqual(out.entity_id, born.entity_id)
        self.assertEqual(out.parent_entity_id, born.entity_id)

    def test_retired_id_not_reused(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        self.registry.retire(born.entity_id)
        shutil.rmtree(a)
        b = self.root / "Alpha2"
        born2 = self.registry.preflight(b, entity_name="Alpha")
        self.assertNotEqual(born.entity_id, born2.entity_id)
        self.assertIn(born.entity_id, self.registry.retired_ids)

    def test_birth_event_precedes_normal_use_surface(self):
        a = self.root / "Alpha"
        born = self.registry.preflight(a, entity_name="Alpha")
        events = [json.loads(x) for x in (a / BIRTH_EVENTS_REL).read_text().splitlines()]
        self.assertEqual(events[0]["event"], "ENTITY_BIRTH")
        self.assertEqual(events[0]["pulse_index"], 1)
        self.assertEqual(events[0]["entity_id"], born.entity_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
