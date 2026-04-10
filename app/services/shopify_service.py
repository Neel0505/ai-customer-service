"""Shopify Admin REST API service — all Shopify interactions."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.utils.error_handler import ShopifyError, retry_async

logger = logging.getLogger(__name__)


class ShopifyService:
    """Wraps the Shopify Admin REST API for product, order, customer, and return operations."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.shopify_base_url
        self.headers = {
            "X-Shopify-Access-Token": settings.shopify_admin_api_token,
            "Content-Type": "application/json",
        }
        self.currency = settings.shopify_currency
        self.location_id = settings.shopify_location_id
        self.return_policy_url = settings.shopify_return_policy_url
        self.tracking_url_template = settings.shopify_tracking_url_template
        self.return_window_days = settings.shopify_return_window_days

    async def _request(
        self, method: str, endpoint: str, params: dict | None = None, json: dict | None = None
    ) -> dict[str, Any]:
        """Make an authenticated Shopify API request with rate-limit retry."""

        async def _do_request() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    method,
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    params=params,
                    json=json,
                )
                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", "2.0"))
                    raise ShopifyError(f"Rate limited, retry after {retry_after}s")
                if resp.status_code >= 400:
                    raise ShopifyError(
                        f"Shopify API error {resp.status_code}: {resp.text}",
                        should_escalate=(resp.status_code >= 500),
                    )
                return resp.json()

        return await retry_async(_do_request, max_retries=3, backoff_base=1.5)

    # ── Orders ─────────────────────────────────────────────────

    async def get_order(self, order_id: str) -> dict[str, Any]:
        """Get order by ID or order number (e.g., '#1042' or '1042')."""
        order_id_clean = order_id.strip().lstrip("#")

        # Try by order number first
        result = await self._request(
            "GET", "orders.json", params={"name": order_id_clean, "status": "any"}
        )
        orders = result.get("orders", [])
        if orders:
            return orders[0]

        # Try by order ID
        try:
            result = await self._request("GET", f"orders/{order_id_clean}.json")
            return result.get("order", {})
        except ShopifyError:
            return {}

    async def search_orders_by_customer(self, email: str | None = None, phone: str | None = None) -> list[dict]:
        """Find all orders for a customer by email or phone."""
        params: dict[str, Any] = {"status": "any", "limit": 10}
        if email:
            params["email"] = email
        elif phone:
            params["phone"] = phone
        else:
            return []

        result = await self._request("GET", "orders.json", params=params)
        return result.get("orders", [])

    async def get_fulfillment(self, order_id: str) -> list[dict]:
        """Get fulfillment/tracking info for an order."""
        result = await self._request("GET", f"orders/{order_id}/fulfillments.json")
        return result.get("fulfillments", [])

    # ── Products ───────────────────────────────────────────────

    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Get full product details."""
        result = await self._request("GET", f"products/{product_id}.json")
        return result.get("product", {})

    async def search_products(self, query: str, limit: int = 10) -> list[dict]:
        """Search products by title."""
        result = await self._request(
            "GET", "products.json", params={"title": query, "limit": limit}
        )
        return result.get("products", [])

    async def check_inventory(self, inventory_item_ids: list[str]) -> list[dict]:
        """Check stock levels for inventory items."""
        ids_str = ",".join(inventory_item_ids)
        params: dict[str, Any] = {"inventory_item_ids": ids_str}
        if self.location_id:
            params["location_ids"] = self.location_id
        result = await self._request("GET", "inventory_levels.json", params=params)
        return result.get("inventory_levels", [])

    async def list_all_products(self, limit: int = 250) -> list[dict]:
        """Paginate through all products for ingestion."""
        all_products: list[dict] = []
        params: dict[str, Any] = {"limit": limit}

        while True:
            result = await self._request("GET", "products.json", params=params)
            products = result.get("products", [])
            if not products:
                break
            all_products.extend(products)

            # Shopify pagination via Link header (simplified: use since_id)
            last_id = products[-1]["id"]
            params["since_id"] = last_id

        logger.info("Fetched %d products from Shopify", len(all_products))
        return all_products

    # ── Customers ──────────────────────────────────────────────

    async def get_customer(
        self, email: str | None = None, phone: str | None = None
    ) -> dict[str, Any] | None:
        """Search for a Shopify customer by email or phone."""
        query = email or phone
        if not query:
            return None
        result = await self._request(
            "GET", "customers/search.json", params={"query": query}
        )
        customers = result.get("customers", [])
        return customers[0] if customers else None

    # ── Draft Orders ───────────────────────────────────────────

    async def create_draft_order(
        self, line_items: list[dict], customer_email: str | None = None
    ) -> dict[str, Any]:
        """Create a draft order (quote)."""
        payload: dict[str, Any] = {"draft_order": {"line_items": line_items}}
        if customer_email:
            payload["draft_order"]["customer"] = {"email": customer_email}
        result = await self._request("POST", "draft_orders.json", json=payload)
        return result.get("draft_order", {})

    # ── Discounts ──────────────────────────────────────────────

    async def get_price_rules(self) -> list[dict]:
        """Get all price rules (discount codes)."""
        result = await self._request("GET", "price_rules.json")
        return result.get("price_rules", [])

    async def validate_discount_code(self, code: str) -> dict[str, Any] | None:
        """Check if a discount code exists and is valid."""
        price_rules = await self.get_price_rules()
        for rule in price_rules:
            rule_id = rule.get("id")
            codes_resp = await self._request(
                "GET", f"price_rules/{rule_id}/discount_codes.json"
            )
            for dc in codes_resp.get("discount_codes", []):
                if dc.get("code", "").upper() == code.upper():
                    return {
                        "code": dc["code"],
                        "value": rule.get("value"),
                        "value_type": rule.get("value_type"),
                        "title": rule.get("title"),
                    }
        return None

    # ── Returns & Refunds ──────────────────────────────────────

    async def initiate_return(self, order_id: str, line_item_ids: list[str] | None = None) -> dict[str, Any]:
        """Initiate a return request for an order."""
        # Build return line items from the order
        order = await self.get_order(order_id)
        if not order:
            raise ShopifyError(f"Order {order_id} not found")

        return_line_items = []
        for item in order.get("line_items", []):
            if line_item_ids is None or str(item["id"]) in line_item_ids:
                return_line_items.append({
                    "fulfillment_line_item_id": item["id"],
                    "quantity": item["quantity"],
                    "return_reason": "CUSTOMER_REQUEST",
                })

        payload = {"return": {"order_id": order["id"], "return_line_items": return_line_items}}

        try:
            result = await self._request("POST", "returns.json", json=payload)
            return result.get("return", {})
        except ShopifyError:
            # Return API may not be available — return the order info for manual handling
            return {"status": "manual_required", "order_id": order_id}

    async def get_refund_status(self, order_id: str) -> list[dict]:
        """Get refund info for an order."""
        result = await self._request("GET", f"orders/{order_id}/refunds.json")
        return result.get("refunds", [])

    # ── Collections ────────────────────────────────────────────

    async def get_collections(self) -> list[dict]:
        """Get all collections (categories)."""
        result = await self._request("GET", "custom_collections.json")
        custom = result.get("custom_collections", [])
        result2 = await self._request("GET", "smart_collections.json")
        smart = result2.get("smart_collections", [])
        return custom + smart

    # ── Metafields ─────────────────────────────────────────────

    async def get_product_metafields(self, product_id: str) -> list[dict]:
        """Get metafields for a product (warranty, specs, etc.)."""
        result = await self._request("GET", f"products/{product_id}/metafields.json")
        return result.get("metafields", [])
