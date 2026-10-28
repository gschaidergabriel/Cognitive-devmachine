#!/usr/bin/env python3
"""stdlib-only regression checks: python3 -m unittest discover -s grid_exchange -p 'test_*.py'"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from grid_exchange import connect, make, apply

class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "grid.sqlite")
    def tearDown(self):
        self.db.close()
        self.temp.cleanup()
    def packet(self, rev, operation="merge", data=None, parent=None):
        return make("gabriel","grid10","node-1",rev,operation,data or {"x":1},parent,
                    "2026-10-29T00:00:00Z")
    def get(self):
        return self.db.execute("SELECT revision,event_id,payload FROM state").fetchone()
    def test_apply_merge_idempotence_and_cas(self):
        first=self.packet(1,data={"x":1})
        self.assertEqual(apply(self.db,first),"applied")
        self.assertEqual(apply(self.db,first),"duplicate")
        second=self.packet(2,data={"y":2},parent=first["event_id"])
        self.assertEqual(apply(self.db,second),"applied")
        self.assertEqual(json.loads(self.get()[2]),{"x":1,"y":2})
        with self.assertRaisesRegex(ValueError,"CAS"):
            apply(self.db,self.packet(3,data={"z":3},parent="wrong"))
    def test_owner_host_tamper_rejected(self):
        packet=self.packet(1)
        packet["machine_id"]="andreas-maco"
        with self.assertRaisesRegex(ValueError,"owner/host"):
            apply(self.db,packet)
    def test_payload_tamper_rejected(self):
        packet=self.packet(1)
        packet["payload"]["x"]=2
        with self.assertRaisesRegex(ValueError,"hash"):
            apply(self.db,packet)
    def test_delete_proposal_does_not_delete(self):
        first=self.packet(1,operation="replace",data={"keep":True})
        apply(self.db,first)
        second=self.packet(2,operation="delete_proposal",data={"reason":"candidate"},parent=first["event_id"])
        apply(self.db,second)
        self.assertEqual(json.loads(self.get()[2]),{"keep":True})
    def test_no_owner_mix(self):
        p1=self.packet(1)
        p2=make("andreas","grid10","node-1",1,"merge",{"a":2},None,"2026-10-29T00:00:00Z")
        self.assertEqual(apply(self.db,p1),"applied")
        self.assertEqual(apply(self.db,p2),"applied")
        self.assertEqual(self.db.execute("SELECT count(*) FROM state").fetchone()[0],2)

if __name__=="__main__":unittest.main()
