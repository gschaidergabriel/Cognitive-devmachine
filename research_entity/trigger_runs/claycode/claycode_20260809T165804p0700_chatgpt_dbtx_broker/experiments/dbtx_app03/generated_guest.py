import os,sys,json,socket
RESOURCE='db.main'
ACTIONS=json.loads('[{"mode":"IMMEDIATE","op":"begin"},{"amount":30,"from":"alice","key":"k1","op":"transfer_once","to":"bob"},{"op":"commit"},{"account":"alice","op":"balance"},{"account":"bob","op":"balance"},{"mode":"IMMEDIATE","op":"begin"},{"amount":20,"from":"alice","key":"k2","op":"transfer_once","to":"bob"},{"op":"rollback"},{"account":"alice","op":"balance"},{"account":"bob","op":"balance"},{"mode":"IMMEDIATE","op":"begin"},{"amount":30,"from":"alice","key":"k1","op":"transfer_once","to":"bob"},{"op":"commit"},{"account":"alice","op":"balance"},{"account":"bob","op":"balance"}]')
try:
    fd=int(os.environ["CLAY_DB_FD"])
    s=socket.socket(fileno=fd)
except Exception as e:
    print(json.dumps({"status":"DENIED_NO_VALID_RESOURCE","error":type(e).__name__}))
    raise SystemExit(77)
f=s.makefile("rwb", buffering=0)
out=[]
for action in ACTIONS:
    req={"resource":RESOURCE,**action}
    f.write((json.dumps(req,separators=(",",":"))+"\n").encode())
    line=f.readline()
    if not line:
        print(json.dumps({"status":"BROKER_CLOSED","responses":out}))
        raise SystemExit(79)
    resp=json.loads(line)
    out.append(resp)
    if resp.get("status")=="DENIED":
        print(json.dumps({"status":"DENIED","responses":out},sort_keys=True))
        raise SystemExit(78)
print(json.dumps({"status":"OK","responses":out},sort_keys=True))
