"""One bounded unusual experiment: crash/reopen ABA fencing across the two user perspectives."""
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
import time,pytest
def test_cross_user_crash_reopen_aba_fence(tmp_path):
    p=tmp_path/'u.db'; db=UnifiedDB(p); r=IdentityRouter(db,{'g':'gabriel','a':'andreas'}); g,gs=r.resolve('g'); a,as_=r.resolve('a'); old=db.acquire_lease('shared:deploy','gabriel-worker',ttl=.01); db.close(); time.sleep(.02); db=UnifiedDB(p); new=db.acquire_lease('shared:deploy','andreas-worker',ttl=5)
    with pytest.raises(StaleGeneration): db.assert_lease(old)
    db.assert_lease(new); db.bump_generation(gs); _,digest=db.checkpoint('post-aba-fence'); assert len(digest)==64; db.close()
