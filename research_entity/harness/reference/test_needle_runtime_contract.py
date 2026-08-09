import json, random, string, unittest
from needle_runtime_contract import *

REG = json.load(open("registry.json"))
BLOCKED = set(REG["gesperrt"])
ACTIVE = {n:v for n,v in REG["werkzeuge"].items() if n not in BLOCKED and not v.get("gesperrt")}

def frank_tools():
    out=[]
    for name,v in ACTIVE.items():
        props={a:{"type":"string"} for a in v.get("argumente",[])}
        out.append({"name":name,"description":v.get("beschreibung",""),"parameters":{"type":"object","properties":props,"required":list(v.get("argumente",[]))}})
    return out

class RuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tools, cls.contract = canonicalize_tools(frank_tools())

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
    def test_zero_arg(self):
        nt,c=canonicalize_tools([{"name":"ping","parameters":{}}],AliasProfile({},{})); self.assertTrue(validate_output('[{"name":"ping","arguments":{}}]',nt,c,AliasProfile({},{})).accepted)
    def test_no_tool(self):
        r=validate_output("[]",self.tools,self.contract); self.assertTrue(r.accepted); self.assertEqual(r.outcome,"NO_TOOL_PROPOSAL"); self.assertEqual(r.authority,"NONE"); self.assertFalse(r.effect_eligible); self.assertTrue(r.effect_gate_required)
    def test_unoffered_tool_rejected(self): self.assertFalse(validate_output('[{"name":"evil","arguments":{}}]',self.tools,self.contract).accepted)
    def test_blocked_tool_absent_and_rejected(self):
        blocked=next(iter(BLOCKED)); self.assertNotIn(blocked,{x["name"] for x in self.tools}); self.assertFalse(validate_output(json.dumps([{"name":blocked,"arguments":{}}]),self.tools,self.contract).accepted)
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
    def test_extra_call_fields_rejected(self):
        t=next(t for t in self.tools if not t["parameters"]); self.assertFalse(validate_output(json.dumps([{"name":t["name"],"arguments":{},"authority":"RUN"}]),self.tools,self.contract).accepted)
    def test_type_validation(self):
        src=[{"name":"set_n","parameters":{"type":"object","properties":{"n":{"type":"integer"},"ok":{"type":"boolean"}},"required":["n","ok"]}}]
        nt,c=canonicalize_tools(src,AliasProfile({},{})); self.assertTrue(validate_output('[{"name":"set_n","arguments":{"n":3,"ok":true}}]',nt,c,AliasProfile({},{})).accepted); self.assertFalse(validate_output('[{"name":"set_n","arguments":{"n":"3","ok":true}}]',nt,c,AliasProfile({},{})).accepted)
    def test_name_collision_fails(self):
        with self.assertRaises(NeedleAdapterError): canonicalize_tools([{"name":"foo-bar","parameters":{}},{"name":"foo_bar","parameters":{}}],AliasProfile({},{}))
    def test_param_alias_collision_fails(self):
        with self.assertRaises(NeedleAdapterError): canonicalize_tools([{"name":"x","parameters":{"a":{},"b":{}}}],AliasProfile({}, {"x":{"a":"z","b":"z"}}))
    def test_toolset_hash_deterministic(self): self.assertEqual(validate_output("[]",self.tools,self.contract).toolset_sha256,validate_output("[]",self.tools,self.contract).toolset_sha256)
    def test_raw_hash_tamper_detectable(self): self.assertNotEqual(validate_output("[]",self.tools,self.contract).raw_output_sha256,validate_output("[ ]",self.tools,self.contract).raw_output_sha256)
    def test_budget_exact(self): self.assertEqual(assert_complete_encoder_budget(100,700,1024,200),801)
    def test_budget_fail_closed(self):
        with self.assertRaises(NeedleAdapterError): assert_complete_encoder_budget(100,800,1024,200)
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

if __name__=="__main__": unittest.main(verbosity=2)
