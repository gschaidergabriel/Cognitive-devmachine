import unittest
from tools import trigger1_cross_task_abstract_control_gate_v2 as g

def valid():
    basis=[]
    vecs=[[1.0,0.1,0.0],[1.0,0.08,0.02],[1.0,0.12,-0.01]]
    for i,v in enumerate(vecs):
        basis.append({"family_id":f"basis-{i}","task_grammar_id":f"basis-grammar-{i}","direction":v})
    causal=[]
    for fi in range(3):
        fam=f"hold-{fi}"; grammar=f"hold-grammar-{fi}"
        for target in g.STATES:
            for code in g.CODES:
                for ri in range(2):
                    for pol in g.POLARITIES:
                        for ctrl in g.CONTROLS:
                            margin={"TARGET":0.5,"NULL":0.0,"SIGN_FLIP":-0.4,"ORTHOGONAL":0.0,"PERMUTED":0.0,"NUISANCE":0.0}[ctrl]
                            causal.append({"family_id":fam,"task_grammar_id":grammar,"vector_state_id":target,"requested_code":code,"probe_polarity":pol,"proof_topology_id":f"top-{ri}","demo_context_id":f"demo-{target}-{code}-r{ri}","prompt_tokens":128+ri,"probe_tokens":16,"last_token_index":127+ri,"replicate_id":f"r{ri}","control":ctrl,"target_margin":margin})
    off=[]
    for fi in range(3):
        for ri in range(3):
            off.append({"family_id":f"hold-{fi}","replicate_id":f"o{ri}","control":"TARGET","unrelated_task_margin":0.01})
            off.append({"family_id":f"hold-{fi}","replicate_id":f"o{ri}","control":"NULL","unrelated_task_margin":0.0})
    return {
        "schema":g.ATTESTATION_SCHEMA,
        "primary_settings":{"gguf_sha256":g.PINNED_GGUF_SHA256,"llama_cpp_commit":g.PINNED_LLAMA_CPP_COMMIT,"injection_layer":20,"gain":32.0,"gain_selected_on_evaluation":False,"token_scope":"ALL_PROMPT_TOKENS"},
        "basis_family_directions":basis,
        "rank_consistency":{"representation_rank":"TWO_DIMENSIONAL_REQUIRED","intervention_rank":"TWO_DIMENSIONAL_REQUIRED","downstream_rank":"TWO_DIMENSIONAL_REQUIRED","analyzer":"trigger1_semantic_simplex_rank_analyze.py","shared_geometry_scale_preserved":True,"zero_sum_simplex_preserved":True,"downstream_coordinates_in_admitted_orthonormal_basis":True,"independent_unit_normalization_used":False},
        "rank2_target_to_target_displacement_verified":True,
        "simple_sign_flip_used_as_semantic_opposite":False,
        "position_length_design":{"tokenizer_identity_bound_to_pinned_runtime":True,"length_position_nuisance_fit_calibration_only_and_frozen":True,"target_token_count_predictability_above_null":False},
        "geometry_permutation_null":{"pairwise_cosine_q95":0.2,"loo_cosine_q95":0.2,"derived_from_preregistered_class_assignment_permutations":True},
        "holdout_causal_rows":causal,
        "off_target_rows":off,
    }

class GateTests(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(g.adjudicate(valid())["cross_task_abstract_native_control_pass"])
    def test_gain_tuning_fails(self):
        x=valid(); x["primary_settings"]["gain_selected_on_evaluation"]=True
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_pooled_effect_cannot_hide_target_failure(self):
        x=valid()
        for r in x["holdout_causal_rows"]:
            if r["family_id"]=="hold-0" and r["vector_state_id"]=="S2" and r["control"]=="TARGET":
                r["target_margin"]=-0.1
        out=g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(any("PER_TARGET_POLARITY_EFFECT_NOT_POSITIVE:hold-0:S2:" in f for f in out["failures"]))
    def test_signflip_must_reverse(self):
        x=valid()
        for r in x["holdout_causal_rows"]:
            if r["control"]=="SIGN_FLIP": r["target_margin"]=-0.01
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_replication_required(self):
        x=valid()
        x["holdout_causal_rows"]=[r for r in x["holdout_causal_rows"] if not (r["family_id"]=="hold-1" and r["vector_state_id"]=="S1" and r["requested_code"]=="B" and r["probe_polarity"]=="NEGATED" and r["replicate_id"]=="r1")]
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_polarity_factorial_required(self):
        x=valid()
        x["holdout_causal_rows"]=[r for r in x["holdout_causal_rows"] if not (r["family_id"]=="hold-0" and r["vector_state_id"]=="S0" and r["requested_code"]=="C" and r["probe_polarity"]=="NEGATED")]
        out=g.adjudicate(x)
        self.assertFalse(out["cross_task_abstract_native_control_pass"])
        self.assertTrue(any("POLARITY" in f or "FACTORIAL" in f for f in out["failures"]))
    def test_demo_context_must_match_across_polarity(self):
        x=valid()
        for r in x["holdout_causal_rows"]:
            if r["family_id"]=="hold-0" and r["vector_state_id"]=="S0" and r["requested_code"]=="A" and r["replicate_id"]=="r0" and r["probe_polarity"]=="NEGATED":
                r["demo_context_id"]="different-demo"
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_off_target_effect_fails(self):
        x=valid()
        for r in x["off_target_rows"]:
            if r["family_id"]=="hold-2" and r["control"]=="TARGET": r["unrelated_task_margin"]=0.2
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_position_length_target_distribution_mismatch_fails(self):
        x=valid()
        for r in x["holdout_causal_rows"]:
            if r["family_id"]=="hold-0" and r["vector_state_id"]=="S2" and r["control"]=="TARGET":
                r["prompt_tokens"] += 7; r["last_token_index"] += 7
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_tokenizer_binding_required(self):
        x=valid(); x["position_length_design"]["tokenizer_identity_bound_to_pinned_runtime"]=False
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_rank_mismatch_fails(self):
        x=valid(); x["rank_consistency"]["downstream_rank"]="ONE_DIMENSIONAL_SUPPORTED"
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_shared_scale_required(self):
        x=valid(); x["rank_consistency"]["shared_geometry_scale_preserved"]=False
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_proof_topology_target_confound_fails(self):
        x=valid()
        for r in x["holdout_causal_rows"]:
            if r["vector_state_id"]=="S2": r["proof_topology_id"]="special-s2"
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_rank2_requires_target_displacement(self):
        x=valid(); x["rank2_target_to_target_displacement_verified"]=False
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])
    def test_geometry_null_fails(self):
        x=valid(); x["geometry_permutation_null"]["pairwise_cosine_q95"]=0.99999
        self.assertFalse(g.adjudicate(x)["cross_task_abstract_native_control_pass"])

if __name__=="__main__":
    unittest.main()
