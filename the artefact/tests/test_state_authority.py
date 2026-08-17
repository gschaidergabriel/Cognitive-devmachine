import hashlib,sqlite3,threading,time
import pytest
from clayverse.engine import ClayVerseEngine
from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.store import UnifiedDB


def test_compression_preserves_immutable_raw_turn_ledger(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); mm=MemoryManager(db); originals=[]; tids=[]
    for i in range(45):
        text=f'turn {i} '+('raw-payload ' * 50); originals.append(text); tids.append(db.append_turn(sid,uid,'user',text))
    assert mm.compact(sid)>0
    projected=db.all_turns(sid)[0]['content']; ledger=db.raw_turn(tids[0])
    assert projected!=originals[0]
    assert ledger['raw_content']==originals[0]
    assert ledger['raw_sha256']==hashlib.sha256(originals[0].encode()).hexdigest()
    with pytest.raises(sqlite3.DatabaseError): db.db.execute("UPDATE turn_ledger SET raw_content='tampered' WHERE turn_id=?",(tids[0],))
    db.close()


def test_v1_lossy_migration_fails_closed(tmp_path):
    p=tmp_path/'v1.db'; raw=sqlite3.connect(p)
    raw.executescript("""
    CREATE TABLE turns(turn_id TEXT PRIMARY KEY,content TEXT NOT NULL,compression_generation INTEGER NOT NULL DEFAULT 0);
    INSERT INTO turns VALUES('old','already compressed',1);
    """); raw.close()
    with pytest.raises(RuntimeError,match='cannot migrate compressed turns'):
        UnifiedDB(p)


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
