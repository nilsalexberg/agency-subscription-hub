from __future__ import annotations

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .client import Client
    from .split_config import SplitConfig


class BillingCycle(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    efi_plan_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    split_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("split_configs.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    split_config: Mapped[SplitConfig | None] = relationship(back_populates="plans")
    clients: Mapped[list[Client]] = relationship(back_populates="plan")
