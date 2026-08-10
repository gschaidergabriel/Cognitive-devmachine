#!/usr/bin/env python3
from __future__ import annotations
import sqlite3, tempfile, unittest
from pathlib import Path

from semantic_access_pulse_v12 import AccessPath, PulsePlan
from semantic_access_pulse_v12_1 import ConcurrentSafeSegmentedPulseProjection


def model():
    versions={"seed:a":0}
    def recompute(seed):
        v=versions[seed]
        return [AccessPath(
            target_record_id=f"rec:{seed}:v{v}", target_logical_id="node:a", path_rank=1,
            hop_count=1, path_weight=1.0, dependencies=(seed,"node:a"),
        )]
    return versions,recompute


class RaceInjectProjection(ConcurrentSafeSegmentedPulseProjection):
    def arm(self, callback):
        self._race_callback=callback; self._race_armed=True
    def _head(self):
        head=super()._head()
        if getattr(self,"_race_armed",False):
            self._race_armed=False
            self._race_callback()
        return head


class PulseV121ConcurrencyTests(unittest.TestCase):
    def test_schema_rejects_two_current_generations(self):
        with tempfile.TemporaryDirectory() as td:
            p=ConcurrentSafeSegmentedPulseProjection(str(Path(td)/"db.sqlite"))
            try:
                versions,recompute=model()
                p.bootstrap(event_id="boot",source_epoch=1,graph_epoch=1,seeds=("seed:a",),recompute_seed=recompute)
                with self.assertRaises(sqlite3.IntegrityError):
                    with p.con:
                        p.con.execute("INSERT INTO access_generation VALUES('evil',2,1,'h',1,'CURRENT',1,NULL)")
                self.assertEqual(p.con.execute("SELECT count(*) FROM access_generation WHERE status='CURRENT'").fetchone()[0],1)
            finally: p.close()

    def test_stale_parent_race_rolls_back_and_preserves_winner(self):
        with tempfile.TemporaryDirectory() as td:
            path=str(Path(td)/"db.sqlite")
            winner=ConcurrentSafeSegmentedPulseProjection(path)
            stale=RaceInjectProjection(path)
            versions,recompute=model()
            try:
                boot=winner.bootstrap(event_id="boot",source_epoch=1,graph_epoch=1,seeds=("seed:a",),recompute_seed=recompute)
                winner_generation={"id":None}
                def publish_winner():
                    versions["seed:a"]=1
                    r=winner.apply_pulse(
                        PulsePlan("winner","VALUE_UPDATE",("node:a",),("seed:a",),True,2,1),
                        recompute_seed=recompute,recompute_all_seeds=lambda:("seed:a",),
                    )
                    winner_generation["id"]=r.generation_id
                stale.arm(publish_winner)
                with self.assertRaises(sqlite3.IntegrityError):
                    stale.apply_pulse(
                        PulsePlan("stale","VALUE_UPDATE",("node:a",),("seed:a",),True,2,1),
                        recompute_seed=recompute,recompute_all_seeds=lambda:("seed:a",),
                    )
                head=winner._head()
                self.assertEqual(head["generation_id"],winner_generation["id"])
                self.assertNotEqual(head["generation_id"],boot.generation_id)
                self.assertEqual(winner.con.execute("SELECT count(*) FROM access_generation WHERE status='CURRENT'").fetchone()[0],1)
                self.assertEqual(winner.query("seed:a"),("rec:seed:a:v1",))
                self.assertIsNone(winner.con.execute("SELECT generation_id FROM access_generation WHERE generation_id LIKE 'gen-%' AND generation_id NOT IN (?,?) AND status='CURRENT'",(boot.generation_id,winner_generation["id"])).fetchone())
            finally:
                stale.close(); winner.close()

    def test_normal_incremental_pulse_still_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            p=ConcurrentSafeSegmentedPulseProjection(str(Path(td)/"db.sqlite")); versions,recompute=model()
            try:
                p.bootstrap(event_id="boot",source_epoch=1,graph_epoch=1,seeds=("seed:a",),recompute_seed=recompute)
                versions["seed:a"]=1
                r=p.apply_pulse(
                    PulsePlan("normal","VALUE_UPDATE",("node:a",),("seed:a",),True,2,1),
                    recompute_seed=recompute,recompute_all_seeds=lambda:("seed:a",),
                )
                self.assertEqual(r.mode,"FULL_FALLBACK" if r.affected_fraction>0.25 else "SEGMENTED_INCREMENTAL_PULSE")
                self.assertEqual(p.query("seed:a"),("rec:seed:a:v1",))
                self.assertEqual(p.con.execute("SELECT count(*) FROM access_generation WHERE status='CURRENT'").fetchone()[0],1)
            finally: p.close()

if __name__=="__main__": unittest.main(verbosity=2)
