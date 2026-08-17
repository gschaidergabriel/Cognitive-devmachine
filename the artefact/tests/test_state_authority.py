import sqlite3
import threading
import time

from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


def test_fresh_unifieddb_has_no_hidden_raw_turn_ledger(tmp_path):
    db=UnifiedDB(tmp_path/'u.db')
    tables={row[0] for row in db.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert 'turn_ledger' not in tables
    assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]=='3'
    db.close()


def test_rejected_v2_raw_turn_ledger_is_removed_on_open(tmp_path):
    p=tmp_path/'rejected-v2.db'; raw=sqlite3.connect(p)
    raw.executescript("""
    CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    INSERT INTO meta VALUES('schema_version','2');
    CREATE TABLE turn_ledger(turn_id TEXT PRIMARY KEY,raw_content TEXT NOT NULL,raw_sha256 TEXT NOT NULL,recorded_at REAL NOT NULL);
    INSERT INTO turn_ledger VALUES('old','hidden full transcript','bad',0);
    """); raw.close()
    db=UnifiedDB(p)
    assert db.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='turn_ledger'").fetchone() is None
    assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]=='3'
    db.close()


class _ConcurrencyProbe:
    def __init__(self): self.lock=threading.Lock(); self.active=0; self.max_active=0
    def reason(self,world,observation):
        with self.lock:
            self.active+=1; self.max_active=max(self.max_active,self.active)
        time.sleep(.03)
        with self.lock: self.active-=1
        return {'text':f'ack:{observation}','selection':'respond','effect':None}


def test_central_entity_turns_are_serialized_across_users(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); probe=_ConcurrencyProbe(); engine=ClayVerseEngine(db,{'g':'gabriel','a':'andreas'},inference=probe); errors=[]
    def run(subject,text):
        try: engine.ingest(subject,text)
        except Exception as exc: errors.append(exc)
    threads=[threading.Thread(target=run,args=('g','one')),threading.Thread(target=run,args=('a','two'))]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert not errors and probe.max_active==1
    assert db.db.execute('SELECT COUNT(*) FROM causal_episodes WHERE reentered=1').fetchone()[0]==2
    assert db.db.execute('SELECT COUNT(*) FROM turns').fetchone()[0]==4
    db.close()
