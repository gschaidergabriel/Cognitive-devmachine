from __future__ import annotations

import hashlib
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import miniunifieddb_cognition_store_v1 as store


class CurrentGenerationAdmissionFenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute(
            "CREATE TABLE entity_state(id INTEGER PRIMARY KEY CHECK(id=1), generation INTEGER NOT NULL)"
        )
        self.db.execute("INSERT INTO entity_state(id,generation) VALUES(1,3)")
        self.db.commit()
        store.install_schema(self.db)
        self.digests: dict[str, str] = {}
        for kind in store.BOOT_FIELD_KINDS.values():
            payload = {"kind": kind, "fixture": "generation-fence"}
            digest = store.sha256_obj(payload)
            store.register_object(
                self.db,
                object_kind=kind,
                object_version="v1",
                object_digest=digest,
                digest_basis="CANONICAL_JSON",
                payload=payload,
                provenance_refs=["test:fixture"],
            )
            self.digests[kind] = digest
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    @staticmethod
    def _receipt(kind: str, generation: int) -> str:
        return hashlib.sha256(f"receipt:{kind}:{generation}".encode()).hexdigest()

    def _admit(self, kind: str, generation: int) -> None:
        store.admit_object(
            self.db,
            object_kind=kind,
            object_version="v1",
            object_digest=self.digests[kind],
            entity_generation=generation,
            admission_receipt_digest=self._receipt(kind, generation),
        )

    def _boot_kwargs(self, generation: int) -> dict[str, object]:
        return {
            "entity_generation": generation,
            **{
                field: self.digests[kind]
                for field, kind in store.BOOT_FIELD_KINDS.items()
            },
            "provenance_refs": ["test:boot"],
        }

    def test_current_generation_admissions_allow_boot(self) -> None:
        for kind in store.BOOT_FIELD_KINDS.values():
            self._admit(kind, 3)
        result = store.admit_boot_binding(self.db, **self._boot_kwargs(3))
        self.assertTrue(result["ok"])

    def test_mixed_generation_boot_ancestry_poison_fails_closed(self) -> None:
        """Unusual intervention: one stale object among otherwise current boot ancestry."""
        kinds = list(store.BOOT_FIELD_KINDS.values())
        stale_kind = "ZERO_IDENTITY"
        for kind in kinds:
            self._admit(kind, 3)
        self.db.commit()

        self.db.execute("UPDATE entity_state SET generation=4 WHERE id=1")
        self.db.commit()
        for kind in kinds:
            if kind != stale_kind:
                self._admit(kind, 4)
        self.db.commit()

        with self.assertRaisesRegex(
            store.CognitionStoreError,
            r"COGNITION_OBJECT_NOT_ADMITTED:ZERO_IDENTITY",
        ):
            store.admit_boot_binding(self.db, **self._boot_kwargs(4))

        row = self.db.execute(
            "SELECT binding_digest FROM mini_cognition_boot_bindings WHERE entity_generation=4"
        ).fetchone()
        self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
