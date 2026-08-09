import json, sys
def gate(case):
    return {
        'recognition_fast_path': bool(case.get('known_high_confidence', False)) and bool(case.get('open_set_ok', False)) and bool(case.get('calibration_current', False)) and bool(case.get('version_compatible', False)) and bool(case.get('no_conflict', False)),
        'promotion_allowed': bool(case.get('trusted_tier', False)) and bool(case.get('candidate_eval_pass', False)) and bool(case.get('rollback_ready', False)) and bool(case.get('budget_ok', False)),
        'publication_allowed': bool(case.get('source_admitted', False)) and bool(case.get('schema_preflight_ok', False)) and bool(case.get('projection_closed', False)) and bool(case.get('atomic_commit_ready', False)) and bool(case.get('replay_ready', False)),
    }
if __name__ == "__main__":
    case = json.loads(sys.argv[1])
    print(json.dumps(gate(case), sort_keys=True))
