import pytest
from clayverse.store import UnifiedDB
from clayverse.identity import IdentityRouter
from clayverse.workspace import Workspace,WorkspaceSelectionError,WorkspaceStateError

def test_workspace_selection_is_bounded_and_single_use(tmp_path):
    db=UnifiedDB(tmp_path/'u.db')
    uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g')
    turn=db.append_turn(sid,uid,'user','hello')
    workspace=Workspace(db)
    ws=workspace.open(sid,turn,'hello',[])
    with pytest.raises(WorkspaceSelectionError): workspace.select(ws['episode_id'],'NOT_OFFERED')
    row=db.db.execute('select selected,state from workspace_episodes where episode_id=?',(ws['episode_id'],)).fetchone()
    assert row['selected'] is None and row['state']=='OPEN'
    assert workspace.select(ws['episode_id'],'respond')=='respond'
    with pytest.raises(WorkspaceStateError): workspace.select(ws['episode_id'],'defer_effect')
    row=db.db.execute('select selected,state from workspace_episodes where episode_id=?',(ws['episode_id'],)).fetchone()
    assert row['selected']=='respond' and row['state']=='SELECTED'
    db.close()
