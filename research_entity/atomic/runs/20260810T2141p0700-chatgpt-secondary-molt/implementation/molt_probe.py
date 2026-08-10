#!/usr/bin/env python3
import hashlib, json, os, random, struct, tempfile, time
from pathlib import Path

PREFIX_SIZE = 4096
PREFIX_MAGIC = b'MOLTIMG1'
FRAME_MAGIC = b'MOLTRCD1'
COMMIT = b'MOLTCMT1'
ZERO_HEAD = '0'*64

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def canon(obj) -> bytes: return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()

def build_prefix(root_bytes: bytes, model_bytes: bytes=b'') -> bytes:
    manifest={'schema':1,'root_sha256':sha(root_bytes),'model_sha256':sha(model_bytes),'root_len':len(root_bytes),'model_len':len(model_bytes)}
    mb=canon(manifest); body=PREFIX_MAGIC+struct.pack('>I',len(mb))+mb+root_bytes+model_bytes
    if len(body)>PREFIX_SIZE: raise ValueError('prefix too large')
    return body+b'\0'*(PREFIX_SIZE-len(body))

def parse_prefix(data: bytes):
    if len(data)<PREFIX_SIZE or data[:8]!=PREFIX_MAGIC: raise ValueError('bad prefix')
    n=struct.unpack('>I',data[8:12])[0]; manifest=json.loads(data[12:12+n]); pos=12+n
    root=data[pos:pos+manifest['root_len']]; pos+=manifest['root_len']; model=data[pos:pos+manifest['model_len']]
    if sha(root)!=manifest['root_sha256'] or sha(model)!=manifest['model_sha256']: raise ValueError('immutable hash mismatch')
    return manifest,sha(canon(manifest))

def make_frame(root_id,epoch,prev_head,tx_id,payload_obj):
    payload=canon(payload_obj); payload_hash=sha(payload)
    state_head=sha((prev_head+payload_hash+tx_id+str(epoch)+root_id).encode())
    hdr={'schema':1,'root_id':root_id,'epoch':epoch,'prev_head':prev_head,'state_head':state_head,'tx_id':tx_id,'payload_sha256':payload_hash,'payload_len':len(payload)}
    hb=canon(hdr); pre=FRAME_MAGIC+struct.pack('>II',len(hb),len(payload))+hb+payload
    return pre+hashlib.sha256(pre).digest()+COMMIT

def recover(path):
    data=Path(path).read_bytes(); manifest,root_id=parse_prefix(data[:PREFIX_SIZE]); pos=PREFIX_SIZE; epoch=0; head=ZERO_HEAD; state={}; valid_frames=0; tail_status='CLEAN'
    while pos<len(data):
        start=pos
        if len(data)-pos<16 or data[pos:pos+8]!=FRAME_MAGIC: tail_status='QUARANTINED_SUFFIX'; break
        hlen,plen=struct.unpack('>II',data[pos+8:pos+16]); total=16+hlen+plen+32+8
        if len(data)-pos<total: tail_status='TRUNCATED_SUFFIX'; break
        hb=data[pos+16:pos+16+hlen]; payload=data[pos+16+hlen:pos+16+hlen+plen]; frame_hash=data[pos+16+hlen+plen:pos+16+hlen+plen+32]; commit=data[pos+total-8:pos+total]; pre=data[pos:pos+16+hlen+plen]
        if commit!=COMMIT or hashlib.sha256(pre).digest()!=frame_hash: tail_status='CORRUPT_SUFFIX'; break
        try: hdr=json.loads(hb); payload_obj=json.loads(payload)
        except Exception: tail_status='CORRUPT_SUFFIX'; break
        if hdr.get('root_id')!=root_id or hdr.get('epoch')!=epoch+1 or hdr.get('prev_head')!=head: tail_status='CHAIN_REJECTED'; break
        if hdr.get('payload_len')!=len(payload) or hdr.get('payload_sha256')!=sha(payload): tail_status='CORRUPT_SUFFIX'; break
        expected_head=sha((head+hdr['payload_sha256']+hdr['tx_id']+str(hdr['epoch'])+root_id).encode())
        if hdr.get('state_head')!=expected_head: tail_status='CHAIN_REJECTED'; break
        if set(payload_obj)-{'set','delete'}: tail_status='SEMANTIC_REJECTED'; break
        for k,v in payload_obj.get('set',{}).items():
            if k.startswith('__root') or k.startswith('__model') or k.startswith('__authority'):
                return {'root_id':root_id,'epoch':epoch,'head':head,'state':state,'valid_frames':valid_frames,'tail_status':'SEMANTIC_REJECTED'}
            state[k]=v
        for k in payload_obj.get('delete',[]): state.pop(k,None)
        epoch=hdr['epoch']; head=hdr['state_head']; valid_frames+=1; pos=start+total
    return {'root_id':root_id,'epoch':epoch,'head':head,'state':state,'valid_frames':valid_frames,'tail_status':tail_status}

