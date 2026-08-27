#!/usr/bin/env python3
import hashlib,json,random
random.seed(160612)
def h(s): return hashlib.sha256(s.encode()).hexdigest()
semantic_ir='{"kind":"HttpService","route":"/health","effect":"READ_RESOURCE"}'
stable='HTTP_SERVICE_V2\nROUTE=/health\nCAPABILITY_SOURCE=runtime_handle\n'
v1=set();v2=set();deploy=set();trials=10000
for _ in range(trials):
    token=f"cap-{random.getrandbits(128):032x}"; th=h(token)
    v1.add(h(stable+f'EMBEDDED_TOKEN_HASH={th}\n'))
    v2.add(h(stable))
    deploy.add(h(h(semantic_ir)+"|"+h(stable)+"|"+th))
print(json.dumps({"experiment_id":"EXP-CC-AUTHORITY-INSTANCE-HASH-002","trials":trials,"v1_embedded_runtime_authority_unique_artifact_hashes":len(v1),"v2_runtime_handle_unique_artifact_hashes":len(v2),"v2_unique_deployment_instance_hashes":len(deploy),"stable_artifact_identity_with_runtime_handle":len(v2)==1,"runtime_authority_instances_remain_distinct":len(deploy)==trials},sort_keys=True))
