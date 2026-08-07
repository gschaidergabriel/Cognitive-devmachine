#!/usr/bin/env python3
"""Build a rebuildable embedded SQLite materialization of the RAE research graph.

Git/raw source archives/append-only ledgers remain canonical. SQLite is a DERIVED CACHE:
it may be deleted and reconstructed at any time. Direct text sources plus text derivatives
extracted from PDFs/ZIPs are indexed together, content-deduplicated by SHA-256.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEXT_ROOT=ROOT/'research_sources'/'text'
DERIVED_ROOT=ROOT/'research_sources'/'derived'
CLAIMS=ROOT/'research_entity'/'ledgers'/'CLAIMS.jsonl'
CLAIM_STATUS=ROOT/'research_entity'/'ledgers'/'CLAIM_STATUS_EVENTS.jsonl'
EVENTS=ROOT/'research_entity'/'events'
PACKETS=ROOT/'research_entity'/'topic_packets'
TEXT_EXTS={'.txt','.md','.json','.jsonl','.csv','.tsv','.py','.sh','.yaml','.yml','.toml','.ini','.cfg','.conf','.sql','.xml','.html','.js','.ts','.cc','.c','.h','.hpp','.rs','.go','.java','.ebnf','.log'}

SCHEMA='''
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY,path TEXT UNIQUE,sha256 TEXT,bytes INTEGER,text TEXT);
CREATE TABLE IF NOT EXISTS source_alias(source_id TEXT,path TEXT,kind TEXT,PRIMARY KEY(source_id,path));
CREATE TABLE IF NOT EXISTS chunks(chunk_id TEXT PRIMARY KEY,source_id TEXT,ordinal INTEGER,text TEXT,FOREIGN KEY(source_id) REFERENCES sources(source_id));
CREATE TABLE IF NOT EXISTS claims(claim_id TEXT PRIMARY KEY,first_status TEXT,scope TEXT,proposition TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS claim_status_events(event_id TEXT PRIMARY KEY,claim_id TEXT,timestamp TEXT,from_status TEXT,to_status TEXT,reason TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS claim_current_status(claim_id TEXT PRIMARY KEY,status TEXT,timestamp TEXT,status_event_id TEXT);
CREATE TABLE IF NOT EXISTS claim_evidence(claim_id TEXT,evidence_ref TEXT,PRIMARY KEY(claim_id,evidence_ref));
CREATE TABLE IF NOT EXISTS claim_topic(claim_id TEXT,packet_id TEXT,PRIMARY KEY(claim_id,packet_id));
CREATE TABLE IF NOT EXISTS claim_domain(claim_id TEXT,domain_id TEXT,PRIMARY KEY(claim_id,domain_id));
CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,event_type TEXT,status TEXT,prompt_id TEXT,reasoning_summary TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS event_parent(event_id TEXT,parent_event_id TEXT,PRIMARY KEY(event_id,parent_event_id));
CREATE TABLE IF NOT EXISTS event_source(event_id TEXT,source_ref TEXT,PRIMARY KEY(event_id,source_ref));
CREATE TABLE IF NOT EXISTS event_topic(event_id TEXT,packet_id TEXT,PRIMARY KEY(event_id,packet_id));
CREATE TABLE IF NOT EXISTS event_domain(event_id TEXT,domain_id TEXT,PRIMARY KEY(event_id,domain_id));
CREATE TABLE IF NOT EXISTS packets(packet_id TEXT PRIMARY KEY,status TEXT,title TEXT,summary TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS packet_domain(packet_id TEXT,domain_id TEXT,PRIMARY KEY(packet_id,domain_id));
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(chunk_id,source_id,text);
CREATE VIRTUAL TABLE IF NOT EXISTS claim_fts USING fts5(claim_id,status,scope,proposition);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_source_alias_source ON source_alias(source_id);
CREATE INDEX IF NOT EXISTS idx_claim_status ON claim_current_status(status);
CREATE INDEX IF NOT EXISTS idx_claim_topic_packet ON claim_topic(packet_id);
CREATE INDEX IF NOT EXISTS idx_claim_domain_domain ON claim_domain(domain_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_event_prompt ON events(prompt_id);
CREATE VIEW IF NOT EXISTS current_claims AS
  SELECT c.*, s.status AS current_status, s.timestamp AS status_timestamp
  FROM claims c LEFT JOIN claim_current_status s USING(claim_id)
  WHERE COALESCE(s.status,c.first_status)='CURRENT';
CREATE VIEW IF NOT EXISTS open_claims AS
  SELECT c.*, s.status AS current_status, s.timestamp AS status_timestamp
  FROM claims c LEFT JOIN claim_current_status s USING(claim_id)
  WHERE COALESCE(s.status,c.first_status)='OPEN';
'''


def jsonl(p):
    if not p.exists(): return []
    out=[]
    for lineno,line in enumerate(p.read_text(encoding='utf-8',errors='strict').splitlines(),1):
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except Exception as e: raise RuntimeError(f'{p}:{lineno}: {e}') from e
    return out


def text_sources():
    if TEXT_ROOT.exists():
        for p in sorted(TEXT_ROOT.rglob('*')):
            if p.is_file(): yield 'text',p
    if DERIVED_ROOT.exists():
        for p in sorted(DERIVED_ROOT.rglob('*')):
            if not p.is_file(): continue
            posix=p.as_posix()
            if p.name=='document.txt' or '/text/' in posix or p.suffix.lower() in TEXT_EXTS:
                yield 'derived',p


def chunks(text, max_chars=5000):
    paras=[re.sub(r'\s+',' ',x).strip() for x in re.split(r'\n\s*\n+',text) if x.strip()]
    cur=[]; n=0
    for p in paras:
        if cur and n+len(p)>max_chars:
            yield '\n\n'.join(cur); cur=[]; n=0
        cur.append(p); n+=len(p)
    if cur: yield '\n\n'.join(cur)


def reset(con):
    for t in ['sources','source_alias','chunks','chunk_fts','claims','claim_fts','claim_status_events','claim_current_status','claim_evidence','claim_topic','claim_domain','events','event_parent','event_source','event_topic','event_domain','packets','packet_domain']:
        con.execute(f'DELETE FROM {t}')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(ROOT/'research_sources'/'sources.db'))
    args=ap.parse_args(); db=Path(args.db); db.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(db); con.executescript(SCHEMA); reset(con)

    seen=set()
    for kind,p in text_sources():
        data=p.read_bytes(); sha=hashlib.sha256(data).hexdigest(); sid=sha; rel=str(p.relative_to(ROOT))
        con.execute('INSERT OR IGNORE INTO source_alias VALUES(?,?,?)',(sid,rel,kind))
        if sid in seen: continue
        seen.add(sid); text=data.decode('utf-8',errors='ignore')
        con.execute('INSERT INTO sources VALUES(?,?,?,?,?)',(sid,rel,sha,len(data),text))
        for i,ch in enumerate(chunks(text)):
            cid=hashlib.sha256((sid+':'+str(i)+':'+ch).encode()).hexdigest()
            con.execute('INSERT INTO chunks VALUES(?,?,?,?)',(cid,sid,i,ch)); con.execute('INSERT INTO chunk_fts VALUES(?,?,?)',(cid,sid,ch))

    claims=jsonl(CLAIMS)
    for c in claims:
        cid=c['claim_id']
        con.execute('INSERT OR REPLACE INTO claims VALUES(?,?,?,?,?)',(cid,c.get('first_status','OPEN'),c.get('scope',''),c.get('proposition',''),json.dumps(c,ensure_ascii=False)))
        for ref in c.get('evidence_refs',[]): con.execute('INSERT OR IGNORE INTO claim_evidence VALUES(?,?)',(cid,ref))
        if c.get('experiment_ref'): con.execute('INSERT OR IGNORE INTO claim_evidence VALUES(?,?)',(cid,'experiment:'+c['experiment_ref']))
        for packet in c.get('topic_packets',[]): con.execute('INSERT OR IGNORE INTO claim_topic VALUES(?,?)',(cid,packet))
        for domain in c.get('domains',[]): con.execute('INSERT OR IGNORE INTO claim_domain VALUES(?,?)',(cid,domain))

    latest={c['claim_id']:(c.get('first_status','OPEN'),'','') for c in claims}
    for s in jsonl(CLAIM_STATUS):
        con.execute('INSERT OR REPLACE INTO claim_status_events VALUES(?,?,?,?,?,?,?)',(s['event_id'],s['claim_id'],s.get('timestamp',''),s.get('from'),s.get('to'),s.get('reason',''),json.dumps(s,ensure_ascii=False)))
        prev=latest.get(s['claim_id'])
        if prev is None or s.get('timestamp','') >= prev[1]: latest[s['claim_id']]=(s.get('to'),s.get('timestamp',''),s['event_id'])
        for ref in s.get('evidence_refs',[]): con.execute('INSERT OR IGNORE INTO claim_evidence VALUES(?,?)',(s['claim_id'],ref))
    for cid,(status,ts,eid) in latest.items():
        con.execute('INSERT OR REPLACE INTO claim_current_status VALUES(?,?,?,?)',(cid,status,ts,eid))
    for c in claims:
        status=latest[c['claim_id']][0]
        con.execute('INSERT INTO claim_fts VALUES(?,?,?,?)',(c['claim_id'],status,c.get('scope',''),c.get('proposition','')))

    if EVENTS.exists():
        for p in sorted(EVENTS.rglob('*.jsonl')):
            for e in jsonl(p):
                eid=e.get('event_id')
                if not eid: continue
                con.execute('INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?)',(eid,e.get('event_type'),e.get('status'),e.get('prompt_id'),e.get('reasoning_summary',''),json.dumps(e,ensure_ascii=False)))
                for x in e.get('parent_event_ids',[]): con.execute('INSERT OR IGNORE INTO event_parent VALUES(?,?)',(eid,x))
                for x in e.get('source_refs',[]): con.execute('INSERT OR IGNORE INTO event_source VALUES(?,?)',(eid,x))
                for x in e.get('topic_packet_ids',[]): con.execute('INSERT OR IGNORE INTO event_topic VALUES(?,?)',(eid,x))
                for x in e.get('domains',[]): con.execute('INSERT OR IGNORE INTO event_domain VALUES(?,?)',(eid,x))

    if PACKETS.exists():
        for p in sorted(PACKETS.rglob('PACKET.json')):
            x=json.loads(p.read_text(encoding='utf-8')); pid=x.get('packet_id')
            con.execute('INSERT OR REPLACE INTO packets VALUES(?,?,?,?,?)',(pid,x.get('status'),x.get('title'),x.get('summary',''),json.dumps(x,ensure_ascii=False)))
            for d in x.get('domains',[]): con.execute('INSERT OR IGNORE INTO packet_domain VALUES(?,?)',(pid,d))

    con.commit()
    stats={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['sources','source_alias','chunks','claims','claim_status_events','claim_evidence','claim_topic','claim_domain','events','packets']}
    checks={'current_claims':con.execute('SELECT COUNT(*) FROM current_claims').fetchone()[0],
      'open_claims':con.execute('SELECT COUNT(*) FROM open_claims').fetchone()[0],
      'integrity_check':con.execute('PRAGMA integrity_check').fetchone()[0]}
    con.close(); print(json.dumps({'db':str(db),'stats':stats,'checks':checks},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
