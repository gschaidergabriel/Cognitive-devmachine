import json, random, string, unittest
from pathlib import Path
from needle_runtime_contract import *

FIXTURE = Path(__file__).parent / "fixtures" / "frank_needle_active_tools_20260804.json"
FRANK_TOOLS = json.loads(FIXTURE.read_text(encoding="utf-8"))

class RuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools, cls.contract = canonicalize_tools(FRANK_TOOLS)

    def test_real_registry_count(self): self.assertEqual(len(self.tools), 51)
    def test_real_registry_aliases(self):
        names={t["name"] for t in self.tools}; self.assertIn("list_capabilities",names); self.assertIn("search_knowledge",names)
        calc=next(t for t in self.tools if t["name"]=="calc"); self.assertIn("expression",calc["parameters"]); self.assertNotIn("ausdruck",calc["parameters"])
    def test_nested_openai_schema_flattens(self):
        src=[{"name":"get_weather","description":"","parameters":{"type":"object","properties":{"location":{"type":"string"}},"required":["location"]}}]
        nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertEqual(set(nt[0]["parameters"]),{"location"}); self.assertEqual(c["get_weather"]["required"],["location"])
    def test_flat_schema_preserved(self):
        src=[{"name":"get_weather","parameters":{"location":{"type":"string","required":True}}}]
        nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertEqual(set(nt[0]["parameters"]),{"location"}); self.assertEqual(c["get_weather"]["required"],["location"])
    def test_required_absent_from_properties_fails(self):
        with self.assertRaises(NeedleAdapterError): canonicalize_tools([{"name":"x","parameters":{"type":"object","properties":{},"required":["missing"]}}],AliasProfile({},{}))
    def test_zero_arg(self):
        nt,c=canonicalize_tools([{"name":"ping","parameters":{}}],AliasProfile({},{})); self.assertTrue(validate_output('[{"name":"ping","arguments":{}}]',nt,c,AliasProfile({},{})).accepted)
    def test_no_tool(self):
        r=validate_output("[]",self.tools,self.contract); self.assertTrue(r.accepted); self.assertEqual(r.outcome,"NO_TOOL_PROPOSAL"); self.assertEqual(r.authority,"NONE"); self.assertFalse(r.effect_eligible); self.assertTrue(r.effect_gate_required)
    def test_unoffered_tool_rejected(self): self.assertFalse(validate_output('[{"name":"evil","arguments":{}}]',self.tools,self.contract).accepted)
    def test_unknown_arg_rejected(self):
        t=next(t for t in self.tools if not t["parameters"]); self.assertFalse(validate_output(json.dumps([{"name":t["name"],"arguments":{"x":"y"}}]),self.tools,self.contract).accepted)
    def test_missing_required_rejected(self):
        t=next(t for t in self.tools if t["parameters"]); self.assertFalse(validate_output(json.dumps([{"name":t["name"],"arguments":{}}]),self.tools,self.contract).accepted)
    def test_valid_real_tool_reverse_maps(self):
        r=validate_output('[{"name":"calc","arguments":{"expression":"2+2"}}]',self.tools,self.contract); self.assertTrue(r.accepted); self.assertEqual(r.frank_calls[0]["arguments"],{"ausdruck":"2+2"})
    def test_tool_alias_reverse_maps(self):
        t=next(t for t in self.tools if t["name"]=="list_capabilities"); args={k:"x" for k in t["parameters"]}; r=validate_output(json.dumps([{"name":"list_capabilities","arguments":args}]),self.tools,self.contract); self.assertTrue(r.accepted); self.assertEqual(r.frank_calls[0]["name"],"moeglichkeiten")
    def test_malformed_json_rejected(self): self.assertFalse(validate_output('[{"name":',self.tools,self.contract).accepted)
    def test_top_level_dict_rejected(self): self.assertFalse(validate_output('{"name":"x","arguments":{}}',self.tools,self.contract).accepted)
    def test_duplicate_name_key_rejected(self):
        self.assertFalse(validate_output('[{"name":"evil","name":"calc","arguments":{"expression":"2+2"}}]',self.tools,self.contract).accepted)
    def test_duplicate_argument_key_rejected(self):
        self.assertFalse(validate_output('[{"name":"calc","arguments":{"expression":"2+2","expression":"rm -rf /"}}]',self.tools,self.contract).accepted)
    def test_nan_rejected(self):
        src=[{"name":"set_n","parameters":{"type":"object","properties":{"n":{"type":"number"}},"required":["n"]}}]; nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertFalse(validate_output('[{"name":"set_n","arguments":{"n":NaN}}]',nt,c,AliasProfile({},{})).accepted)
    def test_infinity_rejected(self):
        src=[{"name":"set_n","parameters":{"type":"object","properties":{"n":{"type":"number"}},"required":["n"]}}]; nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertFalse(validate_output('[{"name":"set_n","arguments":{"n":Infinity}}]',nt,c,AliasProfile({},{})).accepted); self.assertFalse(validate_output('[{"name":"set_n","arguments":{"n":1e999}}]',nt,c,AliasProfile({},{})).accepted)
    def test_extra_call_fields_rejected(self):
        t=next(t for t in self.tools if not t["parameters"]); self.assertFalse(validate_output(json.dumps([{"name":t["name"],"arguments":{},"authority":"RUN"}]),self.tools,self.contract).accepted)
    def test_type_validation(self):
        src=[{"name":"set_n","parameters":{"type":"object","properties":{"n":{"type":"integer"},"ok":{"type":"boolean"}},"required":["n","ok"]}}]
        nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertTrue(validate_output('[{"name":"set_n","arguments":{"n":3,"ok":true}}]',nt,c,AliasProfile({},{})).accepted); self.assertFalse(validate_output('[{"name":"set_n","arguments":{"n":"3","ok":true}}]',nt,c,AliasProfile({},{})).accepted)
    def test_unknown_schema_type_rejected(self):
        src=[{"name":"x","parameters":{"type":"object","properties":{"v":{"type":"mystery"}},"required":["v"]}}]; nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertFalse(validate_output('[{"name":"x","arguments":{"v":"a"}}]',nt,c,AliasProfile({},{})).accepted)
    def test_name_collision_fails(self):
        with self.assertRaises(NeedleAdapterError): canonicalize_tools([{"name":"foo-bar","parameters":{}},{"name":"foo_bar","parameters":{}}],AliasProfile({},{}))
    def test_param_alias_collision_fails(self):
        with self.assertRaises(NeedleAdapterError): canonicalize_tools([{"name":"x","parameters":{"a":{},"b":{}}}],AliasProfile({}, {"x":{"a":"z","b":"z"}}))
    def test_toolset_hash_deterministic(self): self.assertEqual(validate_output("[]",self.tools,self.contract).toolset_sha256,validate_output("[]",self.tools,self.contract).toolset_sha256)
    def test_raw_hash_tamper_detectable(self): self.assertNotEqual(validate_output("[]",self.tools,self.contract).raw_output_sha256,validate_output("[ ]",self.tools,self.contract).raw_output_sha256)
    def test_budget_exact(self): self.assertEqual(assert_complete_encoder_budget(100,700,1024,200),801)
    def test_budget_fail_closed(self):
        with self.assertRaises(NeedleAdapterError): assert_complete_encoder_budget(100,800,1024,200)
    def test_budget_negative_rejected(self):
        with self.assertRaises(NeedleAdapterError): assert_complete_encoder_budget(-1,100,1024,0)
    def test_confidence_metadata_does_not_grant_authority(self):
        r=validate_output("[]",self.tools,self.contract,preconstraint_margin=9.0,preconstraint_entropy=.01); self.assertTrue(r.accepted); self.assertEqual(r.authority,"NONE"); self.assertFalse(r.effect_eligible)
    def test_random_invalid_tool_fuzz(self):
        offered={t["name"] for t in self.tools}
        for _ in range(1000):
            name="zz_"+''.join(random.choice(string.ascii_lowercase) for _ in range(12)); self.assertNotIn(name,offered); self.assertFalse(validate_output(json.dumps([{"name":name,"arguments":{}}]),self.tools,self.contract).accepted)
    def test_random_unknown_arg_fuzz(self):
        t=next(t for t in self.tools if not t["parameters"])
        for _ in range(1000):
            k="zz_"+''.join(random.choice(string.ascii_lowercase) for _ in range(10)); self.assertFalse(validate_output(json.dumps([{"name":t["name"],"arguments":{k:"v"}}]),self.tools,self.contract).accepted)
    def test_multi_call_rejected_for_frank_single_shot(self):
        noargs=[x for x in self.tools if not x["parameters"]][:2]
        raw=json.dumps([{"name":noargs[0]["name"],"arguments":{}},{"name":noargs[1]["name"],"arguments":{}}],separators=(",",":"))
        r=validate_output(raw,self.tools,self.contract)
        self.assertFalse(r.accepted)
        self.assertTrue(r.fallback_required)
        self.assertTrue(any(x.startswith("MULTI_CALL_FORBIDDEN:") for x in r.rejection_reasons))
    def test_no_tool_requires_fallback_to_4b(self):
        r=validate_output("[]",self.tools,self.contract)
        self.assertTrue(r.accepted)
        self.assertEqual(r.outcome,"NO_TOOL_PROPOSAL")
        self.assertTrue(r.fallback_required)
    def test_valid_route_does_not_require_semantic_fallback(self):
        r=validate_output('[{"name":"calc","arguments":{"expression":"2+2"}}]',self.tools,self.contract)
        self.assertTrue(r.accepted)
        self.assertEqual(r.outcome,"ROUTE_PROPOSAL")
        self.assertFalse(r.fallback_required)

if __name__=="__main__": unittest.main(verbosity=2)
