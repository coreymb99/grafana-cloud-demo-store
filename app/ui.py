from __future__ import annotations


def render_demo_console() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Demo Store Control Room</title>
  <style>
    :root {
      --bg: #07111f;
      --panel: rgba(8, 21, 40, 0.88);
      --panel-strong: rgba(13, 29, 53, 0.96);
      --line: rgba(147, 197, 253, 0.18);
      --text: #edf4ff;
      --muted: #96a5c0;
      --accent: #6ee7b7;
      --accent-2: #fb923c;
      --danger: #fb7185;
      --gold: #fbbf24;
      --shadow: 0 24px 80px rgba(1, 6, 17, 0.45);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(110, 231, 183, 0.12), transparent 32%),
        radial-gradient(circle at top right, rgba(59, 130, 246, 0.16), transparent 28%),
        linear-gradient(160deg, #030712 0%, #07111f 42%, #0e172b 100%);
      min-height: 100vh;
    }

    .shell {
      width: min(1200px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      gap: 18px;
    }

    .hero, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      border-radius: 24px;
    }

    .hero {
      padding: 28px;
      display: grid;
      grid-template-columns: 1.3fr 0.9fr;
      gap: 20px;
      overflow: hidden;
      position: relative;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -100px -120px auto;
      width: 280px;
      height: 280px;
      background: radial-gradient(circle, rgba(251, 146, 60, 0.28), transparent 64%);
      pointer-events: none;
    }

    .eyebrow {
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 0.8rem;
      margin-bottom: 10px;
    }

    h1 {
      margin: 0 0 12px;
      font-size: clamp(2.1rem, 5vw, 4rem);
      line-height: 0.96;
      letter-spacing: -0.04em;
    }

    .lead {
      margin: 0;
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
      max-width: 60ch;
    }

    .hero-card {
      align-self: center;
      background: linear-gradient(180deg, rgba(14, 23, 43, 0.95), rgba(6, 14, 29, 0.98));
      border: 1px solid rgba(148, 163, 184, 0.12);
      border-radius: 20px;
      padding: 18px;
    }

    .hero-card h2 {
      margin: 0 0 8px;
      font-size: 1.1rem;
    }

    .hero-card p {
      margin: 0 0 16px;
      color: var(--muted);
      line-height: 1.6;
    }

    .hero-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }

    .hero-metrics div {
      border: 1px solid rgba(148, 163, 184, 0.12);
      border-radius: 16px;
      padding: 12px;
      background: rgba(7, 17, 31, 0.7);
    }

    .hero-metrics span {
      display: block;
      font-size: 0.78rem;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .hero-metrics strong {
      font-size: 1.2rem;
    }

    .company-badge {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border-radius: 999px;
      padding: 10px 14px;
      background: rgba(251, 191, 36, 0.14);
      color: #fde68a;
      font-weight: 700;
      margin-bottom: 16px;
    }

    .company-badge::before {
      content: "";
      width: 12px;
      height: 12px;
      border-radius: 999px;
      background: currentColor;
      box-shadow: 0 0 18px rgba(251, 191, 36, 0.5);
    }

    .grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
    }

    .panel {
      padding: 22px;
    }

    .panel h2 {
      margin: 0 0 12px;
      font-size: 1.2rem;
    }

    .muted {
      color: var(--muted);
      line-height: 1.6;
    }

    .controls {
      display: grid;
      gap: 16px;
    }

    .row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    label {
      display: grid;
      gap: 8px;
      font-size: 0.92rem;
      color: var(--muted);
    }

    select, input {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background: rgba(3, 7, 18, 0.72);
      color: var(--text);
      padding: 12px 14px;
      font: inherit;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 8px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 150ms ease, opacity 150ms ease, box-shadow 150ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
    .primary { background: linear-gradient(135deg, #6ee7b7, #2dd4bf); color: #03111c; }
    .secondary { background: rgba(59, 130, 246, 0.2); color: #cfe3ff; border: 1px solid rgba(59, 130, 246, 0.35); }
    .danger { background: rgba(251, 113, 133, 0.16); color: #ffd7de; border: 1px solid rgba(251, 113, 133, 0.34); }

    .status-band {
      margin-top: 16px;
      border-radius: 16px;
      padding: 14px 16px;
      background: var(--panel-strong);
      border: 1px solid rgba(148, 163, 184, 0.14);
      display: grid;
      gap: 8px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 6px 12px;
      width: fit-content;
      background: rgba(110, 231, 183, 0.13);
      color: #d1fae5;
      font-size: 0.88rem;
    }

    .pill::before {
      content: "";
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: currentColor;
    }

    .pill.stopped {
      background: rgba(148, 163, 184, 0.14);
      color: #cbd5e1;
    }

    .story-list, .check-list {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 14px;
    }

    .kpi {
      padding: 16px;
      border-radius: 18px;
      background: rgba(5, 13, 25, 0.72);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .kpi span {
      display: block;
      color: var(--muted);
      font-size: 0.82rem;
      margin-bottom: 8px;
    }

    .kpi strong {
      font-size: 1.8rem;
      letter-spacing: -0.04em;
    }

    .store-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 14px;
    }

    .product-card {
      padding: 16px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(11, 23, 41, 0.84), rgba(6, 14, 26, 0.95));
      border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .product-card small {
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    .product-card h3 {
      margin: 8px 0 6px;
      font-size: 1.1rem;
    }

    .product-card p {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
      min-height: 48px;
    }

    .price-row {
      display: flex;
      justify-content: space-between;
      margin-top: 14px;
      color: #dbeafe;
      font-weight: 700;
    }

    .incident-callout {
      margin-top: 16px;
      padding: 18px;
      border-radius: 18px;
      border: 1px solid rgba(251, 113, 133, 0.26);
      background: linear-gradient(180deg, rgba(63, 16, 26, 0.28), rgba(25, 8, 14, 0.7));
    }

    .incident-callout strong {
      display: block;
      margin-bottom: 8px;
      color: #ffd4dc;
    }

    .story-item, .check-item {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(5, 13, 25, 0.72);
      border: 1px solid rgba(148, 163, 184, 0.12);
    }

    .story-item strong, .check-item strong {
      display: block;
      margin-bottom: 6px;
      font-size: 0.96rem;
    }

    .prompt-box {
      margin-top: 14px;
      padding: 16px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(11, 23, 41, 0.85), rgba(8, 18, 32, 0.98));
      border: 1px solid rgba(148, 163, 184, 0.14);
      color: #dce8fb;
      line-height: 1.65;
      white-space: pre-wrap;
      min-height: 108px;
    }

    .footer-note {
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.6;
    }

    @media (max-width: 900px) {
      .hero, .grid, .row {
        grid-template-columns: 1fr;
      }
      .hero-metrics {
        grid-template-columns: 1fr;
      }
      .kpi-grid, .store-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div>
        <div class="eyebrow">Grafana Cloud Interview Demo</div>
        <div class="company-badge">Northstar Mercantile</div>
        <h1>Demo Store Control Room</h1>
        <p class="lead">
          Northstar Mercantile is a fast-growing premium merch brand for modern engineering teams.
          Use this localhost control room to drive realistic storefront demand, trigger a production incident,
          and then pivot into Grafana Cloud to explain user pain and business impact.
        </p>
      </div>
      <div class="hero-card">
        <h2>Live Demo Arc</h2>
        <p id="scenarioNarrative">Healthy buying activity with occasional payment noise.</p>
        <div class="hero-metrics">
          <div><span>Company</span><strong>Northstar</strong></div>
          <div><span>Service</span><strong>checkout-service</strong></div>
          <div><span>Environment</span><strong>demo</strong></div>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Traffic Controls</h2>
        <p class="muted">Start or stop synthetic demand, switch scenarios, and narrate the incident as your Grafana dashboards react.</p>
        <div class="controls">
          <div class="row">
            <label>
              Scenario
              <select id="scenario"></select>
            </label>
            <label>
              Worker Concurrency
              <input id="concurrency" type="number" min="1" max="24" value="6" />
            </label>
          </div>
          <label>
            Target Base URL
            <input id="baseUrl" type="text" value="http://127.0.0.1:8000" />
          </label>
          <div class="actions">
            <button class="primary" id="startButton">Generate Data</button>
            <button class="secondary" id="scenarioButton">Apply Scenario</button>
            <button class="secondary" id="incidentButton">Trigger Payment Incident</button>
            <button class="danger" id="stopButton">Stop Traffic</button>
          </div>
        </div>
        <div class="status-band">
          <span id="trafficState" class="pill stopped">Traffic stopped</span>
          <div id="statusText" class="footer-note">Ready to begin the story.</div>
        </div>
        <div class="kpi-grid">
          <div class="kpi"><span>Generated Requests</span><strong id="requestsCount">0</strong></div>
          <div class="kpi"><span>Checkout Attempts</span><strong id="checkoutsCount">0</strong></div>
          <div class="kpi"><span>Observed Errors</span><strong id="errorsCount">0</strong></div>
          <div class="kpi"><span>Scenario</span><strong id="scenarioLabel">Steady</strong></div>
        </div>
      </div>

      <div class="panel">
        <h2>Storefront Preview</h2>
        <p class="muted">Ground the observability conversation in a real customer experience instead of abstract metrics.</p>
        <div class="store-grid">
          <div class="product-card">
            <small>Best Seller</small>
            <h3>Cloud Ops Hoodie</h3>
            <p>A premium launch-week item popular with engineering leaders and platform teams.</p>
            <div class="price-row"><span>Apparel</span><span>$72</span></div>
          </div>
          <div class="product-card">
            <small>Promo Item</small>
            <h3>Incident Response Notebook</h3>
            <p>Commonly bundled during campaign pushes, which raises cart size and payment latency.</p>
            <div class="price-row"><span>Office</span><span>$24</span></div>
          </div>
        </div>
        <div class="incident-callout">
          <strong>Why the payment incident lands well in an interview</strong>
          It creates a visible customer-impact story: users can browse and add to cart, but checkout slows down and some orders fail,
          which gives you a clean path from signals to root cause to revenue impact.
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Interview Story Beats</h2>
        <p class="muted">Use these talking points while data is streaming into Grafana Cloud.</p>
        <div class="story-list">
          <div class="story-item">
            <strong>1. Establish baseline</strong>
            Northstar Mercantile is running normally: healthy throughput, stable checkout p95, and low failed payments.
          </div>
          <div class="story-item">
            <strong>2. Trigger an incident</strong>
            A payment provider starts timing out during a campaign push, so checkouts get slower and conversion starts to slip.
          </div>
          <div class="story-item">
            <strong>3. Investigate with Grafana AI</strong>
            Ask what changed, which dependency is driving the issue, and how the customer journey is being affected.
          </div>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Suggested AI Prompt</h2>
        <p class="muted">This updates automatically based on the scenario you pick.</p>
        <div id="promptBox" class="prompt-box"></div>
      </div>

      <div class="panel">
        <h2>Operator Checklist</h2>
        <p class="muted">Quick reminders for the live walkthrough.</p>
        <div class="check-list">
          <div class="check-item">
            <strong>Keep Grafana Cloud open on two tabs</strong>
            One for Application Observability and one for the custom storefront dashboard.
          </div>
          <div class="check-item">
            <strong>Let the scenario run for 60-90 seconds</strong>
            That gives p95, error rate, and trace samples enough time to stand out.
          </div>
          <div class="check-item">
            <strong>Pivot from symptoms to business impact</strong>
            Tie latency and failed payments back to checkout success and revenue.
          </div>
        </div>
      </div>
    </section>
  </main>

  <script>
      const prompts = {
      "steady-state": "Ask Grafana Assistant: Summarize the health of Northstar Mercantile checkout-service over the last 15 minutes and call out any early warning signs.",
      "payment-incident": "Ask Grafana Assistant: Why did Northstar Mercantile checkout latency and failed payments increase, and which dependency is contributing most to the slowdown?",
      "inventory-hotspot": "Ask Grafana Assistant: Which part of checkout is slowing down at Northstar Mercantile, and is the problem isolated to a specific product or region?",
      "flash-sale": "Ask Grafana Assistant: How did the Northstar Mercantile flash sale affect throughput, checkout latency, and conversion outcomes across customer tiers?"
    };

    async function loadStatus() {
      const response = await fetch("/api/demo/status");
      const payload = await response.json();
      const selector = document.getElementById("scenario");
      if (!selector.children.length) {
        payload.scenario.available.forEach((scenario) => {
          const option = document.createElement("option");
          option.value = scenario.name;
          option.textContent = scenario.label;
          selector.appendChild(option);
        });
      }
      selector.value = payload.scenario.current.name;
      document.getElementById("scenarioNarrative").textContent = payload.scenario.current.narrative;
      document.getElementById("promptBox").textContent = prompts[payload.scenario.current.name];
      document.getElementById("scenarioLabel").textContent = payload.scenario.current.label;
      document.getElementById("concurrency").value = payload.traffic.concurrency;
      document.getElementById("baseUrl").value = payload.traffic.base_url;
      document.getElementById("requestsCount").textContent = payload.traffic.request_count;
      document.getElementById("checkoutsCount").textContent = payload.traffic.checkout_count;
      document.getElementById("errorsCount").textContent = payload.traffic.error_count;

      const running = payload.traffic.running;
      const stateEl = document.getElementById("trafficState");
      const textEl = document.getElementById("statusText");
      stateEl.textContent = running ? "Traffic running" : "Traffic stopped";
      stateEl.className = running ? "pill" : "pill stopped";
      textEl.textContent = running
        ? `Sending ${payload.traffic.concurrency} workers to ${payload.traffic.base_url} under the ${payload.scenario.current.label} scenario.`
        : "Ready to begin the story.";
    }

    async function postJson(path, body) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail || "Request failed");
      }
      return response.json();
    }

    document.getElementById("startButton").addEventListener("click", async () => {
      try {
        await postJson("/api/demo/start", {
          scenario: document.getElementById("scenario").value,
          concurrency: Number(document.getElementById("concurrency").value),
          base_url: document.getElementById("baseUrl").value,
        });
        await loadStatus();
      } catch (error) {
        alert(error.message);
      }
    });

    document.getElementById("scenarioButton").addEventListener("click", async () => {
      try {
        await postJson("/api/demo/scenario", { scenario: document.getElementById("scenario").value });
        await loadStatus();
      } catch (error) {
        alert(error.message);
      }
    });

    document.getElementById("incidentButton").addEventListener("click", async () => {
      try {
        document.getElementById("scenario").value = "payment-incident";
        await postJson("/api/demo/start", {
          scenario: "payment-incident",
          concurrency: Number(document.getElementById("concurrency").value),
          base_url: document.getElementById("baseUrl").value,
        });
        await loadStatus();
      } catch (error) {
        alert(error.message);
      }
    });

    document.getElementById("stopButton").addEventListener("click", async () => {
      try {
        await postJson("/api/demo/stop", {});
        await loadStatus();
      } catch (error) {
        alert(error.message);
      }
    });

    loadStatus();
    setInterval(loadStatus, 4000);
  </script>
</body>
</html>
"""
