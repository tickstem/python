# tickstem-python

[![PyPI](https://img.shields.io/pypi/v/tickstem)](https://pypi.org/project/tickstem/)
[![Python](https://img.shields.io/pypi/pyversions/tickstem)](https://pypi.org/project/tickstem/)
[![CI](https://github.com/tickstem/python/actions/workflows/release.yml/badge.svg)](https://github.com/tickstem/python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python SDK for [Tickstem](https://tickstem.dev) — cron jobs, uptime monitoring, heartbeat checks, and email verification under a single API key.

```
pip install tickstem
```

Requires Python 3.11+.

---

## Cron jobs

Schedule HTTP endpoints on a cron expression. Works on Vercel, Railway, Render, and Fly.io — no background processes required.

```python
from tickstem import CronClient, CronRegisterParams

client = CronClient("tsk_your_api_key")

job = client.register(CronRegisterParams(
    name="Send digest",
    schedule="0 9 * * 1-5",   # 9am weekdays
    endpoint="https://yourapp.com/webhooks/digest",
    method="POST",
))

print(job.id, job.next_run_at)

# List jobs and executions
jobs = client.list()
executions = client.executions(job.id)

# Pause / resume / delete
client.pause(job.id)
client.resume(job.id)
client.delete(job.id)
```

## Uptime monitoring

Poll HTTP endpoints and get alerted by email on failure, recovery, and SSL expiry.

```python
from tickstem import UptimeClient, UptimeCreateParams, Assertion

client = UptimeClient("tsk_your_api_key")

monitor = client.create(UptimeCreateParams(
    name="Production API",
    url="https://api.yourapp.com/health",
    interval_secs=60,
    assertions=[
        Assertion(source="status_code",   comparison="eq", target="200"),
        Assertion(source="response_time", comparison="lt", target="2000"),
        Assertion(source="body",          comparison="contains", target='"status":"ok"'),
    ],
))

# Check history
checks = client.checks(monitor.id, limit=50)
for check in checks:
    print(check.status, check.duration_ms, "ms")

# Pause / resume / delete
client.update(monitor.id, UptimeUpdateParams(status="paused"))
client.delete(monitor.id)
```

## Heartbeat monitoring

Dead man's switch for scheduled jobs. Ping after each successful run — get alerted if pings stop arriving.

```python
from tickstem import HeartbeatClient, HeartbeatCreateParams

client = HeartbeatClient("tsk_your_api_key")

# Create once — save the token
hb = client.create(HeartbeatCreateParams(
    name="daily backup",
    interval_secs=86400,  # expect a ping every 24h
    grace_secs=3600,      # 1h grace before alerting
))

# At the end of every successful job run — no API key needed
status = client.ping(hb.token)
print(status)  # "ok" or "paused"

# Pause / resume
client.pause(hb.id)
client.resume(hb.id)
```

## Email verification

Check syntax, MX records, disposable domains, and role-based prefixes before storing an address.

```python
from tickstem import VerifyClient

client = VerifyClient("tsk_your_api_key")

result = client.verify("user@example.com")
print(result.valid)      # True
print(result.disposable) # False
print(result.role_based) # False
print(result.reason)     # "" (empty when valid)

# Verification history
history = client.history(limit=20)
```

---

## Error handling

```python
from tickstem import CronClient, APIError, is_unauthorized, is_quota_exceeded

client = CronClient("tsk_your_api_key")

try:
    jobs = client.list()
except APIError as err:
    if is_unauthorized(err):
        print("invalid API key")
    elif is_quota_exceeded(err):
        print("plan limit reached")
    else:
        print(f"error {err.status}: {err.message}")
```

## Custom base URL / HTTP client

```python
import httpx
from tickstem import CronClient

# Override base URL (e.g. for testing)
client = CronClient("tsk_test", base_url="http://localhost:8080/v1")

# Bring your own httpx.Client (timeouts, proxies, etc.)
http = httpx.Client(timeout=30.0)
client = CronClient("tsk_your_api_key", http_client=http)

# Use as a context manager to ensure the connection is closed
with CronClient("tsk_your_api_key") as client:
    jobs = client.list()
```

---

## Links

- [Dashboard](https://app.tickstem.dev)
- [Documentation](https://tickstem.dev/docs)
- [API reference](https://tickstem.dev/openapi.yaml)
- [Support](mailto:hi@tickstem.dev)
