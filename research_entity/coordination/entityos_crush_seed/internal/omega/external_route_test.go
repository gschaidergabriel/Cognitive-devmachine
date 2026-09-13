package omega

import (
	"context"
	"path/filepath"
	"testing"
)

func TestExternalOrganRoutesAreDistinctNormalizedEvidence(t *testing.T) {
	chatgpt := ObserveChatGPTBridge("  frankenstein-chatgpt-burst  ", " openai ", " gpt-5.6-sol ")
	claude := ObserveClaudeCodeBridge(" claude-cli ", " anthropic ", " claude-code ")
	freePool := ObserveFreePoolProvider(" crush-free-pool ", " free-provider ", " free-model ")

	if chatgpt.Kind != ExternalRouteKindBridge || chatgpt.OrganID != ExternalOrganChatGPT || chatgpt.AdapterID != "frankenstein-chatgpt-burst" {
		t.Fatalf("unexpected normalized ChatGPT route: %#v", chatgpt)
	}
	if claude.Kind != ExternalRouteKindBridge || claude.OrganID != ExternalOrganClaudeCode {
		t.Fatalf("unexpected Claude route: %#v", claude)
	}
	if freePool.Kind != ExternalRouteKindProvider || freePool.OrganID != ExternalOrganFreePool {
		t.Fatalf("unexpected Free-Pool route: %#v", freePool)
	}

	digests := map[string]bool{}
	for _, route := range []OrganRoute{chatgpt, claude, freePool} {
		digest := route.Digest()
		if digest == "" {
			t.Fatalf("route produced empty digest: %#v", route)
		}
		if digests[digest] {
			t.Fatalf("distinct organ routes collapsed to one digest: %s", digest)
		}
		digests[digest] = true
	}
}

func TestObserveCrushProviderRouteClassifiesExistingHarnessRoutes(t *testing.T) {
	tests := []struct {
		name       string
		providerID string
		modelID    string
		wantKind   string
		wantOrgan  string
	}{
		{
			name:       "explicit claude cli",
			providerID: "claude-cli",
			modelID:    "claude-sonnet-5",
			wantKind:   ExternalRouteKindBridge,
			wantOrgan:  ExternalOrganClaudeCode,
		},
		{
			name:       "freepool nvidia",
			providerID: "freepool-nvidia",
			modelID:    "nvidia/nemotron-3-super-120b-a12b",
			wantKind:   ExternalRouteKindProvider,
			wantOrgan:  ExternalOrganFreePool,
		},
		{
			name:       "freepool groq",
			providerID: "freepool-groq",
			modelID:    "openai/gpt-oss-120b",
			wantKind:   ExternalRouteKindProvider,
			wantOrgan:  ExternalOrganFreePool,
		},
		{
			name:       "freepool mistral",
			providerID: "freepool-mistral",
			modelID:    "mistral-small-latest",
			wantKind:   ExternalRouteKindProvider,
			wantOrgan:  ExternalOrganFreePool,
		},
		{
			name:       "freepool openrouter",
			providerID: "freepool-openrouter",
			modelID:    "deepseek/deepseek-chat",
			wantKind:   ExternalRouteKindProvider,
			wantOrgan:  ExternalOrganFreePool,
		},
		{
			name:       "ordinary crush provider stays generic",
			providerID: "openai",
			modelID:    "gpt-test",
			wantKind:   ExternalRouteKindProvider,
			wantOrgan:  ExternalOrganCrushModel,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			route := ObserveCrushProviderRoute("  "+tt.providerID+"  ", "  "+tt.modelID+"  ")
			if route.Kind != tt.wantKind || route.OrganID != tt.wantOrgan {
				t.Fatalf("unexpected classification: %#v", route)
			}
			if route.AdapterID != CrushNativeAdapter {
				t.Fatalf("unexpected adapter: got %q want %q", route.AdapterID, CrushNativeAdapter)
			}
			if route.ProviderID != tt.providerID || route.ModelID != tt.modelID {
				t.Fatalf("selected provider/model evidence changed: %#v", route)
			}
			if route.Digest() == "" {
				t.Fatal("classified route produced empty digest")
			}
		})
	}
}

func TestExternalRouteEvidenceDoesNotLeakIntoSystemContext(t *testing.T) {
	route := ObserveChatGPTBridge("frankenstein-chatgpt-burst", "openai", "gpt-5.6-sol")
	frame := Frame{Version: Version, RouteDigest: route.Digest()}
	if got := frame.RenderSystemContext(); got != "" {
		t.Fatalf("route-only evidence leaked into model context: %q", got)
	}
}

func TestExternalOrganSwapPreservesEntityIdentityAndReentry(t *testing.T) {
	ctx := context.Background()
	statePath := filepath.Join(t.TempDir(), "omega", "state.json")
	runtime, err := NewPersistentRuntime(statePath)
	if err != nil {
		t.Fatal(err)
	}

	routes := []OrganRoute{
		ObserveChatGPTBridge("frankenstein-chatgpt-burst", "openai", "gpt-5.6-sol"),
		ObserveClaudeCodeBridge("claude-cli", "anthropic", "claude-code"),
		ObserveFreePoolProvider("crush-free-pool", "free-provider", "free-model"),
	}
	runIDs := []string{"chatgpt-turn", "claude-turn", "free-pool-turn"}

	var entityID string
	var predecessor string
	for i, route := range routes {
		frame, err := runtime.Compile(ctx, TurnInput{
			SessionID: "external-organ-swap",
			RunID:     runIDs[i],
			Prompt:    "same semantic input",
			Route:     route,
		})
		if err != nil {
			t.Fatal(err)
		}
		if i == 0 {
			entityID = frame.EntityID
		} else {
			if frame.EntityID != entityID {
				t.Fatalf("entity identity changed across organ swap: %q -> %q", entityID, frame.EntityID)
			}
			if frame.PredecessorTurnID != predecessor {
				t.Fatalf("reentry chain broke at organ %d: got predecessor %q want %q", i, frame.PredecessorTurnID, predecessor)
			}
		}
		if frame.RouteDigest != route.Digest() {
			t.Fatalf("compiled route digest mismatch: got %q want %q", frame.RouteDigest, route.Digest())
		}
		if err := runtime.Reenter(ctx, frame, TurnOutcome{
			SessionID: "external-organ-swap",
			RunID:     runIDs[i],
			Text:      "observed outcome",
		}); err != nil {
			t.Fatal(err)
		}
		predecessor = frame.TurnID
	}

	snapshot, err := runtime.Snapshot()
	if err != nil {
		t.Fatal(err)
	}
	if snapshot.EntityID != entityID {
		t.Fatalf("persisted entity identity changed: got %q want %q", snapshot.EntityID, entityID)
	}
	if snapshot.Revision != uint64(len(routes)) {
		t.Fatalf("unexpected revision: got %d want %d", snapshot.Revision, len(routes))
	}
	if len(snapshot.Turns) != len(routes) {
		t.Fatalf("unexpected turn history length: got %d want %d", len(snapshot.Turns), len(routes))
	}
	for i, record := range snapshot.Turns {
		if record.RouteDigest != routes[i].Digest() {
			t.Fatalf("turn %d persisted wrong route digest: got %q want %q", i, record.RouteDigest, routes[i].Digest())
		}
	}
}
