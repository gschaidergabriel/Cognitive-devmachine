#!/usr/bin/env python3
from enum import Enum
from dataclasses import dataclass

class Admissibility(str, Enum):
    AUTHORITATIVE_EXACT='AUTHORITATIVE_EXACT'
    EXACT_DERIVED='EXACT_DERIVED'
    APPROXIMATE_CANDIDATE='APPROXIMATE_CANDIDATE'
    SALIENCE_ONLY='SALIENCE_ONLY'
    MODEL_INTERNAL_ONLY='MODEL_INTERNAL_ONLY'
    EXTERNAL_EVIDENCE='EXTERNAL_EVIDENCE'

class Stage(str, Enum):
    STATE='STATE'; CANDIDATE='CANDIDATE'; WORKSPACE='WORKSPACE'; READER='READER'; INTERNAL='INTERNAL'; PROPOSAL='PROPOSAL'

DESTRUCTIVE={'DELETE','UNLINK','TRUNCATE','DROP','FORMAT','WIPE','OVERWRITE_IN_PLACE'}
STAGE_NEXT={Stage.STATE:{Stage.CANDIDATE},Stage.CANDIDATE:{Stage.WORKSPACE},Stage.WORKSPACE:{Stage.READER},Stage.READER:{Stage.INTERNAL,Stage.PROPOSAL},Stage.INTERNAL:{Stage.PROPOSAL},Stage.PROPOSAL:set()}

@dataclass(frozen=True)
class Value:
    admissibility: Admissibility
    stage: Stage

def check(v: Value, op: str, dst: Stage|None=None, token_origin: str|None=None):
    if op in DESTRUCTIVE:
        return False, 'DESTRUCTION_NOT_IN_MODEL_EFFECT_ALGEBRA'
    if op == 'FACT_COMMIT':
        if v.stage != Stage.STATE: return False, 'FACT_COMMIT_STAGE'
        if v.admissibility != Admissibility.AUTHORITATIVE_EXACT: return False, 'NONEXACT_TO_CANONICAL'
        if token_origin != 'HOST': return False, 'HOST_COMMIT_CAPABILITY_REQUIRED'
        return True, 'OK'
    if op == 'STAGE':
        if dst not in STAGE_NEXT[v.stage]: return False, 'CAUSAL_STAGE_SKIP_OR_BACKCAST'
        return True, 'OK'
    if op == 'AUTHORIZE_EFFECT':
        if v.stage != Stage.PROPOSAL: return False, 'AUTH_STAGE'
        if token_origin != 'HOST': return False, 'UNFORGEABLE_HOST_CAPABILITY_REQUIRED'
        return True, 'OK'
    return False, 'UNKNOWN_OR_UNTYPED_OPERATION'

if __name__ == '__main__':
    p=Value(Admissibility.SALIENCE_ONLY, Stage.PROPOSAL)
    assert check(p,'FORMAT',token_origin='MODEL')[0] is False
    assert check(p,'AUTHORIZE_EFFECT',token_origin='MODEL')[0] is False
    q=Value(Admissibility.AUTHORITATIVE_EXACT, Stage.STATE)
    assert check(q,'FACT_COMMIT',token_origin='HOST')[0] is True
    print('MCAAT_CHECKER_SMOKE_OK')
