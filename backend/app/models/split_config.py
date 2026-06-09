from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .plan import Plan
    from .recipient import Recipient


class SplitConfig(Base, TimestampMixin):
    __tablename__ = "split_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    split_config_recipients: Mapped[list[SplitConfigRecipient]] = relationship(
        back_populates="split_config", cascade="all, delete-orphan"
    )
    plans: Mapped[list[Plan]] = relationship(back_populates="split_config")


class SplitConfigRecipient(Base):
    """Association between a split config and a recipient, carrying the split percentage."""

    __tablename__ = "split_config_recipients"

    split_config_id: Mapped[int] = mapped_column(
        ForeignKey("split_configs.id"), primary_key=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("recipients.id"), primary_key=True
    )
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    split_config: Mapped[SplitConfig] = relationship(
        back_populates="split_config_recipients"
    )
    recipient: Mapped[Recipient] = relationship(
        back_populates="split_config_recipients"
    )
