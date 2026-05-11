from __future__ import annotations

import httpx

from ._version import __version__

DEFAULT_BASE_URL = "https://api.tickstem.dev/v1"


class APIError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message

    def __repr__(self) -> str:
        return f"APIError(status={self.status}, message={self.message!r})"


def is_unauthorized(err: Exception) -> bool:
    return isinstance(err, APIError) and err.status == 401


def is_quota_exceeded(err: Exception) -> bool:
    return isinstance(err, APIError) and err.status == 402


class TickstemClient:
    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL, http_client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._http = http_client or httpx.Client()

    def _request(self, method: str, path: str, *, json: object = None, auth: bool = True) -> object:
        headers = {
            "User-Agent": f"tickstem-python/{__version__}",
            "Accept": "application/json",
        }
        if auth:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if json is not None:
            headers["Content-Type"] = "application/json"

        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            headers=headers,
            json=json,
        )

        if not response.is_success:
            message = response.reason_phrase
            try:
                body = response.json()
                message = body.get("error") or body.get("message") or message
            except Exception:
                pass
            raise APIError(response.status_code, message)

        if response.content:
            return response.json()
        return None

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> TickstemClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
