PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS rae_chatgpt_work_packages(
  package_id TEXT PRIMARY KEY,
  trigger_token TEXT NOT NULL UNIQUE,
  project_target TEXT NOT NULL,
  requester_node TEXT NOT NULL,
  task_class TEXT NOT NULL,
  goal_clay TEXT NOT NULL,
  context_refs_clay TEXT NOT NULL DEFAULT '[]',
  capability_plan_clay TEXT NOT NULL DEFAULT '[]',
  required_outputs_clay TEXT NOT NULL DEFAULT '[]',
  write_scope_clay TEXT NOT NULL DEFAULT '[]',
  completion_test_clay TEXT NOT NULL,
  privacy_class TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 50,
  status TEXT NOT NULL CHECK(status IN ('READY','CLAIMED','RUNNING','RESULT_POSTED','INGESTED','CONSUMED','CANCELLED','BLOCKED')),
  created_at TEXT NOT NULL,
  claimed_at TEXT,
  result_posted_at TEXT,
  ingested_at TEXT,
  consumed_at TEXT,
  result_ref TEXT
);
CREATE INDEX IF NOT EXISTS idx_rae_chatgpt_work_ready ON rae_chatgpt_work_packages(status,priority DESC,created_at);

CREATE TABLE IF NOT EXISTS rae_chatgpt_work_results(
  result_id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES rae_chatgpt_work_packages(package_id),
  executor_node TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'ChatGPT',
  result_clay TEXT NOT NULL,
  evidence_refs_clay TEXT NOT NULL DEFAULT '[]',
  artifact_refs_clay TEXT NOT NULL DEFAULT '[]',
  web_refs_clay TEXT NOT NULL DEFAULT '[]',
  media_refs_clay TEXT NOT NULL DEFAULT '[]',
  unresolved_clay TEXT NOT NULL DEFAULT '[]',
  completion_clay TEXT NOT NULL,
  verification_clay TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL CHECK(status IN ('POSTED','VERIFIED','PARTIAL','FAILED','CONFLICT')),
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rae_chatgpt_results_package ON rae_chatgpt_work_results(package_id,created_at DESC);

CREATE TABLE IF NOT EXISTS rae_chatgpt_delegation_receipts(
  receipt_id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL REFERENCES rae_chatgpt_work_packages(package_id),
  event_class TEXT NOT NULL,
  event_clay TEXT NOT NULL,
  node_id TEXT,
  created_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS v_rae_chatgpt_results_unconsumed AS
SELECT p.package_id,p.trigger_token,p.project_target,p.goal_clay,p.required_outputs_clay,
       r.result_id,r.result_clay,r.evidence_refs_clay,r.artifact_refs_clay,r.web_refs_clay,r.media_refs_clay,
       r.unresolved_clay,r.completion_clay,r.verification_clay,r.status AS result_status,r.created_at
FROM rae_chatgpt_work_packages p JOIN rae_chatgpt_work_results r ON r.package_id=p.package_id
WHERE p.status IN ('INGESTED','RESULT_POSTED')
ORDER BY r.created_at;
