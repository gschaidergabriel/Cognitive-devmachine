from __future__ import annotations

import contextlib
import hashlib
import json
import re
import time
import uuid

from .effects import EffectGate, EffectRequest
from .graph import ClayGraphProjection
from .hyperposition import HyperpositionProjector
from .memory import MemoryManager
from .needle import NeedleRouter
from .retrieval import WorldAssembler
from .store import StaleGeneration, UnifiedDB
from .workspace import Workspace

_EXPLICIT_RESOURCE = re.compile(r"(?i)\b(repo|branch|deploy|machine|task|db|service|file|resource)\s*:\s*([^\s,;]+)")
_PATH = re.compile(r"(?<![\w.-])(?:\.?\.?/|/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
_FILE = re.compile(r"(?<![\w.-])[A-Za-z0-9_.-]+\.(?:py|js|jsx|ts|tsx|json|jsonl|ya?ml|toml|md|sql|clay|service|timer|conf|cfg)(?![\w.-])", re.I)


class TurnLifecycleError(RuntimeError):
    pass


def infer_resource_refs(text: str) -> list[str]:
    refs: set[str] = set()
    for kind, value in _EXPLICIT_RESOURCE.findall(text): refs.add(f"{kind.lower()}:{value.strip()}")
    for value in _PATH.findall(text): refs.add(f"path:{value}")
    for value in _FILE.findall(text): refs.add(f"file:{value}")
    return sorted(refs)[:50]


class TurnLifecycle:
    """Deterministic per-turn lifecycle shared by Claude hooks and MCP effects."""
    def __init__(self, db: UnifiedDB, user_id: str, session_id: str, entityos_bridge=None):
        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}": raise PermissionError("invalid terminal/session binding")
        db.assert_session_owner(session_id, user_id)
        self.db=db; self.user_id=user_id; self.session_id=session_id
        self.memory=MemoryManager(db); self.world=WorldAssembler(db); self.workspace=Workspace(db)
        self.effects=EffectGate(db,allow_process=False,entityos_bridge=entityos_bridge); self.graph=ClayGraphProjection(db)

    def active(self): return self.db.db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()

    @staticmethod
    def _bound_world(world: dict, max_chars: int = 350_000) -> dict:
        packed={
            "own_recent":list(world.get("own_recent",[])),
            "cross_session_collision":list(world.get("cross_session_collision",[])),
            "durable_memory":list(world.get("durable_memory",[])),
            # Receipts are part of the canonical context contract. They are small,
            # authority-bearing metadata and must not disappear during context packing.
            "retrieval_receipt":dict(world.get("retrieval_receipt") or {}),
            "method_receipt":dict(world.get("method_receipt") or {}),
        }
        def size(): return len(json.dumps(packed,ensure_ascii=False,sort_keys=True,default=str))
        while size()>max_chars and packed["durable_memory"]: packed["durable_memory"].pop()
        while size()>max_chars and len(packed["own_recent"])>4: packed["own_recent"].pop(0)
        while size()>max_chars and packed["cross_session_collision"]: packed["cross_session_collision"].pop()
        if size()>max_chars:
            for item in packed["own_recent"]:
                if len(str(item.get("content","")))>20_000: item["content"]=str(item["content"])[:20_000]+"…[context-truncated]"
        return packed

    def _persisted_effect_in_tx(self,db,row):
        effects=db.execute("SELECT * FROM effects WHERE episode_id=? ORDER BY ts,effect_id",(row["episode_id"],)).fetchall()
        if len(effects)>1: raise TurnLifecycleError("multiple effect records for active episode")
        if not effects:
            if row["effect_id"] is not None: raise TurnLifecycleError("active turn references missing effect")
            return row,None,None
        effect=effects[0]
        if effect["status"]=="PENDING": raise TurnLifecycleError("effect outcome pending; automatic replay denied until recovery")
        causal=db.execute("SELECT * FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1",(effect["effect_id"],)).fetchone()
        if causal is None: raise TurnLifecycleError("final effect lacks causal re-entry")
        if causal["causal_id"]!=row["causal_id"]: raise TurnLifecycleError("persisted effect causal identity diverged")
        if row["effect_id"] is not None and row["effect_id"]!=effect["effect_id"]: raise TurnLifecycleError("active turn effect identity diverged")
        if row["effect_id"] is None:
            cur=db.execute("UPDATE active_turns SET effect_id=?,outcome=?,workspace_selected=1 WHERE session_id=? AND causal_id=? AND effect_id IS NULL",(effect["effect_id"],effect["outcome"],self.session_id,row["causal_id"]))
            if cur.rowcount!=1: raise TurnLifecycleError("active turn changed during effect rebind")
            row=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
            if row is None: raise TurnLifecycleError("active turn disappeared during effect rebind")
        return row,effect,causal

    def _effect_request_matches(self,effect,capability,target,argv):
        if effect["capability"]!=capability: return False
        journal=self.effects.journal
        expected_target=journal._payload(journal._target_receipt(target))
        expected_argv=journal._argv_receipt(argv)
        expected_argv=json.dumps(expected_argv,sort_keys=True,separators=(",",":")) if expected_argv else None
        return effect["target"]==expected_target and effect["argv"]==expected_argv

    @staticmethod
    def _recovered_effect_result(effect,causal):
        try: receipt=json.loads(effect["outcome"]) if effect["outcome"] else None
        except (TypeError,json.JSONDecodeError): receipt={"audit":"invalid-persisted-outcome-receipt"}
        verified=bool(effect["status"]=="VERIFIED" and isinstance(receipt,dict) and receipt.get("ok") is True)
        return {"effect_id":effect["effect_id"],"causal_id":causal["causal_id"],"verified":verified,"outcome":{"recovered":True,"replayed":False,"status":effect["status"],"receipt":receipt}}

    def _abort_active_in_tx(self,db,reason:str,*,finalize_projection:bool)->dict:
        if not self.db.db.in_transaction: raise TurnLifecycleError("abort requires active transaction")
        row=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
        if row is None: return {"aborted":False,"reason":"no_active_turn"}
        row,_,_=self._persisted_effect_in_tx(db,row)
        ws=db.execute("SELECT state FROM workspace_episodes WHERE episode_id=?",(row["episode_id"],)).fetchone()
        if ws is None: raise TurnLifecycleError("active turn workspace missing during abort")
        if ws["state"]=="OPEN": self.workspace.select_in_tx(row["episode_id"],"defer_effect")
        elif ws["state"]!="SELECTED": raise TurnLifecycleError(f"workspace is {ws['state']}, not abortable")
        existing_causal=db.execute("SELECT causal_id FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1",(row["effect_id"],)).fetchone() if row["effect_id"] else None
        if row["effect_id"] and existing_causal is None: raise TurnLifecycleError("effect lacks causal re-entry during abort")
        if existing_causal and existing_causal["causal_id"]!=row["causal_id"]: raise TurnLifecycleError("effect causal identity diverged during abort")
        now=time.time(); system_id=str(uuid.uuid4()); reason=str(reason)[:2000]; reason_hash=hashlib.sha256(reason.encode("utf-8")).hexdigest()
        ordinal=int(db.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",(self.session_id,)).fetchone()[0])
        db.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",(system_id,self.session_id,self.user_id,ordinal,now,"system",f"TURN_ABORTED:{reason}",row["resource_refs"],json.dumps([row["effect_id"]] if row["effect_id"] else []),json.dumps({"source":"claude-hook:failure","causal_id":row["causal_id"],"entity_generation":int(row["generation"])},sort_keys=True)))
        if existing_causal is None: db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(row["causal_id"],row["episode_id"],None,row["turn_id"],reason_hash,0.0,1,now))
        cur=db.execute("UPDATE workspace_episodes SET state='ABORTED' WHERE episode_id=? AND state='SELECTED'",(row["episode_id"],))
        if cur.rowcount!=1: raise TurnLifecycleError("workspace did not terminalize during abort")
        cur=db.execute("DELETE FROM active_turns WHERE session_id=? AND causal_id=?",(self.session_id,row["causal_id"]))
        if cur.rowcount!=1: raise TurnLifecycleError("active turn changed during abort")
        db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,self.session_id))
        if finalize_projection:
            self.memory.compact(self.session_id); self.graph.rebuild_in_tx()
        return {"aborted":True,"causal_id":row["causal_id"],"reason":reason}

    @contextlib.contextmanager
    def begin_admission(self,prompt:str,resources:list[str]|None=None,*,claude_session_id:str|None=None):
        prompt=str(prompt)
        if not prompt or len(prompt)>100_000: raise ValueError("invalid prompt")
        if claude_session_id is not None and (not isinstance(claude_session_id,str) or not claude_session_id or len(claude_session_id)>2048): raise ValueError("invalid Claude session id")
        resource_refs=sorted(set(resources or infer_resource_refs(prompt)))[:50]; turn_id=str(uuid.uuid4()); episode_id=str(uuid.uuid4()); causal_id=str(uuid.uuid4())
        alternatives=[{"id":"respond","kind":"reason"},{"id":"request_effect","kind":"effect_intent"},{"id":"defer_effect","kind":"no_effect"}]
        with self.db.tx() as db:
            predecessor=self._abort_active_in_tx(db,"previous_turn_interrupted_before_next_prompt",finalize_projection=False)
            if self.active() is not None: raise TurnLifecycleError("active turn remained after predecessor retirement")
            generation=self.db.session_generation(self.session_id); entity_generation=self.db.entity_generation()
            if generation!=entity_generation: raise StaleGeneration("entity_generation")
            now=time.time(); salience=min(1.0,0.15+0.03*len(resource_refs)+min(len(prompt),1200)/2400)
            provenance={"source":"claude-hook:UserPromptSubmit","session_generation":generation,"entity_generation":entity_generation,"causal_id":causal_id}
            if claude_session_id is not None: provenance["claude_session_id"]=claude_session_id
            ordinal=int(db.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",(self.session_id,)).fetchone()[0])
            db.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",(turn_id,self.session_id,self.user_id,ordinal,now,"user",prompt,json.dumps(resource_refs),"[]",json.dumps(provenance,sort_keys=True)))
            db.execute("INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",(episode_id,self.session_id,now,turn_id,salience,json.dumps(alternatives),None,"OPEN"))
            db.execute("INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(self.session_id,self.user_id,turn_id,episode_id,causal_id,generation,json.dumps(resource_refs),None,None,0,now))
            db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,self.session_id))
            self.memory.extract_explicit(turn_id,self.user_id,prompt); self.memory.compact(self.session_id)
            if predecessor["aborted"]: self.graph.rebuild_in_tx()
            world=self._bound_world(self.world.assemble(self.session_id,resource_refs)); hyperpositions=HyperpositionProjector.from_world(world); needle=NeedleRouter.analyze(prompt,world,hyperpositions,resource_refs)
            yield {"user_id":self.user_id,"session_id":self.session_id,"turn_id":turn_id,"episode_id":episode_id,"causal_id":causal_id,"generation":generation,"resources":resource_refs,"workspace":{"salience":salience,"alternatives":alternatives},"hyperpositions":hyperpositions,"needle":needle,"context":world}

    def begin(self,prompt:str,resources:list[str]|None=None)->dict:
        with self.begin_admission(prompt,resources) as result: return result

    def request_effect(self,capability:str,target:str,argv:list[str]|None=None)->dict:
        with self.db.tx() as db:
            row=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
            if row is None: raise TurnLifecycleError("no active turn; effect denied")
            if int(row["generation"])!=self.db.entity_generation(): raise StaleGeneration("entity_generation")
            if not int(row["workspace_selected"]):
                ws=db.execute("SELECT state,selected FROM workspace_episodes WHERE episode_id=?",(row["episode_id"],)).fetchone()
                if ws is None: raise TurnLifecycleError("active turn workspace missing before effect")
                if ws["state"]=="OPEN": self.workspace.select_in_tx(row["episode_id"],"request_effect")
                elif not (ws["state"]=="SELECTED" and ws["selected"]=="request_effect"): raise TurnLifecycleError("workspace already selected for a different action")
                cur=db.execute("UPDATE active_turns SET workspace_selected=1 WHERE session_id=? AND causal_id=?",(self.session_id,row["causal_id"]))
                if cur.rowcount!=1: raise TurnLifecycleError("active turn changed during effect selection")
                row=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
            row,effect,causal=self._persisted_effect_in_tx(db,row)
            if effect is not None:
                if not self._effect_request_matches(effect,capability,target,argv): raise TurnLifecycleError("different effect already persisted for active turn")
                return self._recovered_effect_result(effect,causal)
        try:
            effect_id,outcome=self.effects.execute(EffectRequest(self.user_id,self.session_id,capability,target,argv,int(row["generation"])),row["episode_id"])
        except RuntimeError as exc:
            if "effect already persisted for episode" not in str(exc): raise
            with self.db.tx() as db:
                current=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
                if current is None: raise TurnLifecycleError("active turn disappeared while reconciling effect") from exc
                current,effect,causal=self._persisted_effect_in_tx(db,current)
                if effect is None or not self._effect_request_matches(effect,capability,target,argv): raise TurnLifecycleError("persisted effect does not match retry") from exc
                return self._recovered_effect_result(effect,causal)
        causal_id=self.effects.causal_for_effect(effect_id)
        if causal_id!=row["causal_id"]: raise TurnLifecycleError("verified effect re-entered through wrong causal identity")
        with self.db.tx() as db:
            current=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
            if current is None or current["causal_id"]!=row["causal_id"]: raise TurnLifecycleError("active turn changed before effect binding")
            current,effect,causal=self._persisted_effect_in_tx(db,current)
            if effect is None or effect["effect_id"]!=effect_id: raise TurnLifecycleError("journaled effect unavailable for active binding")
        return {"effect_id":effect_id,"causal_id":causal_id,"verified":bool(isinstance(outcome,dict) and outcome.get("ok") is True),"outcome":outcome}

    def complete(self,response:str)->dict:
        response=str(response)
        if len(response)>200_000: raise ValueError("assistant response too large")
        now=time.time(); assistant_id=str(uuid.uuid4()); response_hash=hashlib.sha256(response.encode("utf-8")).hexdigest()
        with self.db.tx() as db:
            row=db.execute("SELECT * FROM active_turns WHERE session_id=?",(self.session_id,)).fetchone()
            if row is None: return {"completed":False,"reason":"no_active_turn"}
            row,_,_=self._persisted_effect_in_tx(db,row)
            if not int(row["workspace_selected"]): self.workspace.select_in_tx(row["episode_id"],"respond")
            effect_id=row["effect_id"]; existing_causal=db.execute("SELECT causal_id,credit FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1",(effect_id,)).fetchone() if effect_id else None
            if effect_id and existing_causal is None: raise TurnLifecycleError("effect lacks causal re-entry before Stop")
            if existing_causal and existing_causal["causal_id"]!=row["causal_id"]: raise TurnLifecycleError("effect causal identity diverged before Stop")
            credit=float(existing_causal["credit"]) if existing_causal else 0.0
            ordinal=int(db.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",(self.session_id,)).fetchone()[0])
            db.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",(assistant_id,self.session_id,self.user_id,ordinal,now,"assistant",response,row["resource_refs"],json.dumps([effect_id] if effect_id else []),json.dumps({"source":"claude-hook:Stop","causal_id":row["causal_id"],"entity_generation":int(row["generation"])},sort_keys=True)))
            if existing_causal is None: db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(row["causal_id"],row["episode_id"],None,row["turn_id"],response_hash,0.0,1,now))
            cur=db.execute("UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=? AND state='SELECTED'",(row["episode_id"],))
            if cur.rowcount!=1: raise TurnLifecycleError("workspace did not terminalize during Stop")
            self.memory.compact(self.session_id); self.graph.rebuild_in_tx()
            cur=db.execute("DELETE FROM active_turns WHERE session_id=? AND causal_id=?",(self.session_id,row["causal_id"]))
            if cur.rowcount!=1: raise TurnLifecycleError("active turn changed during Stop")
            db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,self.session_id))
            result={"completed":True,"assistant_turn_id":assistant_id,"causal_id":row["causal_id"],"effect_id":effect_id,"credit":credit}
        return result

    def abort(self,reason:str)->dict:
        with self.db.tx() as db: return self._abort_active_in_tx(db,reason,finalize_projection=True)
