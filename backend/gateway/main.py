"""Thin API gateway — forwards all /api/* traffic to the api service.

This exists to give the demo a second traced hop before the database
(frontend -> gateway -> api -> db), so Datadog APM's service map and
distributed traces have something real to show once instrumentation is
added later — not to hold any business logic of its own (that all lives
in backend-api/main.py). Do the minimum a real gateway would: forward the
request, tag it with a request id, log a structured line.

See references/architecture_patterns.md for the full picture and
references/logging_and_correlation.md for why logs are JSON from the
start.
"""

import json
import logging
import os
import sys
import time
import uuid

import httpx
from ddtrace import tracer
from fastapi import FastAPI, Request, Response

API_URL = os.environ.get("API_URL", "http://api:8001")

app = FastAPI(title="Customer Demo Gateway")

# --- structured JSON logging (see references/logging_and_correlation.md) ---


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
            "dd.service": os.environ.get("DD_SERVICE", "gateway"),
            "dd.env": os.environ.get("DD_ENV", "demo"),
            "dd.version": os.environ.get("DD_VERSION", "0.1.0"),
            "dd.trace_id": trace_id,
            "dd.span_id": span_id,
        }
        payload.update(getattr(record, "extra_fields", {}))
        return json.dumps(payload)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())
logger = logging.getLogger("gateway")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False


@app.get("/health")
def health():
    # Gateway's own liveness only — used by the compose healthcheck, never
    # exposed externally (nginx only proxies /api/, see templates/frontend).
    # The application-level health check is GET /api/health, which this
    # gateway forwards to the api service like any other request below.
    return {"status": "ok"}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = time.monotonic()
    body = await request.body()

    forward_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")
    }
    forward_headers["x-request-id"] = request_id

    async with httpx.AsyncClient() as client:
        upstream = await client.request(
            request.method,
            f"{API_URL}/api/{path}",
            params=request.query_params,
            content=body,
            headers=forward_headers,
            timeout=30.0,
        )

    logger.info(
        "proxied request",
        extra={
            "extra_fields": {
                "http.method": request.method,
                "http.path": f"/api/{path}",
                "http.status_code": upstream.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 1),
                "request_id": request_id,
            }
        },
    )
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={"content-type": upstream.headers.get("content-type", "application/json")},
    )
