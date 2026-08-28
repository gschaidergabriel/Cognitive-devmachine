from __future__ import annotations
import hashlib,json
from .store import UnifiedDB
class ClayGraphProjection:
    """Rebuildable semantic projection; compression/provenance control records are not semantic truth nodes."""
    def __init__(self,db:UnifiedDB): self.db=db
    @staticmethod
    def _id(*parts): return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]
    def rebuild_in_tx(self):
        if not self.db.db.in_transaction: raise RuntimeError('ClayGraph rebuild requires active transaction')
        db=self.db.db
        db.execute("DELETE FROM graph_edges"); db.execute("DELETE FROM graph_nodes")
        for m in db.execute("SELECT * FROM durable_memory WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance')"):
            nid=self._id("memory",m['memory_id']); db.execute("INSERT INTO graph_nodes VALUES(?,?,?,?,?)",(nid,"memory",m['value'][:120],"durable_memory",m['memory_id']))
            uid=self._id("user",m['user_id'] or "shared"); db.execute("INSERT OR IGNORE INTO graph_nodes VALUES(?,?,?,?,?)",(uid,"user",m['user_id'] or "shared","users",m['user_id'] or "shared")); db.execute("INSERT INTO graph_edges VALUES(?,?,?,?,?)",(self._id(uid,nid,"owns_memory"),uid,nid,"owns_memory",json.dumps({"source":m['memory_id']})))
        for c in db.execute("SELECT * FROM causal_episodes WHERE reentered=1"):
            nid=self._id("causal",c['causal_id']); db.execute("INSERT INTO graph_nodes VALUES(?,?,?,?,?)",(nid,"causal_episode",c['causal_id'],"causal_episodes",c['causal_id']))
        return self.counts()
    def rebuild(self):
        with self.db.tx(): return self.rebuild_in_tx()
    def counts(self): return {"nodes":self.db.db.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0],"edges":self.db.db.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]}
