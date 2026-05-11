from __future__ import annotations

from dataclasses import dataclass

from ._base import TickstemClient


@dataclass
class VerifyResult:
    id: str
    email: str
    valid: bool
    mx_found: bool
    disposable: bool
    role_based: bool
    reason: str
    created_at: str

    @classmethod
    def _from_dict(cls, d: dict) -> "VerifyResult":
        return cls(
            id=d["id"],
            email=d["email"],
            valid=d["valid"],
            mx_found=d["mx_found"],
            disposable=d["disposable"],
            role_based=d["role_based"],
            reason=d.get("reason", ""),
            created_at=d["created_at"],
        )


class VerifyClient(TickstemClient):
    def verify(self, email: str) -> VerifyResult:
        data = self._request("POST", "/verify", json={"email": email})
        return VerifyResult._from_dict(data)

    def history(self, *, limit: int = 20, offset: int = 0) -> list[VerifyResult]:
        data = self._request("GET", f"/verify/history?limit={limit}&offset={offset}")
        return [VerifyResult._from_dict(r) for r in (data.get("results") or [])]
