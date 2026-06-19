"""Request/response shapes for the Efí Cobranças one-step charge API.

Mirrors the JSON documented in docs/efi.md. Two payment-method-specific
customer models exist on purpose: banking_billet nests `address` inside
`customer`, while credit_card keeps `billing_address` as a sibling field.
Modeling them separately makes that gotcha a type error instead of a
runtime 422 from Efí.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator, model_validator


def _strip_non_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


class Address(BaseModel):
    street: str
    number: str
    neighborhood: str
    zipcode: str
    city: str
    state: str
    complement: str | None = None

    @field_validator("zipcode")
    @classmethod
    def normalize_zipcode(cls, value: str) -> str:
        return _strip_non_digits(value)


class Customer(BaseModel):
    name: str
    cpf: str
    email: str
    birth: str
    phone_number: str

    @field_validator("cpf", "phone_number")
    @classmethod
    def normalize_digits(cls, value: str) -> str:
        return _strip_non_digits(value)


class BankingBilletCustomer(Customer):
    address: Address


class Repasse(BaseModel):
    """Marketplace split recipient. `percentage` basis is x100 (10.00% -> 1000)."""

    payee_code: str
    percentage: int


class Marketplace(BaseModel):
    repasses: list[Repasse]


class Item(BaseModel):
    """`value` is an integer in cents (R$19.90 -> 1990)."""

    name: str
    value: int
    amount: int
    marketplace: Marketplace | None = None


class Shipping(BaseModel):
    name: str
    value: int


class ChargeMetadata(BaseModel):
    notification_url: str | None = None
    custom_id: str | None = None


class CreditCardPayment(BaseModel):
    customer: Customer
    payment_token: str
    billing_address: Address
    installments: int = 1


class BankingBilletPayment(BaseModel):
    customer: BankingBilletCustomer
    expire_at: str  # YYYY-MM-DD
    message: str | None = None


class Payment(BaseModel):
    credit_card: CreditCardPayment | None = None
    banking_billet: BankingBilletPayment | None = None

    @model_validator(mode="after")
    def exactly_one_payment_method(self) -> Payment:
        if (self.credit_card is None) == (self.banking_billet is None):
            raise ValueError("exactly one of credit_card or banking_billet must be set")
        return self


class ChargeRequest(BaseModel):
    payment: Payment
    items: list[Item]
    shippings: list[Shipping] | None = None
    metadata: ChargeMetadata | None = None


class RefusalInfo(BaseModel):
    reason: str | None = None

    model_config = {"extra": "allow"}


class PixInfo(BaseModel):
    qrcode: str | None = None
    qrcode_image: str | None = None


class PdfInfo(BaseModel):
    charge: str | None = None


class ChargeData(BaseModel):
    charge_id: int
    status: str
    refusal: RefusalInfo | None = None
    barcode: str | None = None
    pix: PixInfo | None = None
    pdf: PdfInfo | None = None

    # Efí does not publish a full response schema; unmodeled fields pass through.
    model_config = {"extra": "allow"}


class ChargeResponse(BaseModel):
    data: ChargeData


class InstallmentOption(BaseModel):
    """`interest_percentage` basis is x100 (250 -> 2.50%)."""

    installment: int
    currency: str
    has_interest: bool
    interest_percentage: int


class NotificationIdentifiers(BaseModel):
    charge_id: int


class NotificationStatus(BaseModel):
    current: str


class NotificationEvent(BaseModel):
    identifiers: NotificationIdentifiers
    status: NotificationStatus
