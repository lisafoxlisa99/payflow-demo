# Payflow Demo

A local demo application styled after a payments/fintech SaaS product (calibrated from Stripe's public homepage for palette/typography/layout only — no real markup, copy, or images were reused). "Payflow" is a fictional company; nothing here reflects a real business's actual product or data.

Built for a Datadog SE to use in a sales call, POV, or workshop — a credible-looking product with realistic operational problems wired in to demonstrate observability value.

## Architecture

Four-container chain, all orchestrated via `docker-compose.yml`:

```
frontend (nginx, static site) -> gateway (FastAPI pass-through) -> api (FastAPI + Postgres) -> db (Postgres)
```

- **frontend/** — marketing homepage, signup/login, and a transactions dashboard (static HTML/CSS/JS served by nginx, proxying `/api/` to the gateway)
- **backend/gateway/** — thin FastAPI reverse proxy; exists only to give APM's service map and distributed traces a second real hop
- **backend/api/** — FastAPI service with all business logic and the only service that talks to Postgres
- **db/** — Postgres 16, seeded via `db/init.sql` with synthetic customers, transactions, and a dispute archive

No real payment processing happens anywhere — every endpoint returns synthetic data.

## Running it

Requires Docker (or finch) with compose support.

```bash
cd payflow-demo
cp .env.example .env   # fill in DD_API_KEY, DD_SITE if wiring up Datadog (see below)
docker compose up --build -d
```

Then open **http://localhost:8080/**.

Check container health and run a smoke test:

```bash
docker compose ps
curl http://localhost:8080/api/health
```

Tear down with `docker compose down` (add `-v` to also drop the Postgres volume).

## Pages

| Path | Purpose |
|---|---|
| `/` | Marketing homepage — hero, product features, developer section, a fee calculator, testimonial, final CTA |
| `/signup.html` | Signup form → `POST /api/signup` |
| `/login.html` | Trivial demo login (any credentials work) → `POST /api/login` |
| `/dashboard.html` | Transactions dashboard — metric cards, searchable transaction table |
| `/transaction.html?id=<id>` | Transaction detail view |

## Seeded observability scenarios

Three deliberate, reliably-reproducible issues are wired into real UI actions/endpoints (not a separate "demo controls" panel) — see `backend/api/main.py` and `frontend/site/js/fee-calculator.js` for the implementation and inline comments.

| # | Scenario | Where | Trigger |
|---|---|---|---|
| 1 | **Frontend error** | Homepage → pricing/fee calculator | Set currency to **"Other / unlisted currency"** and click **Calculate fee** → uncaught `TypeError` in the browser console (no rate entry exists for that option) |
| 2 | **Backend error from a DB access** | Dashboard → transaction detail | Click into the transaction for **Northwind Traders** dated **2026-07-09** (`id = txn_demo_investigate`) → `GET /api/transactions/{id}` 500s. The query succeeds; the seeded row has `settled_at = NULL`, and the code crashes computing settlement duration right after |
| 3 | **Slow, N+1-shaped request** | Dashboard → transaction search | Type **`review queue`** into the search box and hit Search → ~3s response. Pulls all 130 seeded rows from `dispute_archive` and does a separate customer lookup query per row instead of a join (100+ individual queries) |

Every other page interaction, search term, and transaction should behave normally — these three are the only rigged paths, each behind a specific, deterministic trigger.

## Datadog wiring

This demo ships with real Datadog Agent, APM, and RUM wiring (not just the demo shell) — see `docker-compose.yml`, `backend/gateway/main.py`, `backend/api/main.py`, and `frontend/site/js/rum.js`.

### Agent + APM

The `datadog-agent` service in `docker-compose.yml` reads `DD_API_KEY` and `DD_SITE` from `.env` (never commit `.env` — see `.gitignore`). Both `gateway` and `api` run under `ddtrace-run` and point at the agent via `DD_AGENT_HOST` / `DD_TRACE_AGENT_PORT`. Structured JSON logs from both services include real `dd.trace_id` / `dd.span_id` values for log/trace correlation once a request is traced.

To set this up:

```bash
cp .env.example .env
# edit .env: set DD_API_KEY (a real, unrevoked key) and DD_SITE
docker compose up --build -d
```

Verify the agent is healthy and receiving traces:

```bash
docker compose exec datadog-agent agent status
```

Look for `API Keys status: API Key valid` and, after generating some traffic, an APM receiver entry showing a Python client.

### RUM

`frontend/site/js/rum.js` initializes Datadog Browser RUM (`service: payflow-frontend`, `env: demo`) and is included on every page. `sessionSampleRate` is 100 and `sessionReplaySampleRate` is 100, so every session should also produce a session replay. RUM Application ID and Client Token are embedded directly in `rum.js` — these are designed to be public (shipped to every visitor's browser), unlike the Agent's `DD_API_KEY`, so this is expected and not a leak.

To point RUM at a different Datadog RUM application, edit `applicationId` / `clientToken` / `site` in `frontend/site/js/rum.js` directly, then rebuild the frontend:

```bash
docker compose up --build -d frontend
```

## Notes

- This is a demo shell with synthetic data only — no real customer data, no real payment processing, no production credentials.
- Meant to run locally and be torn down after use; not deployed anywhere externally reachable.
- The three seeded issues above are fiction, invented purely to have something to point at in Datadog — they say nothing about any real company's actual systems.
