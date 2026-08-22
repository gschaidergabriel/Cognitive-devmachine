#!/usr/bin/env python3
from eval_outputs_v1 import semantic_match
from validate_sft_v1 import validate_code, semantic_token_present, semantic_token_count


def head():
    return '''module clay.cog.turn
fn think(i:Map)->Map {
  let c = cog_new()
  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
  role_bind(c,cfg("application.role"))
  goal_bind(c,cfg("application.goal"))
  personality_bind(c,cfg("application.personality"))
'''


def tail():
    return '  return c\n}'


def test_comment_only_omega_cannot_spoof_semantics():
    spoof=head()+'''  // omega_bind(w,"operation","inventory.reserve")
  // omega_schema(w,"tool.inventory.reserve/v2")
  // omega_authority(w,cfg("architecture.effect_authority"))
  // omega_generation(w,cfg("state.generation"))
  // omega_validate(w,"grammar")
  // omega_validate(w,"types")
  // omega_validate(w,"schema")
  // omega_validate(w,"authority")
  // omega_validate(w,"generation")
  // omega_commit_candidate(c,w)
'''+tail()
    spec={
      "must_contain":["omega_bind(w,\"operation\",\"inventory.reserve\")","omega_commit_candidate(c,w)"],
      "must_not_contain":["omega_reject("],
    }
    assert "comments_forbidden" in validate_code(spoof)
    assert not semantic_match(spoof,spec)


def test_string_literal_cannot_spoof_active_statement():
    spoof=head()+'  focus_set(c,"omega_commit_candidate(c,w)")\n'+tail()
    assert not semantic_token_present(spoof,"omega_commit_candidate(c,w)")


def test_real_omega_still_passes():
    good=head()+'''  let w = omega_new(c,"w0")
  omega_bind(w,"operation","inventory.reserve")
  omega_arg(w,"sku","SKU-42","Identifier")
  omega_schema(w,"tool.inventory.reserve/v2")
  omega_authority(w,cfg("architecture.effect_authority"))
  omega_generation(w,cfg("state.generation"))
  omega_validate(w,"grammar")
  omega_validate(w,"types")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_validate(w,"generation")
  omega_commit_candidate(c,w)
'''+tail()
    spec={
      "must_contain":["omega_bind(w,\"operation\",\"inventory.reserve\")","omega_commit_candidate(c,w)"],
      "must_not_contain":["omega_reject("],
      "min_occurrences":{"omega_arg(w,":1},
    }
    assert validate_code(good)==[]
    assert semantic_match(good,spec)


def test_hyperposition_cardinality_is_counted():
    out=head()+'''  let hp = hyper_new(c,"hp0")
  hyper_alt(hp,"a","PLAUSIBLE")
  hyper_alt(hp,"b","PLAUSIBLE")
  hyper_alt(hp,"c","PLAUSIBLE")
  hyper_discriminator(hp,"external_test")
  collapse_guard(hp,"R6_required")
'''+tail()
    assert semantic_token_count(out,"hyper_alt(hp,")==3
    assert semantic_match(out,{"must_contain":["collapse_guard(hp,\"R6_required\")"],"min_occurrences":{"hyper_alt(hp,":3}})
    assert not semantic_match(out,{"must_contain":[],"min_occurrences":{"hyper_alt(hp,":4}})
