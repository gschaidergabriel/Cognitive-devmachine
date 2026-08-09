import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("freeze", str(Path(__file__).resolve().parents[1] / "reference" / "hwp01_freeze_compiler.py"))
freeze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze)

ARCH = {
  "schema_version":"1.0","architecture_id":"FRANK-V0.1-CLAY-NATIVE-LOOP-BASE-BRIDGE",
  "canonical_parent":"r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346",
  "target_host":"UBUNTU_LINUX_DEVELOPER_SYSTEM",
  "fixed_contracts": freeze.REQ_FIXED,
  "semantic_organs":[{"id":x,"role":"r","semantic_boundary":"CLAY_NATIVE"} for x in sorted(freeze.REQ_ORGANS)],
  "state_contracts":{"LoopDynamicsReadout":{"fields":["state_delta_norm","residual_pressure"]},"RecurrenceDecision":{"variants":["CONTINUE","ROLLBACK"]}},
  "causal_relations":["observation->semantic_state","gwt_workspace->effect_gateway"],
  "operations":[{"id":"measure_loop","effects":[]}],
  "invariants":["recurrence_is_not_emergence","activation_is_not_truth","selection_is_not_authority","model_output_is_not_execution_authority","semantic_hash_is_distinct_from_exact_contract_hash"]
}

FULL = "\n".join([
  "C9 + owner-fixed Clay-native/Retina/online-learning contracts",
  "The Thalamus is retained as a core logical organ",
  "The target organism can now be summarized as these logical planes",
  *[f"{i}. {name};" if i < 13 else f"{i}. {name}." for i,name in enumerate(freeze.PLANES,1)]
])
DOCS = {
 "full_lineage_fusion": FULL,
 "clay_native_contract": "PROJECT-OWNER ARCHITECTURE DIRECTIVE\nThe target FRANK system is Clay-native end to end.\nNeedle is the one intentionally retained non-Clay subsystem.\nThere must not be a second independent semantic architecture",
 "digital_retina_contract": "PROJECT-OWNER ARCHITECTURE DIRECTIVE\nDigital Retina is no longer required to survive as a semantically independent cognitive subsystem/process boundary\nPerceptualField\nVisualPercept\nadaptive Micro Visual Classifier\nNo untyped natural-language caption, opaque model embedding or Micro Visual Classifier output may silently become architectural truth",
 "adaptive_visual_learning_directive": "PROJECT-OWNER FIXED FRANK 0.1 REQUIREMENT\nmicro_classifier_prediction != sensor_truth\nGOLD/SILVER\nBRONZE one-shot/self-generated labels MUST NOT autonomously become training truth\nKNOWN_HIGH_CONFIDENCE\nUNKNOWN\nCONFLICT\npromote atomically only when gates pass\nlast known-good classifier/prototype state for rollback\nMVC-E1\nMVC-E7",
 "gwt_overlay": "Trajectory-Capacity Recurrent Workspace Control\nsemantic_state_hash\nstate_version_hash\ntrace_root_hash\nsmall_step != convergence\nreentry != authority",
}

class T(unittest.TestCase):
  def setup_tree(self):
    td=tempfile.TemporaryDirectory(); root=Path(td.name); sources=[]
    ap=root/'arch.json'; ap.write_text(json.dumps(ARCH,indent=2)+'\n')
    data=ap.read_bytes(); sources.append({"role":"loop_projection","path":"arch.json","git_blob_sha":freeze.blob(data)})
    for role,text in DOCS.items():
      p=root/(role+'.txt'); p.write_text(text+'\n'); data=p.read_bytes()
      sources.append({"role":role,"path":p.name,"git_blob_sha":freeze.blob(data)})
    lock=root/'lock.json'; lock.write_text(json.dumps({"sources":sources},indent=2)+'\n')
    return td,root,lock

  def test_build_verify_and_identity_split(self):
    td,root,lock=self.setup_tree()
    try:
      f1,v=freeze.build(root,lock); self.assertEqual(v,[])
      self.assertEqual(len(f1['logical_planes']),13)
      self.assertIn('micro_visual_classifier',{m['id'] for m in f1['modules']})
      self.assertIn('thalamus_attention',{m['id'] for m in f1['modules']})
      out=root/'freeze.json'; out.write_text(json.dumps(f1,indent=2)+'\n')
      self.assertEqual(freeze.verify(root,freeze.load(out)),[])
      ap=root/'arch.json'; ap.write_text(json.dumps(ARCH,separators=(',',':'))+'\n')
      data=ap.read_bytes(); lock_obj=json.loads(lock.read_text())
      for e in lock_obj['sources']:
        if e['role']=='loop_projection': e['git_blob_sha']=freeze.blob(data)
      lock.write_text(json.dumps(lock_obj,indent=2)+'\n')
      f2,v2=freeze.build(root,lock); self.assertEqual(v2,[])
      self.assertEqual(f1['architecture_semantic_hash'],f2['architecture_semantic_hash'])
      self.assertNotEqual(f1['exact_contract_hash'],f2['exact_contract_hash'])
    finally: td.cleanup()

  def test_missing_mvc_contract_marker_fails_closed(self):
    td,root,lock=self.setup_tree()
    try:
      p=root/'adaptive_visual_learning_directive.txt'; p.write_text('PROJECT-OWNER FIXED FRANK 0.1 REQUIREMENT\n')
      obj=json.loads(lock.read_text())
      for e in obj['sources']:
        if e['role']=='adaptive_visual_learning_directive': e['git_blob_sha']=freeze.blob(p.read_bytes())
      lock.write_text(json.dumps(obj))
      _,v=freeze.build(root,lock)
      self.assertTrue(any('adaptive_visual_learning_directive missing marker' in x for x in v))
    finally: td.cleanup()

  def test_source_sha_mismatch_fails_closed(self):
    td,root,lock=self.setup_tree()
    try:
      obj=json.loads(lock.read_text()); obj['sources'][0]['git_blob_sha']='0'*40; lock.write_text(json.dumps(obj))
      _,v=freeze.build(root,lock); self.assertTrue(any('git blob mismatch' in x for x in v))
    finally: td.cleanup()

  def test_missing_required_organ_fails(self):
    td,root,lock=self.setup_tree()
    try:
      bad=dict(ARCH); bad['semantic_organs']=[x for x in ARCH['semantic_organs'] if x['id']!='effect_gateway']
      p=root/'arch.json'; p.write_text(json.dumps(bad)+'\n'); obj=json.loads(lock.read_text())
      for e in obj['sources']:
        if e['role']=='loop_projection': e['git_blob_sha']=freeze.blob(p.read_bytes())
      lock.write_text(json.dumps(obj))
      _,v=freeze.build(root,lock); self.assertIn('missing organ:effect_gateway',v)
    finally: td.cleanup()

if __name__=='__main__': unittest.main(verbosity=2)
