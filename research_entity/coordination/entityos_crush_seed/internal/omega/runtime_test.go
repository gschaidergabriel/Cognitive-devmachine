package omega

import (
	"context"
	"strings"
	"testing"
)

func TestNoopRuntimePreservesUpstreamPrompt(t *testing.T) {
	rt := NoopRuntime{}
	frame, err := rt.Compile(context.Background(), TurnInput{
		SessionID: "s1",
		RunID:     "r1",
		Prompt:    "hello",
	})
	if err != nil {
		t.Fatal(err)
	}
	if got := frame.RenderSystemContext(); got != "" {
		t.Fatalf("noop runtime injected context: %q", got)
	}
	if err := rt.Reenter(context.Background(), frame, TurnOutcome{}); err != nil {
		t.Fatal(err)
	}
}

func TestFrameRenderIsDeterministicAcrossProductionOrder(t *testing.T) {
	a := Candidate{ID: "a", Kind: "hypothesis", Source: "grid", Payload: "A", Salience: .8, Confidence: .9, Urgency: .1}
	b := Candidate{ID: "b", Kind: "goal", Source: "titan", Payload: "B", Salience: .4, Confidence: .9, Urgency: .2}

	f1 := Frame{Version: Version, TurnID: "t1", StateDigest: "deadbeef", Candidates: []Candidate{a, b}}
	f2 := Frame{Version: Version, TurnID: "t1", StateDigest: "deadbeef", Candidates: []Candidate{b, a}}

	got1 := f1.RenderSystemContext()
	got2 := f2.RenderSystemContext()
	if got1 != got2 {
		t.Fatalf("render depends on candidate order:\n%s\n---\n%s", got1, got2)
	}
	if strings.Index(got1, `id="a"`) > strings.Index(got1, `id="b"`) {
		t.Fatalf("higher-utility candidate did not win ordering:\n%s", got1)
	}
}

func TestFrameDoesNotDumpAbsentState(t *testing.T) {
	got := (Frame{
		Version:       Version,
		SystemContext: "only-current-broadcast",
	}).RenderSystemContext()
	if !strings.Contains(got, "only-current-broadcast") {
		t.Fatalf("missing current broadcast: %s", got)
	}
	if strings.Contains(got, "memory") || strings.Contains(got, "history") {
		t.Fatalf("unexpected implicit memory/history dump: %s", got)
	}
}
