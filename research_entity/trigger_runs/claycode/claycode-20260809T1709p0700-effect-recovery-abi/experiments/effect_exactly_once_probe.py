from dataclasses import dataclass
from enum import Enum
import json

class LocalState(str, Enum):
    NONE='NONE'; PREPARED='PREPARED'; DONE='DONE'

@dataclass
class Remote:
    count: int = 0
    seen: set = None
    def __post_init__(self):
        if self.seen is None: self.seen = set()
    def effect_plain(self, op_id):
        self.count += 1
    def effect_idempotent(self, op_id):
        if op_id not in self.seen:
            self.seen.add(op_id)
            self.count += 1

def local_only_recovery(world, strategy):
    r=Remote(); state=LocalState.PREPARED; op_id='op-1'
    if world=='AFTER_EFFECT': r.effect_plain(op_id)
    if strategy=='RETRY':
        r.effect_plain(op_id); state=LocalState.DONE
    elif strategy=='ABSTAIN':
        pass
    else: raise ValueError(strategy)
    return {'world':world,'strategy':strategy,'count':r.count,'success_exactly_once':r.count==1}

def remote_idempotency_recovery(world):
    r=Remote(); state=LocalState.PREPARED; op_id='op-1'
    if world=='AFTER_EFFECT': r.effect_idempotent(op_id)
    r.effect_idempotent(op_id); state=LocalState.DONE
    return {'world':world,'strategy':'REMOTE_IDEMPOTENT_RETRY','count':r.count,'success_exactly_once':r.count==1}

def run():
    worlds=['BEFORE_EFFECT','AFTER_EFFECT']
    local=[local_only_recovery(w,s) for s in ['RETRY','ABSTAIN'] for w in worlds]
    remote=[remote_idempotency_recovery(w) for w in worlds]
    return {
      'local_only':local,
      'local_strategy_pass_counts':{s:sum(x['success_exactly_once'] for x in local if x['strategy']==s) for s in ['RETRY','ABSTAIN']},
      'remote_idempotent':remote,
      'remote_pass_count':sum(x['success_exactly_once'] for x in remote),
      'indistinguishability_claim':'The durable local state PREPARED is identical in BEFORE_EFFECT and AFTER_EFFECT worlds; a recovery decision using only that local state cannot know whether the external effect occurred.',
      'conclusion':'A generic external-effect ABI cannot promise exactly-once from local lifecycle state alone. It needs remote idempotency/deduplication, transactional coupling, or a queryable/reconcilable remote effect identity; otherwise recovery must expose an UNCERTAIN outcome rather than inventing DONE.'
    }

if __name__=='__main__':
    print(json.dumps(run(),sort_keys=True,indent=2))
