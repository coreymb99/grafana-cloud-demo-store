from __future__ import annotations

import asyncio
import os
import random
from uuid import uuid4

import httpx


BASE_URL = os.getenv("DEMO_STORE_URL", "http://127.0.0.1:8000")

USER_TIERS = ["trial", "pro", "enterprise"]
REGIONS = ["us-east", "us-west", "eu-west"]
PRODUCT_IDS = ["sku-100", "sku-101", "sku-102", "sku-103", "sku-104"]


async def generate_catalog_traffic(client: httpx.AsyncClient) -> None:
    if random.random() < 0.3:
        await client.get(f"{BASE_URL}/api/catalog", params={"search": "Cloud"})
    else:
        await client.get(f"{BASE_URL}/api/catalog")


async def generate_product_traffic(client: httpx.AsyncClient) -> None:
    product_id = random.choice(PRODUCT_IDS)
    await client.get(f"{BASE_URL}/api/products/{product_id}")


async def generate_checkout_traffic(client: httpx.AsyncClient) -> None:
    items = [
        {"product_id": random.choice(PRODUCT_IDS), "quantity": random.randint(1, 3)},
    ]
    if random.random() < 0.35:
        items.append({"product_id": random.choice(PRODUCT_IDS), "quantity": 1})

    payload = {
        "user_id": f"user-{uuid4().hex[:6]}",
        "region": random.choices(REGIONS, weights=[0.55, 0.25, 0.20])[0],
        "user_tier": random.choices(USER_TIERS, weights=[0.65, 0.25, 0.10])[0],
        "items": items,
        "promo_code": "LAUNCH15" if random.random() < 0.12 else None,
    }
    await client.post(f"{BASE_URL}/api/checkout", json=payload)


async def worker() -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            try:
                action = random.choices(
                    [generate_catalog_traffic, generate_product_traffic, generate_checkout_traffic],
                    weights=[0.55, 0.25, 0.20],
                )[0]
                await action(client)
            except Exception:
                pass
            await asyncio.sleep(random.uniform(0.15, 1.0))


async def main() -> None:
    concurrency = int(os.getenv("TRAFFIC_CONCURRENCY", "6"))
    await asyncio.gather(*(worker() for _ in range(concurrency)))


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
