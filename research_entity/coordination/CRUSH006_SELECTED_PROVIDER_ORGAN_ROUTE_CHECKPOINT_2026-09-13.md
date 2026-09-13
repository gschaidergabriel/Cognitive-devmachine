# CRUSH006 — SELECTED PROVIDER / ORGAN ROUTE CHECKPOINT — 2026-09-13

Status: **FULL BOUNDED EXACT-DONOR COMPILE PASS**

This checkpoint promotes only post-selection route classification for the existing Free-Frank/Crush provider surfaces. It does not dispatch a provider, reactivate FreeSwarm/Free-Pool authority, mutate Gabriel's live Free-Frank harness, install a production Crush binary, create a second router/event bus/turn loop, or promote whole OMEGA/HCU/GRID/GWT/J-Space/training/product credit.

## Exact subjects

- research branch: `chatgpt-work/entityos-crush-omega-bootstrap-20260913`
- CRUSH006 source head under validation: `90f3193e74026344d0e0ed8c368e0251d8f3e6a5`
- source commits:
  - `395a53b21cbb05347853c1811be5f25c43ed8791` — `CRUSH006: classify already-selected Crush organ route`
  - `4e8a49490003271fabe066d9d5f77be7071cdc98` — `CRUSH006: test selected-provider organ classification`
  - `90f3193e74026344d0e0ed8c368e0251d8f3e6a5` — `CRUSH006: observe selected Free-Frank provider family`
- exact upstream donor: `charmbracelet/crush@d333e04385f9e1d1523cea7b417cb5e8798a713a`
- validation host: `machine_id=ai-core-node`, `owner=gabriel`, `execution_boundary=REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

## Why this gate exists

CRUSH004 established one portable `omega.OrganRoute` contract and persisted its digest through OMEGA turn/reentry history.

CRUSH005 established evidence-only constructors for already-existing ChatGPT, Claude Code/CLI, and Free-Pool execution surfaces.

The remaining ambiguity was at the real Free-Frank/Crush callsite: the agent still emitted every already-selected Crush provider as generic `crush-model`, even though Gabriel's live harness has semantically distinct provider families.

CRUSH006 closes that ambiguity without adding a router. Classification happens **after Crush has already selected `largeModel.ModelCfg.Provider` and `.Model`**.

## Real Free-Frank route evidence

A read-only Local-Bridge forensic on Gabriel's live host, command

`crush006-ai-core-node-20260913-live-harness-route-forensic`

returned PASS/0 and bound the current harness provider identities.

Existing Free-Pool provider IDs in `/home/ai-core-node/.claude/star/harness_crush.py`:

- `freepool-nvidia` -> `nvidia/nemotron-3-super-120b-a12b`
- `freepool-groq` -> `openai/gpt-oss-120b`
- `freepool-mistral` -> `mistral-small-latest`
- `freepool-openrouter` -> `deepseek/deepseek-chat`

Existing explicit Claude CLI route:

- provider id: `claude-cli`
- loopback OpenAI-compatible shim: `http://127.0.0.1:8420/v1`
- existing backend/service lineage: `claude_cli_shim.py` / `claude-cli-shim.service`
- representative configured models include `claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5-20251001`
- source explicitly keeps this lane outside Free-Pool automatic fallback; it is an explicitly selected paid Claude route.

The Free-Frank button only checks/displays the separate existing ChatGPT-Bridge service status. That status probe is **not** treated as evidence that the Crush model inference ran through ChatGPT.

## CRUSH006 delta

`internal/omega/external_route.go` now defines the pure post-selection classifier:

`ObserveCrushProviderRoute(providerID, modelID string) OrganRoute`

Rules:

- exact provider `claude-cli`
  -> `kind=bridge`, `organ_id=claude-code`, `adapter_id=crush-native`
- provider prefix `freepool-`
  -> `kind=provider`, `organ_id=free-pool`, `adapter_id=crush-native`
- any other already-selected Crush provider
  -> `kind=provider`, `organ_id=crush-model`, `adapter_id=crush-native`

The exact selected `provider_id` and `model_id` remain in the evidence/digest.

This function performs **no**:

- provider lookup;
- credential read;
- authority decision;
- fallback selection;
- retry;
- network dispatch;
- model invocation;
- effect;
- state-authority creation.

`patch_agent.py` now passes:

`omega.ObserveCrushProviderRoute(largeModel.ModelCfg.Provider, largeModel.ModelCfg.Model)`

into the existing single `cognitiveRuntime.Compile(...)` call. There is no second compile, router, event loop, or state path.

## Tests

The CRUSH006 package test covers the exact current provider families observed on Gabriel's live harness plus a generic provider control.

It checks:

