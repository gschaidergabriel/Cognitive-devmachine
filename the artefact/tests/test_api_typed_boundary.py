import pytest

from clayverse.api import validate_chat_payload


def test_chat_payload_accepts_only_explicit_text_resources_and_request_id():
    content, resources, request_id = validate_chat_payload({"content": "  hello ClayVerse  ", "resources": ["repo:a", "doc:b"], "request_id": "req-1"})
    assert content == "hello ClayVerse"
    assert resources == ["repo:a", "doc:b"]
    assert request_id == "req-1"


@pytest.mark.parametrize("content", [None, 0, 3.14, True, [], {}, ["text"]])
def test_chat_payload_rejects_non_string_content_instead_of_coercing(content):
    with pytest.raises(ValueError):
        validate_chat_payload({"content": content, "request_id": "req-1"})


@pytest.mark.parametrize("body", [None, [], "text", 7, True])
def test_chat_payload_requires_json_object(body):
    with pytest.raises(ValueError):
        validate_chat_payload(body)


def test_chat_payload_rejects_unknown_fields_fail_closed():
    with pytest.raises(ValueError):
        validate_chat_payload({"content": "hello", "request_id": "req-1", "effect": {"capability": "process.exec"}})


@pytest.mark.parametrize("resources", [None, "repo:a", ["ok", 3], {"repo": "a"}])
def test_chat_payload_rejects_non_string_list_resources(resources):
    with pytest.raises(ValueError):
        validate_chat_payload({"content": "hello", "resources": resources, "request_id": "req-1"})


@pytest.mark.parametrize("request_id", [None, "", 7, [], {}, "x" * 129])
def test_chat_payload_requires_bounded_request_id(request_id):
    with pytest.raises(ValueError):
        validate_chat_payload({"content": "hello", "request_id": request_id})
