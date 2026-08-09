# 666 Run Report — PF ce007 semantic lineage

## Identity
- Trigger: `666`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Level: L0 Archive Assimilation
- Task: `666-l0-pf-ce007-semantic-lineage-20260809T1210p0700`

## Scope
Bounded semantic architecture-lineage audit of Project-Frankenstein commit `ce00787f4cabe65859132a762251e39449ad5ca5` against base `0fd27f23e87cd1f0b53ce838347d1cdbcb7bd9bb`. Existing workers own Segment02b path/blob denominator closure; this run does not claim exhaustive changed-path coverage.

## Evidence read
- exact commit/diff metadata for `ce00787...`
- `router/app.py` before/after
- `modeld/app.py` before/after
- `services/consciousness_daemon.py` before/after
- deleted overlay evidence showing WebUI↔Overlay synchronization

## Synthesis
1. The headline migration removes the desktop overlay and writer surfaces and elevates the already-existing Web UI to the sole interaction interface.
2. The same commit also collapses the router from Qwen2.5-3B + Llama 8B + DeepSeek-R1 tiers to direct single-model Qwen2.5-3B routing.
3. `modeld` simultaneously loses its DeepSeek backend and remains as an empty-backend service skeleton.
4. Persistent consciousness/workspace state machinery remains present. The change therefore cuts presentation/inference topology more aggressively than persistent cognitive-state topology.
5. Because the commit description under-specifies the router/modeld collapse, path/blob identity alone is insufficient for semantic archive assimilation of high-impact runtime files.

## Epistemic limits
- Historical lineage evidence only; no claim that this architecture was better, stable, or current.
- Persistence of code is not proof that GWT-like causal function was preserved at runtime.
- No global L0 percentage added; full Project-Frankenstein tree/history denominator remains gate work.

## Durable artifact
`research_entity/archive_assimilation/receipts/666_20260809T1216p0700_chatgpt_secondary_pf_ce007_semantic_lineage.json`

## Branch feedback
- FRANK: preserve separation between interface topology, inference routing and persistent cognitive-state mechanisms in lineage/migration reasoning.
- GWT: code persistence across UI/router simplification is lineage evidence, not causal validation; lesion/rescue remains necessary.
- CENTER: add semantic-read guard for high-impact modified runtime paths alongside exact identity enumeration.
