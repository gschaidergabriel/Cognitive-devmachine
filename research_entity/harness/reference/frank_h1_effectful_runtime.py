from __future__ import annotations
from pathlib import Path
from typing import Any

from .frank_h1_full_runtime import FrankH1FullRuntime
from .effect_gateway_runtime import SandboxEffectGateway, SandboxWriteProposal, InjectedCrash
from .unifieddb_query_plane import QuerySpec, SelectionPolicy
from .state_ledger import h

class FrankH1EffectfulRuntime:
    """Full H1 cognition plus a real sandbox side-effect and outcome re-entry."""
    def __init__(self, effect_root: str, ledger_path=':memory:'):
        self.full=FrankH1FullRuntime(ledger_path)
        self.effect_gateway=SandboxEffectGateway(self.full.spine.ledger,effect_root)

    @property
    def ledger(self): return self.full.spine.ledger
    def close(self): self.full.close()

    def run_and_write(self, *, text:str, visual:dict[str,Any], options:list[dict[str,Any]],
                      effect_id:str, relative_path:str, content:str, mode='instruct',
                      peer_capability=None, peer_semantics=None, peer_raw_prose='', crash_at=None):
        cognition=self.full.run(text=text,visual=visual,options=options,mode=mode,
                                peer_capability=peer_capability,peer_semantics=peer_semantics,
                                peer_raw_prose=peer_raw_prose)
        proposal=SandboxWriteProposal(effect_id,relative_path,content,authority='NONE')
        permit=self.effect_gateway.issue_permit(proposal,max_bytes=max(1024,len(content.encode('utf-8'))+32))
        try:
            outcome=self.effect_gateway.execute(proposal,permit,crash_at=crash_at)
            crashed=False
        except InjectedCrash:
            crashed=True
            outcome=self.effect_gateway.recover_pending(effect_id)
        q=self.full.udb.query(QuerySpec(
            query_id=f'effect-reentry-{self.ledger.epoch}',domains=('effect',),keys=(effect_id,),statuses=('CURRENT',),
            epistemic=('KNOWN','CONFLICT','UNKNOWN'),basis_epoch=self.ledger.epoch,limit=16,
            purpose='EFFECT_OUTCOME_REENTRY'))
        reentry=self.full.udb.select_for_assembly(q,SelectionPolicy(allow_epistemic=('KNOWN',),max_items=16))
        result={
            'cognition_audit':cognition['integration_audit'],
            'effect_outcome':outcome,
            'crash_injected':crashed,
            'effect_reentry':reentry,
            'target_path':str((self.effect_gateway.root/relative_path).resolve()),
            'state_hash_after_effect':self.ledger.semantic_state_hash,
            'trace_root_after_effect':self.ledger.trace_root_hash,
        }
        result['pass']=bool(
            cognition['integration_audit']['pass'] and
            outcome.get('status') in {'COMMITTED_VERIFIED','RECOVERED_COMMITTED_VERIFIED','ALREADY_COMMITTED'} and
            any(x['key']==effect_id for x in reentry['selected']) and
            reentry['authority']=='ASSEMBLY_CONTEXT_ONLY'
        )
        result['result_hash']=h({k:v for k,v in result.items() if k!='result_hash'})
        return result

    def recovery(self): return self.full.recovery()
