#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import sqlite3
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import miniunifieddb_cognition_store_v1 as store

class CognitionBindingIntegrityTests(unittest.TestCase):
    @staticmethod
    def digest(label: str) -> str:
        return hashlib.sha256(label.encode()).hexdigest()
    def make_bound(self):
        db=sqlite3.connect(':memory:')
        db.execute('CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)')
        db.execute('INSERT INTO entity_state VALUES(1,3)')
        store.install_schema(db)
        vals={}
        for field,kind in store.BOOT_FIELD_KINDS.items():
            dig=self.digest(field); vals[field]=dig
            store.register_object(db,object_kind=kind,object_version='v1',object_digest=dig,
                                  digest_basis='EXTERNAL_BYTES',payload={'identity':field},
                                  provenance_refs=['test:'+field])
            store.admit_object(db,object_kind=kind,object_version='v1',object_digest=dig,
                               entity_generation=3,
                               admission_receipt_digest=self.digest('receipt:'+field))
        boot=store.admit_boot_binding(db,entity_generation=3,provenance_refs=['test:boot'],**vals)['binding_digest']
        store.bind_turn(db,entity_generation=3,causal_turn_id='turn',boot_binding_digest=boot,
                        task_text='task',workspace_digest=self.digest('workspace'),
                        selected_workspace_slots=['slot'],contradiction_state='NONE',
                        provenance_refs=['test:turn'],required_zero_mode='ACTIVE')
        return db,boot
    def test_turn_row_tamper_fails_closed(self):
        db,_=self.make_bound()
        db.execute("UPDATE mini_cognition_turn_bindings SET workspace_digest=? WHERE causal_turn_id='turn'",
                   (self.digest('forged-workspace'),))
        with self.assertRaisesRegex(store.CognitionStoreError,'TURN_BINDING_DIGEST_MISMATCH'):
            store.resolve_prepare_binding(db,entity_generation=3,causal_turn_id='turn',task_text='task')
    def test_boot_row_tamper_fails_closed(self):
        db,boot=self.make_bound()
        db.execute('UPDATE mini_cognition_boot_bindings SET zero_identity_digest=? WHERE binding_digest=?',
                   (self.digest('forged-zero'),boot))
        with self.assertRaisesRegex(store.CognitionStoreError,'BOOT_BINDING_DIGEST_MISMATCH'):
            store.resolve_prepare_binding(db,entity_generation=3,causal_turn_id='turn',task_text='task')

if __name__=='__main__': unittest.main()
