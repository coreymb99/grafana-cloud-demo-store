# Grafana Cloud Demo Store

This is a small ecommerce-style service built to show a strong Grafana Cloud workflow in an interview:

- realistic HTTP traffic instead of a hello-world app
- a localhost control room UI for a polished live demo
- traces that break checkout into inventory, pricing, shipping, and payment spans
- business metrics like checkout outcomes, revenue, and failed payments
- logs correlated with traces so you can pivot from a failure to the related trace
- a traffic generator to keep the dashboard populated during a demo

## Why this app is a good fit

For a Senior Solutions Engineer interview, this demo gives you a practical observability story:

- show how to instrument an app directly with OTLP for a fast proof of value
- explain how the same design would move behind Grafana Alloy in production
- demonstrate metrics, logs, and traces together instead of treating them as separate tools
- create a believable incident: elevated payment latency and failures in checkout

## Project layout

- `app/main.py`: FastAPI service and business logic
- `app/demo_control.py`: live scenario and traffic controls
- `app/ui.py`: interview-friendly localhost UI
- `app/telemetry.py`: OpenTelemetry setup for traces, metrics, and logs
- `traffic.py`: synthetic load generator
- `dashboard/storefront-overview.json`: importable Grafana dashboard
- `.env.example`: Grafana Cloud OTLP environment variable template

## Setup

1. Create and sync the environment:

```bash
cd /Users/coreybartlett/Documents/Playground/grafana-cloud-demo-store
uv sync
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. In Grafana Cloud, open your stack and go to:

- `Connections`
- `OpenTelemetry`
- `Configure`

Copy the values for:

- `OTEL_EXPORTER_OTLP_PROTOCOL`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_EXPORTER_OTLP_HEADERS`

Grafana’s OTLP docs note that for Python, the authorization header should use `Basic%20` instead of `Basic `.

4. Run the API and open the demo console:

```bash
set -a
source .env
set +a
uv run demo-store
```

Then open:

`http://127.0.0.1:8000`

The built-in control room lets you:

- start or stop data generation without a second terminal
- switch scenarios like steady state, payment incident, inventory hotspot, and flash sale
- trigger a one-click payment incident for the strongest interview demo
- show live request, checkout, and error counters before you pivot to Grafana Cloud
- narrate what the interviewer should see in Grafana Cloud while the data changes

5. Optional: if you want a terminal-only mode instead, use the standalone generator in another shell:

```bash
cd /Users/coreybartlett/Documents/Playground/grafana-cloud-demo-store
set -a
source .env
set +a
uv run demo-traffic
```

## Demo knobs

For the polished demo, use the localhost UI instead of environment variables. It can change scenarios live without restarting the service.

## Dashboard import

Import `/Users/coreybartlett/Documents/Playground/grafana-cloud-demo-store/dashboard/storefront-overview.json` into Grafana and bind:

- the Prometheus/Mimir data source to the `Metrics` variable
- the Loki data source to the `Logs` variable

If a metric name looks slightly different in your stack, open Explore and search for `storefront_`. Grafana Cloud converts OpenTelemetry metric names to Prometheus-compatible names by replacing `.` or `-` with `_` and adding standard suffixes such as `_total` or `_seconds`.

## Suggested Grafana Assistant prompts

Use prompts like these once data is flowing:

1. `Why did checkout latency spike in the last 15 minutes?`
2. `Which dependency is contributing most to checkout p95 latency?`
3. `Are payment failures concentrated in one region or customer tier?`
4. `Show me traces related to recent payment_failed logs.`
5. `Did revenue drop when checkout errors increased?`
6. `Compare enterprise checkout latency to trial users over the last 30 minutes.`

## Suggested Interview Narrative

Use a story like this:

1. `Northstar Mercantile is a premium ecommerce brand for engineering teams, and this service owns the digital checkout journey.`
2. `I instrumented it with OpenTelemetry and sent traces, metrics, and logs directly to Grafana Cloud to get to value quickly.`
3. `In the steady state, we expect healthy browse traffic, stable checkout latency, and a small background level of payment noise.`
4. `Now I’m going to trigger a payment-provider incident from the localhost control room so we can watch the customer impact appear in real time.`
5. `In Grafana Cloud, we can see checkout latency climb, failed payments increase, and logs correlate directly with the degraded payment dependency.`
6. `From there, I can use Application Observability, the custom dashboard, and Grafana AI to move from symptom to probable root cause to business impact.`
7. `For production, I’d likely put Grafana Alloy in front of this pipeline for resiliency, enrichment, and routing, but for a demo this direct OTLP setup is the fastest proof of value.`

## Interview framing

You can tell the interviewer:

- this uses direct OTLP export because it is the fastest path to value for a demo
- in production, you would usually place Grafana Alloy between the app and Grafana Cloud for resiliency, enrichment, sampling, and routing
- the service intentionally emits both technical and business telemetry so the observability conversation reaches customer impact, not just CPU charts

## References

- Grafana Cloud OTLP endpoint docs: <https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/>
- OTLP format considerations: <https://grafana.com/docs/grafana-cloud/send-data/otlp/otlp-format-considerations/>
