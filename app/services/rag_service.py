"""RAG service — pgvector semantic search for product knowledge base."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_embedding import ProductEmbedding
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RAGService:
    """Semantic search against the pgvector product embeddings table."""

    def __init__(self, db: AsyncSession, llm_service: LLMService):
        self.db = db
        self.llm = llm_service

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Embed the query and find the most similar product chunks."""
        # Generate query embedding
        query_embedding = await self.llm.embed_text(query)

        # pgvector cosine distance search
        stmt = (
            select(
                ProductEmbedding.shopify_product_id,
                ProductEmbedding.title,
                ProductEmbedding.content,
                ProductEmbedding.price_range,
                ProductEmbedding.metadata_,
                ProductEmbedding.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .order_by(ProductEmbedding.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "shopify_product_id": row.shopify_product_id,
                "title": row.title,
                "content": row.content,
                "price_range": row.price_range,
                "metadata": row.metadata_,
                "similarity": 1.0 - row.distance,
            }
            for row in rows
        ]

    def format_context(self, results: list[dict[str, Any]]) -> str:
        """Format RAG results into a context string for the system prompt."""
        if not results:
            return ""

        chunks = []
        for r in results:
            chunk = f"Product: {r['title']}"
            if r.get("price_range"):
                chunk += f" | Price: {r['price_range']}"
            chunk += f"\n{r['content']}"
            if r.get("metadata"):
                meta = r["metadata"]
                if meta.get("tags"):
                    chunk += f"\nTags: {', '.join(meta['tags'])}"
                if meta.get("vendor"):
                    chunk += f"\nVendor: {meta['vendor']}"
            chunks.append(chunk)

        return "\n\n---\n\n".join(chunks)
