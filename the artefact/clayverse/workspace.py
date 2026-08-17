from __future__ import annotations
import json,time,uuid
from .store import UnifiedDB
class Workspace:
    """Bounded Hyperposition alternatives represented inside a GWT-like workspace episode."""
    def __init__(self,db:UnifiedDB): self.db=db
    def open(self,session_id,observation_turn_id,content,resource_refs):
        salience=min(1.0,0.15+0.03*len(resource_refs)+min(len(content),1200)/2400); alternatives=[{"id":"respond","kind":"reason"},{"id":"defer_effect","kind":"no_effect"}]; eid=str(uuid.uuid4())
        self.db.db.execute("INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",(eid,session_id,time.time(),observation_turn_id,salience,json.dumps(alternatives),None,"OPEN")); return {"episode_id":eid,"salience":salience,"alternatives":alternatives}
    def select(self,episode_id,selection): self.db.db.execute("UPDATE workspace_episodes SET selected=?,state='SELECTED' WHERE episode_id=?",(selection,episode_id))
