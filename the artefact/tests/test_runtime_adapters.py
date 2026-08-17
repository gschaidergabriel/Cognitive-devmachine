import json
import os
import stat
import time
from pathlib import Path
from threading import Thread, Barrier, Lock
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from clayverse.adapters import AuthenticationError, ClerkConfig, ClerkTokenVerifier, ClaudeCodeInference
from clayverse.api import ClayVerseAPI


def keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    return private, pem


def token(private, **overrides):
    now = int(time.time())
    claims = {
        "iss": "https://clerk.example",
        "sub": "user_g",
        "sid": "sess_1",
        "azp": "https://clay.example",
        "iat": now,
        "nbf": now - 1,
        "exp": now + 60,
        **overrides,
    }
    return jwt.encode(claims, private, algorithm="RS256")


def test_clerk_networkless_verification_and_authorized_party():
    private, pem = keypair()
    verifier = ClerkTokenVerifier(ClerkConfig(
        issuer="https://clerk.example",
        jwt_key=pem,
        authorized_parties=("https://clay.example",),
    ))
    assert verifier.verify(token(private))["sub"] == "user_g"
    with pytest.raises(AuthenticationError):
        verifier.verify(token(private, azp="https://evil.example"))
    with pytest.raises(AuthenticationError):
        verifier.verify(token(private, exp=int(time.time()) - 60))


def test_clerk_config_fails_closed_without_authorized_parties(monkeypatch):
    monkeypatch.setenv("CLERK_ISSUER", "https://clerk.example")
    monkeypatch.setenv("CLERK_JWT_KEY", "pem")
    monkeypatch.delenv("CLERK_AUTHORIZED_PARTIES", raising=False)
    with pytest.raises(RuntimeError, match="AUTHORIZED_PARTIES"):
        ClerkConfig.from_env()


def test_claude_code_adapter_is_toolless_ephemeral_structured_one_turn(tmp_path):
    log = tmp_path / "args.json"
    envlog = tmp_path / "env.json"
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os,sys\n"
        "open(os.environ['FAKE_LOG'],'w').write(json.dumps(sys.argv[1:]))\n"
        "open(os.environ['FAKE_ENVLOG'],'w').write(json.dumps({'skip_history':os.environ.get('CLAUDE_CODE_SKIP_PROMPT_HISTORY')}))\n"
        "print(json.dumps({'structured_output':{'text':'ok','effect':None}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    old_log = os.environ.get("FAKE_LOG")
    old_envlog = os.environ.get("FAKE_ENVLOG")
    os.environ["FAKE_LOG"] = str(log)
    os.environ["FAKE_ENVLOG"] = str(envlog)
    try:
        adapter = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5)
        out = adapter.reason({"shared": "state"}, "hello; touch /tmp/SHOULD_NOT_EXIST")
    finally:
        if old_log is None: os.environ.pop("FAKE_LOG", None)
        else: os.environ["FAKE_LOG"] = old_log
        if old_envlog is None: os.environ.pop("FAKE_ENVLOG", None)
        else: os.environ["FAKE_ENVLOG"] = old_envlog
    args = json.loads(log.read_text())
    env = json.loads(envlog.read_text())
    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert "--bare" not in args
    assert "-p" in args
    assert args[args.index("--permission-mode") + 1] == "plan"
    assert args[args.index("--max-turns") + 1] == "1"
    assert args[args.index("--tools") + 1] == ""
    assert "--no-session-persistence" in args
    assert "--json-schema" in args
    schema = json.loads(args[args.index("--json-schema") + 1])
    capability = schema["properties"]["effect"]["anyOf"][1]["properties"]["capability"]
    assert set(capability["enum"]) == {"entityos.exec", "state.noop"}
    assert env["skip_history"] == "1"
    prompt = args[args.index("-p") + 1]
    assert "hello; touch /tmp/SHOULD_NOT_EXIST" in prompt
    assert not Path("/tmp/SHOULD_NOT_EXIST").exists()


def test_claude_code_structured_effect_is_only_an_intent(tmp_path):
    fake = tmp_path / "claude"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "print(json.dumps({'structured_output':{'text':'request','effect':{'capability':'entityos.exec','target':'test','argv':['status']}}}))\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    out = ClaudeCodeInference(binary=str(fake), cwd=str(tmp_path), timeout=5).reason({}, "status")
    assert out == {
        "text": "request",
        "selection": "request_effect",
        "effect": {"capability": "entityos.exec", "target": "test", "argv": ["status"]},
    }


class FakeVerifier:
    @staticmethod
    def bearer(value):
        if value != "Bearer good":
            raise AuthenticationError("bad")
        return "good"

    def verify(self, token):
        return {"sub": "clerk-g"}


class FakeEngine:
    def __init__(self):
        self.calls = []

    def ingest(self, subject, content, *, resources=None):
        self.calls.append((subject, content, resources))
        return {"decision": {"text": "ack"}}


def test_http_boundary_requires_auth_and_routes_subject_to_engine():
    engine = FakeEngine()
    api = ClayVerseAPI(engine, FakeVerifier())
    server = ThreadingHTTPServer(("127.0.0.1", 0), api.handler())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with pytest.raises(HTTPError) as exc:
            urlopen(base + "/api/status")
        assert exc.value.code == 401
        body = json.dumps({"content": "hello", "resources": ["repo:x"]}).encode()
        req = Request(base + "/api/chat", data=body, headers={"Authorization": "Bearer good", "Content-Type": "application/json"}, method="POST")
        out = json.loads(urlopen(req).read())
        assert out["decision"]["text"] == "ack"
        assert engine.calls == [("clerk-g", "hello", ["repo:x"])]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class SerialProbeEngine:
    def __init__(self):
        self.active = 0
        self.max_active = 0
        self.lock = Lock()

    def ingest(self, subject, content, *, resources=None):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.05)
            return {"decision": {"text": content}}
        finally:
            with self.lock:
                self.active -= 1


def test_product_http_server_serializes_central_mutation_lane():
    engine = SerialProbeEngine()
    api = ClayVerseAPI(engine, FakeVerifier())
    server = api.server("127.0.0.1", 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    barrier = Barrier(3)
    results = []

    def send(msg):
        barrier.wait()
        req = Request(
            base + "/api/chat",
            data=json.dumps({"content": msg}).encode(),
            headers={"Authorization": "Bearer good", "Content-Type": "application/json"},
            method="POST",
        )
        results.append(json.loads(urlopen(req, timeout=3).read())["decision"]["text"])

    workers = [Thread(target=send, args=(x,)) for x in ("one", "two")]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(timeout=3)
    try:
        assert sorted(results) == ["one", "two"]
        assert engine.max_active == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
