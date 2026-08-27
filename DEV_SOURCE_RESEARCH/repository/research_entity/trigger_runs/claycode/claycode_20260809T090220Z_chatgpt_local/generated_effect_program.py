import os, json, hashlib, sys, pathlib
TOKEN = '4ee98c08134361566be7161dda7ac6acf0c91f8518438785057b9e260ae843ad'
ROOT = pathlib.Path('/mnt/data/claycode_20260809T090220Z_chatgpt_local/sandbox').resolve()

def run(req):
    if req.get("token") != TOKEN:
        return {"ok": False, "reason": "DENY_INVALID_CAPABILITY"}
    rel = req.get("path","")
    target = (ROOT / rel).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        return {"ok": False, "reason": "DENY_SCOPE_ESCAPE"}
    data = req.get("text","")
    if len(data.encode()) > 4096:
        return {"ok": False, "reason": "DENY_RESOURCE_BUDGET"}
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(data)
    os.replace(tmp, target)
    return {"ok": True, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "path": str(target)}

data=json.loads(sys.stdin.read())
if isinstance(data, list):
    print(json.dumps([run(x) for x in data], sort_keys=True))
else:
    print(json.dumps(run(data), sort_keys=True))
