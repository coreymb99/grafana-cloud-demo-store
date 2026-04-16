from __future__ import annotations

import random
import threading
import time
from dataclasses import asdict, dataclass
from uuid import uuid4

import httpx


USER_TIERS = ["trial", "pro", "enterprise"]
REGIONS = ["us-east", "us-west", "eu-west"]
PRODUCT_IDS = ["sku-100", "sku-101", "sku-102", "sku-103", "sku-104"]


@dataclass
class DemoScenario:
    name: str
    label: str
    narrative: str
    payment_degradation: float
    payment_failure_rate: float
    inventory_spike_multiplier: float
    checkout_weight: float


SCENARIOS: dict[str, DemoScenario] = {
    "steady-state": DemoScenario(
        name="steady-state",
        label="Steady State",
        narrative="Healthy buying activity with occasional payment noise.",
        payment_degradation=1.0,
        payment_failure_rate=0.03,
        inventory_spike_multiplier=1.0,
        checkout_weight=0.20,
    ),
    "payment-incident": DemoScenario(
        name="payment-incident",
        label="Payment Incident",
        narrative="A third-party payment provider is degrading and throwing more authorizations.",
        payment_degradation=2.8,
        payment_failure_rate=0.22,
        inventory_spike_multiplier=1.0,
        checkout_weight=0.24,
    ),
    "inventory-hotspot": DemoScenario(
        name="inventory-hotspot",
        label="Inventory Hotspot",
        narrative="One popular product is causing inventory lookups to pile up.",
        payment_degradation=1.0,
        payment_failure_rate=0.04,
        inventory_spike_multiplier=3.2,
        checkout_weight=0.22,
    ),
    "flash-sale": DemoScenario(
        name="flash-sale",
        label="Flash Sale",
        narrative="Traffic surges and checkout volume climbs as a promotion launches.",
        payment_degradation=1.6,
        payment_failure_rate=0.08,
        inventory_spike_multiplier=1.4,
        checkout_weight=0.34,
    ),
}


class RuntimeSettings:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scenario = SCENARIOS["steady-state"]

    def current(self) -> DemoScenario:
        with self._lock:
            return self._scenario

    def set_scenario(self, scenario_name: str) -> DemoScenario:
        if scenario_name not in SCENARIOS:
            raise KeyError(scenario_name)
        with self._lock:
            self._scenario = SCENARIOS[scenario_name]
            return self._scenario


runtime_settings = RuntimeSettings()


class TrafficController:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._base_url = "http://127.0.0.1:8000"
        self._concurrency = 6
        self._started_at = 0.0
        self._request_count = 0
        self._checkout_count = 0
        self._error_count = 0

    def status(self) -> dict[str, object]:
        with self._lock:
            running = self._thread is not None and self._thread.is_alive()
            return {
                "running": running,
                "base_url": self._base_url,
                "concurrency": self._concurrency,
                "started_at": self._started_at,
                "request_count": self._request_count,
                "checkout_count": self._checkout_count,
                "error_count": self._error_count,
            }

    def start(self, base_url: str, concurrency: int) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._base_url = base_url.rstrip("/")
            self._concurrency = concurrency
            self._started_at = time.time()
            self._request_count = 0
            self._checkout_count = 0
            self._error_count = 0
            self._stop_event = threading.Event()
            self._thread = threading.Thread(target=self._run, daemon=True, name="traffic-controller")
            self._thread.start()

    def stop(self) -> None:
        thread: threading.Thread | None
        with self._lock:
            self._stop_event.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)
        with self._lock:
            self._thread = None
            self._started_at = 0.0

    def _run(self) -> None:
        workers = []
        for _ in range(self._concurrency):
            worker = threading.Thread(target=self._worker, daemon=True)
            workers.append(worker)
            worker.start()

        for worker in workers:
            worker.join()

    def _worker(self) -> None:
        with httpx.Client(timeout=5.0) as client:
            while not self._stop_event.is_set():
                try:
                    self._send_request(client)
                except Exception:
                    pass
                self._stop_event.wait(random.uniform(0.12, 0.85))

    def _send_request(self, client: httpx.Client) -> None:
        scenario = runtime_settings.current()
        actions = ["catalog", "product", "checkout"]
        weights = [0.50, 0.25, scenario.checkout_weight]
        action = random.choices(actions, weights=weights)[0]
        if action == "catalog":
            if random.random() < 0.35:
                response = client.get(f"{self._base_url}/api/catalog", params={"search": "Cloud"})
            else:
                response = client.get(f"{self._base_url}/api/catalog")
            self._record_response(response.status_code, checkout=False)
            return
        if action == "product":
            response = client.get(f"{self._base_url}/api/products/{random.choice(PRODUCT_IDS)}")
            self._record_response(response.status_code, checkout=False)
            return
        payload = {
            "user_id": f"user-{uuid4().hex[:6]}",
            "region": random.choices(REGIONS, weights=[0.55, 0.25, 0.20])[0],
            "user_tier": random.choices(USER_TIERS, weights=[0.65, 0.25, 0.10])[0],
            "items": [{"product_id": random.choice(PRODUCT_IDS), "quantity": random.randint(1, 3)}],
            "promo_code": "LAUNCH15" if random.random() < 0.14 else None,
        }
        if random.random() < 0.40:
            payload["items"].append({"product_id": random.choice(PRODUCT_IDS), "quantity": 1})
        response = client.post(f"{self._base_url}/api/checkout", json=payload)
        self._record_response(response.status_code, checkout=True)

    def _record_response(self, status_code: int, checkout: bool) -> None:
        with self._lock:
            self._request_count += 1
            if checkout:
                self._checkout_count += 1
            if status_code >= 400:
                self._error_count += 1


traffic_controller = TrafficController()


def scenario_snapshot() -> dict[str, object]:
    current = runtime_settings.current()
    return {
        "current": asdict(current),
        "available": [asdict(scenario) for scenario in SCENARIOS.values()],
    }
