from __future__ import annotations
import json,os,signal,sys,time
from .store import UnifiedDB
from .identity import IdentityRouter
from .graph import ClayGraphProjection
from .integrity import seal,verify_latest
def main():
    state_root=os.environ.get('CLAYVERSE_STATE_ROOT','/var/lib/clayverse'); os.makedirs(state_root,exist_ok=True); db=UnifiedDB(os.path.join(state_root,'unified.db')); verified=verify_latest(db); IdentityRouter(db,{}); ClayGraphProjection(db).rebuild(); cid,digest=seal(db,'boot'); print(json.dumps({'service':'clayverse','status':'ready','state_root':state_root,'checkpoint':cid,'state_hash':digest,'previous_integrity_seal':verified['checkpoint_id'] if verified else None,'users':['gabriel','andreas']}),flush=True)
    if '--once' in sys.argv: db.close(); return 0
    running=True
    def stop(*_):
        nonlocal running; running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    while running: time.sleep(1)
    seal(db,'shutdown'); db.close(); return 0
if __name__=='__main__': raise SystemExit(main())
