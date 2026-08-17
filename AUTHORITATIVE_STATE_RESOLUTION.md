# AUTHORITATIVE STATE RESOLUTION — RAE-8.8

## Owner mission authority

The sole current product/research mission directive is:

`CLAYVERSE_CANONICAL_DIRECTIVE.md`

It is the highest current owner instruction for target selection, product boundary and `go` behavior. Older mission/scope/bootstrap files are historical evidence wherever they conflict with it.

This does **not** erase empirical research continuity. The canonical research-state object below remains authoritative for its own revision/hash/evidence lineage. Governance-only mission changes do not automatically increment a research revision or Clay generation.

## Canonical empirical-state authority order

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
They are historical inputs, not the current canonical empirical head.

Current canonical empirical research state recorded by `RESEARCH_ENTITY_CANONICAL.json`:
- Research Entity revision: 2
- Clay generation: 3
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Boot rule

Boot mission first from `CLAYVERSE_CANONICAL_DIRECTIVE.md`, then resolve empirical continuity.

Never select a state by filename or modification time alone.
Resolve revision + parent_revision + parent_state_hash + state_hash + backend commit lineage.
If two valid heads diverge, preserve both branches and merge explicitly.

For implementation technologies, also resolve commit lineage, successor status, negative evidence, candidate/promoted/canonical status and exact receipts before choosing a ClayVerse generation.

## Research revision rule

Repository/bootstrap/governance/configuration changes do not increment the Research Entity revision or Clay generation unless they contain a valid empirical research progression event.

## Scope rule

The active product/research scope is now ClayVerse as defined by `CLAYVERSE_CANONICAL_DIRECTIVE.md`.

UCM/UCM2, Frank, ClayCode, UnifiedDB, ClayGraph, Hyperposition, GWT and EntityOS remain valid research/evidence/donor lineages but are no longer independent competing mission targets.
