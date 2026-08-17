import json,stat
from pathlib import Path
import pytest
from clayverse.effects import EffectRequest,EntityOSBridgeError,EntityOSProcessExecutor
from clayverse.store import Lease

def fake_entityos(tmp_path,mode='ok'):
    p=tmp_path/'EntityOS'
    p.write_text("#!/usr/bin/env python3\nimport json,sys\nreq=json.load(sys.stdin)\nmode="+repr(mode)+"\nif sys.argv[1] != 'clayverse-process-v1': sys.exit(64)\nif mode=='badjson': print('nope')\nelif mode=='wronggen': print(json.dumps({'schema':'ClayVerseEntityOSProcessOutcome/v1','resource':req['resource'],'generation':req['generation']+1,'ok':True}))\nelse: print(json.dumps({'schema':'ClayVerseEntityOSProcessOutcome/v1','resource':req['resource'],'generation':req['generation'],'ok':True,'argv':req['argv']}))\n")
    p.chmod(p.stat().st_mode|stat.S_IXUSR)
    return p

def test_entityos_stdio_contract_roundtrip(tmp_path):
    binary=fake_entityos(tmp_path)
    lease=Lease('repo:x','worker',7,9999999999.0,'nonce')
    req=EffectRequest('gabriel','session:gabriel','process.exec','repo:x',['/usr/bin/printf','ok'])
    out=EntityOSProcessExecutor(binary=str(binary),timeout=2).execute_process(req,lease)
    assert out['ok'] is True and out['generation']==7 and out['resource']=='repo:x'
    assert out['argv']==['/usr/bin/printf','ok']

def test_entityos_bridge_rejects_unbound_outcome(tmp_path):
    lease=Lease('repo:x','worker',7,9999999999.0,'nonce')
    req=EffectRequest('gabriel','session:gabriel','process.exec','repo:x',['/usr/bin/true'])
    with pytest.raises(EntityOSBridgeError,match='generation/resource mismatch'):
        EntityOSProcessExecutor(binary=str(fake_entityos(tmp_path,'wronggen')),timeout=2).execute_process(req,lease)
