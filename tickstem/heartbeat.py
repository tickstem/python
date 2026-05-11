from dataclasses import dataclass
from typing import Optional

from ._base import TickstemClient


@dataclass
class Heartbeat:
    id: str
    name: str
    token: str
    interval_secs: int
    grace_secs: int
    status: str
    consecutive_misses: int
    last_pinged_at: Optional[str]
    next_expected_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "Heartbeat":
        return cls(
            id=d["id"],
            name=d["name"],
            token=d["token"],
            interval_secs=d["interval_secs"],
            grace_secs=d["grace_secs"],
            status=d["status"],
            consecutive_misses=d.get("consecutive_misses", 0),
            last_pinged_at=d.get("last_pinged_at"),
            next_expected_at=d.get("next_expected_at"),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )


@dataclass
class Ping:
    id: str
    heartbeat_id: str
    pinged_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "Ping":
        return cls(id=d["id"], heartbeat_id=d["heartbeat_id"], pinged_at=d["pinged_at"])


@dataclass
class CreateParams:
    name: str
    interval_secs: int
    grace_secs: int = 0

    def _to_dict(self) -> dict:
        return {"name": self.name, "interval_secs": self.interval_secs, "grace_secs": self.grace_secs}


class HeartbeatClient(TickstemClient):
    def list(self) -> list[Heartbeat]:
        data = self._request("GET", "/heartbeats")
        return [Heartbeat._from_dict(h) for h in (data.get("heartbeats") or [])]

    def get(self, heartbeat_id: str) -> Heartbeat:
        data = self._request("GET", f"/heartbeats/{heartbeat_id}")
        return Heartbeat._from_dict(data)

    def create(self, params: CreateParams) -> Heartbeat:
        data = self._request("POST", "/heartbeats", json=params._to_dict())
        return Heartbeat._from_dict(data)

    def pause(self, heartbeat_id: str) -> Heartbeat:
        data = self._request("PATCH", f"/heartbeats/{heartbeat_id}", json={"status": "paused"})
        return Heartbeat._from_dict(data)

    def resume(self, heartbeat_id: str) -> Heartbeat:
        data = self._request("PATCH", f"/heartbeats/{heartbeat_id}", json={"status": "active"})
        return Heartbeat._from_dict(data)

    def delete(self, heartbeat_id: str) -> None:
        self._request("DELETE", f"/heartbeats/{heartbeat_id}")

    def ping(self, token: str) -> str:
        data = self._request("POST", f"/heartbeats/{token}/ping", auth=False)
        return data.get("status", "ok")

    def pings(self, heartbeat_id: str, *, limit: int = 50) -> list[Ping]:
        data = self._request("GET", f"/heartbeats/{heartbeat_id}/pings?limit={limit}")
        return [Ping._from_dict(p) for p in (data.get("pings") or [])]
