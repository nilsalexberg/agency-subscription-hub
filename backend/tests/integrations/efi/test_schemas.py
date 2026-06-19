import pytest
from pydantic import ValidationError

from app.integrations.efi.schemas import (
    Address,
    BankingBilletCustomer,
    BankingBilletPayment,
    BilletConfigurations,
    ChargeRequest,
    CreateSubscriptionOneStepRequest,
    CreditCardPayment,
    Customer,
    Item,
    Payment,
    PlanRequest,
    SubscriptionBilletCustomer,
    SubscriptionBilletPayment,
    SubscriptionCreditCardPayment,
    SubscriptionPayment,
)


def _address(**overrides) -> dict:
    return {
        "street": "Avenida Juscelino Kubitschek",
        "number": "909",
        "neighborhood": "Bauxita",
        "zipcode": "35400-000",
        "city": "Ouro Preto",
        "state": "MG",
        **overrides,
    }


def _customer(**overrides) -> dict:
    return {
        "name": "Gorbadoc Oldbuck",
        "cpf": "942.715.646-56",
        "email": "client@server.com.br",
        "birth": "1990-01-01",
        "phone_number": "(11) 99999-9999",
        **overrides,
    }


def test_address_strips_non_digits_from_zipcode():
    address = Address.model_validate(_address())
    assert address.zipcode == "35400000"


def test_customer_strips_non_digits_from_cpf_and_phone():
    customer = Customer.model_validate(_customer())
    assert customer.cpf == "94271564656"
    assert customer.phone_number == "11999999999"


def test_banking_billet_customer_requires_nested_address():
    customer = BankingBilletCustomer.model_validate({**_customer(), "address": _address()})
    assert customer.address.city == "Ouro Preto"


def test_credit_card_payment_keeps_billing_address_as_sibling():
    payment = CreditCardPayment.model_validate(
        {
            "customer": _customer(),
            "payment_token": "tok_abc",
            "billing_address": _address(),
        }
    )
    assert payment.billing_address.city == "Ouro Preto"
    assert not hasattr(payment.customer, "address")


def test_payment_rejects_neither_method_set():
    with pytest.raises(ValidationError):
        Payment()


def test_payment_rejects_both_methods_set():
    with pytest.raises(ValidationError):
        Payment(
            credit_card=CreditCardPayment(
                customer=Customer.model_validate(_customer()),
                payment_token="tok_abc",
                billing_address=Address.model_validate(_address()),
            ),
            banking_billet=BankingBilletPayment(
                customer=BankingBilletCustomer.model_validate(
                    {**_customer(), "address": _address()}
                ),
                expire_at="2026-06-30",
            ),
        )


def test_charge_request_serializes_cents_as_int():
    request = ChargeRequest(
        items=[Item(name="Plano", value=1990, amount=1)],
        payment=Payment(
            banking_billet=BankingBilletPayment(
                customer=BankingBilletCustomer.model_validate(
                    {**_customer(), "address": _address()}
                ),
                expire_at="2026-06-30",
            )
        ),
    )
    body = request.model_dump(mode="json", exclude_none=True)
    assert body["items"][0]["value"] == 1990
    assert "credit_card" not in body["payment"]


# --- Subscription schema tests ---


def _sub_billet_customer(**overrides) -> dict:
    return {
        "name": "Gorbadoc Oldbuck",
        "cpf": "942.715.646-56",
        "email": "client@server.com.br",
        "phone_number": "(11) 99999-9999",
        "address": _address(),
        **overrides,
    }


def test_subscription_billet_customer_normalizes_digits():
    customer = SubscriptionBilletCustomer.model_validate(_sub_billet_customer())
    assert customer.cpf == "94271564656"
    assert customer.phone_number == "11999999999"


def test_subscription_billet_customer_birth_is_optional():
    customer = SubscriptionBilletCustomer.model_validate(_sub_billet_customer())
    assert customer.birth is None


def test_subscription_payment_rejects_neither_method():
    with pytest.raises(ValidationError):
        SubscriptionPayment()


def test_subscription_payment_rejects_both_methods():
    billet = SubscriptionBilletPayment(
        customer=SubscriptionBilletCustomer.model_validate(_sub_billet_customer()),
        expire_at="2026-06-30",
    )
    card = SubscriptionCreditCardPayment(
        customer=Customer.model_validate(_customer()),
        payment_token="tok_abc",
        billing_address=Address.model_validate(_address()),
    )
    with pytest.raises(ValidationError):
        SubscriptionPayment(banking_billet=billet, credit_card=card)


def test_plan_request_omits_none_repeats_on_serialization():
    plan = PlanRequest(name="Monthly Plan", interval=1)
    body = plan.model_dump(mode="json", exclude_none=True)
    assert body == {"name": "Monthly Plan", "interval": 1}
    assert "repeats" not in body


def test_plan_request_includes_repeats_when_set():
    plan = PlanRequest(name="Annual Plan", interval=12, repeats=1)
    body = plan.model_dump(mode="json", exclude_none=True)
    assert body["repeats"] == 1


def test_subscription_billet_payment_includes_configurations():
    payment = SubscriptionBilletPayment(
        customer=SubscriptionBilletCustomer.model_validate(_sub_billet_customer()),
        expire_at="2026-06-30",
        configurations=BilletConfigurations(fine=200, interest=33),
    )
    body = payment.model_dump(mode="json", exclude_none=True)
    assert body["configurations"] == {"fine": 200, "interest": 33}


def test_create_subscription_one_step_serializes_without_none():
    request = CreateSubscriptionOneStepRequest(
        items=[Item(name="Plano", value=5990, amount=1)],
        payment=SubscriptionPayment(
            banking_billet=SubscriptionBilletPayment(
                customer=SubscriptionBilletCustomer.model_validate(_sub_billet_customer()),
                expire_at="2026-12-30",
            )
        ),
    )
    body = request.model_dump(mode="json", exclude_none=True)
    assert body["items"][0]["value"] == 5990
    assert "credit_card" not in body["payment"]
    assert "trial_days" not in body["payment"].get("banking_billet", {})
