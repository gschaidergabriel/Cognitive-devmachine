# RAE-vNext Reserved Research Trigger System — Implementation Report

**Date:** 2026-08-08  
**Origin actor:** `chatgpt-secondary`  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Scientific revision changed:** no  
**Canonical scientific parent:** RAE-8.8 revision 2 / Clay G3 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Implemented

The project now has exact full-message research triggers:

`dump · clay · gwt · frank · emergenz · claycode · hyperposition`

Trigger matching is case-insensitive but only fires when the entire trimmed user message equals the trigger word.

The authoritative registry is `research_entity/global/RESEARCH_TRIGGER_REGISTRY.json`; the existing `PROJECT_COMMAND_REGISTRY.json` mirrors those commands for boot-time routing.

## Master research cycle

Non-dump research triggers use `research_entity/triggers/MASTER_RESEARCH_TRIGGER_PROTOCOL.md`:

boot/ground evidence → Fusion 1 → falsifiable hypotheses/counterhypotheses → clustered arXiv/GitHub/Reddit/primary-source research → Fusion 2 + contradiction/pattern analysis → transformed hypothesis generation → feasible empirical tests → synthesis/architecture delta → surgical micro-packets + Topic Packets → final report/promotion decision.

`clay` is the integrated master foundry and explicitly covers GWT-in-AI, whole-FRANK architecture, emergence measurement, ClayCode/4B internal-language research, hyperposition/higher-order codependency, near-zero-latency software and cross-platform/Android constraints. It targets at least 50 materially distinct first-generation falsifiable hypotheses per full master run.

## Claude Code enforcement

`.claude/hooks/rae_hook.py` now resolves the exact trigger registry before ordinary task routing. A recognized research trigger receives:
- a task-specific RAE context;
- a durable `rae run start` attempt;
- the master research protocol;
- the trigger-specific protocol;
- the mandatory status-footer protocol.

`dump` retains its special fail-closed freeze/hash/archive lifecycle.

## Knowledge compiler

Added `KNOWLEDGE_MICRO_PACKET_PROTOCOL.md` for small independently retrievable text packets with source/actor/model/status/falsifier metadata.

Added `tools/materialize_micro_packets.py`, which creates a rebuildable text projection under `research_sources/derived/knowledge_micro_packets/`; the existing SQLite source materialization can index that derivative without treating it as raw evidence.

An initial Synthetic Clay seed was compiled from the uploaded `SYNTHETIC_CLAY_RAE83_G1_COMPLETE_RUN.zip`, SHA-256 `9e09b772e470adf89367c109b3f4491995fd7e5928de653222ea82441d2cdaa0`. Seed packets include the multi-plane world model, hyperposition semantics, activation-vs-truth separation, causal GWT episodes, adaptive coupling, emergence certificate, Qwen-4B transform-kernel hypothesis, ClayCode authority boundary, Anti-Goodhart active-context result and G1 evidence boundaries.

## Visible operational status

Every substantive Research-Entity response must follow `STATUS_FOOTER_PROTOCOL.md`, reporting current-session Entity/GitHub verification, canonical revision/hash, actor, active trigger, write state, all trigger words and an honest completion percentage for the last user prompt.

## Validation

CI was extended to:
- validate the trigger registry/protocol paths;
- compile the Claude hook;
- materialize micro-packets before source/topic/SQLite materialization;
- verify that the micro-packet projection reaches the searchable SQLite source plane;
- preserve existing retrieval, writer and dump-lifecycle checks.

This report records implementation, not a claim that every future trigger run will succeed or that every historical source has already been micro-packetized. Full-corpus packet compilation remains an incremental source-processing task.
