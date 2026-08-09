# KMP — ClayCode control/effect closure candidate

packet_id: `KMP-CC-CONTROL-EFFECT-CLOSURE-20260809`  
domains: `xeno_claycode`, `security_capabilities`, `formal_methods_testing`, `frank_gwt`  
epistemic_class: `EXECUTABLE_PROXY_SUPPORTED_HYPOTHESIS`  
status_hint: `OPEN`  
origin_actor: `chatgpt-secondary`  
provider/model: `OpenAI / GPT-5.6 Sol`  
canonical_parent: `RAE-8.8 r2 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Atomic claim

ClayCode's next BASE control-flow gap can be approached in canonical typed IR without a new FRANK-specific primitive, while function effect summaries must close transitively over calls and remain distinct from runtime execution authority.

Candidate invariant:

`potential_effect_summary != runtime_effect_authority`

and

`recursive/reentry semantic lineage != carried-forward permit`.

## Evidence

Local isolated Linux executable proxy, seed `202608091724`:

- 50,000 branch + recursive-call + Result/match semantic differential cases: 0 mismatches;
- 20,000 randomized transitive-effect graph mutations: 0 false accepts after deleting an actually inferred effect;
- omitted transitive caller effect: rejected;
- valid static effect closure with absent runtime permit: rejected;
- same effect with matching runtime permit: executed;
- runaway recursion without sufficient step budget: rejected;
- undefined static call: rejected.

Program semantic identity changed for control/effect semantic mutations and remained unchanged for set-order-equivalent effect representation. Runtime permit identity was intentionally excluded from the program semantic hash.

Independent comparison anchors: WebAssembly structured control, LLVM control/call + memory-effect properties, and Koka row-polymorphic effect typing. These do not select ClayCode syntax.

## Negative / boundary

This is not production G9 compiler evidence, E2B evidence, target Ubuntu evidence, Qwen-reader evidence, application-suite PASS or scientific promotion.

## Falsifier / next test

Integrate the smallest control/effect form into the production parser + canonical typed IR + type/effect checker, lower it on Andreas' Ubuntu developer target, then test capability revoke/regrant and FFI/subprocess escape. Reject/refine this packet if a simpler production mechanism preserves semantics, diagnostics and authority non-amplification with lower repair/runtime cost.

## Source refs

- `research_entity/trigger_runs/claycode/claycode-20260809T1724p0700-chatgpt-secondary-control-effect-closure/EXECUTABLE_RESEARCH_RECEIPT.json`
- `research_entity/trigger_runs/claycode/claycode-20260809T1724p0700-chatgpt-secondary-control-effect-closure/HYPOTHESIS_MATRIX.json`
- `research_entity/trigger_runs/claycode/claycode-20260809T1724p0700-chatgpt-secondary-control-effect-closure/NEGATIVE_RESULTS.json`
