package omega

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

const (
	StateSchema     = "OMEGACV1_STATE/v1"
	maxTurnRecords = 64
)

type TurnRecord struct {
	TurnID            string `json:"turn_id"`
	SessionID         string `json:"session_id"`
	RunID             string `json:"run_id,omitempty"`
	InputDigest       string `json:"input_digest"`
	OutputDigest      string `json:"output_digest,omitempty"`
	Status            string `json:"status"`
	PredecessorDigest string `json:"predecessor_digest"`
	AppliedToDigest   string `json:"applied_to_digest"`
	ConcurrentReentry bool   `json:"concurrent_reentry,omitempty"`
}

type PersistentState struct {
	Schema     string       `json:"schema"`
	EntityID   string       `json:"entity_id"`
	Revision   uint64       `json:"revision"`
	LastTurnID string       `json:"last_turn_id,omitempty"`
	Turns      []TurnRecord `json:"turns,omitempty"`
}

// PersistentRuntime is the first native state substrate below Crush sessions.
// It deliberately stores no raw prompt or model output. Until TITAN/GRID are
// ported, it records only causal lineage and content digests, so enabling state
// persistence cannot silently turn into transcript injection.
type PersistentRuntime struct {
	mu   sync.Mutex
	path string
}

func NewPersistentRuntime(path string) (*PersistentRuntime, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil, errors.New("omega state path is empty")
	}
	return &PersistentRuntime{path: path}, nil
}

func DefaultStatePath(dataDir string) string {
	if override := strings.TrimSpace(os.Getenv("OMEGACV1_STATE_PATH")); override != "" {
		return override
	}
	if strings.TrimSpace(dataDir) == "" {
		return ""
	}
	return filepath.Join(dataDir, "omega", "state.json")
}

func (r *PersistentRuntime) Compile(_ context.Context, in TurnInput) (Frame, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	state, err := r.loadOrInitLocked()
	if err != nil {
		return Frame{}, err
	}
	stateDigest, err := digestState(state)
	if err != nil {
		return Frame{}, err
	}
	inputDigest := digestText(in.Prompt)
	turnID := digestText(strings.Join([]string{
		state.EntityID,
		stateDigest,
		state.LastTurnID,
		in.SessionID,
		in.RunID,
		inputDigest,
	}, "\x00"))

	return Frame{
		Version:           Version,
		TurnID:            turnID,
		StateDigest:       stateDigest,
		EntityID:          state.EntityID,
		Revision:          state.Revision,
		InputDigest:       inputDigest,
		PredecessorTurnID: state.LastTurnID,
	}, nil
}

func (r *PersistentRuntime) Reenter(_ context.Context, frame Frame, outcome TurnOutcome) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	state, err := r.loadOrInitLocked()
	if err != nil {
		return err
	}
	appliedToDigest, err := digestState(state)
	if err != nil {
		return err
	}

	status := "ok"
	switch {
	case outcome.Cancelled:
		status = "cancelled"
	case strings.TrimSpace(outcome.Err) != "":
		status = "error"
	}

	record := TurnRecord{
		TurnID:            frame.TurnID,
		SessionID:         outcome.SessionID,
		RunID:             outcome.RunID,
		InputDigest:       frame.InputDigest,
		OutputDigest:      digestText(outcome.Text),
		Status:            status,
		PredecessorDigest: frame.StateDigest,
		AppliedToDigest:   appliedToDigest,
		ConcurrentReentry: frame.StateDigest != "" && frame.StateDigest != appliedToDigest,
	}
	state.Turns = append(state.Turns, record)
	if len(state.Turns) > maxTurnRecords {
		state.Turns = append([]TurnRecord(nil), state.Turns[len(state.Turns)-maxTurnRecords:]...)
	}
	state.Revision++
	state.LastTurnID = frame.TurnID
	return r.writeLocked(state)
}

func (r *PersistentRuntime) Snapshot() (PersistentState, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.loadOrInitLocked()
}

func (r *PersistentRuntime) loadOrInitLocked() (PersistentState, error) {
	b, err := os.ReadFile(r.path)
	if err == nil {
		var state PersistentState
		if err := json.Unmarshal(b, &state); err != nil {
			return PersistentState{}, fmt.Errorf("decode omega state: %w", err)
		}
		if state.Schema != StateSchema {
			return PersistentState{}, fmt.Errorf("unsupported omega state schema %q", state.Schema)
		}
		if strings.TrimSpace(state.EntityID) == "" {
			return PersistentState{}, errors.New("omega state has empty entity_id")
		}
		return state, nil
	}
	if !errors.Is(err, os.ErrNotExist) {
		return PersistentState{}, fmt.Errorf("read omega state: %w", err)
	}

	entityID, err := newEntityID()
	if err != nil {
		return PersistentState{}, err
	}
	state := PersistentState{Schema: StateSchema, EntityID: entityID}
	if err := r.writeLocked(state); err != nil {
		return PersistentState{}, err
	}
	return state, nil
}

func (r *PersistentRuntime) writeLocked(state PersistentState) error {
	if err := os.MkdirAll(filepath.Dir(r.path), 0o700); err != nil {
		return fmt.Errorf("create omega state directory: %w", err)
	}
	b, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return fmt.Errorf("encode omega state: %w", err)
	}
	b = append(b, '\n')
	tmp := r.path + ".tmp"
	if err := os.WriteFile(tmp, b, 0o600); err != nil {
		return fmt.Errorf("write omega state temp file: %w", err)
	}
	if err := os.Rename(tmp, r.path); err != nil {
		_ = os.Remove(tmp)
		return fmt.Errorf("commit omega state: %w", err)
	}
	return nil
}

func digestState(state PersistentState) (string, error) {
	b, err := json.Marshal(state)
	if err != nil {
		return "", err
	}
	s := sha256.Sum256(b)
	return hex.EncodeToString(s[:]), nil
}

func digestText(s string) string {
	h := sha256.Sum256([]byte(s))
	return hex.EncodeToString(h[:])
}

func newEntityID() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", fmt.Errorf("generate omega entity id: %w", err)
	}
	// UUIDv4-compatible formatting without adding a dependency.
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	h := hex.EncodeToString(b[:])
	return h[0:8] + "-" + h[8:12] + "-" + h[12:16] + "-" + h[16:20] + "-" + h[20:32], nil
}
