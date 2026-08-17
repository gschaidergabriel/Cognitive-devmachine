import json
from threading import Event, Thread
from urllib.request import Request, urlopen

from clayverse.adapters import AuthenticationError
from clayverse.api import ClayVerseAPI


class FakeVerifier:
    @staticmethod
    def bearer(value):
        if value != "Bearer good":
            raise AuthenticationError("bad")
        return "good"

    def verify(self, token):
        return {"sub": "clerk-g"}


class BlockingEngine:
    def __init__(self):
        self.entered = Event()
        self.release = Event()

    def ingest(self, subject, content, *, resources=None):
        self.entered.set()
        if not self.release.wait(2):
            raise RuntimeError("test mutation lane was not released")
        return {"decision": {"text": content}}


def test_healthz_stays_responsive_while_cognition_holds_mutation_lane():
    engine = BlockingEngine()
    api = ClayVerseAPI(engine, FakeVerifier())
    server = api.server("127.0.0.1", 0)
    assert server.daemon_threads is False
    assert server.block_on_close is True

    serving = Thread(target=server.serve_forever, daemon=True)
    serving.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    post_error = []

    def send_chat():
        try:
            req = Request(
                base + "/api/chat",
                data=json.dumps({"content": "long turn"}).encode(),
                headers={"Authorization": "Bearer good", "Content-Type": "application/json"},
                method="POST",
            )
            result = json.loads(urlopen(req, timeout=3).read())
            assert result["decision"]["text"] == "long turn"
        except Exception as exc:
            post_error.append(exc)

    worker = Thread(target=send_chat)
    worker.start()
    try:
        assert engine.entered.wait(1), "chat mutation never entered the serialized lane"
        # This is the exact liveness property required by the Docker HEALTHCHECK:
        # a healthy process must answer even while cognition is intentionally slow.
        health = json.loads(urlopen(base + "/healthz", timeout=0.5).read())
        assert health == {"ok": True, "service": "clayverse"}
    finally:
        engine.release.set()
        worker.join(timeout=3)
        server.shutdown()
        server.server_close()
        serving.join(timeout=2)

    assert not worker.is_alive()
    assert not post_error
