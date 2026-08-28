import os
import sqlite3
import tempfile
import unittest

from xeno_s1_readonly_connection_v1 import open_ordinary_s1_read_only
from xeno_s1_sqlite_cas_v1 import open_or_initialize, read_snapshot


class OrdinaryS1ReadOnlyConnectionTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(prefix="xeno-s1-ro-", suffix=".sqlite3")
        os.close(fd)
        self.writer = sqlite3.connect(self.path)
        self.genesis = {
            "nodes": [{"node_id": "n1", "capabilities": ["REASON"], "healthy": True, "load_milli": 0}],
            "tasks": [],
            "workspace": {"branches": []},
            "gwt": {"broadcast": [], "uptake": [], "reentry": []},
        }
        self.initial = open_or_initialize(self.writer, genesis_state=self.genesis)

    def tearDown(self):
        self.writer.close()
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass

    def test_ordinary_connection_observes_exact_snapshot_but_raw_update_is_rejected(self):
        ro = open_ordinary_s1_read_only(self.path)
        try:
            observed = read_snapshot(ro)
            self.assertEqual(self.initial.epoch, observed.epoch)
            self.assertEqual(self.initial.digest, observed.digest)
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute("UPDATE hcu_s1_state SET epoch=999 WHERE slot=1")
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute("CREATE TABLE ordinary_escape(x INTEGER)")
        finally:
            ro.close()
        after = read_snapshot(self.writer)
        self.assertEqual(self.initial.epoch, after.epoch)
        self.assertEqual(self.initial.digest, after.digest)

    def test_missing_store_fails_closed_without_creating_file(self):
        missing = self.path + ".missing"
        self.assertFalse(os.path.exists(missing))
        with self.assertRaisesRegex(Exception, "S1_STORE_FILE_REQUIRED"):
            open_ordinary_s1_read_only(missing)
        self.assertFalse(os.path.exists(missing))


if __name__ == "__main__":
    unittest.main()
