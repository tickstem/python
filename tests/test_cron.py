import json
import pytest
import respx
import httpx

from tickstem import CronClient, CronRegisterParams, APIError, is_unauthorized, is_quota_exceeded

BASE = "https://api.tickstem.dev/v1"

JOB = {
    "id": "job-1",
    "name": "Send digest",
    "schedule": "0 9 * * 1-5",
    "endpoint": "https://example.com/digest",
    "method": "POST",
    "status": "active",
    "timeout_secs": 30,
    "next_run_at": "2026-05-12T09:00:00Z",
    "created_at": "2026-05-01T00:00:00Z",
    "updated_at": "2026-05-01T00:00:00Z",
}

EXECUTION = {
    "id": "exec-1",
    "job_id": "job-1",
    "status": "success",
    "status_code": 200,
    "duration_ms": 120,
    "triggered_at": "2026-05-11T09:00:00Z",
}


@respx.mock
def test_given_valid_key_when_list_then_returns_jobs():
    respx.get(f"{BASE}/jobs").mock(return_value=httpx.Response(200, json={"jobs": [JOB]}))
    client = CronClient("tsk_test")
    jobs = client.list()
    assert len(jobs) == 1
    assert jobs[0].id == "job-1"
    assert jobs[0].name == "Send digest"


@respx.mock
def test_given_empty_response_when_list_then_returns_empty_list():
    respx.get(f"{BASE}/jobs").mock(return_value=httpx.Response(200, json={"jobs": None}))
    client = CronClient("tsk_test")
    assert client.list() == []


@respx.mock
def test_given_valid_key_when_get_then_returns_job():
    respx.get(f"{BASE}/jobs/job-1").mock(return_value=httpx.Response(200, json=JOB))
    client = CronClient("tsk_test")
    job = client.get("job-1")
    assert job.id == "job-1"
    assert job.schedule == "0 9 * * 1-5"


@respx.mock
def test_given_valid_params_when_register_then_returns_job():
    respx.post(f"{BASE}/jobs").mock(return_value=httpx.Response(201, json=JOB))
    client = CronClient("tsk_test")
    job = client.register(CronRegisterParams(name="Send digest", schedule="0 9 * * 1-5", endpoint="https://example.com/digest"))
    assert job.id == "job-1"


@respx.mock
def test_given_job_when_pause_then_returns_paused_job():
    paused = {**JOB, "status": "paused"}
    respx.post(f"{BASE}/jobs/job-1/pause").mock(return_value=httpx.Response(200, json=paused))
    client = CronClient("tsk_test")
    job = client.pause("job-1")
    assert job.status == "paused"


@respx.mock
def test_given_paused_job_when_resume_then_returns_active_job():
    respx.post(f"{BASE}/jobs/job-1/resume").mock(return_value=httpx.Response(200, json=JOB))
    client = CronClient("tsk_test")
    job = client.resume("job-1")
    assert job.status == "active"


@respx.mock
def test_given_job_when_delete_then_no_error():
    respx.delete(f"{BASE}/jobs/job-1").mock(return_value=httpx.Response(204))
    client = CronClient("tsk_test")
    client.delete("job-1")


@respx.mock
def test_given_job_when_executions_then_returns_list():
    respx.get(f"{BASE}/executions", params={"job_id": "job-1"}).mock(
        return_value=httpx.Response(200, json={"executions": [EXECUTION]})
    )
    client = CronClient("tsk_test")
    execs = client.executions("job-1")
    assert len(execs) == 1
    assert execs[0].status == "success"
    assert execs[0].duration_ms == 120


@respx.mock
def test_given_invalid_key_when_list_then_raises_api_error():
    respx.get(f"{BASE}/jobs").mock(return_value=httpx.Response(401, json={"error": "unauthorized"}))
    client = CronClient("tsk_bad")
    with pytest.raises(APIError) as exc_info:
        client.list()
    assert exc_info.value.status == 401
    assert is_unauthorized(exc_info.value)


@respx.mock
def test_given_quota_exceeded_when_register_then_raises_api_error():
    respx.post(f"{BASE}/jobs").mock(return_value=httpx.Response(402, json={"error": "quota exceeded"}))
    client = CronClient("tsk_test")
    with pytest.raises(APIError) as exc_info:
        client.register(CronRegisterParams(name="x", schedule="* * * * *", endpoint="https://example.com"))
    assert is_quota_exceeded(exc_info.value)


@respx.mock
def test_given_request_when_sent_then_user_agent_header_set():
    route = respx.get(f"{BASE}/jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    client = CronClient("tsk_test")
    client.list()
    assert route.called
    assert "tickstem-python/" in route.calls[0].request.headers["user-agent"]
