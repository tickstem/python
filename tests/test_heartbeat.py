import pytest
import respx
import httpx

from tickstem import HeartbeatClient, HeartbeatCreateParams, APIError, is_quota_exceeded

BASE = "https://api.tickstem.dev/v1"

HB = {
    "id": "hb-1",
    "name": "daily backup",
    "token": "abc123token",
    "interval_secs": 86400,
    "grace_secs": 3600,
    "status": "active",
    "consecutive_misses": 0,
    "last_pinged_at": None,
    "next_expected_at": None,
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

PING = {
    "id": "ping-1",
    "heartbeat_id": "hb-1",
    "pinged_at": "2026-05-11T12:00:00Z",
}


@respx.mock
def test_given_valid_key_when_list_then_returns_heartbeats():
    respx.get(f"{BASE}/heartbeats").mock(return_value=httpx.Response(200, json={"heartbeats": [HB]}))
    client = HeartbeatClient("tsk_test")
    heartbeats = client.list()
    assert len(heartbeats) == 1
    assert heartbeats[0].token == "abc123token"


@respx.mock
def test_given_valid_params_when_create_then_returns_heartbeat():
    respx.post(f"{BASE}/heartbeats").mock(return_value=httpx.Response(201, json=HB))
    client = HeartbeatClient("tsk_test")
    hb = client.create(HeartbeatCreateParams(name="daily backup", interval_secs=86400, grace_secs=3600))
    assert hb.id == "hb-1"
    assert hb.interval_secs == 86400


@respx.mock
def test_given_heartbeat_when_pause_then_returns_paused():
    paused = {**HB, "status": "paused"}
    respx.patch(f"{BASE}/heartbeats/hb-1").mock(return_value=httpx.Response(200, json=paused))
    client = HeartbeatClient("tsk_test")
    hb = client.pause("hb-1")
    assert hb.status == "paused"


@respx.mock
def test_given_paused_when_resume_then_returns_active():
    respx.patch(f"{BASE}/heartbeats/hb-1").mock(return_value=httpx.Response(200, json=HB))
    client = HeartbeatClient("tsk_test")
    hb = client.resume("hb-1")
    assert hb.status == "active"


@respx.mock
def test_given_token_when_ping_then_no_auth_header_sent():
    route = respx.post(f"{BASE}/heartbeats/abc123token/ping").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = HeartbeatClient("tsk_test")
    status = client.ping("abc123token")
    assert status == "ok"
    assert "authorization" not in route.calls[0].request.headers


@respx.mock
def test_given_heartbeat_when_pings_then_returns_ping_history():
    respx.get(f"{BASE}/heartbeats/hb-1/pings").mock(
        return_value=httpx.Response(200, json={"pings": [PING]})
    )
    client = HeartbeatClient("tsk_test")
    pings = client.pings("hb-1")
    assert len(pings) == 1
    assert pings[0].pinged_at == "2026-05-11T12:00:00Z"


@respx.mock
def test_given_quota_exceeded_when_create_then_raises():
    respx.post(f"{BASE}/heartbeats").mock(return_value=httpx.Response(402, json={"error": "quota exceeded"}))
    client = HeartbeatClient("tsk_test")
    with pytest.raises(APIError) as exc_info:
        client.create(HeartbeatCreateParams(name="x", interval_secs=3600))
    assert is_quota_exceeded(exc_info.value)
