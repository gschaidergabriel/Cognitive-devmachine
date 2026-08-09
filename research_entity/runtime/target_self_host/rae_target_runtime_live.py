#!/usr/bin/env python3
"""Live evidence head for the Research-Entity target runtime."""
from __future__ import annotations
import argparse, contextlib, io, json
import rae_target_runtime_current as current

V = 'RAE-TARGET-0.2.1+live-evidence-20260809T2226p0700'
_CURRENT_BOOT = current.boot
COMPOSITE = (
    'whole-frank-v2-corrected','frank',
    'research_entity/rooms/center_events/20260809T2226p0700_frank_v01_whole_sandbox_v2_corrected.json',
    'c41d233f7960f206c0a5969630071abbfa451806','CURRENT'
)

def boot(u,g):
    _CURRENT_BOOT(u,g)
    iid,domain,ref,commit,status=COMPOSITE; t=current.base.now()
    u.execute('INSERT OR REPLACE INTO research_imports VALUES(?,?,?,?,?,?,?,?,?)',
              (iid,domain,ref,commit,'CORRECTED_SANDBOX_COMPOSITE',status,ref,current.base.h(ref),t))
    u.execute("INSERT OR REPLACE INTO meta VALUES('live_evidence_head',?)",(commit,))
    u.commit();g.commit()

current.base.boot=boot

def open_pair(root,create=False):return current.base.open_pair(root,create)

def self_test(root):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): result=current.self_test(root)
    u,g=open_pair(root,False)
    try:
        row=u.execute("SELECT source_commit FROM research_imports WHERE import_id='whole-frank-v2-corrected'").fetchone()
        assert row and row[0]==COMPOSITE[3]
        result['checks'].append('latest_corrected_composite_imported')
        result['passed']=len(result['checks'])
        result['target_version']=V
        result['live_evidence_head']=COMPOSITE[3]
        print(json.dumps(result,indent=2));return result
    finally:u.close();g.close()

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
    x=sp.add_parser('init');x.add_argument('--root',required=True)
    x=sp.add_parser('self-test');x.add_argument('--root',required=True)
    a=p.parse_args()
    if a.cmd=='init':
        u,g=open_pair(a.root,True);print(json.dumps({'status':'INITIALIZED','target_version':V,'live_evidence_head':COMPOSITE[3]}));u.close();g.close()
    else:self_test(a.root)
if __name__=='__main__':main()
