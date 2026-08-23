import crypto from 'node:crypto';

const CANONICALIZATION_SCHEMA = 'ENTITYOS_ENTRY_CANONICAL_JSON_JCS_SUBSET/v1';
const EXPECTED = 'd6f14d8792c1653b19c95ec4f39653a671772f809e238c8e8e91a19df26ea5de';

function canonicalize(value) {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') {
    return JSON.stringify(value);
  }
  if (typeof value === 'number') {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error('SAFE_NONNEGATIVE_INTEGER_REQUIRED');
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (typeof value === 'object') {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(',')}}`;
  }
  throw new Error('UNSUPPORTED_TYPE');
}

const basis = {
  schema: 'ENTITYOS_ENTRY_PACKET/v1',
  canonicalization_schema: CANONICALIZATION_SCHEMA,
  event_id: 'evt-001',
  source: 'urn:entityos:test',
  event_type: 'human.prompt',
  causal_id: 'cause-001',
  entity_generation: 7,
  modality: 'TEXT',
  observed_at: '2026-08-23T15:00:00Z',
  received_at: '2026-08-23T15:00:00Z',
  capability_scope: ['cognition.request', 'state.read'],
  budget: [['max_cells', 10], ['max_ms', 4000], ['max_tokens', 2048]],
  payload_ref: 'unifieddb://entry/evt-001',
  payload_sha256: 'a'.repeat(64),
  provenance_sha256: 'b'.repeat(64),
  parent_id: null,
  stream_id: 'session-1',
  trace_id: null,
  parent_span_id: null,
};

const bytes = Buffer.from(canonicalize(basis), 'utf8');
const digest = crypto.createHash('sha256').update(bytes).digest('hex');
if (digest !== EXPECTED) {
  console.error(JSON.stringify({status: 'FAIL', expected: EXPECTED, observed: digest}));
  process.exit(1);
}
console.log(JSON.stringify({status: 'PASS', canonicalization_schema: CANONICALIZATION_SCHEMA, entry_sha256: digest}));
