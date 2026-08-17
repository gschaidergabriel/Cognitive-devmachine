import hashlib,sqlite3,threading,time
import pytest
from clayverse.engine import ClayVerseEngine
from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.store import UnifiedDB


def _legacy_turns_table(conn, *, compression_generation):
    conn.executescript("""
    CREATE TABLE turns(
      turn_id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      ordinal INTEGER NOT NULL,
      ts REAL NOT NULL,
      role TEXT NOT NULL,
      content TEXT NOT NULL,
      fidelity TEXT NOT NULL DEFAULT 'full',
      compression_generation INTEGER NOT NULL DEFAULT 0,
      resource_refs TEXT NOT NULL DEFAULT '[]',
      causal_refs TEXT NOT NULL DEFAULT '[]',
      provenance TEXT NOT NULL DEFAULT '{}',
      UNIQUE(session_id, ordinal)
    );
    """)
    conn.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,fidelity,compression_generation) VALUES(?,?,?,?,?,?,?,?,?)",
        ('old','legacy-session','gabriel',1,0.0,'user','legacy raw source','full' if compression_generation == 0 else 'detailed_summary',compression_generation),
    )
    conn.commit()


def test_compression_preserves_immutable_raw_turn_ledger(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); mm=MemoryManager(db); originals=[]; tids=[]
    for i in range(45):
        text='FACT: '+' '.join(f'raw-{i}-{j}' for j in range(100)); originals.append(text); tids.append(db.append_turn(sid,uid,'user',text))
    assert mm.compact(sid)>0
    projected=db.all_turns(sid)[0]['content']; ledger=db.raw_turn(tids[0])
    assert projected!=originals[0]
    assert ledger['raw_content']==originals[0]
    assert ledger['raw_sha256']==hashlib.sha256(originals[0].encode()).hexdigest()
    with pytest.raises(sqlite3.DatabaseError): db.db.execute("UPDATE turn_ledger SET raw_content='tampered' WHERE turn_id=?",(tids[0],))
    with pytest.raises(sqlite3.DatabaseError): db.db.execute("DELETE FROM turn_ledger WHERE turn_id=?",(tids[0],))
    db.close()


def test_v1_lossy_migration_fails_closed_before_inventing_raw_source(tmp_path):
    p=tmp_path/'v1-lossy.db'; raw=sqlite3.connect(p); _legacy_turns_table(raw,compression_generation=1); raw.close()
    with pytest.raises(RuntimeError,match='cannot migrate compressed turns without immutable raw ledger'):
        UnifiedDB(p)
    check=sqlite3.connect(p)
    assert check.execute('SELECT COUNT(*) FROM turn_ledger').fetchone()[0]==0
    check.close()


def test_v1_lossless_migration_backfills_exact_raw_bytes(tmp_path):
    p=tmp_path/'v1-lossless.db'; raw=sqlite3.connect(p); _legacy_turns_table(raw,compression_generation=0); raw.close()
    db=UnifiedDB(p); ledger=db.raw_turn('old')
    assert ledger['raw_content']=='legacy raw source'
    assert ledger['raw_sha256']==hashlib.sha256(b'legacy raw source').hexdigest()
    assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]=='2'
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
    for t in threads: t.start()
    for t in threads: t.join()
    assert not errors and probe.max_active==1
    assert db.db.execute('SELECT COUNT(*) FROM causal_episodes WHERE reentered=1').fetchone()[0]==2
    assert db.db.execute('SELECT COUNT(*) FROM turn_ledger').fetchone()[0]==4
    db.close()
