#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

class Plane(str, Enum):
    SEMANTIC = 'SEMANTIC'
    ACTIVE = 'ACTIVE'
    COORDINATION = 'COORDINATION'
    PHYSICAL = 'PHYSICAL'

ALL_PLANES = tuple(Plane)

@dataclass(frozen=True)
class Snapshot:
    semantic_root: str
    active_root: str
    coordination_root: str
    physical_root: str
    state_epoch: int
    execution_generation: int
    delivery_generation: int
    schema_version: str = 'TopologyScope/v1'

    def root(self, p: Plane) -> str:
        return {
            Plane.SEMANTIC: self.semantic_root,
            Plane.ACTIVE: self.active_root,
            Plane.COORDINATION: self.coordination_root,
            Plane.PHYSICAL: self.physical_root,
        }[p]

def h(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()

def canonical_reads(reads: Iterable[str]):
    vals = {Plane(x) for x in reads}
    vals.add(Plane.SEMANTIC)
    return sorted(x.value for x in vals)

def compile_certificate(spec: dict, snap: Snapshot) -> dict:
    declared = canonical_reads(spec.get('reads', []))
    observed = set(canonical_reads(spec.get('observed_reads', declared)))
    declared_set = set(declared)
    closure_complete = bool(spec.get('closure_complete', False))
    law_status = spec.get('law_status', 'UNKNOWN')
    effect = spec.get('effect', 'UNKNOWN')

    if not closure_complete:
        dependency_precision = 'CONSERVATIVE_ALL'
        bound = [p.value for p in ALL_PLANES]
        exact_rewrite_admissible = False
    else:
        missing = sorted(observed - declared_set)
        if missing:
            return {'status':'REJECTED_UNDECLARED_TOPOLOGY_READ','missing':missing}
        dependency_precision = 'EXACT_DECLARED'
        bound = declared
        exact_rewrite_admissible = law_status in ('PROVED','TESTED_BOUNDED')

    speculative_multi_alternative_execution = effect not in ('EXTERNAL','SECURITY_SENSITIVE','UNKNOWN')
    roots = {p: snap.root(Plane(p)) for p in bound}
    semantic_payload = {
        'program': spec['program'],
        'reads': declared,
        'effect': effect,
        'law_status': law_status,
    }
    contract_payload = {
        **semantic_payload,
        'raw_reads': spec.get('reads', []),
        'provenance': spec.get('provenance', []),
        'closure_complete': closure_complete,
    }
    return {
        'status':'OK',
        'schema':'TopologyScopeCertificate/v1-candidate',
        'program':spec['program'],
        'semantic_hash':h(semantic_payload),
        'contract_hash':h(contract_payload),
        'dependency_precision':dependency_precision,
        'bound_planes':bound,
        'plane_roots':roots,
        'state_epoch':snap.state_epoch,
        'execution_generation':snap.execution_generation,
        'delivery_generation':snap.delivery_generation,
        'schema_version':snap.schema_version,
        'effect':effect,
        'exact_rewrite_admissible':exact_rewrite_admissible,
        'speculative_multi_alternative_execution':speculative_multi_alternative_execution,
        'authority':'NONE',
        'promotion':'NONE',
    }

def validate(cert: dict, current: Snapshot) -> tuple[bool,str]:
    if cert.get('status') != 'OK':
        return False, cert.get('status','INVALID')
    for field in ('state_epoch','execution_generation','delivery_generation','schema_version'):
        if cert[field] != getattr(current, field):
            return False, f'{field.upper()}_MISMATCH'
    for p in cert['bound_planes']:
        if cert['plane_roots'][p] != current.root(Plane(p)):
            return False, f'{p}_TOPOLOGY_MISMATCH'
    return True, 'VALID'

def selftest():
    base=Snapshot('S1','A1','C1','P1',7,11,19)
    active_changed=Snapshot('S1','A2','C1','P1',7,11,19)
    coord_changed=Snapshot('S1','A1','C2','P1',7,11,19)

    active={'program':'active_projection','reads':['ACTIVE'],'observed_reads':['ACTIVE'],'closure_complete':True,'law_status':'TESTED_BOUNDED','effect':'READ_ONLY','provenance':['T1']}
    c1=compile_certificate(active,base)
    assert validate(c1,base)==(True,'VALID')
    assert validate(c1,active_changed)==(False,'ACTIVE_TOPOLOGY_MISMATCH')

    semantic={'program':'semantic_query','reads':[],'observed_reads':[],'closure_complete':True,'law_status':'PROVED','effect':'PURE','provenance':['T2']}
    c2=compile_certificate(semantic,base)
    assert validate(c2,active_changed)==(True,'VALID')
    assert validate(c2,coord_changed)==(True,'VALID')

    coord={'program':'lease_guard','reads':['COORDINATION'],'observed_reads':['COORDINATION'],'closure_complete':True,'law_status':'TESTED_BOUNDED','effect':'READ_ONLY','provenance':['T3']}
    c3=compile_certificate(coord,base)
    assert validate(c3,coord_changed)==(False,'COORDINATION_TOPOLOGY_MISMATCH')

    bad={'program':'hidden_read','reads':['SEMANTIC'],'observed_reads':['SEMANTIC','ACTIVE'],'closure_complete':True,'law_status':'TESTED_BOUNDED','effect':'PURE'}
    c4=compile_certificate(bad,base)
    assert c4['status']=='REJECTED_UNDECLARED_TOPOLOGY_READ'

    unknown={'program':'dynamic_read','reads':['ACTIVE'],'observed_reads':['ACTIVE'],'closure_complete':False,'law_status':'TESTED_BOUNDED','effect':'UNKNOWN'}
    c5=compile_certificate(unknown,base)
    assert set(c5['bound_planes'])==set(p.value for p in ALL_PLANES)
    assert c5['exact_rewrite_admissible'] is False
    assert c5['speculative_multi_alternative_execution'] is False

    a={'program':'same','reads':['ACTIVE','SEMANTIC','ACTIVE'],'observed_reads':['ACTIVE'],'closure_complete':True,'law_status':'PROVED','effect':'PURE','provenance':['p1']}
    b={'program':'same','reads':['SEMANTIC','ACTIVE'],'observed_reads':['ACTIVE'],'closure_complete':True,'law_status':'PROVED','effect':'PURE','provenance':['p2']}
    ca,cb=compile_certificate(a,base),compile_certificate(b,base)
    assert ca['semantic_hash']==cb['semantic_hash']
    assert ca['contract_hash']!=cb['contract_hash']

    return {
      'tests':7,
      'passed':7,
      'active_mutation_rejected':True,
      'semantic_only_survives_unbound_active_mutation':True,
      'coordination_mutation_rejected':True,
      'undeclared_topology_read_rejected':True,
      'unknown_read_closure_binds_all_and_blocks_exact_rewrite':True,
      'semantic_hash_set_normalization_preserved':True,
      'contract_hash_provenance_sensitive':True,
    }

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--selftest':
        print(json.dumps(selftest(), indent=2, sort_keys=True))
    else:
        print('use --selftest')
