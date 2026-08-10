from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from research_entity.runtime.gwt_sibling_quorum_workspace_v1 import benchmark
from research_entity.runtime.mcp_telemetry_identity_contract_v1 import inspect_path


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--episodes',type=int,default=20_000)
    p.add_argument('--telemetry-db',default='/srv/frank-telemetry/frank_telemetry.sqlite3')
    p.add_argument('--output',required=True)
    a=p.parse_args()
    out={
        'schema_version':'1.0',
        'iteration':3,
        'fresh_evidence_method':'GRT_OUTER_THINKSPACE_GWT_OPTIONAL_CAUSAL_CHALLENGER',
        'gwt_sibling_quorum':benchmark(a.episodes),
        'mcp_telemetry_identity_contract':inspect_path(a.telemetry_db),
        'promotion_boundaries':{
            'quorum_promoted':False,
            'live_telemetry_migration_performed':False,
            'telemetry_probe_authority':'READ_ONLY',
        },
    }
    q=out['gwt_sibling_quorum']
    out['acceptance']={
        'forged_origin_rejected':q['forged_origin_reject_rate']==1.0,
        'stale_lease_rejected':q['stale_lease_reject_rate']==1.0,
        'self_attribution_errors_zero':q['self_attribution_errors']==0,
        'quorum_reduced_to_stronger_simple_mechanism':q['promotion_decision']=='REFUTED_USE_SIMPLE_PROVENANCE_VALIDATED_MEDIAN_REDUCER',
    }
    path=Path(a.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
