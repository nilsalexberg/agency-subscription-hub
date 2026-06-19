import pytest
from pydantic import ValidationError

from app.integrations.efi.schemas import (
    Address,
    BankingBilletCustomer,
    BankingBilletPayment,
    ChargeRequest,
    CreditCardPayment,
    Customer,
    Item,
    Payment,
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
