import unittest
from tools import trigger1_cross_task_abstract_control_gate_v7 as g


def candidate(selected=1, pos=(0.12,0.10,0.09), neg=(-0.04,-0.03,-0.02)):
    rows=[]
    for si,state in enumerate(g.v6.STATES):
        for code in g.v6.CODES:
            for pol in g.v6.POLARITIES:
                for rep in range(2):
                    for sign,means in ((1,pos),(-1,neg)):
                        rows.append({
                            "family_id":"CAL0",
                            "vector_state_id":state,
                            "requested_code":code,
                            "probe_polarity":pol,
                            "replicate_id":f"r{rep}",
                            "actuator_sign":sign,
                            "gain":32.0,
                            "target_margin_delta_vs_baseline":means[si],
                        })
    return {
        "primary_settings":{"gain":32.0,"actuator_sign":selected},
        "actuator_orientation_calibration":{
            "schema":g.ORIENTATION_SCHEMA,
            "fit_split":"CALIBRATION",
            "frozen_before_holdout":True,
            "holdout_seen_during_selection":False,
            "selection_rule":"MAXIMIZE_WORST_STATE_MEAN_TARGET_MARGIN_DELTA",
            "selected_actuator_sign":selected,
            "rows":rows,
        },
    }


class ActuatorOrientationGateV7Test(unittest.TestCase):
    def test_positive_sign_selected_only_when_worst_state_is_positive(self):
        x=candidate()
        failures=[]
        out=g._orientation(x,failures)
        self.assertEqual(failures,[])
        self.assertEqual(out["computed_selected_actuator_sign"],1)
        self.assertGreater(out["worst_state_mean_delta_by_sign"]["1"],g.MIN_CAL_EFFECT)

    def test_negative_sign_can_be_calibration_selected_without_semantic_opposite_claim(self):
        x=candidate(selected=-1,pos=(-0.03,-0.02,-0.04),neg=(0.11,0.09,0.08))
        failures=[]
        out=g._orientation(x,failures)
        self.assertEqual(failures,[])
        self.assertEqual(out["computed_selected_actuator_sign"],-1)

    def test_incomplete_plus_minus_pair_fails_closed(self):
        x=candidate()
        rows=x["actuator_orientation_calibration"]["rows"]
        x["actuator_orientation_calibration"]["rows"]=[r for i,r in enumerate(rows) if not (i==0 and r["actuator_sign"]==1)]
        failures=[]
        g._orientation(x,failures)
        self.assertTrue(any("SIGN_PAIR_INCOMPLETE" in f for f in failures))

    def test_pooled_success_cannot_hide_one_bad_state(self):
        x=candidate(pos=(0.20,0.20,-0.01),neg=(-0.10,-0.10,-0.10))
        failures=[]
        out=g._orientation(x,failures)
        self.assertEqual(out["computed_selected_actuator_sign"],1)
        self.assertTrue(any("NO_POSITIVE_WORST_STATE_CALIBRATION_EFFECT" in f for f in failures))

    def test_declared_sign_must_equal_rule_optimum(self):
        x=candidate(selected=-1)
        failures=[]
        g._orientation(x,failures)
        self.assertIn("ACTUATOR_ORIENTATION_SELECTED_SIGN_NOT_RULE_OPTIMUM",failures)

    def test_holdout_must_not_be_seen_during_selection(self):
        x=candidate()
        x["actuator_orientation_calibration"]["holdout_seen_during_selection"]=True
        failures=[]
        g._orientation(x,failures)
        self.assertIn("ACTUATOR_ORIENTATION_HOLDOUT_LEAK",failures)


if __name__=="__main__":
    unittest.main()
