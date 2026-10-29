from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

import httpx

from .config import Settings


class PortalError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class UrjaPortalClient:
    """Read-only portal client with cookie-based session renewal."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.settings = settings
        self.http = httpx.AsyncClient(
            base_url=str(settings.urja_base_url).rstrip("/"),
            timeout=settings.request_timeout_seconds,
            follow_redirects=False,
            transport=transport,
            headers={"Accept": "application/json"},
        )
        self._authenticated = False

    async def close(self) -> None:
        await self.http.aclose()

    async def _login(self) -> None:
        response = await self.http.post(
            "/login",
            data={"email": self.settings.urja_email, "password": self.settings.urja_password.get_secret_value()},
            headers={"Origin": str(self.settings.urja_base_url).rstrip("/"), "X-Sveltekit-Action": "true"},
        )
        if response.status_code not in {200, 303}:
            raise PortalError(502, "The upstream portal rejected authentication.")
        if not self.http.cookies.get("__Secure-better-auth.session_token"):
            raise PortalError(502, "The upstream portal did not issue a session cookie.")
        self._authenticated = True

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self._authenticated:
            await self._login()

        response = await self.http.get(path, params=params)
        if response.status_code in {401, 403}:
            self._authenticated = False
            await self._login()
            response = await self.http.get(path, params=params)
        if response.status_code >= 400:
            raise PortalError(502, f"The upstream portal returned HTTP {response.status_code}.")
        try:
            return response.json()
        except ValueError as exc:
            raise PortalError(502, "The upstream portal returned invalid JSON.") from exc

    async def search_meters(self, query: str, page: int) -> Any:
        return await self.get_json(self.settings.urja_search_path, {"q": query, "page": page})

    async def meter_geo(self, meter_id: str) -> Any:
        return await self.get_json(self.settings.urja_geo_path_template.format(meter_id=meter_id))

    async def meter_energy(self, meter_id: str, params: dict[str, str | int]) -> Any:
        path = self.settings.urja_energy_path_template.format(meter_id=meter_id)
        return await self.get_json(path, params)

    async def export_meters(self) -> Any:
        """Use the portal's user-visible signed export flow without exposing its key."""
        key_document = await self.get_json("/portal/keys")
        secret = key_document["data"]["signingSecret"]
        query = "page=1"
        timestamp = str(int(time.time()))
        payload = f"GET\n/portal/export\n{query}\n{timestamp}".encode()
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        if not self._authenticated:
            await self._login()
        response = await self.http.get(
            f"/portal/export?{query}",
            headers={"x-timestamp": timestamp, "x-signature": signature},
        )
        if response.status_code >= 400:
            raise PortalError(502, f"The upstream export returned HTTP {response.status_code}.")
        return response.json()

