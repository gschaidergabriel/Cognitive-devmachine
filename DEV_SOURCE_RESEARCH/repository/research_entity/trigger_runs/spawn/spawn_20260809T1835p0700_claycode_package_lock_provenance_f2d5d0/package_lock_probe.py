#!/usr/bin/env python3
import json, hashlib, random

SEED = 202608091831
N = 10000
R = random.Random(SEED)

def h(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def semver(v):
    return tuple(map(int,v.split(".")))

def pkg_node(name, version, source, payload, deps=None):
    return {
        "name":name,"version":version,"source_namespace":source,
        "digest":hashlib.sha256(payload.encode()).hexdigest(),
        "deps": sorted(deps or [])
    }

def canonical_graph(nodes, edges):
    nn=sorted(
        [{"name":n["name"],"version":n["version"],"source_namespace":n["source_namespace"],"digest":n["digest"]} for n in nodes],
        key=lambda x:(x["name"],x["version"],x["source_namespace"],x["digest"])
    )
    ee=sorted([list(e) for e in edges])
    return {"nodes":nn,"edges":ee}

def graph_id(nodes, edges):
    return h(canonical_graph(nodes,edges))

def projection_id(nodes, edges, target, features, active_edges):
    return h({
        "resolved_graph":canonical_graph(nodes,edges),
        "target":target,
        "features":sorted(features),
        "active_edges":sorted([list(e) for e in active_edges])
    })

resolver_diverge=0
resolver_same=0
for i in range(N):
    nvers=R.randint(2,5)
    versions=[f"1.{j}.0" for j in range(nvers)]
    minv=min(versions,key=semver)
    maxv=max(versions,key=semver)
    if minv != maxv: resolver_diverge += 1
    else: resolver_same += 1

unlocked_drift=0
locked_drift=0
for i in range(N):
    base_count=R.randint(1,4)
    old=[f"1.{j}.0" for j in range(base_count)]
    old_sel=max(old,key=semver)
    newv=f"1.{base_count}.0"
    grown=old+[newv]
    new_sel=max(grown,key=semver)
    unlocked_drift += (old_sel != new_sel)
    locked_drift += (old_sel != old_sel)

version_only_collision=0
digest_guard_detect=0
for i in range(N):
    name=f"p{i%97}"
    version=f"1.{i%11}.0"
    source=f"registry://example/{name}"
    payload=f"payload-{i}-{R.getrandbits(64)}"
    mutated=payload + "-MUT"
    old=pkg_node(name,version,source,payload)
    new=pkg_node(name,version,source,mutated)
    version_only_collision += ((old["name"],old["version"],old["source_namespace"]) ==
                               (new["name"],new["version"],new["source_namespace"]))
    digest_guard_detect += (old["digest"] != new["digest"])

canon_mismatch=0
for i in range(N):
    k=R.randint(3,9)
    nodes=[]
    edges=[]
    for j in range(k):
        nodes.append(pkg_node(f"p{j}",f"1.{R.randint(0,4)}.0",f"registry://r/p{j}",f"{i}-{j}-{R.getrandbits(64)}"))
    for j in range(1,k):
        parent=R.randrange(0,j)
        edges.append((f"p{parent}",f"p{j}"))
    base=graph_id(nodes,edges)
    n2=nodes[:]
    e2=edges[:]
    R.shuffle(n2)
    R.shuffle(e2)
    if graph_id(n2,e2)!=base:
        canon_mismatch += 1

naive_projection_collisions=0
full_projection_detect=0
for i in range(N):
    nodes=[
        pkg_node("app","1.0.0","workspace://app",f"app-{i}"),
        pkg_node("core","1.0.0","registry://r/core",f"core-{i}"),
        pkg_node("linuxio","1.0.0","registry://r/linuxio",f"linux-{i}"),
        pkg_node("winio","1.0.0","registry://r/winio",f"win-{i}")
    ]
    all_edges=[("app","core"),("app","linuxio"),("app","winio")]
    naive=graph_id(nodes,all_edges)
    linux_active=[("app","core"),("app","linuxio")]
    win_active=[("app","core"),("app","winio")]
    naive2=graph_id(nodes,all_edges)
    naive_projection_collisions += (naive == naive2)
    pl=projection_id(nodes,all_edges,"linux-x86_64",{"default"},linux_active)
    pw=projection_id(nodes,all_edges,"windows-x86_64",{"default"},win_active)
    full_projection_detect += (pl != pw)

semantic_graph_stable_across_policy=0
trust_receipt_changed=0
for i in range(N):
    nodes=[pkg_node("x","1.2.3","registry://r/x",f"x-{i}")]
    edges=[]
    gid=graph_id(nodes,edges)
    trust_before=h({"graph_id":gid,"repo_snapshot":100,"status":"ACCEPT","yanked":[]})
    trust_after=h({"graph_id":gid,"repo_snapshot":101,"status":"REJECT","yanked":["x@1.2.3"]})
    semantic_graph_stable_across_policy += (gid == graph_id(nodes,edges))
    trust_receipt_changed += (trust_before != trust_after)

guard_denied_without_grant=0
bad_design_would_allow=0
grant_allows=0
for i in range(N):
    dependency_declares={"net"}
    external_grant=set()
    bad_allow="net" in dependency_declares
    guarded_allow="net" in external_grant
    bad_design_would_allow += bad_allow
    guard_denied_without_grant += (not guarded_allow)
    external_grant={"net"}
    grant_allows += ("net" in external_grant)

resolver_receipt_changes_graph_stable=0
for i in range(N):
    nodes=[pkg_node("a","1.2.0","registry://r/a",f"a-{i}")]
    edges=[]
    gid=graph_id(nodes,edges)
    r1=h({"manifest":"a>=1,<2","resolver":"max-compatible@1","resolved_graph_id":gid})
    r2=h({"manifest":"a>=1,<2","resolver":"sat-solver@7","resolved_graph_id":gid})
    resolver_receipt_changes_graph_stable += (gid==graph_id(nodes,edges) and r1!=r2)

results={
    "evidence_class":"HOSTED_SYNTHETIC_PROXY_NOT_PRODUCTION_CLAYCODE",
    "seed":SEED,
    "trials_per_test":N,
    "A_resolver_policy":{"different_exact_selection":resolver_diverge,"same":resolver_same},
    "B_registry_growth":{"unlocked_selection_drift":unlocked_drift,"locked_selection_drift":locked_drift},
    "C_same_version_payload_mutation":{"version_only_identity_collision":version_only_collision,"digest_guard_detected":digest_guard_detect},
    "D_canonical_order":{"hash_mismatches_after_shuffle":canon_mismatch},
    "E_target_projection":{"naive_graph_identity_collisions":naive_projection_collisions,"projection_identity_detected_change":full_projection_detect},
    "F_freshness_policy":{"semantic_graph_stable":semantic_graph_stable_across_policy,"trust_receipt_changed":trust_receipt_changed},
    "G_authority":{"bad_dependency_implies_authority_allows":bad_design_would_allow,"guard_denied_without_external_grant":guard_denied_without_grant,"explicit_grant_allows":grant_allows},
    "H_resolver_provenance":{"same_graph_distinct_resolver_receipts":resolver_receipt_changes_graph_stable}
}

# I: factorial identity-boundary discrimination.
R2=random.Random(202608091832)
M=5000

def version_only_id(state):
    return h(sorted((n["name"],n["version"]) for n in state["nodes"]))

def candidate_semantic_id(state):
    return h({
        "graph": canonical_graph(state["nodes"], state["edges"]),
        "target": state["target"],
        "features": sorted(state["features"]),
        "active_edges": sorted([list(e) for e in state["active_edges"]])
    })

def giant_id(state):
    return h(state)

semantic_mutations=["version","source","payload","edge","target","features"]
nonsemantic_mutations=["resolver","trust","builder","manifest_range","fetch_locator"]
schemes={"version_only":version_only_id,"candidate":candidate_semantic_id,"giant":giant_id}
scores={s:{"semantic_detect":0,"semantic_total":0,"nonsemantic_stable":0,"nonsemantic_total":0,"by_kind":{}} for s in schemes}

for i in range(M):
    base={
        "nodes":[
            pkg_node("a","1.2.0","registry://r/a",f"a-{i}"),
            pkg_node("b","1.0.0","registry://r/b",f"b-{i}")
        ],
        "edges":[("a","b")],
        "target":"linux-x86_64",
        "features":["default"],
        "active_edges":[("a","b")],
        "resolver":"max-compatible@1",
        "trust":{"snapshot":100,"verdict":"ACCEPT"},
        "builder":"host-stage1@abc",
        "manifest_range":"a>=1,<2",
        "fetch_locator":"https://mirror-a.example/a-1.2.0.tgz"
    }
    for kind in semantic_mutations+nonsemantic_mutations:
        mut=json.loads(json.dumps(base))
        if kind=="version":
            mut["nodes"][0]["version"]="1.3.0"
        elif kind=="source":
            mut["nodes"][0]["source_namespace"]="registry://other-authority/a"
        elif kind=="payload":
            mut["nodes"][0]["digest"]=hashlib.sha256(f"a-{i}-mut".encode()).hexdigest()
        elif kind=="edge":
            mut["edges"]=[]
            mut["active_edges"]=[]
        elif kind=="target":
            mut["target"]="linux-aarch64"
        elif kind=="features":
            mut["features"]=["default","simd"]
        elif kind=="resolver":
            mut["resolver"]="sat-solver@7"
        elif kind=="trust":
            mut["trust"]={"snapshot":101,"verdict":"REJECT_YANKED"}
        elif kind=="builder":
            mut["builder"]="host-stage1@def"
        elif kind=="manifest_range":
            mut["manifest_range"]="a>=1.1,<2"
        elif kind=="fetch_locator":
            mut["fetch_locator"]="https://mirror-b.example/a-1.2.0.tgz"
        semantic = kind in semantic_mutations
        for s,fn in schemes.items():
            changed = fn(mut) != fn(base)
            b=scores[s]["by_kind"].setdefault(kind,{"changed":0,"total":0})
            b["changed"] += int(changed)
            b["total"] += 1
            if semantic:
                scores[s]["semantic_detect"] += int(changed)
                scores[s]["semantic_total"] += 1
            else:
                scores[s]["nonsemantic_stable"] += int(not changed)
                scores[s]["nonsemantic_total"] += 1
results["I_identity_boundary_factorial"] = scores
print("FACTORIAL")
print(json.dumps(scores,indent=2,sort_keys=True))

print('COMBINED')
print(json.dumps(results,indent=2,sort_keys=True))