def init_image(path,root_bytes=b'ROOT-RUNTIME',model_bytes=b'MODEL-WEIGHTS'):
    Path(path).write_bytes(build_prefix(root_bytes,model_bytes)); return recover(path)

def append_tx(path,payload_obj,tx_id):
    rec=recover(path)
    if rec['tail_status']!='CLEAN': raise RuntimeError('tail not clean')
    frame=make_frame(rec['root_id'],rec['epoch']+1,rec['head'],tx_id,payload_obj); fd=os.open(path,os.O_WRONLY|os.O_APPEND)
    try:
        n=os.write(fd,frame)
        if n!=len(frame): raise OSError('short write')
        os.fsync(fd)
    finally: os.close(fd)
    return frame

def crash_cut_matrix():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'self.root.udb'); init_image(p); append_tx(p,{'set':{'counter':1}},'tx1'); before=recover(p)
        full=make_frame(before['root_id'],2,before['head'],'tx2',{'set':{'counter':2}}); base=Path(p).read_bytes(); failures=[]; fully_committed=rolled_back=0
        for cut in range(len(full)+1):
            q=os.path.join(td,f'c{cut}.udb'); Path(q).write_bytes(base+full[:cut]); r=recover(q)
            ok=(r['epoch']==1 and r['state'].get('counter')==1) or (cut==len(full) and r['epoch']==2 and r['state'].get('counter')==2)
            if not ok: failures.append((cut,r))
            if r['epoch']==2: fully_committed+=1
            else: rolled_back+=1
        return {'frame_bytes':len(full),'cuts':len(full)+1,'failures':len(failures),'fully_committed':fully_committed,'rolled_back':rolled_back,'sample_failure':failures[:1]}

def corruption_matrix(seed=1,n=2000):
    rng=random.Random(seed)
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'x.udb'); init_image(p)
        for i in range(1,6): append_tx(p,{'set':{'counter':i}},f'tx{i}')
        original=bytearray(Path(p).read_bytes()); root_fail_closed=state_no_fabrication=state_total=undetected=0; base_rec=recover(p)
        for _ in range(n):
            d=bytearray(original); idx=rng.randrange(len(d)); d[idx]^=1<<rng.randrange(8); q=os.path.join(td,'f.udb'); Path(q).write_bytes(d)
            try:
                r=recover(q)
                if idx<PREFIX_SIZE:
                    if r['root_id']!=base_rec['root_id']: undetected+=1
                else:
                    state_total+=1
                    if 0<=r['epoch']<=5 and r['state'].get('counter',0)==r['epoch']: state_no_fabrication+=1
                    else: undetected+=1
            except Exception:
                if idx<PREFIX_SIZE: root_fail_closed+=1
                else: state_total+=1; state_no_fabrication+=1
        return {'mutations':n,'root_fail_closed':root_fail_closed,'state_cases':state_total,'state_no_fabrication':state_no_fabrication,'undetected_or_bad':undetected}

def attack_geometry():
    with tempfile.TemporaryDirectory() as td:
        naive=os.path.join(td,'naive.udb'); init_image(naive); before=Path(naive).read_bytes()[:PREFIX_SIZE]; fd=os.open(naive,os.O_RDWR)
        try: os.pwrite(fd,b'ATTACK',0); os.fsync(fd)
        finally: os.close(fd)
        naive_prefix_changed=Path(naive).read_bytes()[:PREFIX_SIZE]!=before
        append=os.path.join(td,'append.udb'); init_image(append); before2=Path(append).read_bytes()[:PREFIX_SIZE]; fd=os.open(append,os.O_WRONLY|os.O_APPEND)
        try: os.pwrite(fd,b'ATTACK',0); os.fsync(fd)
        finally: os.close(fd)
        return {'naive_odrdw_prefix_changed':naive_prefix_changed,'o_append_pwrite_prefix_changed':Path(append).read_bytes()[:PREFIX_SIZE]!=before2,'o_append_file_growth':os.path.getsize(append)-PREFIX_SIZE}

