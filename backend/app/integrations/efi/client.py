"""Async client for the Efí (Gerencianet) Cobranças one-step charge API.

See docs/efi.md for the API reference this implements.
"""

from __future__ import annotations

import base64
import time
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings

from .exceptions import EfiAPIError
from .schemas import ChargeRequest, ChargeResponse, InstallmentOption, NotificationEvent

PRODUCTION_BASE_URL = "https://cobrancas.api.efipay.com.br/v1"
SANDBOX_BASE_URL = "https://cobrancas-h.api.efipay.com.br/v1"

# Refresh slightly before the token's reported expiry to avoid racing a 401.
_TOKEN_EXPIRY_LEEWAY_SECONDS = 30
_DEFAULT_TOKEN_TTL_SECONDS = 3600


class EfiClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        sandbox: bool,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        base_url = SANDBOX_BASE_URL if sandbox else PRODUCTION_BASE_URL
        self._http = httpx.AsyncClient(base_url=base_url, timeout=30.0, transport=transport)
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def base_url(self) -> str:
        return str(self._http.base_url)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def create_charge(self, charge: ChargeRequest) -> ChargeResponse:
        body = await self._request(
            "POST",
            "/charge/one-step",
            json=charge.model_dump(mode="json", exclude_none=True),
        )
        return ChargeResponse.model_validate(body)

    async def get_installments(self, brand: str, total: int) -> list[InstallmentOption]:
        body = await self._request(
            "GET", "/installments", params={"brand": brand, "total": total}
        )
        return [InstallmentOption.model_validate(item) for item in body["data"]]

    async def fetch_notification(self, token: str) -> list[NotificationEvent]:
        """Resolve a webhook notification token into the events it represents.

        Efí's webhook POST carries only an opaque token, never the payment
        data itself — this follow-up GET is mandatory to learn what changed.
        """
        body = await self._request("GET", f"/notification/{token}")
        return [NotificationEvent.model_validate(item) for item in body["data"]]

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        token = await self._get_access_token()
        response = await self._http.request(
            method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs
        )
        if response.status_code == 401:
            token = await self._get_access_token(force_refresh=True)
            response = await self._http.request(
                method, path, headers={"Authorization": f"Bearer {token}"}, **kwargs
            )
        _raise_for_error(response)
        return response.json()

    async def _get_access_token(self, force_refresh: bool = False) -> str:
        if (
            not force_refresh
            and self._access_token is not None
            and time.monotonic() < self._token_expires_at
        ):
            return self._access_token

        credentials = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()
        response = await self._http.post(
            "/authorize",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
            json={"grant_type": "client_credentials"},
        )
        _raise_for_error(response)
        body = response.json()
        self._access_token = body["access_token"]
        expires_in = body.get("expires_in", _DEFAULT_TOKEN_TTL_SECONDS)
        self._token_expires_at = time.monotonic() + expires_in - _TOKEN_EXPIRY_LEEWAY_SECONDS
        return self._access_token


def _raise_for_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    try:
        body = response.json()
    except ValueError:
        body = {}
    raise EfiAPIError(
        status_code=response.status_code,
        error_description=body.get("error_description", response.text),
        property=body.get("property"),
    )


@lru_cache
def get_efi_client() -> EfiClient:
    return EfiClient(
        client_id=settings.EFI_CLIENT_ID,
        client_secret=settings.EFI_CLIENT_SECRET,
        sandbox=settings.EFI_SANDBOX,
    )