1. `claude-cli` classifies as the Claude Code/CLI bridge organ.
2. all four current `freepool-*` IDs classify as the Free-Pool provider organ.
3. an ordinary provider remains generic `crush-model`.
4. `adapter_id` remains `crush-native`.
5. exact selected provider/model values are preserved.
6. every classified route yields a non-empty route digest.
7. existing CRUSH005 organ-swap EntityIdentity/reentry tests remain in the same package suite.

## Exact-donor real-host closure

Validator:

`crush006-ai-core-node-20260913-provider-classify-compile`

Receipt:

- status: `PASS`
- exit: `0`
- machine_id: `ai-core-node`
- owner: `gabriel`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- exact donor: `d333e04385f9e1d1523cea7b417cb5e8798a713a`
- exact seed: `90f3193e74026344d0e0ed8c368e0251d8f3e6a5`
- toolchain: `go version go1.27.1 linux/amd64`
- patched exact donor contains exactly one `ObserveCrushProviderRoute` agent callsite
- stale literal agent route binding rejected by validator
- `go test ./internal/omega -count=1` -> PASS
- `go test ./internal/agent -run '^$' -count=1` -> PASS / compile closure

Markers:

- `CRUSH006_PROVIDER_CLASSIFICATION_GO_TEST_PASS`
- `CRUSH006_AGENT_BINDING_COMPILE_PASS`
- `CRUSH006_LIVE_HARNESS_BYTE_INVARIANT_PASS`

## Live-harness invariance

Before and after validation:

- `/home/ai-core-node/.claude/star/harness_crush_knopf.sh`
  - `95a9311a4f47457b3c5e100fe9bd8d62253711eb889386e521bc68a3ddf7fce3`
- `/home/ai-core-node/.claude/star/harness_crush_knopf.py`
  - `db05347f908c891e526bdb47d6497e24aa1defc94b824f502ecd579ab73dbd61`
- `/home/ai-core-node/.claude/star/harness_crush.py`
  - `59a3a043c0b4b687e998837027f86a8fd982ff4038ca58b8834f3243ae2b0613`
- `/home/ai-core-node/frankenstein-repo/CRUSH.md`
  - `1980f471ff088d3fea923b66f69eb1e0e8d837f546c86a84740111bbbeddbf99`

All four subjects remained byte-identical.

## Existing canonical-turn ingress remains single

Readback of the current Frankenstein lane found no reason to create another event fabric:

- `stern.py::_f2wp1207_turn_loop_auto(...)` explicitly remains **the** productive reader/caller for the canonical GRID10 turn-loop on a prompt.
- it feeds the existing strict `F2WP1207_TYPED_ENTRY/v1` bridge and then `run_canonical_turn(...)`.
- the persistent ChatGPT host client already calls this existing hook exactly once in its turn-context path.
- `omega_organ_activity.py` is presentation-floor arbitration, not a canonical state/event authority.

CRUSH006 therefore leaves the Python canonical turn ingress untouched.

## ChatGPT route fence

The portable `ObserveChatGPTBridge(...)` helper remains valid and tested from CRUSH005, but CRUSH006 deliberately does **not** call it from the native Crush inference seam merely because the desktop button reports `ChatGPT-Bridge: AN`.

A service-status probe is not a model-execution receipt.

The real Gabriel terminal/ChatGPT organ path already has its own correlated run lifecycle (`f2_chatgpt_organ_run`) and binds source GRID frame/pointer/turn/runtime/session identifiers. A future ChatGPT route adaptation must attach at the actual `chatgpt_senden` / exact-backend execution boundary or equivalent exact callsite, not at bridge-status presentation and not by adding another canonical turn.

## Promotion fence

Promoted now, and only now:

**CRUSH006 selected-provider organ-route classification for the existing Free-Frank Free-Pool / Claude-CLI lanes + exact-donor Go-1.27 component compile closure.**

Not promoted:

- actual provider execution;
- provider/Free-Pool/FreeSwarm authority;
- automatic Claude fallback;
- actual ChatGPT bridge route adaptation;
- live Free-Frank/Crush installation;
- production Crush binary activation;
- terminal harness T1-T8 acceptance;
- whole OMEGA cognition;
- whole HCU/GRID/GWT/J-Space semantics;
- training;
- Andreas host/runtime state.

## Next nonduplicate boundary

Do not add another router or another canonical turn-loop.

Highest-information next boundary is a **read-only exact-callsite audit of the real ChatGPT organ backend**, followed—only if the execution boundary is unambiguous—by adapting the actual send/harvest execution observation into the same `OrganRoute` evidence contract while preserving exactly-once canonical GRID ownership and the existing bridge's dispatch/login/authority rules.

Production installation of the CRUSH Go seam remains a separate activation gate and requires refreshed current authority because the live Free-Frank harness is intentionally still invariant.
