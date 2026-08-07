# AUTHORITATIVE STATE RESOLUTION — RAE-8.8

## Canonical authority order

1. Verified remote head in the dedicated GitHub backend repository
   `gschaidergabriel/clay-global-research-entity`:
   `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`

2. If remote is temporarily unavailable:
   last locally verified snapshot whose parent/hash lineage matches the remote head.

3. Project Files / File Library:
   SOURCE CACHE ONLY. Never authoritative merely because a file has the same name.

4. Chat history / model memory:
   non-authoritative.

## Known historical state

Older Project/File-Library copies may contain Research Entity revision 1 / Clay generation 2.
They are historical inputs, not the current canonical head.

Current research head:
- Research Entity revision: 2
- Clay generation: 3
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Boot rule

Never select a state by filename or modification time alone.
Resolve revision + parent_revision + parent_state_hash + state_hash + backend commit lineage.
If two valid heads diverge, preserve both branches and merge explicitly.

## Research revision rule

Repository/bootstrap/governance/configuration changes do not increment the Research Entity revision or Clay generation unless they contain a valid empirical research progression event.

## Scope rule

The backend repository name does not constrain the research domain. The Research Entity is project-wide and studies complete cognitive-system architecture. Synthetic Clay is one target substrate; host/runtime/environment research remains independent and cross-platform.
