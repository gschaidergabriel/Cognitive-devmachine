from __future__ import annotations
import json,time,uuid
from .store import UnifiedDB

class WorkspaceSelectionError(ValueError): pass
class WorkspaceStateError(RuntimeError): pass

class Workspace:
    """Bounded Hyperposition alternatives represented inside a GWT-like workspace episode."""
    def __init__(self,db:UnifiedDB): self.db=db
    def open(self,session_id,observation_turn_id,content,resource_refs):
        salience=min(1.0,0.15+0.03*len(resource_refs)+min(len(content),1200)/2400); alternatives=[{"id":"respond","kind":"reason"},{"id":"request_effect","kind":"effect_intent"},{"id":"defer_effect","kind":"no_effect"}]; eid=str(uuid.uuid4())
        self.db.db.execute("INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",(eid,session_id,time.time(),observation_turn_id,salience,json.dumps(alternatives),None,"OPEN")); return {"episode_id":eid,"salience":salience,"alternatives":alternatives}
    def select_in_tx(self,episode_id,selection):
        if not self.db.db.in_transaction: raise WorkspaceStateError('workspace selection requires active transaction')
        db=self.db.db
        row=db.execute("SELECT alternatives,state FROM workspace_episodes WHERE episode_id=?",(episode_id,)).fetchone()
        if row is None: raise KeyError(episode_id)
        if row['state']!='OPEN': raise WorkspaceStateError(f'workspace episode is {row["state"]}, not OPEN')
        alternatives=json.loads(row['alternatives']); allowed={item.get('id') for item in alternatives if isinstance(item,dict) and isinstance(item.get('id'),str)}
        if selection not in allowed: raise WorkspaceSelectionError(f'unoffered workspace selection: {selection!r}')
        cur=db.execute("UPDATE workspace_episodes SET selected=?,state='SELECTED' WHERE episode_id=? AND state='OPEN'",(selection,episode_id))
        if cur.rowcount!=1: raise WorkspaceStateError('workspace episode selection race')
        return selection
    def select(self,episode_id,selection):
        with self.db.tx(): return self.select_in_tx(episode_id,selection)
