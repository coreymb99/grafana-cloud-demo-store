from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field

from app.demo_control import runtime_settings, scenario_snapshot, traffic_controller
from app.telemetry import configure_telemetry
from app.ui import render_demo_console


configure_telemetry()

logger = logging.getLogger("demo-store")
tracer = trace.get_tracer("demo-store")
meter = metrics.get_meter("demo-store")

REQUEST_COUNTER = meter.create_counter(
    "storefront_requests",
    description="Requests handled by the storefront API.",
)
CHECKOUT_COUNTER = meter.create_counter(
    "storefront_checkouts",
    description="Checkout attempts.",
)
REVENUE_COUNTER = meter.create_counter(
    "storefront_revenue_usd",
    unit="USD",
    description="Successful checkout revenue in USD.",
)
FAILED_PAYMENT_COUNTER = meter.create_counter(
    "storefront_failed_payments",
    description="Failed payment authorizations.",
)
CHECKOUT_DURATION = meter.create_histogram(
    "storefront_checkout_duration",
    unit="s",
    description="End-to-end checkout duration.",
)
DEPENDENCY_DURATION = meter.create_histogram(
    "storefront_dependency_duration",
    unit="s",
    description="Dependency latency inside a checkout.",
)

app = FastAPI(title="Grafana Cloud Demo Store", version="0.1.0")
_instrumented = False


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    price: float
    inventory: int


CATALOG: dict[str, Product] = {
    "sku-100": Product("sku-100", "Cloud Hoodie", "apparel", 72.0, 40),
    "sku-101": Product("sku-101", "Tempo Mug", "lifestyle", 18.0, 85),
    "sku-102": Product("sku-102", "LGTM Stickers", "swag", 8.0, 120),
    "sku-103": Product("sku-103", "Incident Notebook", "office", 24.0, 30),
    "sku-104": Product("sku-104", "Pyroscope Beanie", "apparel", 34.0, 55),
}


class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=5)


class CheckoutRequest(BaseModel):
    user_id: str
    region: Literal["us-east", "us-west", "eu-west"] = "us-east"
    user_tier: Literal["trial", "pro", "enterprise"] = "trial"
    items: list[CartItem]
    promo_code: str | None = None


class DemoStartRequest(BaseModel):
    scenario: str = "steady-state"
    concurrency: int = Field(default=6, ge=1, le=24)
    base_url: str = "http://127.0.0.1:8000"


class DemoScenarioRequest(BaseModel):
    scenario: str


def _sleep_with_jitter(base_ms: int, jitter_ms: int) -> float:
    duration = max(0.0, (base_ms + random.randint(0, jitter_ms)) / 1000)
    time.sleep(duration)
    return duration


def _inventory_delay(product_id: str) -> float:
    spike = runtime_settings.current().inventory_spike_multiplier
    base_ms = 25 if product_id != "sku-104" else 90
    return _sleep_with_jitter(int(base_ms * spike), 35)


def _payment_delay(user_tier: str, amount: float) -> float:
    degradation = runtime_settings.current().payment_degradation
    base_ms = 80
    if amount > 100:
        base_ms += 120
    if user_tier == "enterprise":
        base_ms += 40
    return _sleep_with_jitter(int(base_ms * degradation), 140)


def _shipping_delay(region: str) -> float:
    regional_penalty = {
        "us-east": 35,
        "us-west": 60,
        "eu-west": 95,
    }[region]
    return _sleep_with_jitter(regional_penalty, 45)


def _record_request(route: str, method: str, status: str) -> None:
    REQUEST_COUNTER.add(1, {"route": route, "method": method, "status": status})


@app.get("/health")
def health() -> dict[str, str]:
    _record_request("/health", "GET", "ok")
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def demo_console() -> str:
    return render_demo_console()


@app.get("/api/catalog")
def catalog(search: str | None = None) -> dict[str, list[dict[str, str | float | int]]]:
    _sleep_with_jitter(20, 40)
    products = list(CATALOG.values())
    if search:
        products = [product for product in products if search.lower() in product.name.lower()]

    _record_request("/api/catalog", "GET", "ok")
    return {
        "products": [
            {
                "product_id": product.product_id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "inventory": product.inventory,
            }
            for product in products
        ]
    }


@app.get("/api/products/{product_id}")
def product_details(product_id: str) -> dict[str, str | float | int]:
    product = CATALOG.get(product_id)
    if not product:
        _record_request("/api/products/:product_id", "GET", "error")
        raise HTTPException(status_code=404, detail="Product not found")

    _sleep_with_jitter(25, 30)
    _record_request("/api/products/:product_id", "GET", "ok")
    return {
        "product_id": product.product_id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "inventory": product.inventory,
    }


