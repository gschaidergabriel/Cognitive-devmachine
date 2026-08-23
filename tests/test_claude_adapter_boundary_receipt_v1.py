import importlib.util, pathlib, unittest
P=pathlib.Path(__file__).resolve().parents[1]/"tools"/"validate_claude_adapter_boundary_receipt_v1.py"
S=importlib.util.spec_from_file_location("v",P); v=importlib.util.module_from_spec(S); assert S.loader is not None; S.loader.exec_module(v)
D="a"*64

def receipt(schema):
 r={"schema":schema,"source":{"commit":"6"*40,"tree":"7"*40,"dirty":False},"run":{"test_run_id":"same-run","run_binding_digest":D,"suite_digest":"b"*64,"executor_digest":"c"*64},"claude":{"binary_digest":"d"*64,"adapter_contract_digest":"e"*64,"version":"bound"},"invocation":{"argv":["claude","-p"],"argv_digest":"f"*64,"cwd_digest":"1"*64},"environment":{"keys":["HOME","PATH"],"normalized_class_digest":"2"*64,"raw_values_persisted":False,"credential_material_persisted":False,"credential_admission_mode":"HOME_OAUTH"},"config_sources":{"home_path_digest":"3"*64,"project_cwd_digest":"4"*64,"mcp_config_digest":"5"*64,"unexpected_config_source_count":0},"result":{"exit_code":0,"stdout_digest":"6"*64,"stderr_digest":"7"*64,"raw_envelope_digest":"8"*64,"result_digest":"9"*64}}
 if schema=="TOOLLESS_RECEIPT/v1": r["boundary"]={"passed":True,"tools_flag_empty":True,"strict_mcp_config":True,"permission_mode":"plan","effective_tool_authority_count":0}
 elif schema=="EPHEMERAL_RECEIPT/v1": r["boundary"]={"passed":True,"no_session_persistence":True,"pre_session_artifact_digest":D,"post_session_artifact_digest":D,"cross_turn_state_detected":False,"claude_persistent_state_write_count":0}
 elif schema=="STRUCTURED_OUTPUT_RECEIPT/v1": r["boundary"]={"passed":True,"acceptance_path":"structured_output","direct_raw_text_acceptance":False,"parser_accepted":True,"accepted_structured_output_digest":D}
 else: r["boundary"]={"passed":True,"allowlist_digest":D,"unexpected_env_key_count":0,"unexpected_config_ingress_count":0,"raw_credential_material_exposed_to_receipt":False}
 r["receipt_envelope_digest"]=v.digest(r); return r

class T(unittest.TestCase):
 def test_four_split_receipts(self):
  xs=[v.validate(receipt(s)) for s in v.SCHEMAS]; self.assertEqual({x["run_binding_digest"] for x in xs},{D}); self.assertEqual({x["runtime_credit"] for x in xs},{0})
 def test_tool_authority_cannot_launder_pass(self):
  r=receipt("TOOLLESS_RECEIPT/v1"); r["boundary"]["effective_tool_authority_count"]=1; r["receipt_envelope_digest"]=v.digest(r); self.assertRaisesRegex(v.ReceiptError,"BOUNDARY_PASS_MISMATCH",v.validate,r)
 def test_cross_turn_state_cannot_launder_pass(self):
  r=receipt("EPHEMERAL_RECEIPT/v1"); r["boundary"]["cross_turn_state_detected"]=True; r["receipt_envelope_digest"]=v.digest(r); self.assertRaisesRegex(v.ReceiptError,"BOUNDARY_PASS_MISMATCH",v.validate,r)
 def test_raw_text_cannot_launder_structured_pass(self):
  r=receipt("STRUCTURED_OUTPUT_RECEIPT/v1"); r["boundary"]["direct_raw_text_acceptance"]=True; r["receipt_envelope_digest"]=v.digest(r); self.assertRaisesRegex(v.ReceiptError,"BOUNDARY_PASS_MISMATCH",v.validate,r)
 def test_env_ingress_cannot_launder_pass(self):
  r=receipt("ENV_ISOLATION_RECEIPT/v1"); r["boundary"]["unexpected_config_ingress_count"]=1; r["receipt_envelope_digest"]=v.digest(r); self.assertRaisesRegex(v.ReceiptError,"BOUNDARY_PASS_MISMATCH",v.validate,r)
 def test_failed_receipt_is_valid_negative_evidence(self):
  r=receipt("TOOLLESS_RECEIPT/v1"); r["boundary"].update(passed=False,tools_flag_empty=False); r["receipt_envelope_digest"]=v.digest(r); self.assertFalse(v.validate(r)["boundary_passed"])
 def test_secret_material_field_rejected(self):
  r=receipt("ENV_ISOLATION_RECEIPT/v1"); r["environment"]["secret_value"]="x"; self.assertRaisesRegex(v.ReceiptError,"SECRET_MATERIAL_FIELD_FORBIDDEN",v.digest,r)
if __name__=="__main__": unittest.main()
