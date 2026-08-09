from __future__ import annotations
from dataclasses import dataclass, asdict
from io import BytesIO
from pathlib import Path
from typing import Any
import hashlib, math, time

import numpy as np
from PIL import Image

from .state_ledger import StateLedger, h

FEATURE_VERSION='retina-mvc0-pixel-v1'
CALIBRATION_VERSION='mvc0-calibration-sandbox-v1'

class RetinaError(ValueError): pass

@dataclass(frozen=True)
class LearningBudget:
    max_classes:int=64
    max_versions_per_class:int=128
    max_feature_dim:int=128
    max_update_ms:float=50.0

@dataclass(frozen=True)
class PixelEvidence:
    source_id:str
    capture_epoch:int
    frame_hash:str
    width:int
    height:int
    mode:str
    feature_version:str
    feature_vector:tuple[float,...]
    change_score:float
    changed:bool
    sensor_confidence:float
    authority:str='SENSOR_EVIDENCE_ONLY'

@dataclass(frozen=True)
class FamiliarityResult:
    outcome:str
    candidate_label:str|None
    similarity:float
    margin:float
    support_count:int
    evidence_tier:str|None
    prototype_version:int|None
    calibration_version:str
    feature_version:str
    authority:str='FAMILIARITY_ROUTING_ONLY'

