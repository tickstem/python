import pytest
import respx
import httpx

from tickstem import VerifyClient, VerifyResult, APIError, is_unauthorized

BASE = "https://api.tickstem.dev/v1"

RESULT = {
    "id": "ver-1",
    "email": "user@example.com",
    "valid": True,
    "mx_found": True,
    "disposable": False,
    "role_based": False,
    "reason": "",
    "created_at": "2026-05-11T12:00:00Z",
}


@respx.mock
def test_given_valid_email_when_verify_then_returns_result():
    respx.post(f"{BASE}/verify").mock(return_value=httpx.Response(200, json=RESULT))
    client = VerifyClient("tsk_test")
    result = client.verify("user@example.com")
    assert result.valid is True
    assert result.mx_found is True
    assert result.disposable is False


@respx.mock
def test_given_disposable_email_when_verify_then_valid_false():
    disposable = {**RESULT, "valid": False, "disposable": True, "reason": "disposable domain"}
    respx.post(f"{BASE}/verify").mock(return_value=httpx.Response(200, json=disposable))
    client = VerifyClient("tsk_test")
    result = client.verify("user@mailinator.com")
    assert result.valid is False
    assert result.disposable is True
    assert result.reason == "disposable domain"


@respx.mock
def test_given_history_request_when_called_then_returns_list():
    respx.get(f"{BASE}/verify/history").mock(
        return_value=httpx.Response(200, json={"results": [RESULT]})
    )
    client = VerifyClient("tsk_test")
    history = client.history()
    assert len(history) == 1
    assert history[0].email == "user@example.com"


@respx.mock
def test_given_invalid_key_when_verify_then_raises_unauthorized():
    respx.post(f"{BASE}/verify").mock(return_value=httpx.Response(401, json={"error": "unauthorized"}))
    client = VerifyClient("tsk_bad")
    with pytest.raises(APIError) as exc_info:
        client.verify("user@example.com")
    assert is_unauthorized(exc_info.value)
