package omega

import (
	"crypto/sha256"
	"encoding/hex"
	"strings"
)

// OrganRoute is a portable observation of the execution organ selected by the
// outer harness. OMEGA records this route but does not dispatch providers here:
// Crush and the existing Frankenstein bridges remain the execution authority.
// This makes provider/model swaps observable without creating a second router.
type OrganRoute struct {
	Kind       string `json:"kind,omitempty"`
	OrganID    string `json:"organ_id,omitempty"`
	AdapterID  string `json:"adapter_id,omitempty"`
	ProviderID string `json:"provider_id,omitempty"`
	ModelID    string `json:"model_id,omitempty"`
}

func (r OrganRoute) Normalized() OrganRoute {
	return OrganRoute{
		Kind:       strings.TrimSpace(r.Kind),
		OrganID:    strings.TrimSpace(r.OrganID),
		AdapterID:  strings.TrimSpace(r.AdapterID),
		ProviderID: strings.TrimSpace(r.ProviderID),
		ModelID:    strings.TrimSpace(r.ModelID),
	}
}

func (r OrganRoute) Empty() bool {
	r = r.Normalized()
	return r.Kind == "" && r.OrganID == "" && r.AdapterID == "" && r.ProviderID == "" && r.ModelID == ""
}

// Digest is stable and non-secret. It lets persistent state prove which
// provider/model/bridge route produced a turn without coupling entity identity
// to that route. Changing providers therefore changes route evidence, not SELF.
func (r OrganRoute) Digest() string {
	r = r.Normalized()
	if r.Empty() {
		return ""
	}
	h := sha256.Sum256([]byte(strings.Join([]string{
		r.Kind,
		r.OrganID,
		r.AdapterID,
		r.ProviderID,
		r.ModelID,
	}, "\x00")))
	return hex.EncodeToString(h[:])
}
