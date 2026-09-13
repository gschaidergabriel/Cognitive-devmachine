package omega

import "testing"

func TestOrganRouteDigestIsStableAndRouteSensitive(t *testing.T) {
	a := OrganRoute{Kind: "provider", OrganID: "crush", AdapterID: "native", ProviderID: "openai", ModelID: "gpt-x"}
	b := OrganRoute{Kind: " provider ", OrganID: " crush ", AdapterID: "native", ProviderID: " openai ", ModelID: "gpt-x"}
	c := OrganRoute{Kind: "provider", OrganID: "crush", AdapterID: "native", ProviderID: "anthropic", ModelID: "claude-x"}

	if a.Digest() == "" {
		t.Fatal("non-empty route produced empty digest")
	}
	if a.Digest() != b.Digest() {
		t.Fatal("route digest changed under whitespace-only normalization")
	}
	if a.Digest() == c.Digest() {
		t.Fatal("provider/model swap did not change route digest")
	}
	if got := (OrganRoute{}).Digest(); got != "" {
		t.Fatalf("empty route produced digest %q", got)
	}
}
