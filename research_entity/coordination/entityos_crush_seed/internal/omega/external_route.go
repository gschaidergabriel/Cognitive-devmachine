package omega

const (
	// External route kinds are observations only. They do not grant dispatch,
	// provider, effect, or mutation authority.
	ExternalRouteKindBridge   = "bridge"
	ExternalRouteKindProvider = "provider"

	ExternalOrganChatGPT    = "chatgpt"
	ExternalOrganClaudeCode = "claude-code"
	ExternalOrganFreePool   = "free-pool"
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
