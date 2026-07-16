"""Payflow demo API service — all business logic and DB access lives here.

Sits behind the gateway (frontend -> gateway -> api -> db). This is a
fictional payments platform built for demo purposes only; no real
customer data or real payment processing is involved anywhere here.
"""

import json
import logging
import os
import sys
import time

import psycopg
from ddtrace import tracer
from fastapi import FastAPI, HTTPException

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://demo:demo@db:5432/demo")

app = FastAPI(title="Payflow Demo API")


def get_connection():
    return psycopg.connect(DATABASE_URL)


# --- structured JSON logging ---


def _current_trace_ids():
    ctx = tracer.current_trace_context()
    return (str(ctx.trace_id), str(ctx.span_id)) if ctx else ("0", "0")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        trace_id, span_id = _current_trace_ids()
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "dd.service": os.environ.get("DD_SERVICE", "api"),
            "dd.env": os.environ.get("DD_ENV", "demo"),
            "dd.version": os.environ.get("DD_VERSION", "0.1.0"),
            "dd.trace_id": trace_id,
            "dd.span_id": span_id,
        }
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/signup")
def signup(payload: dict):
    logger.info("signup", extra={"extra_fields": {"company": payload.get("company", "")}})
    return {"status": "created"}


@app.post("/api/login")
def login(payload: dict):
    logger.info("login", extra={"extra_fields": {"email": payload.get("email", "")}})
    return {"status": "ok", "session": "demo-session"}


@app.get("/api/metrics")
def metrics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transactions")
            total_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'success'")
            success_count, success_total = cur.fetchone()
            cur.execute("SELECT COUNT(*) FROM transactions WHERE status = 'disputed'")
            disputes = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status = 'pending'")
            pending_total = cur.fetchone()[0]
    success_rate = round((success_count / total_count) * 100, 1) if total_count else 0
    return {
        "volume_30d": float(success_total),
        "volume_trend": 8.2,
        "success_rate": success_rate,
        "disputes": disputes,
        "payouts_pending": float(pending_total),
    }


@app.get("/api/transactions")
def list_transactions(q: str = ""):
    # "review queue" is the one recognized trigger phrase for the slow,
    # N+1-shaped path below — every other search term (or no search at
    # all) uses the fast joined query.
    if q.strip().lower() == "review queue":
        return _review_queue_slow()

    with get_connection() as conn:
        with conn.cursor() as cur:
            if q:
                like = f"%{q}%"
                cur.execute(
                    """
                    SELECT t.id, c.name, t.amount, t.status, t.created_at
                    FROM transactions t JOIN customers c ON c.id = t.customer_id
                    WHERE t.id ILIKE %s OR c.name ILIKE %s
                    ORDER BY t.created_at DESC LIMIT 25
                    """,
                    (like, like),
                )
            else:
                cur.execute(
                    """
                    SELECT t.id, c.name, t.amount, t.status, t.created_at
                    FROM transactions t JOIN customers c ON c.id = t.customer_id
                    ORDER BY t.created_at DESC LIMIT 25
                    """
                )
            rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "customer": r[1],
            "amount": float(r[2]),
            "status": r[3],
            "created_at": r[4].strftime("%Y-%m-%d"),
        }
        for r in rows
    ]


# N+1-shaped "review queue" lookup: fetches the full dispute archive, then
# looks up each row's customer with its own round-trip instead of a join.
# dispute_archive is seeded with 130+ rows (db/init.sql) specifically so
# this loop issues 100+ individual queries. The artificial per-row sleep
# stands in for a slower query under real load, so the total lands around
# ~3s regardless of how fast the local Postgres actually responds.
N1_TARGET_SECONDS = 3.0
N1_ROW_COUNT = 130
N1_SLEEP_PER_ROW = N1_TARGET_SECONDS / N1_ROW_COUNT


def _review_queue_slow():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, customer_id, amount, created_at FROM dispute_archive ORDER BY created_at DESC")
            archive_rows = cur.fetchall()

        results = []
        for archive_id, customer_id, amount, created_at in archive_rows:  # N+1: one round-trip per row
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM customers WHERE id = %s", (customer_id,))
                customer_row = cur.fetchone()
            time.sleep(N1_SLEEP_PER_ROW)
            results.append(
                {
                    "id": f"disp_{archive_id}",
                    "customer": customer_row[0] if customer_row else "Unknown",
                    "amount": float(amount),
                    "status": "disputed",
                    "created_at": created_at.strftime("%Y-%m-%d"),
                }
            )
    return results


@app.get("/api/transactions/{transaction_id}")
def transaction_detail(transaction_id: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, c.name, t.amount, t.status, t.created_at, t.settled_at
                FROM transactions t JOIN customers c ON c.id = t.customer_id
                WHERE t.id = %s
                """,
                (transaction_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn_id, customer, amount, status, created_at, settled_at = row
    # No null-check here: every transaction is assumed to have settled by
    # the time its detail page is viewed. The one seeded row still under
    # investigation (id 'txn_demo_investigate') breaks that assumption —
    # the query above succeeds fine, this line is where it fails.
    duration = settled_at - created_at  # TypeError if settled_at is NULL

    return {
        "id": txn_id,
        "customer": customer,
        "amount": float(amount),
        "status": status,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
        "settled_at": settled_at.strftime("%Y-%m-%d %H:%M"),
        "settlement_duration": str(duration),
    }
