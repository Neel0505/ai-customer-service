"""Contact model — customer/lead records."""

from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ChannelType(str):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    SIMULATOR = "simulator"


class Contact(UUIDMixin, TimestampMixin, Base):
    """A customer or lead — resolved from channel identity + Shopify."""

    __tablename__ = "contacts"

    shopify_customer_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32), index=True)
    instagram_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=list)
    source_channel: Mapped[str | None] = mapped_column(String(20))
    shopify_data_cache: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    conversations = relationship("Conversation", back_populates="contact", lazy="selectin")
    leads = relationship("Lead", back_populates="contact", lazy="selectin")

    __table_args__ = (
        Index("ix_contacts_email_phone", "email", "phone"),
    )
