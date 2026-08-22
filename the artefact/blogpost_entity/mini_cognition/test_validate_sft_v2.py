#!/usr/bin/env python3
from validate_sft_v2 import validate_code

BASE='''module clay.cog.turn
fn think(i:Map)->Map {
  let c = cog_new()
  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
  role_bind(c,cfg("application.role"))
  goal_bind(c,cfg("application.goal"))
  personality_bind(c,cfg("application.personality"))
%s
  return c
}'''

def main():
    clean=BASE % '  self_state(c,"control_label","uncertainty","COMPUTED")'
    poison_name=BASE % '  self_state(c,"name","Zero","COMPUTED")'
    poison_role=BASE % '  state_note(c,"role","blogger","REPORTED")'
    assert validate_code(clean)==[], validate_code(clean)
    assert "weight_literal_reserved_key:name" in validate_code(poison_name), validate_code(poison_name)
    assert "weight_literal_reserved_key:role" in validate_code(poison_role), validate_code(poison_role)
    print("PASS identity/application weight-literal gate")

if __name__=="__main__": main()
