from __future__ import annotations
import json,os,signal,sys,time
from .store import UnifiedDB
from .identity import IdentityRouter
from .graph import ClayGraphProjection
def main():
    state_root=os.environ.get('CLAYVERSE_STATE_ROOT','/var/lib/clayverse'); os.makedirs(state_root,exist_ok=True); db=UnifiedDB(os.path.join(state_root,'unified.db')); IdentityRouter(db,{}); ClayGraphProjection(db).rebuild(); cid,digest=db.checkpoint('boot'); print(json.dumps({'service':'clayverse','status':'ready','state_root':state_root,'checkpoint':cid,'state_hash':digest,'users':['gabriel','andreas']}),flush=True)
    if '--once' in sys.argv: return 0
    running=True
    def stop(*_):
        nonlocal running; running=False
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    while running: time.sleep(1)
    db.checkpoint('shutdown'); db.close(); return 0
if __name__=='__main__': raise SystemExit(main())
