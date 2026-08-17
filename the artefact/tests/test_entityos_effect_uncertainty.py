"""Regressions for post-start EntityOS timeout epistemic safety."""
import json
import os
import subprocess

import pytest

import clayverse.entityos_bridge as bridge_module
from clayverse.effects import EffectGate,EffectRequest
from clayverse.entityos_bridge import EntityOSBridge,EntityOSOutcomeUnknown
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g')
    return db,uid,sid


class TimeoutBridge:
    sha256='a'*64
    def run(self,argv):
        raise EntityOSOutcomeUnknown('EntityOS execution timed out; external outcome unknown')


def test_bridge_types_subprocess_timeout_as_unknown_after_execution_start(monkeypatch):
    monkeypatch.setattr(EntityOSBridge,'_open_verified',lambda self: os.open('/dev/null',os.O_RDONLY))
    def timeout(*args,**kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0],timeout=kwargs['timeout'])
    monkeypatch.setattr(bridge_module.subprocess,'run',timeout)
    bridge=EntityOSBridge('/unused','a'*64,timeout=0.01)
    with pytest.raises(EntityOSOutcomeUnknown,match='external outcome unknown'):
        bridge.run(['effect'])


def test_effect_gate_journals_timeout_as_unknown_and_does_not_recover_it(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    gate=EffectGate(db,entityos_bridge=TimeoutBridge())
    with pytest.raises(EntityOSOutcomeUnknown):
        gate.execute(EffectRequest(uid,sid,'entityos.exec','transport',['effect']))

    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone()
    receipt=json.loads(effect['outcome'])
    assert effect['status']=='UNKNOWN_AFTER_EXECUTION_TIMEOUT'
    assert receipt['certainty']=='unknown'
    assert receipt['reason']=='entityos_execution_timeout'
    assert receipt['error']=='EntityOSOutcomeUnknown'
    assert receipt['boundary']=='EntityOS'
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone()[0]==0.0
    assert db.db.execute('SELECT COUNT(*) FROM leases').fetchone()[0]==0

    assert gate.journal.recover_pending()==0
    assert db.db.execute('SELECT status FROM effects WHERE effect_id=?',(effect['effect_id'],)).fetchone()[0]=='UNKNOWN_AFTER_EXECUTION_TIMEOUT'
    db.close()
