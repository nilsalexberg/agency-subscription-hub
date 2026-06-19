import httpx
import pytest

from app.integrations.efi.client import EfiClient
from app.integrations.efi.exceptions import EfiAPIError
from app.integrations.efi.schemas import (
    BankingBilletCustomer,
    BankingBilletPayment,
    ChargeRequest,
    Item,
    Payment,
)


def _charge_request() -> ChargeRequest:
    return ChargeRequest(
        items=[Item(name="Plano", value=1990, amount=1)],
        payment=Payment(
            banking_billet=BankingBilletPayment(
                customer=BankingBilletCustomer.model_validate(
                    {
                        "name": "Gorbadoc Oldbuck",
                        "cpf": "94271564656",
                        "email": "client@server.com.br",
                        "birth": "1990-01-01",
                        "phone_number": "11999999999",
                        "address": {
                            "street": "Rua X",
                            "number": "1",
                            "neighborhood": "Centro",
                            "zipcode": "01310100",
                            "city": "São Paulo",
                            "state": "SP",
                        },
                    }
                ),
                expire_at="2026-06-30",
            )
        ),
    )


class FakeEfi:
    """Records every request and serves scripted, route-aware responses."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.authorize_responses: list[httpx.Response] = [
            httpx.Response(200, json={"access_token": "token-1", "expires_in": 3600})
        ]
        self.charge_responses: list[httpx.Response] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if request.url.path.endswith("/authorize"):
            return self.authorize_responses.pop(0)
        if request.url.path.endswith("/charge/one-step"):
            return self.charge_responses.pop(0)
        raise AssertionError(f"unexpected request: {request.method} {request.url.path}")

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)

    def authorize_call_count(self) -> int:
        return sum(1 for c in self.calls if c.url.path.endswith("/authorize"))


@pytest.mark.asyncio
async def test_create_charge_sends_bearer_token_and_parses_response():
    fake = FakeEfi()
    fake.charge_responses.append(
        httpx.Response(200, json={"data": {"charge_id": 123456, "status": "waiting"}})
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    response = await efi.create_charge(_charge_request())

    assert response.data.charge_id == 123456
    assert response.data.status == "waiting"
    assert fake.calls[-1].headers["authorization"] == "Bearer token-1"


@pytest.mark.asyncio
async def test_token_is_cached_across_requests():
    fake = FakeEfi()
    fake.charge_responses.extend(
        [
            httpx.Response(200, json={"data": {"charge_id": 1, "status": "waiting"}}),
            httpx.Response(200, json={"data": {"charge_id": 2, "status": "waiting"}}),
        ]
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    await efi.create_charge(_charge_request())
    await efi.create_charge(_charge_request())

    assert fake.authorize_call_count() == 1


@pytest.mark.asyncio
async def test_expired_token_triggers_reauthentication(monkeypatch):
    clock = {"now": 1_000.0}
    monkeypatch.setattr("app.integrations.efi.client.time.monotonic", lambda: clock["now"])

    fake = FakeEfi()
    fake.authorize_responses.append(
        httpx.Response(200, json={"access_token": "token-2", "expires_in": 3600})
    )
    fake.charge_responses.extend(
        [
            httpx.Response(200, json={"data": {"charge_id": 1, "status": "waiting"}}),
            httpx.Response(200, json={"data": {"charge_id": 2, "status": "waiting"}}),
        ]
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    await efi.create_charge(_charge_request())
    clock["now"] += 3600  # advance past the token's expiry + leeway
    await efi.create_charge(_charge_request())

    assert fake.authorize_call_count() == 2
    assert fake.calls[-1].headers["authorization"] == "Bearer token-2"


@pytest.mark.asyncio
async def test_401_triggers_single_reauth_and_retry():
    fake = FakeEfi()
    fake.authorize_responses.append(
        httpx.Response(200, json={"access_token": "token-2", "expires_in": 3600})
    )
    fake.charge_responses.extend(
        [
            httpx.Response(401, json={"error_description": "token expired"}),
            httpx.Response(200, json={"data": {"charge_id": 1, "status": "waiting"}}),
        ]
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    response = await efi.create_charge(_charge_request())

    assert response.data.charge_id == 1
    assert fake.authorize_call_count() == 2


@pytest.mark.asyncio
async def test_card_charge_unpaid_status_does_not_raise():
    fake = FakeEfi()
    fake.charge_responses.append(
        httpx.Response(
            200,
            json={
                "data": {
                    "charge_id": 1,
                    "status": "unpaid",
                    "refusal": {"reason": "insufficient funds"},
                }
            },
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    response = await efi.create_charge(_charge_request())

    assert response.data.status == "unpaid"
    assert response.data.refusal.reason == "insufficient funds"


@pytest.mark.asyncio
async def test_error_response_raises_efi_api_error_with_property():
    fake = FakeEfi()
    fake.charge_responses.append(
        httpx.Response(
            400,
            json={
                "error_description": "invalid zipcode",
                "property": "/payment/banking_billet/customer/address/zipcode",
            },
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=fake.transport)

    with pytest.raises(EfiAPIError) as exc_info:
        await efi.create_charge(_charge_request())

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_description == "invalid zipcode"
    assert exc_info.value.property == "/payment/banking_billet/customer/address/zipcode"


@pytest.mark.asyncio
async def test_get_installments_parses_basis_points():
    fake = FakeEfi()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.calls.append(request)
        if request.url.path.endswith("/authorize"):
            return fake.authorize_responses.pop(0)
        assert request.url.path.endswith("/installments")
        assert dict(request.url.params) == {"brand": "visa", "total": "19900"}
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "installment": 1,
                        "currency": "199.00",
                        "has_interest": False,
                        "interest_percentage": 0,
                    },
                    {
                        "installment": 2,
                        "currency": "104.50",
                        "has_interest": True,
                        "interest_percentage": 250,
                    },
                ]
            },
        )

    efi = EfiClient("id", "secret", sandbox=True, transport=httpx.MockTransport(handler))

    options = await efi.get_installments(brand="visa", total=19900)

    assert options[1].interest_percentage == 250
    assert options[1].has_interest is True


@pytest.mark.asyncio
async def test_fetch_notification_returns_events():
    fake = FakeEfi()

    def handler(request: httpx.Request) -> httpx.Response:
        fake.calls.append(request)
        if request.url.path.endswith("/authorize"):
            return fake.authorize_responses.pop(0)
        assert request.url.path.endswith("/notification/tok-abc")
        return httpx.Response(
            200,
            json={"data": [{"identifiers": {"charge_id": 123456}, "status": {"current": "paid"}}]},
        )

    efi = EfiClient("id", "secret", sandbox=True, transport=httpx.MockTransport(handler))

    events = await efi.fetch_notification("tok-abc")

    assert events[0].identifiers.charge_id == 123456
    assert events[0].status.current == "paid"


def test_sandbox_flag_selects_sandbox_base_url():
    efi = EfiClient("id", "secret", sandbox=True)
    assert efi.base_url.rstrip("/") == "https://cobrancas-h.api.efipay.com.br/v1"


def test_production_flag_selects_production_base_url():
    efi = EfiClient("id", "secret", sandbox=False)
    assert efi.base_url.rstrip("/") == "https://cobrancas.api.efipay.com.br/v1"
