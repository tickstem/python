from dataclasses import dataclass
from typing import Optional

from ._base import TickstemClient


@dataclass
class Job:
    id: str
    name: str
    schedule: str
    endpoint: str
    method: str
    status: str
    timeout_secs: int
    next_run_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "Job":
        return cls(
            id=d["id"],
            name=d["name"],
            schedule=d["schedule"],
            endpoint=d["endpoint"],
            method=d["method"],
            status=d["status"],
            timeout_secs=d["timeout_secs"],
            next_run_at=d.get("next_run_at"),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )


@dataclass
class Execution:
    id: str
    job_id: str
    status: str
    status_code: Optional[int]
    duration_ms: int
    triggered_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "Execution":
        return cls(
            id=d["id"],
            job_id=d["job_id"],
            status=d["status"],
            status_code=d.get("status_code"),
            duration_ms=d["duration_ms"],
            triggered_at=d["triggered_at"],
        )


@dataclass
class RegisterParams:
    name: str
    schedule: str
    endpoint: str
    method: str = "POST"
    timeout_secs: int = 30
    description: str = ""

    def _to_dict(self) -> dict:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "endpoint": self.endpoint,
            "method": self.method,
            "timeout_secs": self.timeout_secs,
            "description": self.description,
        }


class CronClient(TickstemClient):
    def list(self) -> list[Job]:
        data = self._request("GET", "/jobs")
        jobs = data.get("jobs") or []
        return [Job._from_dict(j) for j in jobs]

    def get(self, job_id: str) -> Job:
        data = self._request("GET", f"/jobs/{job_id}")
        return Job._from_dict(data)

    def register(self, params: RegisterParams) -> Job:
        data = self._request("POST", "/jobs", json=params._to_dict())
        return Job._from_dict(data)

    def update(self, job_id: str, params: RegisterParams) -> Job:
        data = self._request("PUT", f"/jobs/{job_id}", json=params._to_dict())
        return Job._from_dict(data)

    def pause(self, job_id: str) -> Job:
        data = self._request("POST", f"/jobs/{job_id}/pause")
        return Job._from_dict(data)

    def resume(self, job_id: str) -> Job:
        data = self._request("POST", f"/jobs/{job_id}/resume")
        return Job._from_dict(data)

    def delete(self, job_id: str) -> None:
        self._request("DELETE", f"/jobs/{job_id}")

    def executions(self, job_id: str) -> list[Execution]:
        data = self._request("GET", f"/executions?job_id={job_id}")
        execs = data.get("executions") or []
        return [Execution._from_dict(e) for e in execs]
