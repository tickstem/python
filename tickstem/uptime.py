from dataclasses import dataclass, field
from typing import Optional

from ._base import TickstemClient


@dataclass
class Assertion:
    source: str
    comparison: str
    target: str

    def _to_dict(self) -> dict:
        return {"source": self.source, "comparison": self.comparison, "target": self.target}

    @classmethod
    def _from_dict(cls, d: dict) -> "Assertion":
        return cls(source=d["source"], comparison=d["comparison"], target=d["target"])


@dataclass
class Monitor:
    id: str
    name: str
    url: str
    interval_secs: int
    timeout_secs: int
    status: str
    ssl_expires_at: Optional[str]
    next_check_at: Optional[str]
    assertions: list[Assertion]
    created_at: str
    updated_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "Monitor":
        return cls(
            id=d["id"],
            name=d["name"],
            url=d["url"],
            interval_secs=d["interval_secs"],
            timeout_secs=d["timeout_secs"],
            status=d["status"],
            ssl_expires_at=d.get("ssl_expires_at"),
            next_check_at=d.get("next_check_at"),
            assertions=[Assertion._from_dict(a) for a in (d.get("assertions") or [])],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )


@dataclass
class MonitorCheck:
    id: str
    monitor_id: str
    status: str
    status_code: Optional[int]
    duration_ms: int
    error: str
    ssl_expires_at: Optional[str]
    checked_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "MonitorCheck":
        return cls(
            id=d["id"],
            monitor_id=d["monitor_id"],
            status=d["status"],
            status_code=d.get("status_code"),
            duration_ms=d["duration_ms"],
            error=d.get("error", ""),
            ssl_expires_at=d.get("ssl_expires_at"),
            checked_at=d["checked_at"],
        )


@dataclass
class CreateParams:
    name: str
    url: str
    interval_secs: int = 60
    timeout_secs: int = 10
    assertions: list[Assertion] = field(default_factory=list)

    def _to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "interval_secs": self.interval_secs,
            "timeout_secs": self.timeout_secs,
            "assertions": [a._to_dict() for a in self.assertions],
        }


@dataclass
class UpdateParams:
    status: Optional[str] = None
    interval_secs: Optional[int] = None
    timeout_secs: Optional[int] = None
    assertions: Optional[list[Assertion]] = None

    def _to_dict(self) -> dict:
        d: dict = {}
        if self.status is not None:
            d["status"] = self.status
        if self.interval_secs is not None:
            d["interval_secs"] = self.interval_secs
        if self.timeout_secs is not None:
            d["timeout_secs"] = self.timeout_secs
        if self.assertions is not None:
            d["assertions"] = [a._to_dict() for a in self.assertions]
        return d


class UptimeClient(TickstemClient):
    def list(self) -> list[Monitor]:
        data = self._request("GET", "/monitors")
        return [Monitor._from_dict(m) for m in (data.get("monitors") or [])]

    def get(self, monitor_id: str) -> Monitor:
        data = self._request("GET", f"/monitors/{monitor_id}")
        return Monitor._from_dict(data)

    def create(self, params: CreateParams) -> Monitor:
        data = self._request("POST", "/monitors", json=params._to_dict())
        return Monitor._from_dict(data)

    def update(self, monitor_id: str, params: UpdateParams) -> Monitor:
        data = self._request("PATCH", f"/monitors/{monitor_id}", json=params._to_dict())
        return Monitor._from_dict(data)

    def delete(self, monitor_id: str) -> None:
        self._request("DELETE", f"/monitors/{monitor_id}")

    def checks(self, monitor_id: str, *, limit: int = 50, offset: int = 0) -> list[MonitorCheck]:
        data = self._request("GET", f"/monitors/{monitor_id}/checks?limit={limit}&offset={offset}")
        return [MonitorCheck._from_dict(c) for c in (data.get("checks") or [])]
