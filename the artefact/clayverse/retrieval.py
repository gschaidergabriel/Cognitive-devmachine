from __future__ import annotations
import json
from .store import UnifiedDB
class WorldAssembler:
    def __init__(self,db:UnifiedDB): self.db=db
    def assemble(self,session_id,resource_refs):
        session=self.db.db.execute("SELECT user_id FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if not session: raise KeyError(session_id)
        user_id=session['user_id']
        own=[dict(r) for r in self.db.recent_turns(session_id,20)]; other=[]
        if resource_refs:
            wanted=set(resource_refs)
            for r in self.db.db.execute("SELECT * FROM turns WHERE session_id<>? ORDER BY ts DESC LIMIT 200",(session_id,)).fetchall():
                if wanted.intersection(json.loads(r['resource_refs'])):
                    item=dict(r)
                    if int(r['compression_generation'])>0:
                        archive=self.db.db.execute("SELECT value FROM durable_memory WHERE kind='source_archive' AND source_turn_id=? AND user_id=? LIMIT 1",(r['turn_id'],r['user_id'])).fetchone()
                        if archive:
                            item['content']=archive['value']; item['retrieval_fidelity']='source_archive'
                    other.append(item)
                    if len(other)>=10: break
        memories=[dict(r) for r in self.db.db.execute("SELECT * FROM durable_memory WHERE kind<>'source_archive' AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50",(user_id,))]
        return {"own_recent":own,"cross_session_collision":other,"durable_memory":memories}
