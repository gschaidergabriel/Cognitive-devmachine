#include "mini_entity_part00.inc"
#include "mini_entity_part01.inc"
#include "mini_entity_child_env.inc"
#define execvp mini_entity_execvp_isolated
#include "mini_entity_part02.inc"
#undef execvp
#include "mini_entity_part03.inc"
#include "mini_entity_gate.inc"
#define build_user_prompt mini_entity_gated_build_user_prompt
#define commit_run mini_entity_gated_commit_run
#include "mini_entity_part04.inc"
#undef commit_run
#undef build_user_prompt
