from __future__ import annotations
import hashlib,json,time,uuid
from .store import UnifiedDB
from .identity import IdentityRouter
from .memory import MemoryManager
from .retrieval import WorldAssembler
from .workspace import Workspace
from .effects import EffectGate,EffectRequest
from .graph import ClayGraphProjection
from .entityos_bridge import EntityOSBridge
class InferenceAdapter:
    def reason(self,world,observation): raise NotImplementedError
class DeterministicTestInference(InferenceAdapter):
    def reason(self,world,observation): return {"text":f"ack:{observation}","selection":"respond","effect":None}
class ClayVerseEngine:
    def __init__(self,db:UnifiedDB,clerk_map,inference=None,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.identity=IdentityRouter(db,clerk_map); self.memory=MemoryManager(db); self.world=WorldAssembler(db); self.workspace=Workspace(db); self.effects=EffectGate(db,allow_process,entityos_bridge); self.graph=ClayGraphProjection(db); self.inference=inference or DeterministicTestInference()
    def ingest(self,clerk_subject,content,*,resources=None):
        resources=resources or []; uid,sid=self.identity.resolve(clerk_subject); tid=self.db.append_turn(sid,uid,'user',content,resources=resources,provenance={'source':'clerk-terminal'}); self.memory.extract_explicit(tid,uid,content); self.memory.compact(sid); world=self.world.assemble(sid,resources); ws=self.workspace.open(sid,tid,content,resources); reasoning_generation=self.db.session_generation(sid); decision=self.inference.reason(world,content); self.workspace.select(ws['episode_id'],decision.get('selection','respond')); effect_id=None; outcome=None
        eff=decision.get('effect')
        if eff: effect_id,outcome=self.effects.execute(EffectRequest(uid,sid,eff['capability'],eff['target'],eff.get('argv'),reasoning_generation),ws['episode_id'])
        aid=self.db.append_turn(sid,uid,'assistant',decision.get('text',''),resources=resources,causal_refs=[effect_id] if effect_id else [],provenance={'source':'inference-adapter'}); causal_id=str(uuid.uuid4()); out_hash=hashlib.sha256(json.dumps(outcome,sort_keys=True).encode()).hexdigest() if outcome is not None else None; self.db.db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(causal_id,ws['episode_id'],effect_id,tid,out_hash,1.0 if outcome is not None else 0.0,1,time.time())); self.graph.rebuild()
        return {'user_id':uid,'session_id':sid,'turn_id':tid,'assistant_turn_id':aid,'workspace':ws,'decision':decision,'effect_id':effect_id,'outcome':outcome,'causal_id':causal_id,'collision_count':len(world['cross_session_collision'])}
