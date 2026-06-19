import httpx
import pytest

from app.integrations.efi.client import EfiClient
from app.integrations.efi.exceptions import EfiAPIError
from app.integrations.efi.schemas import (
    Address,
    BankingBilletCustomer,
    BankingBilletPayment,
    ChargeRequest,
    CreateSubscriptionOneStepRequest,
    CreateSubscriptionRequest,
    Customer,
    Item,
    Payment,
    PlanRequest,
    RetryChargeRequest,
    RetryChargeCreditCard,
    RetryChargePayment,
    SubscriptionBilletCustomer,
    SubscriptionBilletPayment,
    SubscriptionCreditCardPayment,
    SubscriptionMetadataRequest,
    SubscriptionPayment,
    SubscriptionPayRequest,
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


# --- Subscription client tests ---

_AUTH_RESPONSE = httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})


def _make_handler(*route_responses: tuple[str, httpx.Response]):
    """Build a MockTransport handler that routes by URL path suffix."""
    routes = list(route_responses)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/authorize"):
            return _AUTH_RESPONSE
        for suffix, response in routes:
            if request.url.path.endswith(suffix):
                return response
        raise AssertionError(f"unexpected: {request.method} {request.url.path}")

    return httpx.MockTransport(handler)


def _address() -> dict:
    return {
        "street": "Av. Paulista",
        "number": "1000",
        "neighborhood": "Bela Vista",
        "zipcode": "01310100",
        "city": "São Paulo",
        "state": "SP",
    }


def _customer() -> dict:
    return {
        "name": "Gorbadoc Oldbuck",
        "cpf": "94271564656",
        "email": "client@server.com.br",
        "birth": "1990-08-29",
        "phone_number": "11999999999",
    }


def _sub_billet_customer() -> dict:
    return {**{k: v for k, v in _customer().items() if k != "birth"}, "address": _address()}


def _billet_payment() -> SubscriptionPayment:
    return SubscriptionPayment(
        banking_billet=SubscriptionBilletPayment(
            customer=SubscriptionBilletCustomer.model_validate(_sub_billet_customer()),
            expire_at="2026-12-30",
        )
    )


def _card_payment() -> SubscriptionPayment:
    return SubscriptionPayment(
        credit_card=SubscriptionCreditCardPayment(
            customer=Customer.model_validate(_customer()),
            payment_token="tok_card",
            billing_address=Address.model_validate(_address()),
        )
    )


