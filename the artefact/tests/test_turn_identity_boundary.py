import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def test_turn_write_rejects_cross_user_session_binding(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db')
    try:
        router=IdentityRouter(db,{'g':'gabriel','a':'andreas'})
        gabriel,gabriel_session=router.resolve('g')
        andreas,_=router.resolve('a')

        with pytest.raises(PermissionError,match='session/user identity mismatch'):
            db.append_turn(gabriel_session,andreas,'user','cross-user turn injection')

        turn_id=db.append_turn(gabriel_session,gabriel,'user','same-user turn')
        assert turn_id
        rows=db.all_turns(gabriel_session)
        assert len(rows)==1 and rows[0]['user_id']=='gabriel'
    finally:
        db.close()
