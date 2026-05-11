import pytest
import respx
import httpx

from tickstem import UptimeClient, UptimeCreateParams, UptimeUpdateParams, Assertion, APIError, is_quota_exceeded

BASE = "https://api.tickstem.dev/v1"

MONITOR = {
    "id": "mon-1",
    "name": "Production API",
    "url": "https://api.example.com/health",
    "interval_secs": 60,
    "timeout_secs": 10,
    "status": "active",
    "ssl_expires_at": "2026-08-01T00:00:00Z",
    "next_check_at": "2026-05-11T12:01:00Z",
    "assertions": [{"source": "status_code", "comparison": "eq", "target": "200"}],
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

CHECK = {
    "id": "chk-1",
    "monitor_id": "mon-1",
    "status": "up",
    "status_code": 200,
    "duration_ms": 183,
    "error": "",
    "ssl_expires_at": "2026-08-01T00:00:00Z",
    "checked_at": "2026-05-11T12:00:00Z",
}


@respx.mock
def test_given_valid_key_when_list_then_returns_monitors():
    respx.get(f"{BASE}/monitors").mock(return_value=httpx.Response(200, json={"monitors": [MONITOR]}))
    client = UptimeClient("tsk_test")
    monitors = client.list()
    assert len(monitors) == 1
    assert monitors[0].id == "mon-1"
    assert monitors[0].assertions[0].source == "status_code"


@respx.mock
def test_given_valid_params_when_create_then_returns_monitor():
    respx.post(f"{BASE}/monitors").mock(return_value=httpx.Response(201, json=MONITOR))
    client = UptimeClient("tsk_test")
    monitor = client.create(UptimeCreateParams(
        name="Production API",
        url="https://api.example.com/health",
        assertions=[Assertion(source="status_code", comparison="eq", target="200")],
    ))
    assert monitor.id == "mon-1"
    assert monitor.url == "https://api.example.com/health"


@respx.mock
def test_given_monitor_when_update_then_returns_updated():
    updated = {**MONITOR, "interval_secs": 120}
    respx.patch(f"{BASE}/monitors/mon-1").mock(return_value=httpx.Response(200, json=updated))
    client = UptimeClient("tsk_test")
    monitor = client.update("mon-1", UptimeUpdateParams(interval_secs=120))
    assert monitor.interval_secs == 120


@respx.mock
def test_given_monitor_when_delete_then_no_error():
    respx.delete(f"{BASE}/monitors/mon-1").mock(return_value=httpx.Response(204))
    client = UptimeClient("tsk_test")
    client.delete("mon-1")


@respx.mock
def test_given_monitor_when_checks_then_returns_check_history():
    respx.get(f"{BASE}/monitors/mon-1/checks").mock(
        return_value=httpx.Response(200, json={"checks": [CHECK]})
    )
    client = UptimeClient("tsk_test")
    checks = client.checks("mon-1")
    assert len(checks) == 1
    assert checks[0].status == "up"
    assert checks[0].duration_ms == 183


@respx.mock
def test_given_quota_exceeded_when_create_then_raises():
    respx.post(f"{BASE}/monitors").mock(return_value=httpx.Response(402, json={"error": "quota exceeded"}))
    client = UptimeClient("tsk_test")
    with pytest.raises(APIError) as exc_info:
        client.create(UptimeCreateParams(name="x", url="https://example.com"))
    assert is_quota_exceeded(exc_info.value)