@app.post("/api/checkout")
def checkout(request: CheckoutRequest) -> dict[str, str | float]:
    start = time.perf_counter()
    route = "/api/checkout"

    with tracer.start_as_current_span("checkout.process") as span:
        scenario = runtime_settings.current()
        span.set_attribute("checkout.region", request.region)
        span.set_attribute("checkout.user_tier", request.user_tier)
        span.set_attribute("checkout.item_count", sum(item.quantity for item in request.items))
        span.set_attribute("demo.scenario", scenario.name)

        subtotal = 0.0
        for item in request.items:
            product = CATALOG.get(item.product_id)
            if not product:
                _record_request(route, "POST", "error")
                raise HTTPException(status_code=400, detail=f"Unknown product {item.product_id}")
            subtotal += product.price * item.quantity

            with tracer.start_as_current_span("inventory.reserve") as child_span:
                dependency_seconds = _inventory_delay(item.product_id)
                child_span.set_attribute("dependency.name", "inventory")
                child_span.set_attribute("product.id", item.product_id)
                DEPENDENCY_DURATION.record(
                    dependency_seconds,
                    {"dependency": "inventory", "product_id": item.product_id},
                )

        discount = 0.15 if request.promo_code == "LAUNCH15" else 0.0
        discounted_total = round(subtotal * (1 - discount), 2)

        with tracer.start_as_current_span("pricing.calculate") as child_span:
            dependency_seconds = _sleep_with_jitter(15, 15)
            child_span.set_attribute("dependency.name", "pricing")
            child_span.set_attribute("checkout.discount_rate", discount)
            DEPENDENCY_DURATION.record(dependency_seconds, {"dependency": "pricing", "product_id": "all"})

        with tracer.start_as_current_span("shipping.quote") as child_span:
            dependency_seconds = _shipping_delay(request.region)
            child_span.set_attribute("dependency.name", "shipping")
            child_span.set_attribute("shipping.region", request.region)
            DEPENDENCY_DURATION.record(
                dependency_seconds,
                {"dependency": "shipping", "product_id": request.region},
            )

        with tracer.start_as_current_span("payment.authorize") as child_span:
            dependency_seconds = _payment_delay(request.user_tier, discounted_total)
            child_span.set_attribute("dependency.name", "payment")
            child_span.set_attribute("payment.amount", discounted_total)
            child_span.set_attribute("customer.tier", request.user_tier)
            DEPENDENCY_DURATION.record(
                dependency_seconds,
                {"dependency": "payment", "product_id": request.user_tier},
            )

            payment_failure_threshold = scenario.payment_failure_rate
            if random.random() < payment_failure_threshold:
                child_span.set_attribute("payment.authorized", False)
                child_span.record_exception(RuntimeError("payment authorization failed"))
                FAILED_PAYMENT_COUNTER.add(1, {"region": request.region, "user_tier": request.user_tier})
                CHECKOUT_COUNTER.add(1, {"outcome": "failed", "region": request.region, "user_tier": request.user_tier})
                _record_request(route, "POST", "error")
                logger.warning(
                    "payment_failed scenario=%s user_id=%s region=%s tier=%s total=%.2f",
                    scenario.name,
                    request.user_id,
                    request.region,
                    request.user_tier,
                    discounted_total,
                )
                raise HTTPException(status_code=502, detail="Payment provider timeout")

        order_id = f"ord-{uuid4().hex[:10]}"
        duration = time.perf_counter() - start
        CHECKOUT_COUNTER.add(1, {"outcome": "success", "region": request.region, "user_tier": request.user_tier})
        REVENUE_COUNTER.add(discounted_total, {"region": request.region, "user_tier": request.user_tier})
        CHECKOUT_DURATION.record(duration, {"region": request.region, "user_tier": request.user_tier})
        _record_request(route, "POST", "ok")

        logger.info(
            "checkout_completed scenario=%s order_id=%s user_id=%s region=%s tier=%s total=%.2f duration_ms=%d",
            scenario.name,
            order_id,
            request.user_id,
            request.region,
            request.user_tier,
            discounted_total,
            int(duration * 1000),
        )

        span.set_attribute("checkout.total", discounted_total)
        span.set_attribute("checkout.order_id", order_id)
        return {
            "order_id": order_id,
            "status": "confirmed",
            "total": discounted_total,
            "currency": "USD",
        }


@app.get("/api/demo/status")
def demo_status() -> dict[str, object]:
    return {
        "traffic": traffic_controller.status(),
        "scenario": scenario_snapshot(),
    }


@app.post("/api/demo/start")
def demo_start(request: DemoStartRequest) -> dict[str, object]:
    try:
        runtime_settings.set_scenario(request.scenario)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown scenario {request.scenario}") from exc
    traffic_controller.start(request.base_url, request.concurrency)
    logger.info(
        "demo_traffic_started scenario=%s concurrency=%d base_url=%s",
        request.scenario,
        request.concurrency,
        request.base_url,
    )
    return demo_status()


@app.post("/api/demo/scenario")
def demo_apply_scenario(request: DemoScenarioRequest) -> dict[str, object]:
    try:
        scenario = runtime_settings.set_scenario(request.scenario)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown scenario {request.scenario}") from exc
    logger.info("demo_scenario_changed scenario=%s", scenario.name)
    return demo_status()


@app.post("/api/demo/stop")
def demo_stop() -> dict[str, object]:
    traffic_controller.stop()
    logger.info("demo_traffic_stopped")
    return demo_status()


def create_app() -> FastAPI:
    global _instrumented
    if not _instrumented:
        FastAPIInstrumentor.instrument_app(app)
        _instrumented = True
    return app


def run() -> None:
    create_app()
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


create_app()
