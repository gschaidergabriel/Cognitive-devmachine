from __future__ import annotations
import unittest

from semantic_access_pulse_v12 import (
    AccessPath, PulseInvariantError, PulsePlan, SegmentedPulseProjection, StalePulse
)

def seed_ids():
    return [f"seed:{c}:{i}" for c in range(5) for i in range(4)]

VERSIONS={f"seed:{c}:{i}":0 for c in range(5) for i in range(4)}

def paths_for(seed: str):
    _,cluster,item=seed.split(":")
    v=VERSIONS[seed]
    service=f"service:{cluster}"
    resource=f"resource:{cluster}"
    deps=(seed,f"cluster:{cluster}",service,resource)
    return [
        AccessPath(f"rec:{seed}:svc:v{v}",service,1,1,1.0+v/1000,dependencies=deps),
        AccessPath(f"rec:{seed}:res:v{v}",resource,2,2,0.8+v/1000,dependencies=deps),
    ]

class SegmentedPulseTests(unittest.TestCase):
    def setUp(self):
        for k in VERSIONS: VERSIONS[k]=0

    def make(self):
        x=SegmentedPulseProjection()
        x.bootstrap(event_id="boot",source_epoch=1,graph_epoch=1,seeds=seed_ids(),recompute_seed=paths_for)
        return x

    def test_local_pulse_recomputes_only_impacted_segments(self):
        x=self.make()
        impacted=tuple(f"seed:2:{i}" for i in range(4))
        for s in impacted: VERSIONS[s]=1
        r=x.apply_pulse(
            PulsePlan("p1","VALUE_UPDATE",("cluster:2",),impacted,True,2,1),
            recompute_seed=paths_for,recompute_all_seeds=seed_ids,incremental_fraction_limit=.25,
        )
        self.assertEqual(r.mode,"SEGMENTED_INCREMENTAL_PULSE")
        self.assertEqual(r.affected_seed_count,4)
        self.assertEqual(r.total_seed_count,20)
        self.assertAlmostEqual(r.affected_fraction,.2)
        self.assertEqual(r.new_segment_count,4)
        self.assertEqual(r.reused_segment_count,16)
        self.assertIn(":v1",x.query("seed:2:0")[0])
        self.assertIn(":v0",x.query("seed:1:0")[0])
        x.close()

    def test_incremental_equals_independent_full_rebuild(self):
        inc=self.make()
        full=self.make()
        impacted=tuple(f"seed:3:{i}" for i in range(4))
        for s in impacted: VERSIONS[s]=2
        inc.apply_pulse(
            PulsePlan("i","STATUS_UPDATE",("cluster:3",),impacted,True,2,1),
            recompute_seed=paths_for,recompute_all_seeds=seed_ids,
        )
        full.apply_pulse(
            PulsePlan("f","TOPOLOGY_ADD",("cluster:3",),impacted,False,2,1),
            recompute_seed=paths_for,recompute_all_seeds=seed_ids,
        )
        self.assertEqual(inc.snapshot(),full.snapshot())
        inc.close(); full.close()

    def test_broad_change_falls_back(self):
        x=self.make()
        impacted=tuple(f"seed:{c}:{i}" for c in range(3) for i in range(4))
        for s in impacted: VERSIONS[s]=1
        r=x.apply_pulse(
            PulsePlan("wide","VALUE_UPDATE",("cluster:0","cluster:1","cluster:2"),impacted,True,2,1),
            recompute_seed=paths_for,recompute_all_seeds=seed_ids,incremental_fraction_limit=.25,
        )
        self.assertEqual(r.mode,"FULL_FALLBACK")
        x.close()

    def test_topology_add_incomplete_falls_back(self):
        x=self.make()
        r=x.apply_pulse(
            PulsePlan("add","TOPOLOGY_ADD",("new-edge",),(),False,1,2),
            recompute_seed=paths_for,recompute_all_seeds=seed_ids,
        )
        self.assertEqual(r.mode,"FULL_FALLBACK")
        x.close()

    def test_stale_epoch_rejected(self):
        x=self.make()
        before=x.head_basis()
        with self.assertRaises(StalePulse):
            x.apply_pulse(
                PulsePlan("stale","VALUE_UPDATE",("cluster:1",),("seed:1:0",),True,0,1),
                recompute_seed=paths_for,recompute_all_seeds=seed_ids,
            )
        self.assertEqual(before,x.head_basis())
        x.close()

    def test_failure_preserves_last_known_good(self):
        x=self.make()
        before=x.head_basis()
        impacted=tuple(f"seed:2:{i}" for i in range(4))
        for s in impacted: VERSIONS[s]=1
        def bad(seed):
            if seed.endswith(":1"): raise RuntimeError("injected")
            return paths_for(seed)
        with self.assertRaises(RuntimeError):
            x.apply_pulse(
                PulsePlan("boom","VALUE_UPDATE",("cluster:2",),impacted,True,2,1),
                recompute_seed=bad,recompute_all_seeds=seed_ids,
            )
        self.assertEqual(before,x.head_basis())
        self.assertIn(":v0",x.query("seed:2:0")[0])
        x.close()

    def test_malformed_segment_preserves_head(self):
        x=self.make()
        before=x.head_basis()
        VERSIONS["seed:1:0"]=1
        def bad(seed):
            return [AccessPath("bad","target",0,0,1.0,dependencies=(seed,"target"))]
        with self.assertRaises(PulseInvariantError):
            x.apply_pulse(
                PulsePlan("bad","VALUE_UPDATE",("seed:1:0",),("seed:1:0",),True,2,1),
                recompute_seed=bad,recompute_all_seeds=seed_ids,
            )
        self.assertEqual(before,x.head_basis())
        x.close()

if __name__=="__main__":
    unittest.main()
