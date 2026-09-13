// Package omega defines the portable cognitive runtime seam used by EntityOS.
//
// It intentionally depends only on the Go standard library. The Crush shell
// remains responsible for UI, providers, tools, MCP, permissions, and session
// presentation. OMEGA owns cognitive state formation and reentry.
package omega

import (
	"context"
	"fmt"
	"sort"
	"strings"
)

// Version identifies the first portable EntityOS/OMEGA frame contract.
const Version = "ENTITYOS_OMEGA_FRAME/v1"

// Candidate is one contribution competing for inclusion in the current
// cognitive frame. Scores are deliberately explicit rather than hidden in
// prompt prose so GRID can later replace the baseline ordering without
// changing the Crush-facing seam.
type Candidate struct {
	ID         string
	Kind       string
	Source     string
	Payload    string
	Salience   float64
	Confidence float64
	Urgency    float64
}

// TurnInput is the minimal observation OMEGA receives from the harness.
// It contains no host-specific paths, services, or provider assumptions.
type TurnInput struct {
	SessionID string
	RunID     string
	Prompt    string
}

// Frame is the bounded cognitive state presented to the current model organ.
// StateDigest binds the frame to the persistent state it was compiled from.
// The causal metadata is intentionally separate from SystemContext: state can
// become real and persistent before we earn the right to inject semantic
// content into the model prompt.
type Frame struct {
	Version           string
	TurnID            string
	StateDigest       string
	EntityID          string
	Revision          uint64
	InputDigest       string
	PredecessorTurnID string
	Candidates        []Candidate
	SystemContext     string
}

// TurnOutcome is the terminal observation fed back into OMEGA for reentry.
type TurnOutcome struct {
	SessionID string
	RunID     string
	Text      string
	Err       string
	Cancelled bool
}

// Runtime is the only cognitive contract the Crush agent loop needs.
//
// Compile runs before model inference. Reenter runs once at terminal turn
// completion. Implementations may persist state, run GRID competition, TITAN
// consolidation, LCME transforms, or future cognitive modules behind this
// interface without leaking those concerns into Crush UI/provider/tool code.
type Runtime interface {
	Compile(context.Context, TurnInput) (Frame, error)
	Reenter(context.Context, Frame, TurnOutcome) error
}

// NoopRuntime preserves upstream Crush behavior exactly when no EntityOS
// cognitive runtime has been configured.
type NoopRuntime struct{}

func (NoopRuntime) Compile(context.Context, TurnInput) (Frame, error) {
	return Frame{Version: Version}, nil
}

func (NoopRuntime) Reenter(context.Context, Frame, TurnOutcome) error {
	return nil
}

// RenderSystemContext deterministically serializes the bounded winning
// coalition for model injection. It never serializes the entire persistent
// state. Stable sorting makes identical state/input produce identical frame
// text, independent of candidate production order.
func (f Frame) RenderSystemContext() string {
	if strings.TrimSpace(f.SystemContext) == "" && len(f.Candidates) == 0 {
		return ""
	}

	candidates := append([]Candidate(nil), f.Candidates...)
	sort.SliceStable(candidates, func(i, j int) bool {
		li := candidateUtility(candidates[i])
		lj := candidateUtility(candidates[j])
		if li != lj {
			return li > lj
		}
		return candidates[i].ID < candidates[j].ID
	})

	var b strings.Builder
	b.WriteString("<omega-cognitive-frame version=\"")
	if f.Version == "" {
		b.WriteString(Version)
	} else {
		b.WriteString(escapeAttr(f.Version))
	}
	b.WriteString("\"")
	if f.TurnID != "" {
		fmt.Fprintf(&b, " turn=\"%s\"", escapeAttr(f.TurnID))
	}
	if f.StateDigest != "" {
		fmt.Fprintf(&b, " state=\"%s\"", escapeAttr(f.StateDigest))
	}
	b.WriteString(">\n")

	if s := strings.TrimSpace(f.SystemContext); s != "" {
		b.WriteString("<broadcast>\n")
		b.WriteString(s)
		b.WriteString("\n</broadcast>\n")
	}
	for _, c := range candidates {
		if strings.TrimSpace(c.Payload) == "" {
			continue
		}
		fmt.Fprintf(
			&b,
			"<candidate id=\"%s\" kind=\"%s\" source=\"%s\" salience=\"%.6f\" confidence=\"%.6f\" urgency=\"%.6f\">%s</candidate>\n",
			escapeAttr(c.ID),
			escapeAttr(c.Kind),
			escapeAttr(c.Source),
			c.Salience,
			c.Confidence,
			c.Urgency,
			strings.TrimSpace(c.Payload),
		)
	}
	b.WriteString("</omega-cognitive-frame>")
	return b.String()
}

func candidateUtility(c Candidate) float64 {
	// Baseline only. GRID will own competition in the real runtime.
	return c.Salience * c.Confidence * (1 + c.Urgency)
}

func escapeAttr(s string) string {
	r := strings.NewReplacer(
		"&", "&amp;",
		"\"", "&quot;",
		"<", "&lt;",
		">", "&gt;",
	)
	return r.Replace(s)
}
