from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB

class FakeBridge:
    sha256='b'*64
    def __init__(self,ok): self.ok=ok
    def run(self,argv): return {'ok':self.ok,'exit':0 if self.ok else 1,'stdout':'','stderr':''}

class EffectInference:
    def reason(self,world,observation):
        return {
            'text':'effect observed',
            'selection':'request_effect',
            'effect':{'capability':'entityos.exec','target':'transport','argv':['status']},
        }

def test_failed_effect_reenters_without_positive_credit(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    try:
        result=ClayVerseEngine(db,{'g':'gabriel'},inference=EffectInference(),entityos_bridge=FakeBridge(False)).ingest('g','run expected failing effect')
        assert result['outcome']['ok'] is False
        row=db.db.execute('SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?',(result['causal_id'],)).fetchone()
        assert row['reentered']==1 and row['credit']==0.0 and row['outcome_hash']
        assert db.db.execute('SELECT COUNT(*) FROM causal_episodes WHERE effect_id=?',(result['effect_id'],)).fetchone()[0]==1
    finally: db.close()

def test_successful_effect_gets_positive_credit(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    try:
        result=ClayVerseEngine(db,{'g':'gabriel'},inference=EffectInference(),entityos_bridge=FakeBridge(True)).ingest('g','run expected successful effect')
        assert result['outcome']['ok'] is True
        credit=db.db.execute('SELECT credit FROM causal_episodes WHERE causal_id=?',(result['causal_id'],)).fetchone()[0]
        assert credit==1.0
        assert db.db.execute('SELECT COUNT(*) FROM causal_episodes WHERE effect_id=?',(result['effect_id'],)).fetchone()[0]==1
    finally: db.close()