class AppendBroker:
    def __init__(self,path):
        r=recover(path)
        if r['tail_status']!='CLEAN': raise RuntimeError('unclean tail')
        self.root_id=r['root_id']; self.epoch=r['epoch']; self.head=r['head']; self.fd=os.open(path,os.O_WRONLY|os.O_APPEND)
    def close(self): os.close(self.fd)
    def commit(self,payload_obj,tx_id,sync=True):
        frame=make_frame(self.root_id,self.epoch+1,self.head,tx_id,payload_obj); n=os.write(self.fd,frame)
        if n!=len(frame): raise OSError('short write')
        if sync: os.fsync(self.fd)
        payload=canon(payload_obj); ph=sha(payload); self.epoch+=1; self.head=sha((self.head+ph+tx_id+str(self.epoch)+self.root_id).encode()); return len(frame)

def benchmark(n=500):
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'m.udb'); init_image(p); b=AppendBroker(p); t0=time.perf_counter_ns(); total=0
        for i in range(n): total+=b.commit({'set':{'counter':i}},f'tx{i}',sync=True)
        t1=time.perf_counter_ns(); b.close(); r0=time.perf_counter_ns(); r=recover(p); r1=time.perf_counter_ns()
        q=os.path.join(td,'simple.log'); fd=os.open(q,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_APPEND,0o600); s0=time.perf_counter_ns(); simple_bytes=0
        for i in range(n):
            bb=(json.dumps({'epoch':i+1,'counter':i},separators=(',',':'))+'\n').encode(); simple_bytes+=os.write(fd,bb); os.fsync(fd)
        s1=time.perf_counter_ns(); os.close(fd)
        u=os.path.join(td,'m_nosync.udb'); init_image(u); ub=AppendBroker(u); c0=time.perf_counter_ns()
        for i in range(n): ub.commit({'set':{'counter':i}},f'tx{i}',sync=False)
        c1=time.perf_counter_ns(); os.fsync(ub.fd); ub.close()
        return {'n':n,'molt_durable_total_ms':(t1-t0)/1e6,'molt_durable_mean_us':(t1-t0)/n/1e3,'simple_durable_total_ms':(s1-s0)/1e6,'simple_durable_mean_us':(s1-s0)/n/1e3,'durable_slowdown_ratio':(t1-t0)/(s1-s0),'molt_framing_mean_us_no_fsync':(c1-c0)/n/1e3,'recovery_ms':(r1-r0)/1e6,'molt_bytes_per_tx':total/n,'simple_bytes_per_tx':simple_bytes/n,'epoch':r['epoch']}

def semantic_controls():
    with tempfile.TemporaryDirectory() as td:
        p=os.path.join(td,'x.udb'); init_image(p); b=AppendBroker(p); b.commit({'set':{'counter':1}},'tx1'); b.close(); base=Path(p).read_bytes(); r=recover(p)
        bad=make_frame(r['root_id'],2,r['head'],'tx2',{'set':{'__root_override':'evil'}}); q=os.path.join(td,'bad.udb'); Path(q).write_bytes(base+bad); rb=recover(q)
        dup=make_frame(r['root_id'],1,ZERO_HEAD,'tx1',{'set':{'counter':1}}); z=os.path.join(td,'dup.udb'); Path(z).write_bytes(base+dup); rz=recover(z)
        return {'forbidden_root_semantic_status':rb['tail_status'],'forbidden_root_epoch_admitted':rb['epoch'],'replay_status':rz['tail_status'],'replay_epoch_admitted':rz['epoch']}

def main():
    out={'schema_version':'1.0','candidate':'ATOMIC-CANDIDATE-MOLT-001','evidence_class':'LOCAL_LINUX_USERSPACE_SIMULATION','kernel':os.uname().release,'attack_geometry':attack_geometry(),'crash_cut_matrix':crash_cut_matrix(),'corruption_matrix':corruption_matrix(),'benchmark':benchmark(300),'semantic_controls':semantic_controls()}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