class DigitalRetinaRuntime:
    """Deterministic pixel ingress plus transparent MVC-0 prototype familiarity.

    Numerical image features are physical backing evidence. Semantic state is persisted
    only as typed, provenance-bound receipts; familiarity never becomes truth authority.
    """
    def __init__(self,ledger:StateLedger,learning_budget:LearningBudget=LearningBudget()):
        self.ledger=ledger
        self.learning_budget=learning_budget
        self._last_signature:dict[str,np.ndarray]={}

    @staticmethod
    def _load_image(image:Image.Image|str|Path|bytes|np.ndarray):
        if isinstance(image,Image.Image):
            im=image.copy()
        elif isinstance(image,(str,Path)):
            im=Image.open(image)
        elif isinstance(image,(bytes,bytearray)):
            im=Image.open(BytesIO(bytes(image)))
        elif isinstance(image,np.ndarray):
            arr=np.asarray(image)
            if arr.ndim==2:
                im=Image.fromarray(arr.astype(np.uint8),mode='L')
            elif arr.ndim==3 and arr.shape[2] in (3,4):
                im=Image.fromarray(arr.astype(np.uint8),mode='RGBA' if arr.shape[2]==4 else 'RGB')
            else: raise RetinaError('unsupported ndarray shape')
        else: raise RetinaError('unsupported image input')
        return im.convert('RGB')

    @staticmethod
    def _frame_hash(im:Image.Image):
        return hashlib.sha256((f'{im.width}x{im.height}:RGB:').encode()+im.tobytes()).hexdigest()

    @staticmethod
    def _signature(im:Image.Image):
        return np.asarray(im.convert('L').resize((16,16),Image.Resampling.BILINEAR),dtype=np.float32)/255.0

    @staticmethod
    def _features(im:Image.Image):
        small=np.asarray(im.resize((32,32),Image.Resampling.BILINEAR),dtype=np.float32)/255.0
        rgb_mean=small.mean(axis=(0,1))-.5
        rgb_std=small.std(axis=(0,1))
        gray=np.dot(small[...,:3],np.array([.299,.587,.114],dtype=np.float32))
        hist,_=np.histogram(gray,bins=8,range=(0,1)); hist=hist.astype(np.float32)/gray.size-(1/8)
        quads=np.array([
            gray[:16,:16].mean(),gray[:16,16:].mean(),gray[16:,:16].mean(),gray[16:,16:].mean()
        ],dtype=np.float32)-.5
        dx=np.abs(np.diff(gray,axis=1)).mean(); dy=np.abs(np.diff(gray,axis=0)).mean()
        edges=np.array([dx,dy],dtype=np.float32)
        yy,xx=np.indices(gray.shape,dtype=np.float32); weight=np.maximum(gray,1e-4); total=float(weight.sum())
        centroid=np.array([(float((xx*weight).sum())/total)/31-.5,(float((yy*weight).sum())/total)/31-.5],dtype=np.float32)
        asym=np.array([np.abs(gray-np.fliplr(gray)).mean(),np.abs(gray-np.flipud(gray)).mean()],dtype=np.float32)
        ds=np.asarray(im.convert('L').resize((8,8),Image.Resampling.BILINEAR),dtype=np.float32).reshape(-1)/255.0-.5
        vec=np.concatenate([rgb_mean,rgb_std,hist,quads,edges,centroid,asym,ds]).astype(np.float32)
        norm=float(np.linalg.norm(vec))
        if norm<1e-12: return np.zeros_like(vec)
        return vec/norm

    def capture(self,image,*,source_id:str,capture_epoch:int,sensor_confidence=.95,change_threshold=.015):
        t0=time.perf_counter(); im=self._load_image(image); sig=self._signature(im); prev=self._last_signature.get(source_id)
        change=1.0 if prev is None else float(np.abs(sig-prev).mean())
        self._last_signature[source_id]=sig
        vec=self._features(im); frame_hash=self._frame_hash(im)
        ev=PixelEvidence(source_id,int(capture_epoch),frame_hash,im.width,im.height,'RGB',FEATURE_VERSION,tuple(float(x) for x in vec),round(change,8),bool(change>=change_threshold),float(sensor_confidence))
        metrics={'feature_dim':len(ev.feature_vector),'elapsed_ms':round((time.perf_counter()-t0)*1000,4),'input_pixels':im.width*im.height}
        return ev,metrics

    def _current_prototypes(self):
        out=[]
        for row in self.ledger.materialized():
            if row['domain']!='visual_learning' or not row['key'].startswith('prototype_current:'): continue
            v=row['value'];
            if v.get('feature_version')!=FEATURE_VERSION: continue
            out.append(v)
        return out

    @staticmethod
    def _cos(a,b):
        av=np.asarray(a,dtype=np.float32); bv=np.asarray(b,dtype=np.float32); den=float(np.linalg.norm(av)*np.linalg.norm(bv))
        return 0.0 if den<1e-12 else float(np.dot(av,bv)/den)

    def classify(self,evidence:PixelEvidence,*,context_prior:str|None=None):
        if evidence.feature_version!=FEATURE_VERSION: raise RetinaError('feature version mismatch')
        scores=[]
        for p in self._current_prototypes():
            scores.append((self._cos(evidence.feature_vector,p['vector']),p))
        scores.sort(key=lambda x:(-x[0],x[1]['label']))
        if not scores:
            return FamiliarityResult('UNKNOWN',None,0.0,0.0,0,None,None,CALIBRATION_VERSION,FEATURE_VERSION)
        best,p=scores[0]; second=scores[1][0] if len(scores)>1 else -1.0; margin=best-second
        if context_prior and context_prior!=p['label'] and best>=.96:
            outcome='CONFLICT'
        elif len(scores)>1 and margin<.025 and best>=.94:
            outcome='AMBIGUOUS'
        elif best>=.985 and p['support_count']>=1:
            outcome='KNOWN_HIGH_CONFIDENCE'
        elif best>=.96:
            outcome='KNOWN_NEEDS_CONFIRMATION'
        else:
            outcome='UNKNOWN'
        return FamiliarityResult(outcome,p['label'] if outcome!='UNKNOWN' else None,round(best,6),round(margin,6),int(p['support_count']),p.get('evidence_tier'),int(p['version']),CALIBRATION_VERSION,FEATURE_VERSION)

    def _record(self,key,value,event_type):
        base=self.ledger.epoch; eid=f'{event_type.lower()}:{key}:{base+1}'
        return self.ledger.append_event(event_id=eid,idem=eid,base_epoch=base,event_type=event_type,writer='digital-retina-mvc0',ops=[{'op':'SET','domain':'visual_learning','key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'}],provenance={'feature_version':FEATURE_VERSION},source={'kind':'pixel_evidence'},execution={})

    def admit_example(self,label:str,evidence:PixelEvidence,*,tier:str,evidence_ref:str):
        update_t0=time.perf_counter()
        tier=tier.upper(); label=label.strip()
        if not label: raise RetinaError('label required')
        if evidence.feature_version!=FEATURE_VERSION: return {'status':'REJECTED_FEATURE_VERSION','trained':False}
        if len(evidence.feature_vector)>self.learning_budget.max_feature_dim: return {'status':'PAUSED_RESOURCE_BUDGET_FEATURE_DIM','trained':False}
        current_labels=len(self._current_prototypes())
        if self.ledger.get('visual_learning',f'prototype_current:{label}') is None and current_labels>=self.learning_budget.max_classes: return {'status':'PAUSED_RESOURCE_BUDGET_CLASSES','trained':False}
        if tier=='BRONZE': return {'status':'REJECTED_BRONZE_SELF_TRAINING','trained':False}
        if tier not in {'GOLD','SILVER'}: raise RetinaError('bad evidence tier')
        if tier=='SILVER':
            key=f'silver_buffer:{label}'
            row=self.ledger.get('visual_learning',key); seen=[] if not row else list(row['value']['frame_hashes'])
            if evidence.frame_hash not in seen: seen.append(evidence.frame_hash)
            buf={'label':label,'frame_hashes':seen,'support':len(seen),'feature_version':FEATURE_VERSION,'evidence_ref':evidence_ref}
            self._record(key,buf,'VISUAL_SILVER_BUFFER')
            if len(seen)<2: return {'status':'SILVER_BUFFERED','trained':False,'support':len(seen)}
        current=self.ledger.get('visual_learning',f'prototype_current:{label}')
        if current and int(current['value'].get('version',0))>=self.learning_budget.max_versions_per_class:
            return {'status':'PAUSED_RESOURCE_BUDGET_VERSIONS','trained':False}
        if current:
            cur=current['value']; n=int(cur['support_count']); old=np.asarray(cur['vector'],dtype=np.float32); new=np.asarray(evidence.feature_vector,dtype=np.float32); vec=(old*n+new)/(n+1); norm=float(np.linalg.norm(vec)); vec=vec if norm<1e-12 else vec/norm; version=int(cur['version'])+1; previous_version=int(cur['version'])
        else:
            vec=np.asarray(evidence.feature_vector,dtype=np.float32); version=1; previous_version=None; n=0
        elapsed_ms=(time.perf_counter()-update_t0)*1000
        if elapsed_ms>self.learning_budget.max_update_ms:
            return {'status':'PAUSED_RESOURCE_BUDGET_TIME','trained':False,'update_ms':round(elapsed_ms,4)}
        proto={'label':label,'version':version,'previous_version':previous_version,'vector':[round(float(x),8) for x in vec],'support_count':n+1,'evidence_tier':tier,'feature_version':FEATURE_VERSION,'calibration_version':CALIBRATION_VERSION,'last_frame_hash':evidence.frame_hash,'evidence_ref':evidence_ref,'learning_budget':asdict(self.learning_budget),'authority':'FAMILIARITY_ROUTING_ONLY'}
        self._record(f'prototype_version:{label}:v{version}',proto,'VISUAL_PROTOTYPE_VERSION')
        self._record(f'prototype_current:{label}',proto,'VISUAL_PROTOTYPE_PROMOTION')
        return {'status':'TRAINED_AND_PROMOTED','trained':True,'label':label,'version':version,'previous_version':previous_version,'support_count':n+1}

    def rollback(self,label:str):
        row=self.ledger.get('visual_learning',f'prototype_current:{label}')
        if not row: return {'status':'NO_CURRENT'}
        cur=row['value']; prev=cur.get('previous_version')
        if prev is None: return {'status':'NO_PREVIOUS_VERSION'}
        old=self.ledger.get('visual_learning',f'prototype_version:{label}:v{prev}')
        if not old: return {'status':'MISSING_PREVIOUS_VERSION'}
        restored=dict(old['value'])
        self._record(f'prototype_current:{label}',restored,'VISUAL_PROTOTYPE_ROLLBACK')
        return {'status':'ROLLED_BACK','label':label,'version':restored['version']}

    def materialize_visual_percept(self,evidence:PixelEvidence,familiarity:FamiliarityResult,*,context_prior=None):
        return {
            'source_identity':evidence.source_id,'source_class':'IMAGE_OR_FRAME','capture_epoch':evidence.capture_epoch,
            'frame_hash':evidence.frame_hash,'spatial_frame':{'width':evidence.width,'height':evidence.height,'mode':evidence.mode},
            'change':{'score':evidence.change_score,'changed':evidence.changed},
            'features':{'feature_version':evidence.feature_version,'feature_hash':h(list(evidence.feature_vector)),'dimension':len(evidence.feature_vector)},
            'confidence':evidence.sensor_confidence,'uncertainty':round(1-evidence.sensor_confidence,6),
            'context_prior':context_prior,
            'familiarity':asdict(familiarity),
            'routing_decision':'FAMILIAR_FAST_PATH' if familiarity.outcome=='KNOWN_HIGH_CONFIDENCE' else ('CONFIRMATION_PATH' if familiarity.outcome=='KNOWN_NEEDS_CONFIRMATION' else 'DEEP_PERCEPTION_ESCALATION'),
            'epistemic_state':'CONFLICT' if familiarity.outcome=='CONFLICT' else ('KNOWN' if familiarity.outcome.startswith('KNOWN') else 'UNKNOWN'),
            'authority':'OBSERVATION_ONLY',
        }

    def to_spine_visual(self,evidence:PixelEvidence,familiarity:FamiliarityResult):
        return {
            'source_id':evidence.source_id,'capture_epoch':evidence.capture_epoch,
            'features':{'pixel_feature_hash':h(list(evidence.feature_vector)),'frame_hash':evidence.frame_hash,'change_score':evidence.change_score,'changed':evidence.changed,'feature_version':evidence.feature_version},
            'sensor_confidence':evidence.sensor_confidence,
            'candidate_label':familiarity.candidate_label,
            'prototype_similarity':max(0.0,min(1.0,(familiarity.similarity+1)/2)),
            'sensor_conflict':familiarity.outcome=='CONFLICT',
            'retina_outcome':familiarity.outcome,
        }
