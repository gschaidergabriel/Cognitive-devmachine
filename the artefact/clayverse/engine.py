from __future__ import annotations
import threading,time,uuid
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
        self.db=db; self.identity=IdentityRouter(db,clerk_map); self.memory=MemoryManager(db); self.world=WorldAssembler(db); self.workspace=Workspace(db); self.effects=EffectGate(db,allow_process,entityos_bridge); self.graph=ClayGraphProjection(db); self.inference=inference or DeterministicTestInference(); self._turn_lock=threading.RLock()
    def ingest(self,clerk_subject,content,*,resources=None):
        # One persistent ClayVerse entity has one causal turn frontier. Requests may
        # arrive through multiple authenticated surfaces, but observation -> cognition
        # / effect -> causal re-entry is serialized inside the engine itself.
        with self._turn_lock:
            return self._ingest_locked(clerk_subject,content,resources=resources)
    def _ingest_locked(self,clerk_subject,content,*,resources=None):
        resources=resources or []; uid,sid=self.identity.resolve(clerk_subject); tid=self.db.append_turn(sid,uid,'user',content,resources=resources,provenance={'source':'clerk-terminal'}); self.memory.extract_explicit(tid,uid,content); self.memory.compact(sid); world=self.world.assemble(sid,resources); world['runtime_capabilities']=list(self.effects.available_capabilities()); ws=self.workspace.open(sid,tid,content,resources); reasoning_generation=self.db.session_generation(sid); decision=self.inference.reason(world,content); self.workspace.select(ws['episode_id'],decision.get('selection','respond')); effect_id=None; outcome=None
        eff=decision.get('effect')
        if eff: effect_id,outcome=self.effects.execute(EffectRequest(uid,sid,eff['capability'],eff['target'],eff.get('argv'),reasoning_generation),ws['episode_id'])
        if isinstance(outcome,dict) and outcome.get('denied') is True:
            decision=dict(decision); notice=f"Requested action was not executed ({outcome.get('reason','effect_denied')})."; prior=str(decision.get('text','')).strip(); decision['text']=f"{prior}\n\n{notice}" if prior else notice
        aid=self.db.append_turn(sid,uid,'assistant',decision.get('text',''),resources=resources,causal_refs=[effect_id] if effect_id else [],provenance={'source':'inference-adapter'}); causal_id=self.effects.causal_for_effect(effect_id) if effect_id else None
        if causal_id is None:
            causal_id=str(uuid.uuid4()); self.db.db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(causal_id,ws['episode_id'],effect_id,tid,None,0.0,0,time.time()))
        self.graph.rebuild()
        return {'user_id':uid,'session_id':sid,'turn_id':tid,'assistant_turn_id':aid,'workspace':ws,'decision':decision,'effect_id':effect_id,'outcome':outcome,'causal_id':causal_id,'collision_count':len(world['cross_session_collision'])}
