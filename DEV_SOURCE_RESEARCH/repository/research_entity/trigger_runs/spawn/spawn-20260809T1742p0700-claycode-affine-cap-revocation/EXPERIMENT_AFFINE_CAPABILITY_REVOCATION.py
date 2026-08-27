import json, os, random, tempfile

SEED = 202608091742
rng = random.Random(SEED)

class Registry:
    def __init__(self):
        self.slots = {}
        self.next_slot = 1
    def grant(self, right, mode='own'):
        slot = self.next_slot; self.next_slot += 1
        self.slots[slot] = {'generation': 1, 'live': True, 'right': right, 'mode': mode}
        return (slot, 1, right, mode)
    def borrow(self, owner):
        slot, gen, right, _ = owner
        cur = self.slots[slot]
        if not cur['live'] or cur['generation'] != gen: raise RuntimeError('stale owner')
        return (slot, gen, right, 'borrow')
    def revoke(self, handle):
        slot, gen, *_ = handle
        cur = self.slots[slot]
        if cur['generation'] == gen:
            cur['live'] = False
            cur['generation'] += 1
    def regrant(self, slot, right):
        cur = self.slots[slot]
        cur['generation'] += 1
        cur['live'] = True
        cur['right'] = right
        cur['mode'] = 'own'
        return (slot, cur['generation'], right, 'own')
    def transfer(self, owner):
        slot, gen, right, mode = owner
        if mode != 'own': raise RuntimeError('borrow cannot transfer')
        cur = self.slots[slot]
        if not cur['live'] or cur['generation'] != gen: raise RuntimeError('stale owner')
        cur['generation'] += 1
        return (slot, cur['generation'], right, 'own')
    def authorize(self, handle, required_right):
        slot, gen, right, mode = handle
        cur = self.slots.get(slot)
        return bool(cur and cur['live'] and cur['generation'] == gen and right == required_right and cur['right'] == required_right)

N = 100_000
counts = {k:0 for k in ['no_change','revoke','regrant','transfer','wrong_right']}
safe_mismatch = unsafe_false_accept = 0
stale_revoke_accept = stale_regrant_accept = stale_transfer_borrow_accept = 0
for _ in range(N):
    reg = Registry(); owner = reg.grant('write'); borrow = reg.borrow(owner)
    static_declares = True
    task_snapshot_live = reg.authorize(borrow, 'write')
    event = rng.choice(list(counts)); counts[event]+=1
    expected = True
    if event == 'revoke':
        reg.revoke(owner); expected = False
    elif event == 'regrant':
        slot = owner[0]; reg.revoke(owner); reg.regrant(slot, 'write'); expected = False
    elif event == 'transfer':
        reg.transfer(owner); expected = False
    elif event == 'wrong_right':
        expected = False
    required = 'read' if event == 'wrong_right' else 'write'
    safe = static_declares and reg.authorize(borrow, required)
    unsafe = static_declares and task_snapshot_live
    if safe != expected: safe_mismatch += 1
    if unsafe and not expected: unsafe_false_accept += 1
    if event == 'revoke' and safe: stale_revoke_accept += 1
    if event == 'regrant' and safe: stale_regrant_accept += 1
    if event == 'transfer' and safe: stale_transfer_borrow_accept += 1

forgery_accepts = 0
for _ in range(50_000):
    reg = Registry(); owner = reg.grant('write')
    slot, gen, right, mode = owner
    forged = (slot + rng.randint(1,1000), gen, right, mode)
    forgery_accepts += int(reg.authorize(forged, 'write'))

double_transfer_accepts = 0
for _ in range(20_000):
    reg = Registry(); owner = reg.grant('write')
    moved = reg.transfer(owner)
    try:
        reg.transfer(owner)
        double_transfer_accepts += 1
    except RuntimeError:
        pass
    assert reg.authorize(moved, 'write')

with tempfile.TemporaryDirectory() as td:
    pa = os.path.join(td, 'a'); pb = os.path.join(td, 'b')
    fd_a = os.open(pa, os.O_CREAT | os.O_WRONLY, 0o600)
    old_fd = fd_a
    os.close(fd_a)
    fd_b = os.open(pb, os.O_CREAT | os.O_WRONLY, 0o600)
    new_fd = fd_b
    err = None
    try:
        os.write(old_fd, b'B-MUTATED')
    except OSError as e:
        err = repr(e)
    os.close(fd_b)
    with open(pa, 'rb') as f: a_content = f.read().decode('utf-8', errors='replace')
    with open(pb, 'rb') as f: b_content = f.read().decode('utf-8', errors='replace')

result = {
    'seed': SEED,
    'delayed_cases': N,
    'event_counts': counts,
    'safe_oracle_mismatches': safe_mismatch,
    'unsafe_cached_snapshot_false_accepts': unsafe_false_accept,
    'stale_after_revoke_accepts': stale_revoke_accept,
    'stale_after_regrant_accepts': stale_regrant_accept,
    'stale_borrow_after_transfer_accepts': stale_transfer_borrow_accept,
    'forgery_cases': 50_000,
    'forgery_accepts': forgery_accepts,
    'double_transfer_cases': 20_000,
    'double_transfer_accepts': double_transfer_accepts,
    'fd_reuse_fixture': {
        'old_fd': old_fd,
        'new_fd': new_fd,
        'fd_number_reused': old_fd == new_fd,
        'stale_integer_write_succeeded': err is None,
        'a_content': a_content,
        'b_content': b_content,
        'error': err,
    },
}
print(json.dumps(result, sort_keys=True))