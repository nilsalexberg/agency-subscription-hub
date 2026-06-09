from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .split_config import SplitConfigRecipient


class Recipient(Base, TimestampMixin):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str] = mapped_column(String(20), nullable=False)
    efi_recipient_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    split_config_recipients: Mapped[list[SplitConfigRecipient]] = relationship(
        back_populates="recipient"
    )
