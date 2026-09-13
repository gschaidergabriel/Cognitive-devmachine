package omega

import "strings"

const (
	// External route kinds are observations only. They do not grant dispatch,
	// provider, effect, or mutation authority.
	ExternalRouteKindBridge   = "bridge"
	ExternalRouteKindProvider = "provider"

	ExternalOrganChatGPT    = "chatgpt"
	ExternalOrganClaudeCode = "claude-code"
	ExternalOrganFreePool   = "free-pool"
	ExternalOrganCrushModel = "crush-model"

	// These identifiers are already selected by the existing Free-Frank/Crush
	// harness. OMEGA only classifies the selected route after the fact; it never
	// chooses a provider from these constants.
	CrushNativeAdapter          = "crush-native"
	CrushClaudeCLIProviderID    = "claude-cli"
	CrushFreePoolProviderPrefix = "freepool-"
)

// ObserveChatGPTBridge maps the already-existing Frankenstein ChatGPT bridge
// into OMEGA's portable OrganRoute evidence. It does not send a prompt, harvest
// a result, select a model, or replace the bridge's own login/lock/authority
// gates.
func ObserveChatGPTBridge(adapterID, providerID, modelID string) OrganRoute {
	return OrganRoute{
		Kind:       ExternalRouteKindBridge,
		OrganID:    ExternalOrganChatGPT,
		AdapterID:  adapterID,
		ProviderID: providerID,
		ModelID:    modelID,
	}.Normalized()
}

// ObserveClaudeCodeBridge maps an already-selected Claude Code / CLI path into
// route evidence only. Claude execution and permissions remain owned by the
// existing outer bridge/CLI surface.
func ObserveClaudeCodeBridge(adapterID, providerID, modelID string) OrganRoute {
	return OrganRoute{
		Kind:       ExternalRouteKindBridge,
		OrganID:    ExternalOrganClaudeCode,
		AdapterID:  adapterID,
		ProviderID: providerID,
		ModelID:    modelID,
	}.Normalized()
}

// ObserveFreePoolProvider maps an already-selected Free-Pool provider path into
// route evidence only. In particular, constructing this value cannot admit or
// invoke a provider route; current external-provider authority remains entirely
// outside OMEGA.
func ObserveFreePoolProvider(adapterID, providerID, modelID string) OrganRoute {
	return OrganRoute{
		Kind:       ExternalRouteKindProvider,
		OrganID:    ExternalOrganFreePool,
		AdapterID:  adapterID,
		ProviderID: providerID,
		ModelID:    modelID,
	}.Normalized()
}

// ObserveCrushProviderRoute classifies the provider/model that Crush has
// ALREADY selected for the current inference call. It is deliberately not a
// router: there is no provider lookup, fallback, credential check, dispatch,
// retry, or authority decision here.
//
// The current Free-Frank harness exposes two semantically important provider
// families through Crush itself:
//   - provider id "claude-cli" is the explicit Claude Code/CLI bridge;
//   - provider ids prefixed "freepool-" are the existing Free-Pool lane.
// Everything else stays a generic native Crush model route. Exact provider and
// model ids remain in the evidence so route digests still distinguish concrete
// executions inside the same organ family.
func ObserveCrushProviderRoute(providerID, modelID string) OrganRoute {
	providerID = strings.TrimSpace(providerID)
	modelID = strings.TrimSpace(modelID)

	switch {
	case providerID == CrushClaudeCLIProviderID:
		return ObserveClaudeCodeBridge(CrushNativeAdapter, providerID, modelID)
	case strings.HasPrefix(providerID, CrushFreePoolProviderPrefix):
		return ObserveFreePoolProvider(CrushNativeAdapter, providerID, modelID)
	default:
		return OrganRoute{
			Kind:       ExternalRouteKindProvider,
			OrganID:    ExternalOrganCrushModel,
			AdapterID:  CrushNativeAdapter,
			ProviderID: providerID,
			ModelID:    modelID,
		}.Normalized()
	}
}
