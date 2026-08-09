PRAGMA foreign_keys=ON;

-- UnifiedDB V7: logical cognitive processor substrate.
-- Prompt latency should scale with relevant neighborhood, not total memory.

CREATE TABLE IF NOT EXISTS semantic_dependencies(
  dependency_id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  target_id TEXT NOT NULL,
  dependency_type TEXT NOT NULL,
  strength REAL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  valid_from TEXT,
  valid_to TEXT,
  source_epoch INTEGER,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_semantic_dep_source ON semantic_dependencies(source_kind,source_id,status);
CREATE INDEX IF NOT EXISTS idx_semantic_dep_target ON semantic_dependencies(target_kind,target_id,status);

CREATE TABLE IF NOT EXISTS cognitive_view_specs(
  view_id TEXT PRIMARY KEY,
  view_kind TEXT NOT NULL,
  selector_clay TEXT NOT NULL,
  dependency_query_clay TEXT NOT NULL,
  freshness_policy_clay TEXT NOT NULL,
  evidence_floor REAL,
  materialization_policy TEXT NOT NULL,
  version_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cognitive_view_materializations(
  materialization_id TEXT PRIMARY KEY,
  view_id TEXT NOT NULL REFERENCES cognitive_view_specs(view_id),
  context_key TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  payload_clay TEXT NOT NULL,
  member_refs_clay TEXT NOT NULL,
  contradiction_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  selector_hash TEXT NOT NULL,
  dependency_hash TEXT NOT NULL,
  materialized_at TEXT NOT NULL,
  valid_until TEXT,
  status TEXT NOT NULL,
  UNIQUE(view_id,context_key,source_epoch,status)
);
CREATE INDEX IF NOT EXISTS idx_cognitive_view_context ON cognitive_view_materializations(view_id,context_key,status,source_epoch DESC);

CREATE TABLE IF NOT EXISTS cognitive_invalidation_queue(
  invalidation_id TEXT PRIMARY KEY,
  source_epoch INTEGER NOT NULL,
  changed_ref TEXT NOT NULL,
  affected_views_clay TEXT NOT NULL DEFAULT '[]',
  affected_contexts_clay TEXT NOT NULL DEFAULT '[]',
  reason_class TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  processed_at TEXT,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cognitive_invalidation_status ON cognitive_invalidation_queue(status,source_epoch);

CREATE TABLE IF NOT EXISTS answer_capsules(
  capsule_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT,
  source_epoch INTEGER NOT NULL,
  graph_epoch INTEGER,
  intent_clay TEXT NOT NULL,
  proposition_refs_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL,
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  uncertainty_refs_clay TEXT NOT NULL DEFAULT '[]',
  self_refs_clay TEXT NOT NULL DEFAULT '[]',
  human_refs_clay TEXT NOT NULL DEFAULT '[]',
  build_refs_clay TEXT NOT NULL DEFAULT '[]',
  affordance_refs_clay TEXT NOT NULL DEFAULT '[]',
  next_intents_clay TEXT NOT NULL DEFAULT '[]',
  authority_refs_clay TEXT NOT NULL DEFAULT '[]',
  verification_clay TEXT NOT NULL DEFAULT '[]',
  response_budget_clay TEXT NOT NULL,
  selector_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_answer_capsules_cycle ON answer_capsules(cycle_id,created_at DESC);

CREATE TABLE IF NOT EXISTS capability_sources(
  capability_id TEXT PRIMARY KEY,
  node_id TEXT,
  resource_ref TEXT NOT NULL,
  verbs_clay TEXT NOT NULL,
  constraints_clay TEXT NOT NULL DEFAULT '[]',
  authority_refs_clay TEXT NOT NULL DEFAULT '[]',
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  freshness_limit_seconds INTEGER,
  observed_at TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  reliability REAL,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_capability_source_status ON capability_sources(status,observed_at DESC);

CREATE TABLE IF NOT EXISTS affordance_rules(
  rule_id TEXT PRIMARY KEY,
  rule_version TEXT NOT NULL,
  input_pattern_clay TEXT NOT NULL,
  constraint_clay TEXT NOT NULL,
  consequence_clay TEXT NOT NULL,
  proof_recipe_clay TEXT NOT NULL,
  cost_model_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS affordance_materializations(
  affordance_id TEXT PRIMARY KEY,
  context_key TEXT NOT NULL,
  source_epoch INTEGER NOT NULL,
  component_capabilities_clay TEXT NOT NULL,
  rule_ids_clay TEXT NOT NULL,
  preconditions_clay TEXT NOT NULL,
  effect_clay TEXT NOT NULL,
  constraints_clay TEXT NOT NULL,
  authority_refs_clay TEXT NOT NULL,
  cost_clay TEXT NOT NULL,
  risk_clay TEXT NOT NULL,
  route_proof_ref TEXT,
  evidence_refs_clay TEXT NOT NULL,
  status TEXT NOT NULL,
  materialized_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_affordance_context ON affordance_materializations(context_key,status,source_epoch DESC);

CREATE TABLE IF NOT EXISTS affordance_route_proofs(
  route_proof_id TEXT PRIMARY KEY,
  affordance_id TEXT NOT NULL REFERENCES affordance_materializations(affordance_id),
  source_epoch INTEGER NOT NULL,
  component_refs_clay TEXT NOT NULL,
  rule_version_refs_clay TEXT NOT NULL,
  constraint_epoch_clay TEXT NOT NULL,
  authority_check_clay TEXT NOT NULL,
  freshness_check_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL,
  proof_hash TEXT NOT NULL,
  verified_at TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cognitive_pressure_events(
  pressure_id TEXT PRIMARY KEY,
  pressure_class TEXT NOT NULL,
  semantic_refs_clay TEXT NOT NULL,
  magnitude REAL NOT NULL,
  urgency REAL,
  confidence REAL,
  evidence_refs_clay TEXT NOT NULL,
  valid_from TEXT,
  valid_to TEXT,
  source_epoch INTEGER,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pressure_status ON cognitive_pressure_events(status,pressure_class,created_at DESC);

CREATE TABLE IF NOT EXISTS emergent_coalitions(
  coalition_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  source_epoch INTEGER NOT NULL,
  pressure_refs_clay TEXT NOT NULL,
  semantic_refs_clay TEXT NOT NULL,
  utility REAL,
  urgency REAL,
  coherence REAL,
  conflict_refs_clay TEXT NOT NULL DEFAULT '[]',
  evidence_refs_clay TEXT NOT NULL,
  selected_intent_ref TEXT,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_coalition_cycle ON emergent_coalitions(cycle_id,created_at DESC);

CREATE TABLE IF NOT EXISTS cognitive_stack_receipts(
  stack_receipt_id TEXT PRIMARY KEY,
  cycle_id TEXT,
  node_id TEXT NOT NULL,
  stack_epoch TEXT NOT NULL,
  claycode_ref TEXT NOT NULL,
  claygraph_ref TEXT NOT NULL,
  unifieddb_ref TEXT NOT NULL,
  stack_hash TEXT NOT NULL,
  resolved_at TEXT NOT NULL,
  status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stack_receipt_cycle ON cognitive_stack_receipts(cycle_id,resolved_at DESC);

CREATE VIEW IF NOT EXISTS v_current_capabilities AS
SELECT * FROM capability_sources
WHERE status='CURRENT' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

CREATE VIEW IF NOT EXISTS v_open_pressures AS
SELECT * FROM cognitive_pressure_events
WHERE status='OPEN' AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP);

-- Runtime invariants:
-- 1. prompt read path never executes eager global combinatorial closure;
-- 2. writes enqueue dependency-targeted invalidation;
-- 3. possible/reachable affordance never implies authorized executable effect;
-- 4. coalitions are transient computed priorities, not a canonical explicit goal list;
-- 5. materialized views are derived read products and never outrank source evidence.
