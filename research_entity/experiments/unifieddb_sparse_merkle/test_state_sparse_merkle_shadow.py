import hashlib
import random
import unittest

from .state_sparse_merkle_shadow import SparseMerkleStateShadow


def rh(text): return hashlib.sha256(text.encode()).hexdigest()


class SparseMerkleShadowTests(unittest.TestCase):
    def test_rebuild_is_order_independent(self):
        rows=[('semantic',f'k{i:03d}',rh(f'row-{i}')) for i in range(80)]
        a=SparseMerkleStateShadow(); ar=a.rebuild(rows)
        b=SparseMerkleStateShadow(); shuffled=list(rows); random.Random(91).shuffle(shuffled); br=b.rebuild(shuffled)
        self.assertEqual(ar,br)

    def test_incremental_update_equals_full_rebuild(self):
        rows={('d',f'k{i:03d}'):rh(f'v{i}') for i in range(100)}
        shadow=SparseMerkleStateShadow(); shadow.rebuild((d,k,v) for (d,k),v in rows.items())
        rng=random.Random(7331)
        for step in range(120):
            key=('d',f'k{rng.randrange(100):03d}'); rows[key]=rh(f'v-{step}-{rng.randrange(9999)}')
            shadow.update_hash(domain=key[0],key=key[1],row_hash_hex=rows[key])
            rebuilt=SparseMerkleStateShadow(); rebuilt.rebuild((d,k,v) for (d,k),v in rows.items())
            self.assertEqual(shadow.map_root(),rebuilt.map_root())

    def test_remove_equals_rebuild_without_row(self):
        rows={('d',f'k{i:03d}'):rh(f'v{i}') for i in range(40)}
        s=SparseMerkleStateShadow(); s.rebuild((d,k,v) for (d,k),v in rows.items())
        del rows[('d','k017')]; s.remove(domain='d',key='k017')
        r=SparseMerkleStateShadow(); r.rebuild((d,k,v) for (d,k),v in rows.items())
        self.assertEqual(s.map_root(),r.map_root())

    def test_inclusion_proof_detects_tampering(self):
        s=SparseMerkleStateShadow(); rows=[('memory',f'k{i}',rh(f'value-{i}')) for i in range(20)]; s.rebuild(rows)
        proof=s.proof(domain='memory',key='k7'); self.assertTrue(SparseMerkleStateShadow.verify(proof))
        bad=type(proof)(proof.key_hash_hex,rh('tampered'),proof.siblings_hex,proof.map_root_hex)
        self.assertFalse(SparseMerkleStateShadow.verify(bad))

    def test_committed_root_binds_metadata_and_map(self):
        s=SparseMerkleStateShadow(); s.update_hash(domain='a',key='b',row_hash_hex=rh('row'))
        kw={'global_epoch':7,'domain_epochs_hash_hex':rh('domains'),'semantic_chain_hash_hex':rh('chain')}
        a=s.committed_root(**kw); self.assertEqual(a,s.committed_root(**kw))
        self.assertNotEqual(a,s.committed_root(**{**kw,'global_epoch':8}))
        self.assertNotEqual(a,s.committed_root(**{**kw,'domain_epochs_hash_hex':rh('other')}))
        s.update_hash(domain='a',key='b',row_hash_hex=rh('row2')); self.assertNotEqual(a,s.committed_root(**kw))


if __name__=='__main__': unittest.main()
