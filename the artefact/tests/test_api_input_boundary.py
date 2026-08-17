import http.client
import json
import threading

import pytest

from clayverse.api import ClayVerseAPI


class _Verifier:
    def bearer(self, _header):
        return "token"

    def verify(self, _token):
        return {"sub": "clerk-test-user"}


class _Engine:
    def __init__(self):
        self.calls = []

    def ingest(self, subject, content, *, resources=None):
        self.calls.append((subject, content, resources))
        return {"ok": True, "decision": {"text": content}}


def _post(payload):
    engine = _Engine()
    server = ClayVerseAPI(engine, _Verifier()).server("127.0.0.1", 0)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=3)
        body = json.dumps(payload)
        conn.request(
            "POST",
            "/api/chat",
            body,
            {"content-type": "application/json", "authorization": "Bearer test"},
        )
        response = conn.getresponse()
        decoded = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, decoded, engine.calls
    finally:
        thread.join(timeout=3)
        server.server_close()


@pytest.mark.parametrize("content", [{"typed": "object"}, ["typed", "array"], 7, True, None])
def test_chat_rejects_non_string_content_before_engine(content):
    status, body, calls = _post({"content": content})
    assert status == 400
    assert body == {"error": "invalid_content"}
    assert calls == []


def test_chat_rejects_non_object_json_body_before_engine():
    status, body, calls = _post(["not", "an", "object"])
    assert status == 400
    assert body == {"error": "bad_request"}
    assert calls == []


def test_chat_preserves_valid_string_boundary():
    status, body, calls = _post({"content": "  hello ClayVerse  ", "resources": ["repo:x"]})
    assert status == 200
    assert body["ok"] is True
    assert calls == [("clerk-test-user", "hello ClayVerse", ["repo:x"])]
