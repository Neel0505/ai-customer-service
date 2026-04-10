"""Shopify tools — LLM function definitions for Shopify API operations."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.shopify_service import ShopifyService
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def register_shopify_tools(registry: ToolRegistry, shopify: ShopifyService):
    """Register all Shopify tools with the tool registry."""

    # ── shopify_get_order ──────────────────────────────────────

    async def shopify_get_order(order_id: str) -> str:
        order = await shopify.get_order(order_id)
        if not order:
            return f"No order found with ID/number '{order_id}'."
        return json.dumps({
            "order_number": order.get("name"),
            "status": order.get("fulfillment_status") or "unfulfilled",
            "financial_status": order.get("financial_status"),
            "total_price": order.get("total_price"),
            "currency": order.get("currency"),
            "created_at": order.get("created_at"),
            "line_items": [
                {"title": li["title"], "quantity": li["quantity"], "price": li["price"]}
                for li in order.get("line_items", [])
            ],
        }, indent=2)

    registry.register(
        name="shopify_get_order",
        description="Look up an order by order ID or order number (e.g., '#1042' or '1042'). Returns order status, items, and financial details.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order number (e.g., '1042') or order ID"}
            },
            "required": ["order_id"],
        },
        handler=shopify_get_order,
    )

    # ── shopify_search_orders_by_customer ──────────────────────

    async def shopify_search_orders_by_customer(email: str | None = None, phone: str | None = None) -> str:
        orders = await shopify.search_orders_by_customer(email=email, phone=phone)
        if not orders:
            return "No orders found for this customer."
        return json.dumps([
            {
                "order_number": o.get("name"),
                "status": o.get("fulfillment_status") or "unfulfilled",
                "total": o.get("total_price"),
                "date": o.get("created_at"),
            }
            for o in orders[:5]
        ], indent=2)

    registry.register(
        name="shopify_search_orders_by_customer",
        description="Find all orders for a customer by their email or phone number.",
        parameters={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email address"},
                "phone": {"type": "string", "description": "Customer phone number"},
            },
        },
        handler=shopify_search_orders_by_customer,
    )

    # ── shopify_get_fulfillment ────────────────────────────────

    async def shopify_get_fulfillment(order_id: str) -> str:
        order = await shopify.get_order(order_id)
        if not order:
            return f"Order '{order_id}' not found."
        fulfillments = await shopify.get_fulfillment(str(order.get("id", "")))
        if not fulfillments:
            return f"Order {order.get('name')} has not been shipped yet."
        tracking_url_tpl = shopify.tracking_url_template
        return json.dumps([
            {
                "status": f.get("status"),
                "tracking_number": f.get("tracking_number"),
                "tracking_url": f.get("tracking_url") or (
                    tracking_url_tpl.format(tracking_number=f.get("tracking_number", ""))
                    if tracking_url_tpl and f.get("tracking_number") else None
                ),
                "carrier": f.get("tracking_company"),
                "created_at": f.get("created_at"),
            }
            for f in fulfillments
        ], indent=2)

    registry.register(
        name="shopify_get_fulfillment",
        description="Get shipping/tracking information for an order.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order number or ID"}
            },
            "required": ["order_id"],
        },
        handler=shopify_get_fulfillment,
    )

    # ── shopify_search_products ────────────────────────────────

    async def shopify_search_products(query: str, max_results: int = 5) -> str:
        products = await shopify.search_products(query, limit=max_results)
        if not products:
            return f"No products found matching '{query}'."
        return json.dumps([
            {
                "id": p["id"],
                "title": p["title"],
                "description": (p.get("body_html") or "")[:200],
                "price_range": _get_price_range(p),
                "variants": [
                    {"title": v["title"], "price": v["price"], "available": v.get("inventory_quantity", 0) > 0}
                    for v in p.get("variants", [])[:5]
                ],
                "tags": p.get("tags", "").split(", ") if p.get("tags") else [],
            }
            for p in products
        ], indent=2)

    registry.register(
        name="shopify_search_products",
        description="Search the product catalog by name/keyword. Returns product details with pricing and availability.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Product search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
        handler=shopify_search_products,
    )

    # ── shopify_check_inventory ────────────────────────────────

    async def shopify_check_inventory(product_id: str) -> str:
        product = await shopify.get_product(product_id)
        if not product:
            return f"Product {product_id} not found."
        variants = product.get("variants", [])
        return json.dumps([
            {
                "variant": v.get("title"),
                "sku": v.get("sku"),
                "in_stock": (v.get("inventory_quantity", 0) > 0),
                "quantity": v.get("inventory_quantity", 0),
                "price": v.get("price"),
            }
            for v in variants
        ], indent=2)

    registry.register(
        name="shopify_check_inventory",
        description="Check stock/inventory levels for a product's variants.",
        parameters={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Shopify product ID"}
            },
            "required": ["product_id"],
        },
        handler=shopify_check_inventory,
    )

    # ── shopify_get_customer ───────────────────────────────────

    async def shopify_get_customer(email: str | None = None, phone: str | None = None) -> str:
        customer = await shopify.get_customer(email=email, phone=phone)
        if not customer:
            return "Customer not found."
        return json.dumps({
            "id": customer.get("id"),
            "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            "email": customer.get("email"),
            "phone": customer.get("phone"),
            "orders_count": customer.get("orders_count"),
            "total_spent": customer.get("total_spent"),
            "tags": customer.get("tags"),
        }, indent=2)

    registry.register(
        name="shopify_get_customer",
        description="Look up a Shopify customer by email or phone number.",
        parameters={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Customer email"},
                "phone": {"type": "string", "description": "Customer phone"},
            },
        },
        handler=shopify_get_customer,
    )

    # ── shopify_create_draft_order ─────────────────────────────

    async def shopify_create_draft_order(
        variant_id: str, quantity: int = 1, customer_email: str | None = None
    ) -> str:
        line_items = [{"variant_id": int(variant_id), "quantity": quantity}]
        draft = await shopify.create_draft_order(line_items, customer_email)
        return json.dumps({
            "draft_order_id": draft.get("id"),
            "invoice_url": draft.get("invoice_url"),
            "total": draft.get("total_price"),
            "status": draft.get("status"),
        }, indent=2)

    registry.register(
        name="shopify_create_draft_order",
        description="Create a draft order (quote) for a customer with a specific product variant.",
        parameters={
            "type": "object",
            "properties": {
                "variant_id": {"type": "string", "description": "Shopify variant ID"},
                "quantity": {"type": "integer", "description": "Quantity (default 1)"},
                "customer_email": {"type": "string", "description": "Customer email for the draft order"},
            },
            "required": ["variant_id"],
        },
        handler=shopify_create_draft_order,
    )

    # ── shopify_initiate_return ────────────────────────────────

    async def shopify_initiate_return(order_id: str) -> str:
        result = await shopify.initiate_return(order_id)
        if result.get("status") == "manual_required":
            return "Return requires manual processing. Escalating to team."
        return json.dumps({
            "return_id": result.get("id"),
            "status": result.get("status"),
        }, indent=2)

    registry.register(
        name="shopify_initiate_return",
        description="Initiate a product return for an order. Use after confirming the order is within the return window.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order number or ID to return"}
            },
            "required": ["order_id"],
        },
        handler=shopify_initiate_return,
    )

    # ── shopify_get_refund_status ──────────────────────────────

    async def shopify_get_refund_status(order_id: str) -> str:
        refunds = await shopify.get_refund_status(order_id)
        if not refunds:
            return "No refunds found for this order."
        return json.dumps([
            {
                "amount": r.get("transactions", [{}])[0].get("amount") if r.get("transactions") else None,
                "status": r.get("status"),
                "created_at": r.get("created_at"),
            }
            for r in refunds
        ], indent=2)

    registry.register(
        name="shopify_get_refund_status",
        description="Check refund processing status for an order.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order number or ID"}
            },
            "required": ["order_id"],
        },
        handler=shopify_get_refund_status,
    )

    # ── shopify_get_collections ────────────────────────────────

    async def shopify_get_collections() -> str:
        collections = await shopify.get_collections()
        return json.dumps([
            {"id": c["id"], "title": c["title"]}
            for c in collections[:20]
        ], indent=2)

    registry.register(
        name="shopify_get_collections",
        description="List all product collections/categories in the store.",
        parameters={"type": "object", "properties": {}},
        handler=shopify_get_collections,
    )

    # ── shopify_apply_discount ─────────────────────────────────

    async def shopify_apply_discount(code: str) -> str:
        result = await shopify.validate_discount_code(code)
        if not result:
            return f"Discount code '{code}' is not valid or has expired."
        return json.dumps(result, indent=2)

    registry.register(
        name="shopify_apply_discount",
        description="Validate a discount code and return its value/type.",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Discount code to validate"}
            },
            "required": ["code"],
        },
        handler=shopify_apply_discount,
    )


def _get_price_range(product: dict) -> str:
    """Extract price range from product variants."""
    variants = product.get("variants", [])
    if not variants:
        return "N/A"
    prices = [float(v.get("price", 0)) for v in variants if v.get("price")]
    if not prices:
        return "N/A"
    min_p, max_p = min(prices), max(prices)
    if min_p == max_p:
        return f"{min_p}"
    return f"{min_p} – {max_p}"
