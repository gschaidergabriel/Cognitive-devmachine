#!/usr/bin/env python3
"""Validate split Claude Code adapter diagnostic receipts. Evidence only; zero runtime/product credit."""
import copy, hashlib, json, re, sys

SCHEMAS={"TOOLLESS_RECEIPT/v1","EPHEMERAL_RECEIPT/v1","STRUCTURED_OUTPUT_RECEIPT/v1","ENV_ISOLATION_RECEIPT/v1"}
HEX64=re.compile(r"^[0-9a-f]{64}$"); GIT=re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
FORBIDDEN={"secret","secret_value","password","password_value","token_value","api_key_value","raw_environment","raw_env_values"}
CRED={"NONE","HOME_OAUTH","ANTHROPIC_ENV","HOME_OAUTH_AND_ANTHROPIC_ENV"}
class ReceiptError(ValueError): pass

def scan(v,path="$",key=None):
    if key and key.lower() in FORBIDDEN: raise ReceiptError(f"SECRET_MATERIAL_FIELD_FORBIDDEN:{path}")
    if isinstance(v,dict):
        for k,x in v.items():
            if not isinstance(k,str): raise ReceiptError("NONSTRING_JSON_KEY")
            scan(x,f"{path}.{k}",k)
    elif isinstance(v,list):
        for i,x in enumerate(v): scan(x,f"{path}[{i}]")
    elif v is not None and not isinstance(v,(str,bool,int)): raise ReceiptError(f"UNSUPPORTED_JSON_TYPE:{path}")

def h(v,name,pat=HEX64):
    x=v.get(name)
    if not isinstance(x,str) or not pat.fullmatch(x): raise ReceiptError(f"{name}:DIGEST")
    return x

def digest(r):
    x=copy.deepcopy(r); x.pop("receipt_envelope_digest",None); scan(x)
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def validate(r):
    if not isinstance(r,dict): raise ReceiptError("ROOT_OBJECT_REQUIRED")
    scan(r); schema=r.get("schema")
    if schema not in SCHEMAS: raise ReceiptError("SCHEMA_UNSUPPORTED")
    s=r.get("source",{}); commit=h(s,"commit",GIT); h(s,"tree",GIT)
    if s.get("dirty") is not False: raise ReceiptError("SOURCE_DIRTY_OR_UNKNOWN")
    run=r.get("run",{}); run_id=run.get("test_run_id"); run_bind=h(run,"run_binding_digest"); h(run,"suite_digest"); h(run,"executor_digest")
    if not isinstance(run_id,str) or not run_id: raise ReceiptError("TEST_RUN_ID_REQUIRED")
    c=r.get("claude",{}); h(c,"binary_digest"); h(c,"adapter_contract_digest")
    if not c.get("version"): raise ReceiptError("CLAUDE_VERSION_REQUIRED")
    inv=r.get("invocation",{}); argv=inv.get("argv"); h(inv,"argv_digest"); h(inv,"cwd_digest")
    if not isinstance(argv,list) or not argv or not all(isinstance(x,str) for x in argv): raise ReceiptError("ARGV_REQUIRED")
    env=r.get("environment",{}); keys=env.get("keys"); h(env,"normalized_class_digest")
    if not isinstance(keys,list) or keys!=sorted(set(keys)) or not all(isinstance(x,str) and x for x in keys): raise ReceiptError("ENV_KEYS_SORTED_UNIQUE_REQUIRED")
    if env.get("raw_values_persisted") is not False or env.get("credential_material_persisted") is not False: raise ReceiptError("SECRET_MATERIAL_PERSISTENCE_FORBIDDEN")
    if env.get("credential_admission_mode") not in CRED: raise ReceiptError("CREDENTIAL_MODE_INVALID")
    cfg=r.get("config_sources",{}); h(cfg,"home_path_digest"); h(cfg,"project_cwd_digest"); h(cfg,"mcp_config_digest")
    if type(cfg.get("unexpected_config_source_count")) is not int or cfg["unexpected_config_source_count"]<0: raise ReceiptError("CONFIG_COUNT_INVALID")
    out=r.get("result",{}); [h(out,k) for k in ("stdout_digest","stderr_digest","raw_envelope_digest","result_digest")]
    if type(out.get("exit_code")) is not int: raise ReceiptError("EXIT_CODE_REQUIRED")
    b=r.get("boundary",{}); claimed=b.get("passed")
    if type(claimed) is not bool: raise ReceiptError("BOUNDARY_PASS_REQUIRED")
    if schema=="TOOLLESS_RECEIPT/v1":
        passed=(b.get("tools_flag_empty") is True and b.get("strict_mcp_config") is True and b.get("permission_mode")=="plan" and b.get("effective_tool_authority_count")==0)
    elif schema=="EPHEMERAL_RECEIPT/v1":
        h(b,"pre_session_artifact_digest"); h(b,"post_session_artifact_digest")
        passed=(b.get("no_session_persistence") is True and b.get("cross_turn_state_detected") is False and b.get("claude_persistent_state_write_count")==0)
    elif schema=="STRUCTURED_OUTPUT_RECEIPT/v1":
        h(b,"accepted_structured_output_digest")
        passed=(b.get("acceptance_path")=="structured_output" and b.get("direct_raw_text_acceptance") is False and b.get("parser_accepted") is True)
    else:
        h(b,"allowlist_digest")
        passed=(b.get("unexpected_env_key_count")==0 and b.get("unexpected_config_ingress_count")==0 and b.get("raw_credential_material_exposed_to_receipt") is False)
    if claimed!=passed: raise ReceiptError("BOUNDARY_PASS_MISMATCH")
    envelope=h(r,"receipt_envelope_digest")
    if envelope!=digest(r): raise ReceiptError("RECEIPT_ENVELOPE_DIGEST_MISMATCH")
    return {"ok":True,"schema":schema,"source_commit":commit,"run_binding_digest":run_bind,"boundary_passed":passed,"receipt_digest":envelope,"runtime_credit":0,"product_credit":0}

def main():
    try: print(json.dumps(validate(json.load(sys.stdin)),sort_keys=True)); return 0
    except (ReceiptError,json.JSONDecodeError) as e: print(json.dumps({"ok":False,"error":str(e)},sort_keys=True)); return 2
if __name__=="__main__": raise SystemExit(main())