@pytest.mark.asyncio
async def test_create_plan_sends_body_and_parses_response():
    transport = _make_handler(
        (
            "/plan",
            httpx.Response(
                200,
                json={
                    "data": {
                        "plan_id": 2758,
                        "name": "Monthly Plan",
                        "interval": 1,
                        "repeats": None,
                        "created_at": "2024-01-01 00:00:00",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.create_plan(PlanRequest(name="Monthly Plan", interval=1))

    assert response.data.plan_id == 2758
    assert response.data.interval == 1
    assert response.data.repeats is None


@pytest.mark.asyncio
async def test_create_subscription_one_step_boleto_parses_active_response():
    transport = _make_handler(
        (
            "/subscription/one-step",
            httpx.Response(
                200,
                json={
                    "data": {
                        "subscription_id": 25329,
                        "status": "active",
                        "barcode": "00000.00000",
                        "plan": {"id": 2758, "interval": 1, "repeats": None},
                        "charge": {"id": 511843, "status": "waiting", "parcel": 1, "total": 5990},
                        "first_execution": "31/10/2026",
                        "total": 5990,
                        "payment": "banking_billet",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.create_subscription_one_step(
        plan_id=2758,
        request=CreateSubscriptionOneStepRequest(
            items=[Item(name="Plano", value=5990, amount=1)],
            payment=_billet_payment(),
        ),
    )

    assert response.data.subscription_id == 25329
    assert response.data.status == "active"
    assert response.data.plan.id == 2758
    assert response.data.charge.id == 511843
    assert response.data.barcode == "00000.00000"


@pytest.mark.asyncio
async def test_create_subscription_one_step_card_parses_active_response():
    transport = _make_handler(
        (
            "/subscription/one-step",
            httpx.Response(
                200,
                json={
                    "data": {
                        "subscription_id": 25328,
                        "status": "active",
                        "plan": {"id": 2758, "interval": 1, "repeats": None},
                        "charge": {"id": 511842, "status": "waiting", "parcel": 1, "total": 5990},
                        "first_execution": "31/10/2026",
                        "total": 5990,
                        "payment": "credit_card",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.create_subscription_one_step(
        plan_id=2758,
        request=CreateSubscriptionOneStepRequest(
            items=[Item(name="Plano", value=5990, amount=1)],
            payment=_card_payment(),
        ),
    )

    assert response.data.subscription_id == 25328
    assert response.data.payment == "credit_card"
    assert response.data.barcode is None


@pytest.mark.asyncio
async def test_create_subscription_two_step_returns_pending():
    transport = _make_handler(
        (
            "/plan/2758/subscription",
            httpx.Response(
                200,
                json={
                    "data": {
                        "subscription_id": 25330,
                        "status": "new",
                        "custom_id": None,
                        "charges": [
                            {"charge_id": 511844, "status": "new", "total": 5990, "parcel": 1}
                        ],
                        "created_at": "2026-01-01 00:00:00",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.create_subscription(
        plan_id=2758,
        request=CreateSubscriptionRequest(items=[Item(name="Plano", value=5990, amount=1)]),
    )

    assert response.data.subscription_id == 25330
    assert response.data.status == "new"
    assert response.data.charges[0].charge_id == 511844


@pytest.mark.asyncio
async def test_pay_subscription_returns_active():
    transport = _make_handler(
        (
            "/subscription/25330/pay",
            httpx.Response(
                200,
                json={
                    "data": {
                        "subscription_id": 25330,
                        "status": "active",
                        "plan": {"id": 2758, "interval": 1, "repeats": None},
                        "charge": {"id": 511844, "status": "waiting", "parcel": 1, "total": 5990},
                        "first_execution": "01/02/2026",
                        "total": 5990,
                        "payment": "credit_card",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.pay_subscription(
        subscription_id=25330,
        request=SubscriptionPayRequest(payment=_card_payment()),
    )

    assert response.data.subscription_id == 25330
    assert response.data.status == "active"
    assert response.data.charge.id == 511844


@pytest.mark.asyncio
async def test_retry_charge_parses_response():
    transport = _make_handler(
        (
            "/charge/511844/retry",
            httpx.Response(
                200,
                json={
                    "data": {
                        "installments": 1,
                        "installment_value": 5990,
                        "charge_id": 511844,
                        "status": "waiting",
                        "total": 5990,
                        "payment": "credit_card",
                    }
                },
            ),
        )
    )
    efi = EfiClient("id", "secret", sandbox=True, transport=transport)

    response = await efi.retry_charge(
        charge_id=511844,
        request=RetryChargeRequest(
            payment=RetryChargePayment(
                credit_card=RetryChargeCreditCard(
                    customer=Customer.model_validate(_customer()),
                    billing_address=Address.model_validate(_address()),
                    payment_token="tok_new",
                    update_card=True,
                )
            )
        ),
    )

    assert response.data.charge_id == 511844
    assert response.data.status == "waiting"
    assert response.data.installments == 1


@pytest.mark.asyncio
async def test_cancel_subscription_sends_put_to_cancel_path():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/authorize"):
            return _AUTH_RESPONSE
        assert request.url.path.endswith("/subscription/25329/cancel")
        assert request.method == "PUT"
        return httpx.Response(200, json={"code": 200})

    efi = EfiClient("id", "secret", sandbox=True, transport=httpx.MockTransport(handler))
    await efi.cancel_subscription(25329)

    assert any("/subscription/25329/cancel" in c.url.path for c in calls)


@pytest.mark.asyncio
async def test_cancel_plan_sends_delete():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/authorize"):
            return _AUTH_RESPONSE
        assert request.url.path.endswith("/plan/2758")
        assert request.method == "DELETE"
        return httpx.Response(200, json={"code": 200})

    efi = EfiClient("id", "secret", sandbox=True, transport=httpx.MockTransport(handler))
    await efi.cancel_plan(2758)

    assert any("/plan/2758" in c.url.path and c.method == "DELETE" for c in calls)


@pytest.mark.asyncio
async def test_update_subscription_metadata_sends_put():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/authorize"):
            return _AUTH_RESPONSE
        assert "/subscription/25329/metadata" in request.url.path
        assert request.method == "PUT"
        return httpx.Response(200, json={"code": 200})

    efi = EfiClient("id", "secret", sandbox=True, transport=httpx.MockTransport(handler))
    await efi.update_subscription_metadata(
        25329, SubscriptionMetadataRequest(notification_url="https://example.com/webhook")
    )

    assert any("/subscription/25329/metadata" in c.url.path for c in calls)
