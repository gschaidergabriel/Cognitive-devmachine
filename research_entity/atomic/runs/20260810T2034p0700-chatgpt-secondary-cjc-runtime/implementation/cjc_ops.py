from cjc_core import *
from cjc_core import _sha256_domain

class Transition:
    contract: TransitionContract
    def _validate_symbolic(self,state:JetState)->None:
        if not self.contract.exact_eligible(state.identity): raise CJCError("transition not exact-eligible for current state identity")
        missing=(self.contract.reads|self.contract.writes)-set(state.values)
        if missing: raise CJCError(f"transition references missing state fields: {sorted(missing)}")
    def symbolic(self,state:JetState,policy:JetPolicy)->JetState: raise NotImplementedError
    def concrete(self,state:dict[str,int],enabled_uses:set[str])->dict[str,int]: raise NotImplementedError
    @property
    def use_ref(self)->str:return self.contract.use_ref

@dataclass
class Add(Transition):
    contract:TransitionContract; field:str; amount:int
    def symbolic(self,state,policy):
        self._validate_symbolic(state); out=state.copy(); z=BoolJet.var(self.use_ref); out.values[self.field]=out.values[self.field]+z.scale(self.amount); return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.field]+=self.amount
        return out

@dataclass
class SetValue(Transition):
    contract:TransitionContract; field:str; value:int
    def symbolic(self,state,policy):
        self._validate_symbolic(state); out=state.copy(); z=BoolJet.var(self.use_ref)
        out.values[self.field]=out.values[self.field].mul(BoolJet.const(1)-z,policy)+z.scale(self.value); return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.field]=self.value
        return out

@dataclass
class Scale(Transition):
    contract:TransitionContract; field:str; factor:int
    def symbolic(self,state,policy):
        self._validate_symbolic(state); out=state.copy(); z=BoolJet.var(self.use_ref); gate=BoolJet.const(1)+z.scale(self.factor-1); out.values[self.field]=out.values[self.field].mul(gate,policy); return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.field]*=self.factor
        return out

@dataclass
class CopyAdd(Transition):
    contract:TransitionContract; src:str; dst:str; factor:int=1
    def symbolic(self,state,policy):
        self._validate_symbolic(state); out=state.copy(); z=BoolJet.var(self.use_ref); delta=state.values[self.src].mul(z,policy).scale(self.factor); out.values[self.dst]=out.values[self.dst]+delta; return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.dst]+=self.factor*state[self.src]
        return out

@dataclass
class Swap(Transition):
    contract:TransitionContract; left:str; right:str
    def symbolic(self,state,policy):
        self._validate_symbolic(state); out=state.copy(); z=BoolJet.var(self.use_ref); one_minus=BoolJet.const(1)-z; left_old=state.values[self.left]; right_old=state.values[self.right]
        out.values[self.left]=left_old.mul(one_minus,policy)+right_old.mul(z,policy); out.values[self.right]=right_old.mul(one_minus,policy)+left_old.mul(z,policy); return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.left],out[self.right]=state[self.right],state[self.left]
        return out

@dataclass
class OpaqueTransition(Transition):
    contract:TransitionContract; field:str
    def symbolic(self,state,policy):
        out=state.copy(); out.values[self.field]=BoolJet.unknown(); return out
    def concrete(self,state,enabled_uses):
        out=dict(state)
        if self.use_ref in enabled_uses: out[self.field]^=1
        return out

@dataclass(frozen=True)
class JetCommutatorReceipt:
    pair:tuple[str,str]; state_instance_id:str; transition_hashes:tuple[str,str]; exactness:Exactness; classification:PairClass; observed_full_state_delta:dict[str,int]; hidden_counterfactual_support:tuple[str,...]; commutator_terms:int; max_degree:int; authority_minted:bool=False; architecture_promoted:bool=False
    @property
    def receipt_hash(self)->str:
        return _sha256_domain(b"CJCReceipt/v1\x00",{"pair":self.pair,"state_instance_id":self.state_instance_id,"transition_hashes":self.transition_hashes,"exactness":self.exactness.value,"classification":self.classification.value,"observed_full_state_delta":self.observed_full_state_delta,"hidden_counterfactual_support":self.hidden_counterfactual_support,"commutator_terms":self.commutator_terms,"max_degree":self.max_degree,"authority_minted":self.authority_minted,"architecture_promoted":self.architecture_promoted})
