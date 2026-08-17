from clayverse.api import ClayVerseAPI


class LockProbe:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        self.events.append("lock-enter")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.events.append("lock-exit")
        return False


class EngineProbe:
    def __init__(self, events):
        self.events = events

    def ingest(self, clerk_subject, content, *, resources=None):
        self.events.append("ingest")
        return {"subject": clerk_subject, "content": content, "resources": resources}


def test_chat_ingest_crosses_serialization_gate():
    events = []
    api = ClayVerseAPI(EngineProbe(events), verifier=object())
    api._chat_lock = LockProbe(events)
    result = api.ingest("clerk-g", "hello", resources=["repo:x"])
    assert events == ["lock-enter", "ingest", "lock-exit"]
    assert result == {"subject": "clerk-g", "content": "hello", "resources": ["repo:x"]}
