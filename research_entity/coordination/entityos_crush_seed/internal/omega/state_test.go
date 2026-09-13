package omega

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPersistentRuntimeSurvivesSessionAndProcessReentry(t *testing.T) {
	path := filepath.Join(t.TempDir(), "omega", "state.json")
	rt1, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	frame1, err := rt1.Compile(context.Background(), TurnInput{SessionID: "session-a", RunID: "run-1", Prompt: "first prompt secret"})
	if err != nil {
		t.Fatal(err)
	}
	if frame1.Revision != 0 || frame1.EntityID == "" || frame1.StateDigest == "" {
		t.Fatalf("unexpected initial frame: %#v", frame1)
	}
	if got := frame1.RenderSystemContext(); got != "" {
		t.Fatalf("bootstrap persistence must not inject transcript/state metadata yet: %q", got)
	}
	if err := rt1.Reenter(context.Background(), frame1, TurnOutcome{SessionID: "session-a", RunID: "run-1", Text: "first answer secret"}); err != nil {
		t.Fatal(err)
	}

	// New runtime object simulates process restart. New session simulates a
	// different Crush conversation surface. The entity and revision must persist.
	rt2, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	frame2, err := rt2.Compile(context.Background(), TurnInput{SessionID: "session-b", RunID: "run-2", Prompt: "second prompt"})
	if err != nil {
		t.Fatal(err)
	}
	if frame2.EntityID != frame1.EntityID {
		t.Fatalf("entity changed across restart/session: %s != %s", frame2.EntityID, frame1.EntityID)
	}
	if frame2.Revision != 1 {
		t.Fatalf("revision did not advance: got %d", frame2.Revision)
	}
	if frame2.PredecessorTurnID != frame1.TurnID {
		t.Fatalf("predecessor chain broken: got %q want %q", frame2.PredecessorTurnID, frame1.TurnID)
	}
	if frame2.StateDigest == frame1.StateDigest {
		t.Fatal("state digest did not change after reentry")
	}
}

func TestPersistentRuntimeStoresDigestsNotRawTranscript(t *testing.T) {
	path := filepath.Join(t.TempDir(), "state.json")
	rt, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	prompt := "PRIVATE-PROMPT-SENTINEL"
	answer := "PRIVATE-ANSWER-SENTINEL"
	frame, err := rt.Compile(context.Background(), TurnInput{SessionID: "s", RunID: "r", Prompt: prompt})
	if err != nil {
		t.Fatal(err)
	}
	if err := rt.Reenter(context.Background(), frame, TurnOutcome{SessionID: "s", RunID: "r", Text: answer}); err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	text := string(b)
	if strings.Contains(text, prompt) || strings.Contains(text, answer) {
		t.Fatalf("raw transcript leaked into omega state: %s", text)
	}
	if !strings.Contains(text, digestText(prompt)) || !strings.Contains(text, digestText(answer)) {
		t.Fatalf("expected input/output digests missing: %s", text)
	}
}

func TestPersistentRuntimeMarksConcurrentReentryWithoutDroppingTurn(t *testing.T) {
	path := filepath.Join(t.TempDir(), "state.json")
	rt, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	frameA, err := rt.Compile(context.Background(), TurnInput{SessionID: "a", RunID: "ra", Prompt: "A"})
	if err != nil {
		t.Fatal(err)
	}
	frameB, err := rt.Compile(context.Background(), TurnInput{SessionID: "b", RunID: "rb", Prompt: "B"})
	if err != nil {
		t.Fatal(err)
	}
	if err := rt.Reenter(context.Background(), frameA, TurnOutcome{SessionID: "a", RunID: "ra", Text: "A1"}); err != nil {
		t.Fatal(err)
	}
	if err := rt.Reenter(context.Background(), frameB, TurnOutcome{SessionID: "b", RunID: "rb", Text: "B1"}); err != nil {
		t.Fatal(err)
	}
	state, err := rt.Snapshot()
	if err != nil {
		t.Fatal(err)
	}
	if state.Revision != 2 || len(state.Turns) != 2 {
		t.Fatalf("unexpected state after concurrent reentry: %#v", state)
	}
	if state.Turns[0].ConcurrentReentry {
		t.Fatal("first reentry incorrectly marked concurrent")
	}
	if !state.Turns[1].ConcurrentReentry {
		t.Fatal("stale predecessor was not marked as concurrent reentry")
	}
}

func TestProviderSwapChangesRouteEvidenceNotEntityIdentity(t *testing.T) {
	path := filepath.Join(t.TempDir(), "omega", "state.json")
	firstRoute := OrganRoute{
		Kind:       "provider",
		OrganID:    "crush-model",
		AdapterID:  "crush-native",
		ProviderID: "provider-a",
		ModelID:    "model-a",
	}
	secondRoute := OrganRoute{
		Kind:       "provider",
		OrganID:    "crush-model",
		AdapterID:  "crush-native",
		ProviderID: "provider-b",
		ModelID:    "model-b",
	}

	rt1, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	frame1, err := rt1.Compile(context.Background(), TurnInput{
		SessionID: "session-a",
		RunID:     "run-a",
		Prompt:    "same entity first organ",
		Route:     firstRoute,
	})
	if err != nil {
		t.Fatal(err)
	}
	if frame1.RouteDigest != firstRoute.Digest() {
		t.Fatalf("first route digest mismatch: got %q want %q", frame1.RouteDigest, firstRoute.Digest())
	}
	if err := rt1.Reenter(context.Background(), frame1, TurnOutcome{SessionID: "session-a", RunID: "run-a", Text: "answer-a"}); err != nil {
		t.Fatal(err)
	}

	// Re-open from disk to combine a process restart with a provider/model swap.
	rt2, err := NewPersistentRuntime(path)
	if err != nil {
		t.Fatal(err)
	}
	frame2, err := rt2.Compile(context.Background(), TurnInput{
		SessionID: "session-b",
		RunID:     "run-b",
		Prompt:    "same entity second organ",
		Route:     secondRoute,
	})
	if err != nil {
		t.Fatal(err)
	}
	if frame2.EntityID != frame1.EntityID {
		t.Fatalf("provider swap changed entity identity: %s != %s", frame2.EntityID, frame1.EntityID)
	}
	if frame2.PredecessorTurnID != frame1.TurnID || frame2.Revision != 1 {
		t.Fatalf("provider swap broke reentry chain: %#v", frame2)
	}
	if frame2.RouteDigest != secondRoute.Digest() || frame2.RouteDigest == frame1.RouteDigest {
		t.Fatalf("provider swap not reflected in route evidence: first=%q second=%q", frame1.RouteDigest, frame2.RouteDigest)
	}
	if got := frame2.RenderSystemContext(); got != "" {
		t.Fatalf("route metadata leaked into model context: %q", got)
	}
	if err := rt2.Reenter(context.Background(), frame2, TurnOutcome{SessionID: "session-b", RunID: "run-b", Text: "answer-b"}); err != nil {
		t.Fatal(err)
	}

	state, err := rt2.Snapshot()
	if err != nil {
		t.Fatal(err)
	}
	if state.Revision != 2 || len(state.Turns) != 2 {
		t.Fatalf("unexpected final state: %#v", state)
	}
	if state.Turns[0].RouteDigest != firstRoute.Digest() || state.Turns[1].RouteDigest != secondRoute.Digest() {
		t.Fatalf("persisted route lineage mismatch: %#v", state.Turns)
	}
}
