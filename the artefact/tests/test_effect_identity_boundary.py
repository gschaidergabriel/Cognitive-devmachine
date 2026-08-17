import uuid
import pytest

from clayverse.effects import EffectGate,EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def test_effect_rejects_cross_user_session_binding(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    try:
        router=IdentityRouter(db,{'g':'gabriel','a':'andreas'})
        gabriel,gabriel_session=router.resolve('g')
        andreas,_=router.resolve('a')
        gate=EffectGate(db)
        lease=db.acquire_lease('effect:same-user','worker',60)
        effect_id,outcome=gate.execute(EffectRequest(gabriel,gabriel_session,'state.noop','same-user',None,db.session_generation(gabriel_session),{'source':'test','request_id':uuid.uuid4().hex}),lease=lease)
        assert effect_id and outcome['ok']; db.release_lease(lease)

        with pytest.raises(PermissionError,match='session owner mismatch'):
            gate.execute(EffectRequest(andreas,gabriel_session,'state.noop','cross-user'))

        assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==1
    finally:
        db.close()
