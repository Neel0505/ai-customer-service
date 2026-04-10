"""Identity resolution — maps channel users to Shopify customers and Contact records."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.services.session_service import SessionService
from app.services.shopify_service import ShopifyService

logger = logging.getLogger(__name__)


class IdentityService:
    """Resolves customer identity from channel-specific identifiers."""

    def __init__(
        self, db: AsyncSession, session_service: SessionService, shopify: ShopifyService
    ):
        self.db = db
        self.session_service = session_service
        self.shopify = shopify

    async def resolve(
        self, channel: str, user_id: str, email: str | None = None
    ) -> dict[str, Any]:
        """Resolve a channel user to a Contact + Shopify customer.

        Lookup chain:
        1. Redis identity cache
        2. DB Contact table (by phone/email/PSID)
        3. Shopify customer search
        4. Create new Contact if nothing found
        """
        # 1. Check Redis cache
        cached = await self.session_service.get_identity(channel, user_id)
        if cached:
            return cached

        # 2. Look up in Contact table
        contact = await self._find_contact(channel, user_id, email)
        shopify_customer = None

        # 3. Try Shopify lookup
        lookup_value = email or (user_id if channel == "whatsapp" else None)
        if lookup_value:
            try:
                if "@" in (lookup_value or ""):
                    shopify_customer = await self.shopify.get_customer(email=lookup_value)
                else:
                    shopify_customer = await self.shopify.get_customer(phone=lookup_value)
            except Exception as e:
                logger.warning("Shopify customer lookup failed: %s", e)

        # 4. Create or update Contact
        if not contact:
            contact = Contact(
                source_channel=channel,
                phone=user_id if channel == "whatsapp" else None,
                email=email or (user_id if channel == "email" else None),
                instagram_user_id=user_id if channel == "instagram" else None,
            )
            if shopify_customer:
                contact.shopify_customer_id = str(shopify_customer.get("id", ""))
                contact.name = (
                    f"{shopify_customer.get('first_name', '')} "
                    f"{shopify_customer.get('last_name', '')}"
                ).strip()
                contact.email = contact.email or shopify_customer.get("email")
                contact.phone = contact.phone or shopify_customer.get("phone")

            self.db.add(contact)
            await self.db.flush()

        elif shopify_customer and not contact.shopify_customer_id:
            contact.shopify_customer_id = str(shopify_customer.get("id", ""))
            contact.name = contact.name or (
                f"{shopify_customer.get('first_name', '')} "
                f"{shopify_customer.get('last_name', '')}"
            ).strip()
            await self.db.flush()

        # Build identity dict
        identity = {
            "contact_id": str(contact.id),
            "shopify_customer_id": contact.shopify_customer_id,
            "name": contact.name,
            "email": contact.email,
            "phone": contact.phone,
        }

        # Cache in Redis
        await self.session_service.set_identity(channel, user_id, identity)

        return identity

    async def _find_contact(
        self, channel: str, user_id: str, email: str | None = None
    ) -> Contact | None:
        """Find an existing Contact record by channel-specific identifier."""
        conditions = []

        if channel == "whatsapp":
            conditions.append(Contact.phone == user_id)
        elif channel == "email" or email:
            lookup_email = email or user_id
            conditions.append(Contact.email == lookup_email)
        elif channel == "instagram":
            conditions.append(Contact.instagram_user_id == user_id)

        if not conditions:
            return None

        stmt = select(Contact).where(or_(*conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
