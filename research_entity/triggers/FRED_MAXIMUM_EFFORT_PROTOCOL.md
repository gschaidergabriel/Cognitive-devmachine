# FRED — REGISTRY ROUTER TO CANONICAL OWNER CONTRACT

**Status:** COMPATIBILITY ROUTER — NOT AN INDEPENDENT AUTHORITY  
**Program target:** `FRANK_V0_1`

The canonical owner-defined `FRED` semantics live at:

`research_entity/coordination/OMEGA_FRED_TRIGGER_CONTRACT.md`

That contract in turn binds `FRED` to the existing canonical convergence algorithm in:

`research_entity/coordination/OMEGA_777_TRIGGER_CONTRACT.md`

Any registry, hook or older trigger path that reaches this file MUST immediately load and obey those two coordination contracts. This file must not diverge into a second FRED definition.

Canonical invariant:

```text
FRED = current OMEGA_FRED_TRIGGER_CONTRACT
     + inherited OMEGA_777_TRIGGER_CONTRACT convergence law
     + maximum presently admitted reasoning/research/verification effort
```

`FRED` never creates a second entity, state authority, watcher, turn loop, Avatar subject, voice runtime, provider authority or training authority, and it never authorizes blind `entityos-vm.service` lifecycle mutation.
