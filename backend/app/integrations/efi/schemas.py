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


# ---------------------------------------------------------------------------
# Subscription schemas
# ---------------------------------------------------------------------------


class BilletConfigurations(BaseModel):
    """fine and interest are in basis points (200 = 2.00%)."""

    fine: int | None = None
    interest: int | None = None


class SubscriptionBilletCustomer(BaseModel):
    """Boleto subscription customer — birth not required by Efí for subscriptions."""

    name: str
    cpf: str
    email: str
    phone_number: str
    birth: str | None = None
    address: Address

    @field_validator("cpf", "phone_number")
    @classmethod
    def normalize_digits(cls, value: str) -> str:
        return _strip_non_digits(value)


class SubscriptionBilletPayment(BaseModel):
    customer: SubscriptionBilletCustomer
    expire_at: str  # YYYY-MM-DD
    configurations: BilletConfigurations | None = None
    message: str | None = None


class SubscriptionCreditCardPayment(BaseModel):
    customer: Customer
    payment_token: str
    billing_address: Address
    trial_days: int | None = None


class SubscriptionPayment(BaseModel):
    credit_card: SubscriptionCreditCardPayment | None = None
    banking_billet: SubscriptionBilletPayment | None = None

    @model_validator(mode="after")
    def exactly_one_payment_method(self) -> SubscriptionPayment:
        if (self.credit_card is None) == (self.banking_billet is None):
            raise ValueError("exactly one of credit_card or banking_billet must be set")
        return self


class PlanRequest(BaseModel):
    """interval in months (1–24). repeats=None means indefinite."""

    name: str
    interval: int
    repeats: int | None = None


class PlanData(BaseModel):
    plan_id: int
    name: str
    interval: int
    repeats: int | None = None
    created_at: str


class PlanResponse(BaseModel):
    data: PlanData


class CreateSubscriptionRequest(BaseModel):
    """Two-step step 1: bind items to a plan, get back a pending subscription."""

    items: list[Item]


class CreateSubscriptionOneStepRequest(BaseModel):
    items: list[Item]
    payment: SubscriptionPayment


class SubscriptionPayRequest(BaseModel):
    """Two-step step 2: set payment method on a pending subscription."""

    payment: SubscriptionPayment


class SubscriptionPlanRef(BaseModel):
    id: int
    interval: int
    repeats: int | None = None


class SubscriptionChargeRef(BaseModel):
    id: int
    status: str
    parcel: int
    total: int


class SubscriptionPendingCharge(BaseModel):
    charge_id: int
    status: str
    total: int
    parcel: int


class SubscriptionPendingData(BaseModel):
    """Two-step step 1 response — subscription status is 'new', awaiting payment."""

    subscription_id: int
    status: str
    custom_id: str | None = None
    charges: list[SubscriptionPendingCharge]
    created_at: str

    model_config = {"extra": "allow"}


class SubscriptionPendingResponse(BaseModel):
    data: SubscriptionPendingData


class SubscriptionActiveData(BaseModel):
    """One-step or two-step pay response — subscription status is 'active'."""

    subscription_id: int
    status: str
    plan: SubscriptionPlanRef | None = None
    charge: SubscriptionChargeRef | None = None
    first_execution: str | None = None
    total: int | None = None
    payment: str | None = None
    barcode: str | None = None
    link: str | None = None
    billet_link: str | None = None
    pdf: PdfInfo | None = None
    expire_at: str | None = None

    model_config = {"extra": "allow"}


class SubscriptionActiveResponse(BaseModel):
    data: SubscriptionActiveData


class RetryChargeCreditCard(BaseModel):
    customer: Customer
    billing_address: Address
    payment_token: str
    update_card: bool = False


class RetryChargePayment(BaseModel):
    credit_card: RetryChargeCreditCard


class RetryChargeRequest(BaseModel):
    payment: RetryChargePayment


class RetryChargeData(BaseModel):
    installments: int
    installment_value: int
    charge_id: int
    status: str
    total: int
    payment: str

    model_config = {"extra": "allow"}


class RetryChargeResponse(BaseModel):
    data: RetryChargeData


class SubscriptionMetadataRequest(BaseModel):
    notification_url: str | None = None
    custom_id: str | None = None


class UpdateSubscriptionCustomer(BaseModel):
    email: str | None = None
    phone_number: str | None = None

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _strip_non_digits(value)


class UpdateSubscriptionRequest(BaseModel):
    plan_id: int | None = None
    customer: UpdateSubscriptionCustomer | None = None
    items: list[Item] | None = None
    shippings: list[Shipping] | None = None
    payment_token: str | None = None
