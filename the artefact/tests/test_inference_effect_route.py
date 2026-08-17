from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB

class NoopIntentInference:
    def reason(self,world,observation):
        return {"text":"recorded","selection":"request_effect","effect":{"capability":"state.noop","target":"deterministic inference route regression","argv":None}}

class EntityOSIntentInference:
    def __init__(self): self.world=None
    def reason(self,world,observation):
        self.world=world
        return {"text":"attempting requested action","selection":"request_effect","effect":{"capability":"entityos.exec","target":"unavailable EntityOS regression","argv":["status"]}}

def test_inference_intent_reaches_effect_gate_without_direct_process(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    try:
        engine=ClayVerseEngine(db,{'g':'gabriel'},inference=NoopIntentInference(),allow_process=False); result=engine.ingest('g','record a bounded noop')
        assert result['decision']['selection']=='request_effect' and result['effect_id'] and result['outcome']['ok'] is True and result['outcome']['target']=='deterministic inference route regression'
        row=db.db.execute('SELECT capability,status FROM effects WHERE effect_id=?',(result['effect_id'],)).fetchone(); assert row['capability']=='state.noop' and row['status']=='VERIFIED'
        ws=db.db.execute('SELECT selected,state FROM workspace_episodes WHERE episode_id=?',(result['workspace']['episode_id'],)).fetchone(); assert ws['selected']=='request_effect' and ws['state']=='SELECTED'
        causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE causal_id=?',(result['causal_id'],)).fetchone(); assert causal['credit']==1.0 and causal['reentered']==1
    finally: db.close()

def test_unavailable_entityos_is_denied_without_false_causal_reentry(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); inference=EntityOSIntentInference()
    try:
        engine=ClayVerseEngine(db,{'g':'gabriel'},inference=inference,allow_process=False,entityos_bridge=None); result=engine.ingest('g','perform the requested action if admitted')
        assert inference.world['runtime_capabilities']==['state.noop'] and result['effect_id']
        assert result['outcome']=={'ok':False,'denied':True,'reason':'entityos_unavailable','target':'unavailable EntityOS regression','boundary':'EntityOS'}
        assert 'Requested action was not executed (entityos_unavailable).' in result['decision']['text']
        effect=db.db.execute('SELECT capability,status,outcome FROM effects WHERE effect_id=?',(result['effect_id'],)).fetchone(); assert effect['capability']=='entityos.exec' and effect['status']=='DENIED'
        assistant=db.db.execute('SELECT content,causal_refs FROM turns WHERE turn_id=?',(result['assistant_turn_id'],)).fetchone(); assert 'Requested action was not executed (entityos_unavailable).' in assistant['content'] and result['effect_id'] in assistant['causal_refs']
        causal=db.db.execute('SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?',(result['causal_id'],)).fetchone(); assert causal['credit']==0.0 and causal['reentered']==0 and causal['outcome_hash']
    finally: db.close()
