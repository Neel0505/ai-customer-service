"""Shopify product ingestion pipeline — fetches products, embeds, stores in pgvector."""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_embedding import ProductEmbedding
from app.services.llm_service import LLMService
from app.services.shopify_service import ShopifyService

logger = logging.getLogger(__name__)


class ShopifyIngestionService:
    """Ingests Shopify products into pgvector for RAG retrieval."""

    def __init__(self, db: AsyncSession, llm: LLMService | None = None, shopify: ShopifyService | None = None):
        self.db = db
        self.llm = llm or LLMService()
        self.shopify = shopify or ShopifyService()

    async def ingest_all_products(self) -> int:
        """Fetch all products from Shopify and embed into pgvector.

        Returns the number of products ingested.
        """
        products = await self.shopify.list_all_products()
        logger.info("Fetched %d products from Shopify for ingestion", len(products))

        count = 0
        # Process in batches of 20 for embedding efficiency
        batch_size = 20
        for i in range(0, len(products), batch_size):
            batch = products[i : i + batch_size]
            contents = [self._build_content(p) for p in batch]
            embeddings = await self.llm.embed_batch(contents)

            for product, content, embedding in zip(batch, contents, embeddings):
                await self._upsert_embedding(product, content, embedding)
                count += 1

            logger.info("Ingested batch %d/%d (%d products)", i // batch_size + 1, (len(products) + batch_size - 1) // batch_size, count)

        await self.db.commit()
        logger.info("Ingestion complete: %d products embedded", count)
        return count

    async def upsert_product(self, product_data: dict[str, Any]) -> None:
        """Upsert a single product (called by Shopify webhook)."""
        content = self._build_content(product_data)
        embedding = await self.llm.embed_text(content)
        await self._upsert_embedding(product_data, content, embedding)
        await self.db.commit()

    async def delete_product(self, shopify_product_id: str) -> None:
        """Remove a product embedding (called on product/delete webhook)."""
        stmt = delete(ProductEmbedding).where(
            ProductEmbedding.shopify_product_id == shopify_product_id
        )
        await self.db.execute(stmt)
        await self.db.commit()
        logger.info("Deleted embedding for product %s", shopify_product_id)

    def _build_content(self, product: dict[str, Any]) -> str:
        """Build embeddable text content from a Shopify product."""
        parts = [product.get("title", "")]

        # Strip HTML from body
        body_html = product.get("body_html", "")
        if body_html:
            text = BeautifulSoup(body_html, "html.parser").get_text(separator=" ").strip()
            parts.append(text)

        # Add variant info
        variants = product.get("variants", [])
        if variants:
            variant_lines = []
            for v in variants:
                variant_lines.append(
                    f"Variant: {v.get('title', 'Default')} — "
                    f"Price: {v.get('price', 'N/A')} — "
                    f"SKU: {v.get('sku', 'N/A')}"
                )
            parts.append("\n".join(variant_lines))

        # Add tags
        tags = product.get("tags", "")
        if tags:
            parts.append(f"Tags: {tags}")

        # Add vendor
        vendor = product.get("vendor", "")
        if vendor:
            parts.append(f"Vendor: {vendor}")

        # Add product type
        product_type = product.get("product_type", "")
        if product_type:
            parts.append(f"Category: {product_type}")

        return "\n\n".join(parts)

    async def _upsert_embedding(
        self, product: dict[str, Any], content: str, embedding: list[float]
    ) -> None:
        """Insert or update a product embedding."""
        shopify_id = str(product.get("id", ""))

        stmt = select(ProductEmbedding).where(
            ProductEmbedding.shopify_product_id == shopify_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        variants = product.get("variants", [])
        prices = [float(v.get("price", 0)) for v in variants if v.get("price")]
        price_range = ""
        if prices:
            min_p, max_p = min(prices), max(prices)
            price_range = f"{min_p}" if min_p == max_p else f"{min_p} – {max_p}"

        metadata = {
            "vendor": product.get("vendor"),
            "product_type": product.get("product_type"),
            "tags": product.get("tags", "").split(", ") if product.get("tags") else [],
            "handle": product.get("handle"),
        }

        if existing:
            existing.title = product.get("title", "")
            existing.content = content
            existing.price_range = price_range
            existing.metadata_ = metadata
            existing.embedding = embedding
        else:
            new_emb = ProductEmbedding(
                shopify_product_id=shopify_id,
                title=product.get("title", ""),
                content=content,
                price_range=price_range,
                metadata_=metadata,
                embedding=embedding,
            )
            self.db.add(new_emb)
