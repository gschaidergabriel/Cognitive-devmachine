<!-- RAE_META
{"packet_id":"KMP-CC9-COMPOSITIONAL-EFFECT-CLOSURE","title":"ClayCode effect closure must be transitive, alias-normalized and dispatch-conservative","domains":["xeno_claycode","security_capabilities","systems_architecture"],"topics":["effect system","alias analysis","dynamic dispatch","FFI","capabilities","closure"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"OPEN_REFINED_CANDIDATE","origin_actor":"chatgpt-secondary","origin_run":"claycode-20260808T1723p0700-chatgpt-secondary","affected_branches":["frank","clay","hyperposition","claygraph","claycode"],"falsifier_or_next_test":"Compile 10-20 real FRANK operations and compare inferred closure against fully interposed runtime traces under callbacks, aliases, plugins and FFI."}
RAE_META -->

## Result
CC9 extends CC8's static-envelope/observed-trace rule: static closure must be **compositional** over transitive calls; a finite dynamic-dispatch set contributes the union of all possible target summaries; authority/conflict resources are canonicalized before comparison; unknown reflection/FFI/plugin dispatch maps to incomplete/TOP and escalates.

Local 100k constructed workload: direct-only escape 64.489%; one predicted dynamic target escape 43.816%; closed-world union escape 0%; unknown-dispatch escalation 3.237%. Judge0 50k reproduced 64.15%, 43.8%, 0%, 3.246%. The all-target envelope was substantially wider, so closure width is a required cost shadow.

Alias toy: raw symbolic IDs missed 99.9506% of constructed true alias conflicts; canonical resource identity detected all by construction. Judge0 reproduced 99.9403% raw alias miss among true conflicts.

## External convergence
Koka tracks/composes function effects in types; LLVM documents May/Must/NoAlias analysis and the need to update alias information after transformations; current systems/type literature treats aliasing, effects and capability boundaries as separate but composable concerns.
