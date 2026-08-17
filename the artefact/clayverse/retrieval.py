from __future__ import annotations
import json
from .store import UnifiedDB
class WorldAssembler:
    def __init__(self,db:UnifiedDB): self.db=db
    def assemble(self,session_id,resource_refs):
        own=[dict(r) for r in self.db.recent_turns(session_id,20)]; other=[]
        if resource_refs:
            wanted=set(resource_refs)
            for r in self.db.db.execute("SELECT * FROM turns WHERE session_id<>? ORDER BY ts DESC LIMIT 200",(session_id,)).fetchall():
                if wanted.intersection(json.loads(r['resource_refs'])):
                    other.append(dict(r))
                    if len(other)>=10: break
        memories=[dict(r) for r in self.db.db.execute("SELECT * FROM durable_memory ORDER BY ts DESC LIMIT 50")]
        return {"own_recent":own,"cross_session_collision":other,"durable_memory":memories}
