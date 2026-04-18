"""
Central status aggregator — polls /health (and a representative /api/... call)
on every per-demo Fly.io app, aggregates into one JSON payload, caches 15s.

Deploys as its own Fly app. Frontend (sa-ai-toolkit.vercel.app/status/) hits
this aggregator once instead of 12 separate CORS requests.
"""
from __future__ import annotations
import asyncio
import time
import os
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# (name, base_url, probe_method, probe_path, probe_json)
# probe = one fast real-logic call that proves the API works, not just /health
DEMOS: list[dict[str, Any]] = [
    {"name": "industrial-ai",  "url": "https://sa-industrial-ai.fly.dev",
     "method": "GET",  "path": "/api/industrial?action=detect"},
    {"name": "ceo-agent",      "url": "https://sa-ceo-agent.fly.dev",
     "method": "GET",  "path": "/api/ceo?action=metrics"},
    {"name": "autoresearch",   "url": "https://sa-autoresearch.fly.dev",
     "method": "GET",  "path": "/api/research?action=meta"},
    {"name": "autoresearch-vrp", "url": "https://sa-autoresearch-vrp.fly.dev",
     "method": "GET",  "path": "/api/vrp?action=meta"},
    {"name": "enterprise-gen", "url": "https://sa-enterprise-gen.fly.dev",
     "method": "POST", "path": "/api/enterprise?action=score",
     "json": {"profile": {"company": "Acme", "industry": "banking-finance",
                          "pain_points": ["A"], "audience": "executives",
                          "minutes": 90, "size": "1000-10000"}}},
    {"name": "gstack",         "url": "https://sa-gstack.fly.dev",
     "method": "GET",  "path": "/api/gstack?command=office-hours"},
    {"name": "hypothesis",     "url": "https://sa-hypothesis.fly.dev",
     "method": "POST", "path": "/api/hypothesis",
     "json": {"text": "Market is $2T. However, disruption is coming."}},
    {"name": "karpathy-kb",    "url": "https://sa-karpathy-kb.fly.dev",
     "method": "POST", "path": "/api/karpathy?action=extract",
     "json": {"text": "AI adoption is accelerating. Foundation models dominate.", "n": 3}},
    {"name": "maestro",        "url": "https://sa-maestro.fly.dev",
     "method": "POST", "path": "/api/maestro?action=parse",
     "json": {"yaml": "appId: com.test\n---\n- launchApp\n"}},
    {"name": "org-uplift",     "url": "https://sa-org-uplift.fly.dev",
     "method": "POST", "path": "/api/org_uplift?action=execute",
     "json": {"task": "write spec", "context": "sprint", "player": "A", "scenario": "startup"}},
    {"name": "playwright",     "url": "https://sa-playwright.fly.dev",
     "method": "GET",  "path": "/api/playwright?scenario=bing"},
    {"name": "ppt-gen",        "url": "https://sa-ppt-gen.fly.dev",
     "method": "POST", "path": "/api/ppt",
     "json": {"title": "Smoke", "subtitle": "Check",
              "slides": [{"template": "cover", "fields": {"title": "x"}}],
              "theme": "blue-orange"}},
    {"name": "sa-toolkit",     "url": "https://sa-sa-toolkit.fly.dev",
     "method": "POST", "path": "/api/sa_toolkit?action=gen",
     "json": {"company": "Tencent"}},
]

SLOW_MS = 2000      # slower than this → "slow"
TIMEOUT_S = 10
CACHE_TTL = 15

_cache: dict[str, Any] = {"ts": 0.0, "payload": None}


app = FastAPI(title="SA AI Toolkit — Status Aggregator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


async def _probe(client: httpx.AsyncClient, demo: dict) -> dict:
    t0 = time.perf_counter()
    url = demo["url"].rstrip("/") + demo["path"]
    kwargs: dict[str, Any] = {"timeout": TIMEOUT_S}
    if demo.get("json") is not None:
        kwargs["json"] = demo["json"]
    try:
        method = demo.get("method", "GET").upper()
        resp = await client.request(method, url, **kwargs)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        http_ok = 200 <= resp.status_code < 400
        if not http_ok:
            status = "down"
            error = f"HTTP {resp.status_code}"
        elif ms > SLOW_MS:
            status = "slow"
            error = None  # slow but functional
        else:
            status = "ok"
            error = None
        return {
            "name": demo["name"],
            "url": demo["url"],
            "endpoint": demo["path"],
            "http_status": resp.status_code,
            "latency_ms": ms,
            "status": status,
            "error": error,
        }
    except httpx.ConnectError as e:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"name": demo["name"], "url": demo["url"], "endpoint": demo["path"],
                "latency_ms": ms, "status": "down",
                "error": f"ConnectError: {e}"}
    except httpx.TimeoutException:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"name": demo["name"], "url": demo["url"], "endpoint": demo["path"],
                "latency_ms": ms, "status": "down",
                "error": "timeout"}
    except Exception as e:
        ms = round((time.perf_counter() - t0) * 1000, 1)
        return {"name": demo["name"], "url": demo["url"], "endpoint": demo["path"],
                "latency_ms": ms, "status": "down",
                "error": f"{type(e).__name__}: {e}"}


async def _compute():
    t0 = time.perf_counter()
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_probe(client, d) for d in DEMOS])
    down = sum(1 for r in results if r["status"] == "down")
    slow = sum(1 for r in results if r["status"] == "slow")
    healthy = len(results) - down - slow
    overall = "down" if down >= 3 else ("degraded" if (down + slow) > 0 else "ok")
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall": overall,
        "total_demos": len(results),
        "healthy": healthy,
        "slow": slow,
        "down": down,
        "total_check_ms": round((time.perf_counter() - t0) * 1000, 1),
        "demos": results,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "status-aggregator", "monitors": len(DEMOS)}


@app.get("/api/status")
async def api_status(fresh: bool = False):
    now = time.time()
    if not fresh and _cache["payload"] and now - _cache["ts"] < CACHE_TTL:
        return {**_cache["payload"], "cached": True, "cache_age_s": round(now - _cache["ts"], 1)}
    payload = await _compute()
    _cache["ts"] = now
    _cache["payload"] = payload
    return {**payload, "cached": False}


@app.get("/")
async def root():
    # Simple landing for the aggregator itself
    return {
        "service": "SA AI Toolkit — Status Aggregator",
        "endpoints": {"/api/status": "aggregated health of all demos (15s cached)",
                      "/api/status?fresh=true": "bypass cache"},
        "monitored": [d["name"] for d in DEMOS],
    }
