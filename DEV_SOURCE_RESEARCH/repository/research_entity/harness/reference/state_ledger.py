from __future__ import annotations
import copy, hashlib, json, sqlite3, time
from pathlib import Path

class LedgerError(RuntimeError): pass
class StaleEpoch(LedgerError): pass
class IdempotencyConflict(LedgerError): pass
class InvalidOperation(LedgerError): pass

def canon(v):
    if isinstance(v, dict):
        k=v.get('$kind')
        if k in ('set','ordered'):
            items=v.get('items',[])
            if not isinstance(items,list): raise TypeError('typed collection items must be list')
            xs=[canon(x) for x in items]
            if k=='set':
                d={json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')):x for x in xs}
                xs=[d[x] for x in sorted(d)]
            return {'$kind':k,'items':xs}
        return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,bool)): return v
    if isinstance(v,float):
        if v!=v or v in (float('inf'),float('-inf')): raise ValueError('non-finite float')
        return v
    raise TypeError(type(v).__name__)

def cjson(v): return json.dumps(canon(v),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def h(v): return hashlib.sha256(cjson(v).encode()).hexdigest()
def rawh(s): return hashlib.sha256(s.encode()).hexdigest()
def jstr(v): return json.dumps(str(v),ensure_ascii=False,separators=(',',':'))

SCHEMA='''
PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS domain_epochs(domain TEXT PRIMARY KEY,epoch INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS state(domain TEXT NOT NULL,k TEXT NOT NULL,value_json TEXT,epistemic TEXT NOT NULL,status TEXT NOT NULL,domain_epoch INTEGER NOT NULL,semantic_hash TEXT NOT NULL,PRIMARY KEY(domain,k));
CREATE INDEX IF NOT EXISTS idx_state_current_order ON state(domain,k,epistemic) WHERE status='CURRENT';
CREATE INDEX IF NOT EXISTS idx_state_key_current ON state(k,domain,epistemic) WHERE status='CURRENT';
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,idem TEXT UNIQUE NOT NULL,base_epoch INTEGER NOT NULL,epoch INTEGER UNIQUE NOT NULL,event_type TEXT NOT NULL,writer TEXT NOT NULL,ops_json TEXT NOT NULL,provenance_json TEXT NOT NULL,source_json TEXT NOT NULL,execution_json TEXT NOT NULL,semantic_event_hash TEXT NOT NULL,semantic_chain_hash TEXT NOT NULL,execution_chain_hash TEXT NOT NULL,semantic_state_hash TEXT NOT NULL,trace_root_hash TEXT NOT NULL,committed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,epoch INTEGER NOT NULL,semantic_state_hash TEXT NOT NULL,trace_root_hash TEXT NOT NULL,state_json TEXT NOT NULL,domain_epochs_json TEXT NOT NULL,semantic_chain_hash TEXT NOT NULL,execution_chain_hash TEXT NOT NULL,created_at TEXT NOT NULL);
'''
EPI={'KNOWN','UNKNOWN','CONFLICT','REVOKED'}; STAT={'CURRENT','RETRACTED','SUPERSEDED','QUARANTINED'}; OPS={'SET','RETRACT','SUPERSEDE','DELETE'}

class StateLedger:
    def __init__(self,path=':memory:'):
        self.conn=sqlite3.connect(str(path),timeout=10); self.conn.row_factory=sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON'); self.conn.execute('PRAGMA busy_timeout=10000'); self.conn.executescript(SCHEMA)
        defaults={'global_epoch':'0','semantic_chain_hash':rawh('HWP02:semantic:genesis'),'execution_chain_hash':rawh('HWP02:execution:genesis'),'semantic_state_hash':'','trace_root_hash':''}
        for k,v in defaults.items(): self.conn.execute('INSERT OR IGNORE INTO meta VALUES(?,?)',(k,v))
        if not self._m('semantic_state_hash'):
            s,t=self._roots(); self._set('semantic_state_hash',s); self._set('trace_root_hash',t)
        self.conn.commit()
    def close(self): self.conn.close()
    def __enter__(self): return self
    def __exit__(self,*_): self.close()
    def _m(self,k):
        r=self.conn.execute('SELECT v FROM meta WHERE k=?',(k,)).fetchone()
        if not r: raise LedgerError('missing meta '+k)
        return str(r[0])
    def _set(self,k,v): self.conn.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(k,str(v)))
    @property
    def epoch(self): return int(self._m('global_epoch'))
    @property
    def semantic_state_hash(self): return self._m('semantic_state_hash')
    @property
    def trace_root_hash(self): return self._m('trace_root_hash')
    def domain_epochs(self): return {r[0]:int(r[1]) for r in self.conn.execute('SELECT domain,epoch FROM domain_epochs ORDER BY domain')}
    def materialized(self):
        out=[]
        for r in self.conn.execute('SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state ORDER BY domain,k'):
            out.append({'domain':r[0],'key':r[1],'value':json.loads(r[2]) if r[2] is not None else None,'epistemic':r[3],'status':r[4],'domain_epoch':int(r[5]),'semantic_hash':r[6]})
        return out
    def _semantic_state_hash_streaming(self):
        """Byte-exact equivalent of h(canonical semantic-state object) without materializing it."""
        digest=hashlib.sha256()
        def put(s): digest.update(s.encode())
        put('{"domain_epochs":{')
        first=True
        for r in self.conn.execute('SELECT domain,epoch FROM domain_epochs ORDER BY domain'):
            if not first: put(',')
            first=False; put(jstr(r[0])); put(':'); put(str(int(r[1])))
        put('},"global_epoch":'); put(str(self.epoch))
        put(',"semantic_chain_hash":'); put(jstr(self._m('semantic_chain_hash')))
        put(',"state":[')
        first=True
        for r in self.conn.execute('SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash FROM state ORDER BY domain,k'):
            if not first: put(',')
            first=False
            put('{"domain":'); put(jstr(r[0]))
            put(',"domain_epoch":'); put(str(int(r[5])))
            put(',"epistemic":'); put(jstr(r[3]))
            put(',"key":'); put(jstr(r[1]))
            put(',"semantic_hash":'); put(jstr(r[6]))
            put(',"status":'); put(jstr(r[4]))
            put(',"value":'); put(r[2] if r[2] is not None else 'null')
            put('}')
        put(']}')
        return digest.hexdigest()
    def _roots_legacy(self):
        s=h({'global_epoch':self.epoch,'domain_epochs':self.domain_epochs(),'state':self.materialized(),'semantic_chain_hash':self._m('semantic_chain_hash')})
        return s,h({'semantic_state_hash':s,'execution_chain_hash':self._m('execution_chain_hash')})
    def _roots(self):
        s=self._semantic_state_hash_streaming()
        return s,h({'semantic_state_hash':s,'execution_chain_hash':self._m('execution_chain_hash')})
    def _norm_ops(self,ops):
        out=[]
        for x in ops:
            if not isinstance(x,dict): raise InvalidOperation('op object required')
            op=str(x.get('op','')).upper(); d=str(x.get('domain','')).strip(); k=str(x.get('key','')).strip(); epi=str(x.get('epistemic','KNOWN')).upper(); st=str(x.get('status','CURRENT')).upper(); v=copy.deepcopy(x.get('value'))
            if op not in OPS or not d or not k or epi not in EPI or st not in STAT: raise InvalidOperation('invalid op/domain/key/epistemic/status')
            if op in ('RETRACT','DELETE'): st='RETRACTED'
            elif op=='SUPERSEDE': st='SUPERSEDED'
            cjson(v); out.append({'op':op,'domain':d,'key':k,'value':v,'epistemic':epi,'status':st})
        if not out: raise InvalidOperation('empty transaction')
        return out
    def append_event(self,*,event_id,idem,base_epoch,event_type,writer,ops,provenance=None,source=None,execution=None,committed_at=None):
        ops=self._norm_ops(ops); provenance=copy.deepcopy(provenance or {}); source=copy.deepcopy(source or {}); execution=copy.deepcopy(execution or {})
        cjson(provenance); cjson(source); cjson(execution)
        seh=h({'event_type':event_type,'ops':ops}); ph=h(provenance); sh=h(source); eh=h(execution)
        fingerprint=h({'event_id':event_id,'semantic_event_hash':seh,'provenance_hash':ph,'source_hash':sh})
        old=self.conn.execute('SELECT * FROM events WHERE idem=?',(idem,)).fetchone()
        if old:
            oldfp=h({'event_id':old['event_id'],'semantic_event_hash':old['semantic_event_hash'],'provenance_hash':h(json.loads(old['provenance_json'])),'source_hash':h(json.loads(old['source_json']))})
            if oldfp!=fingerprint: raise IdempotencyConflict(idem)
            return {'status':'ALREADY_COMMITTED','epoch':int(old['epoch']),'semantic_event_hash':old['semantic_event_hash'],'semantic_state_hash':old['semantic_state_hash'],'trace_root_hash':old['trace_root_hash']}
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            cur=self.epoch
            if int(base_epoch)!=cur: raise StaleEpoch(f'{base_epoch}!={cur}')
            ne=cur+1; touched={}
            for d in sorted({x['domain'] for x in ops}):
                r=self.conn.execute('SELECT epoch FROM domain_epochs WHERE domain=?',(d,)).fetchone(); de=(int(r[0]) if r else 0)+1; touched[d]=de
                self.conn.execute('INSERT INTO domain_epochs VALUES(?,?) ON CONFLICT(domain) DO UPDATE SET epoch=excluded.epoch',(d,de))
            for x in ops:
                rh=h({'domain':x['domain'],'key':x['key'],'value':x['value'],'epistemic':x['epistemic'],'status':x['status']})
                self.conn.execute('INSERT INTO state(domain,k,value_json,epistemic,status,domain_epoch,semantic_hash) VALUES(?,?,?,?,?,?,?) ON CONFLICT(domain,k) DO UPDATE SET value_json=excluded.value_json,epistemic=excluded.epistemic,status=excluded.status,domain_epoch=excluded.domain_epoch,semantic_hash=excluded.semantic_hash',(x['domain'],x['key'],cjson(x['value']),x['epistemic'],x['status'],touched[x['domain']],rh))
            sch=h({'prev':self._m('semantic_chain_hash'),'semantic_event_hash':seh,'epoch':ne,'domain_epochs':touched})
            ech=h({'prev':self._m('execution_chain_hash'),'event_id':event_id,'idem':idem,'semantic_event_hash':seh,'provenance_hash':ph,'source_hash':sh,'execution_hash':eh,'epoch':ne})
            self._set('global_epoch',ne); self._set('semantic_chain_hash',sch); self._set('execution_chain_hash',ech); ss,tr=self._roots(); self._set('semantic_state_hash',ss); self._set('trace_root_hash',tr)
            ts=committed_at or time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
            self.conn.execute('INSERT INTO events(event_id,idem,base_epoch,epoch,event_type,writer,ops_json,provenance_json,source_json,execution_json,semantic_event_hash,semantic_chain_hash,execution_chain_hash,semantic_state_hash,trace_root_hash,committed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(event_id,idem,cur,ne,event_type,writer,cjson(ops),cjson(provenance),cjson(source),cjson(execution),seh,sch,ech,ss,tr,ts)); self.conn.commit()
            return {'status':'COMMITTED','epoch':ne,'domain_epochs':touched,'semantic_event_hash':seh,'semantic_state_hash':ss,'execution_hash':eh,'trace_root_hash':tr}
        except Exception:
            self.conn.rollback(); raise
    def get(self,domain,key):
        r=self.conn.execute('SELECT value_json,epistemic,status,domain_epoch,semantic_hash FROM state WHERE domain=? AND k=?',(domain,key)).fetchone()
        return None if not r else {'value':json.loads(r[0]) if r[0] is not None else None,'epistemic':r[1],'status':r[2],'domain_epoch':int(r[3]),'semantic_hash':r[4]}
    def export_events(self):
        out=[]
        for r in self.conn.execute('SELECT * FROM events ORDER BY seq'):
            out.append({'event_id':r['event_id'],'idem':r['idem'],'base_epoch':int(r['base_epoch']),'event_type':r['event_type'],'writer':r['writer'],'ops':json.loads(r['ops_json']),'provenance':json.loads(r['provenance_json']),'source':json.loads(r['source_json']),'execution':json.loads(r['execution_json']),'committed_at':r['committed_at']})
        return out
    @classmethod
    def replay(cls,events,path=':memory:'):
        x=cls(path)
        for e in events: x.append_event(**e)
        return x
    def snapshot(self,sid):
        state=self.materialized(); deps=self.domain_epochs(); s=self.semantic_state_hash; t=self.trace_root_hash; ts=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        self.conn.execute('INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?,?,?,?,?,?)',(sid,self.epoch,s,t,cjson(state),cjson(deps),self._m('semantic_chain_hash'),self._m('execution_chain_hash'),ts)); self.conn.commit(); return {'id':sid,'epoch':self.epoch,'semantic_state_hash':s,'trace_root_hash':t}
    def verify_snapshot(self,sid):
        r=self.conn.execute('SELECT * FROM snapshots WHERE id=?',(sid,)).fetchone()
        if not r: return False
        basis={'global_epoch':int(r['epoch']),'domain_epochs':json.loads(r['domain_epochs_json']),'state':json.loads(r['state_json']),'semantic_chain_hash':r['semantic_chain_hash']}; s=h(basis); t=h({'semantic_state_hash':s,'execution_chain_hash':r['execution_chain_hash']})
        return s==r['semantic_state_hash'] and t==r['trace_root_hash']
