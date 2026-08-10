#!/usr/bin/env python3
import sqlite3,unittest
from pathlib import Path
from semantic_entity_resolver_v12 import SemanticEntityResolverV12
HERE=Path(__file__).resolve().parent
SQL=(HERE/'RAE_UNIFIEDDB_V12_ENTITY_RESOLUTION.sql').read_text(encoding='utf-8')
class EntityResolverV12Tests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:'); self.c.executescript(SQL)
  rows=[('a1','amber relay','component_a','EXPLICIT',1,7,'{}','CURRENT','t'),('a2','amber relay controller','component_a','EXPLICIT',.98,7,'{}','CURRENT','t'),('b1','amber bridge','component_b','EXPLICIT',1,7,'{}','CURRENT','t')]
  self.c.executemany('insert into semantic_entity_aliases values(?,?,?,?,?,?,?,?,?)',rows)
  self.c.executemany('insert into semantic_entity_alias_fts values(?,?,?)',[(r[0],r[1],r[2]) for r in rows]); self.c.commit(); self.r=SemanticEntityResolverV12(self.c)
 def tearDown(self): self.c.close()
 def test_explicit_alias_resolves(self): self.assertEqual(self.r.resolve('service required by amber relay',source_epoch=7).logical_id,'component_a')
 def test_stale_epoch_fails_closed(self): self.assertIsNone(self.r.resolve('amber relay',source_epoch=8).logical_id)
 def test_ambiguous_short_form_fails_closed(self): self.assertIsNone(self.r.resolve('amber',source_epoch=7).logical_id)
 def test_model_proposed_alias_not_auto_anchor(self):
  self.c.execute("insert into semantic_entity_aliases values('m','mystery unit','component_m','MODEL_PROPOSED',1,7,'{}','CURRENT','t')"); self.c.execute("insert into semantic_entity_alias_fts values('m','mystery unit','component_m')"); self.c.commit(); self.assertIsNone(self.r.resolve('mystery unit',source_epoch=7).logical_id)
if __name__=='__main__':unittest.main(verbosity=2)
