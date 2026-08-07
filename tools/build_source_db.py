#!/usr/bin/env python3
"""Build a local SQLite research-source database from archived text, claims, events and topic packets.

The database is a DERIVED CACHE. Git/ledgers/raw archives remain canonical. It is safe to delete and rebuild.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEXT_ROOT=ROOT/'research_sources'/'text'
CLAIMS=ROOT/'research_entity'/'ledgers'/'CLAIMS.jsonl'
EVENTS=ROOT/'research_entity'/'events'
PACKETS=ROOT/'research_entity'/'topic_packets'

SCHEMA='''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY,path TEXT,sha256 TEXT,bytes INTEGER,text TEXT);
CREATE TABLE IF NOT EXISTS chunks(chunk_id TEXT PRIMARY KEY,source_id TEXT,ordinal INTEGER,text TEXT,FOREIGN KEY(source_id) REFERENCES sources(source_id));
CREATE TABLE IF NOT EXISTS claims(claim_id TEXT PRIMARY KEY,status TEXT,scope TEXT,proposition TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,event_type TEXT,status TEXT,prompt_id TEXT,reasoning_summary TEXT,json TEXT);
CREATE TABLE IF NOT EXISTS packets(packet_id TEXT PRIMARY KEY,status TEXT,title TEXT,summary TEXT,json TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(chunk_id,source_id,text);
CREATE VIRTUAL TABLE IF NOT EXISTS claim_fts USING fts5(claim_id,status,scope,proposition);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id,ordinal);
'''

def jsonl(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
        if line.strip():
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def chunks(text, max_chars=5000):
    paras=[re.sub(r'\s+',' ',x).strip() for x in re.split(r'\n\s*\n+',text) if x.strip()]
    cur=[]; n=0
    for p in paras:
        if cur and n+len(p)>max_chars:
            yield '\n\n'.join(cur); cur=[]; n=0
        cur.append(p); n+=len(p)
    if cur: yield '\n\n'.join(cur)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(ROOT/'research_sources'/'sources.db'))
    args=ap.parse_args(); db=Path(args.db); db.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(db); con.executescript(SCHEMA)
    con.execute('DELETE FROM sources'); con.execute('DELETE FROM chunks'); con.execute('DELETE FROM chunk_fts'); con.execute('DELETE FROM claims'); con.execute('DELETE FROM claim_fts'); con.execute('DELETE FROM events'); con.execute('DELETE FROM packets')
    for p in sorted(TEXT_ROOT.rglob('*')) if TEXT_ROOT.exists() else []:
        if not p.is_file(): continue
        data=p.read_bytes(); text=data.decode('utf-8',errors='ignore'); sha=hashlib.sha256(data).hexdigest(); sid=sha
        con.execute('INSERT INTO sources VALUES(?,?,?,?,?)',(sid,str(p.relative_to(ROOT)),sha,len(data),text))
        for i,ch in enumerate(chunks(text)):
            cid=hashlib.sha256((sid+':'+str(i)+':'+ch).encode()).hexdigest()
            con.execute('INSERT INTO chunks VALUES(?,?,?,?)',(cid,sid,i,ch)); con.execute('INSERT INTO chunk_fts VALUES(?,?,?)',(cid,sid,ch))
    for c in jsonl(CLAIMS):
        con.execute('INSERT OR REPLACE INTO claims VALUES(?,?,?,?,?)',(c['claim_id'],c.get('first_status','OPEN'),c.get('scope',''),c.get('proposition',''),json.dumps(c,ensure_ascii=False)))
        con.execute('INSERT INTO claim_fts VALUES(?,?,?,?)',(c['claim_id'],c.get('first_status','OPEN'),c.get('scope',''),c.get('proposition','')))
    if EVENTS.exists():
        for p in EVENTS.rglob('*.jsonl'):
            for e in jsonl(p):
                con.execute('INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?)',(e.get('event_id'),e.get('event_type'),e.get('status'),e.get('prompt_id'),e.get('reasoning_summary',''),json.dumps(e,ensure_ascii=False)))
    if PACKETS.exists():
        for p in PACKETS.rglob('PACKET.json'):
            try: x=json.loads(p.read_text(encoding='utf-8'))
            except Exception: continue
            con.execute('INSERT OR REPLACE INTO packets VALUES(?,?,?,?,?)',(x.get('packet_id'),x.get('status'),x.get('title'),x.get('summary',''),json.dumps(x,ensure_ascii=False)))
    con.commit()
    stats={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['sources','chunks','claims','events','packets']}
    con.close(); print(json.dumps({'db':str(db),'stats':stats},indent=2))
if __name__=='__main__': main()
