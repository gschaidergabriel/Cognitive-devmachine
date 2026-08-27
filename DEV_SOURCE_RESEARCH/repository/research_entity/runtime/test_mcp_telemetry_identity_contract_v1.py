import sqlite3
import tempfile
import unittest
from pathlib import Path

from research_entity.runtime.mcp_telemetry_identity_contract_v1 import inspect_connection, inspect_path


CURRENT_MCP_EVENTS_SCHEMA='''
CREATE TABLE events(
  id INTEGER PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,
  event_ts REAL NOT NULL,
  ingest_ts REAL NOT NULL,
  module TEXT NOT NULL,
  category TEXT NOT NULL,
  event_type TEXT,
  severity TEXT NOT NULL,
  retention_class TEXT NOT NULL,
  retention_rank INTEGER NOT NULL,
  message TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  correlation_id TEXT, episode_id TEXT, session_id TEXT, conversation_id TEXT,
  request_id TEXT, build_id TEXT, model_id TEXT, model_hash TEXT, mmproj_hash TEXT,
  provenance TEXT, state_key TEXT, entity_id TEXT,
  prev_state_hash TEXT, next_state_hash TEXT, parent_event_id TEXT,
  tags_json TEXT NOT NULL DEFAULT '[]', latency_ms REAL, rss_bytes INTEGER,
  gpu_mem_bytes INTEGER, schema_version TEXT NOT NULL
);
CREATE INDEX ix_event_time ON events(event_ts);
CREATE INDEX ix_state_time ON events(state_key,entity_id,event_ts);
'''


class MCPTelemetryIdentityContractV1Test(unittest.TestCase):
    def test_current_pr174_shape_passes_base_but_fails_temporal_entity_v2(self):
        con=sqlite3.connect(':memory:')
        con.executescript(CURRENT_MCP_EVENTS_SCHEMA)
        r=inspect_connection(con)
        self.assertTrue(r['base_contract_pass'])
        self.assertFalse(r['temporal_entity_v2_pass'])
        self.assertEqual(r['status'],'IDENTITY_TIME_FIELDS_NOT_FIRST_CLASS')
        self.assertIn('entity_version',r['missing_temporal_entity_v2'])
        self.assertIn('pulse_seq',r['missing_temporal_entity_v2'])
        self.assertTrue(r['migration_required'])

    def test_v2_shape_is_detected_when_columns_and_indexes_exist(self):
        con=sqlite3.connect(':memory:')
        con.executescript(CURRENT_MCP_EVENTS_SCHEMA)
        for col,typ in [
            ('entity_version','TEXT'),('artifact_digest','TEXT'),('state_lineage_hash','TEXT'),
            ('lease_epoch','INTEGER'),('pulse_seq','INTEGER'),('boot_id','TEXT'),
            ('invocation_id','TEXT'),('gap_class','TEXT')]:
            con.execute(f'ALTER TABLE events ADD COLUMN {col} {typ}')
        con.executescript('''
          CREATE INDEX ix_entity_version_time ON events(entity_id,entity_version,event_ts);
          CREATE INDEX ix_artifact_time ON events(artifact_digest,event_ts);
          CREATE INDEX ix_pulse_entity_seq ON events(entity_id,pulse_seq);
          CREATE INDEX ix_boot_gap_time ON events(boot_id,gap_class,event_ts);
        ''')
        r=inspect_connection(con)
        self.assertTrue(r['temporal_entity_v2_pass'])
        self.assertFalse(r['migration_required'])
        self.assertEqual(r['status'],'TEMPORAL_ENTITY_V2_READY')

    def test_path_probe_is_read_only_and_handles_missing_db(self):
        with tempfile.TemporaryDirectory() as d:
            missing=inspect_path(str(Path(d)/'none.sqlite3'))
            self.assertEqual(missing['status'],'DB_NOT_FOUND')


if __name__=='__main__':
    unittest.main()
