"""
GENESIS x402 Micro-Oracle Suite (Production Deploy Package — Solana Mainnet USDC)
Standalone FastAPI server with official x402 v2.29 Solana SVM middleware + ERC-8004 Agent Card.
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse

import numpy as np
import requests
from fastapi import FastAPI
from pydantic import BaseModel

HL_URL = "https://api.hyperliquid.xyz/info"
TRACKED_COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "AVAX", "LINK", "ARB", "SUI", "HYPE"]

# Solana Mainnet CAIP-2 ID & default PayAI public facilitator (supports Solana Mainnet USDC)
DEFAULT_SOLANA_WALLET = "A1SkZSKsKTqsBqzVrdECXLmqpVdPCzqZu1kuD3LV7MF6"
PAY_TO = os.getenv("X402_PAY_TO", DEFAULT_SOLANA_WALLET).strip()
NETWORK = os.getenv("X402_NETWORK", "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp").strip()
FACILITATOR_URL = os.getenv("X402_FACILITATOR_URL", "https://facilitator.payai.network").strip()

app = FastAPI(
    title="GENESIS x402 Boundary Micro-Oracle (Solana USDC)",
    version="1.0.0",
    description="Zero-auth pay-per-call boundary verification, live perp funding-trap, and SAT solving oracles for AI agents.",
)

X402_ENABLED = False
X402_ERROR = None

if PAY_TO:
    try:
        from x402 import x402ResourceServer
        from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption, RouteConfig
        from x402.http.middleware.fastapi import payment_middleware
        from x402.mechanisms.svm.exact import ExactSvmServerScheme

        facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
        server = x402ResourceServer(facilitator)
        server.register(NETWORK, ExactSvmServerScheme())

        routes = {
            "POST /v1/audit/url-boundary": RouteConfig(
                accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.005", network=NETWORK),
                description="Detect HOST_SPLIT / SSRF parser discrepancies across urllib, httpx, yarl, and pydantic_core.",
                mime_type="application/json",
                service_name="GENESIS Boundary Oracle",
                tags=["security", "ssrf", "url-parser", "audit"],
            ),
            "POST /v1/audit/yaml-boundary": RouteConfig(
                accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.005", network=NETWORK),
                description="Detect YAML config hazards: duplicate keys, YAML 1.1/1.2 boolean traps, and alias bombs.",
                mime_type="application/json",
                service_name="GENESIS Boundary Oracle",
                tags=["security", "yaml", "devops", "audit"],
            ),
            "GET /v1/market/regime-hyperliquid": RouteConfig(
                accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.003", network=NETWORK),
                description="Live Hyperliquid perpetual funding-rate traps and market regime extremes.",
                mime_type="application/json",
                service_name="GENESIS Boundary Oracle",
                tags=["crypto", "hyperliquid", "funding", "regime"],
            ),
            "POST /v1/solve/stillness-sat": RouteConfig(
                accepts=PaymentOption(scheme="exact", pay_to=PAY_TO, price="$0.004", network=NETWORK),
                description="Solve Boolean CNF-SAT constraints with verified assignment via Differential Stillness.",
                mime_type="application/json",
                service_name="GENESIS Boundary Oracle",
                tags=["sat", "solver", "constraints", "logic"],
            ),
        }

        app.middleware("http")(payment_middleware(routes=routes, server=server))
        X402_ENABLED = True
    except Exception as exc:
        X402_ERROR = repr(exc)
        print(f"[x402] Preview mode (middleware not active: {exc})")


class UrlAuditRequest(BaseModel):
    url: str


class YamlAuditRequest(BaseModel):
    yaml_text: str


class SatRequest(BaseModel):
    n_vars: int
    clauses: List[List[int]]
    max_steps: int = 2000


@app.get("/health")
def health():
    return {
        "status": "ok",
        "x402_enabled": X402_ENABLED,
        "x402_error": X402_ERROR,
        "network": NETWORK,
        "pay_to": PAY_TO,
        "facilitator": FACILITATOR_URL,
    }


@app.get("/.well-known/x402.json")
def discovery_manifest():
    return {
        "protocol": "x402",
        "version": 2,
        "service": "GENESIS Boundary Micro-Oracle",
        "x402_payment_active": X402_ENABLED,
        "network": NETWORK,
        "pay_to": PAY_TO,
        "facilitator": FACILITATOR_URL,
        "endpoints": [
            {"method": "POST", "path": "/v1/audit/url-boundary", "price_usdc": "0.005"},
            {"method": "POST", "path": "/v1/audit/yaml-boundary", "price_usdc": "0.005"},
            {"method": "GET", "path": "/v1/market/regime-hyperliquid", "price_usdc": "0.003"},
            {"method": "POST", "path": "/v1/solve/stillness-sat", "price_usdc": "0.004"},
        ],
    }


@app.get("/.well-known/agent-card.json")
def erc8004_agent_card():
    """ERC-8004 / A2A Trustless Agent Card for autonomous discovery and reputation indexing."""
    return {
        "schema": "erc-8004/agent-card/v1",
        "name": "genesis-boundary-oracle",
        "version": "1.0.0",
        "description": "Deterministic boundary-physics verification, market-regime RMT, and CNF-SAT solving oracle.",
        "payment": {
            "protocol": "x402",
            "network": NETWORK,
            "asset": "USDC",
            "payTo": PAY_TO,
            "facilitator": FACILITATOR_URL,
        },
        "capabilities": [
            {
                "id": "url-boundary-ssrf-audit",
                "endpoint": "/v1/audit/url-boundary",
                "method": "POST",
                "price_usdc": "0.005",
                "summary": "Detects HOST_SPLIT SSRF discrepancies across urllib, httpx, yarl, and pydantic_core.",
            },
            {
                "id": "yaml-boundary-hazard-audit",
                "endpoint": "/v1/audit/yaml-boundary",
                "method": "POST",
                "price_usdc": "0.005",
                "summary": "Detects YAML duplicate keys, YAML 1.1/1.2 boolean traps, and alias bombs.",
            },
            {
                "id": "hyperliquid-funding-regime",
                "endpoint": "/v1/market/regime-hyperliquid",
                "method": "GET",
                "price_usdc": "0.003",
                "summary": "Live Hyperliquid perpetual funding-rate traps and market regime extremes.",
            },
            {
                "id": "differential-stillness-sat-solver",
                "endpoint": "/v1/solve/stillness-sat",
                "method": "POST",
                "price_usdc": "0.004",
                "summary": "Solves Boolean CNF-SAT constraints with verified assignments via Differential Stillness.",
            },
        ],
    }


@app.post("/v1/audit/url-boundary")
def audit_url_boundary(req: UrlAuditRequest):
    hosts, errors = {}, {}
    try:
        hosts["urllib.parse"] = (urlparse(req.url).hostname or "").lower()
    except Exception as e:
        errors["urllib.parse"] = str(e)
    for mod_name, fn in [
        ("httpx", lambda s: (__import__("httpx").URL(s).host or "").lower()),
        ("yarl", lambda s: (__import__("yarl").URL(s).host or "").lower()),
        ("pydantic_core", lambda s: (__import__("pydantic_core").Url(s).host or "").lower()),
    ]:
        try:
            hosts[mod_name] = fn(req.url)
        except ImportError:
            pass
        except Exception as e:
            errors[mod_name] = str(e)

    unique_hosts = sorted({h for h in hosts.values() if h})
    severity = "CRITICAL_HOST_SPLIT" if len(unique_hosts) > 1 else ("PARSER_DIVERGENCE" if (unique_hosts and errors) else "CLEAN")
    return {
        "input_url": req.url,
        "severity": severity,
        "host_split_detected": len(unique_hosts) > 1,
        "unique_hosts_seen": unique_hosts,
        "parsers_hosts": hosts,
        "parsers_errors": errors,
    }


@app.post("/v1/audit/yaml-boundary")
def audit_yaml_boundary(req: YamlAuditRequest):
    yaml_text = req.yaml_text
    hazards = []
    anchors = re.findall(r"&([A-Za-z0-9_-]+)", yaml_text)
    aliases = re.findall(r"\*([A-Za-z0-9_-]+)", yaml_text)
    if len(aliases) > 15 or (anchors and len(aliases) > 4 * len(anchors)):
        hazards.append({"type": "YAML_ALIAS_BOMB_RISK", "anchors": len(anchors), "aliases": len(aliases)})

    seen_by_indent: dict[int, set[str]] = {}
    dup_keys = []
    for ln in yaml_text.splitlines():
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        for k in list(seen_by_indent.keys()):
            if k > indent:
                del seen_by_indent[k]
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*:", stripped)
        if m:
            key = m.group(1)
            bucket = seen_by_indent.setdefault(indent, set())
            if key in bucket:
                dup_keys.append(key)
            bucket.add(key)
    if dup_keys:
        hazards.append({"type": "DUPLICATE_MAPPING_KEY", "keys": sorted(set(dup_keys))})

    norway_hits = re.findall(r":\s+(yes|no|on|off|y|n|YES|NO|ON|OFF)\s*(?:#.*)?$", yaml_text, flags=re.MULTILINE)
    if norway_hits:
        hazards.append({"type": "YAML_1_1_BOOL_SPLIT", "tokens": norway_hits[:10]})

    parsed_ok, parse_err = True, None
    try:
        import yaml
        yaml.safe_load(yaml_text)
    except Exception as e:
        parsed_ok, parse_err = False, str(e)

    severity = "HIGH" if any(h["type"] in ("YAML_ALIAS_BOMB_RISK", "DUPLICATE_MAPPING_KEY") for h in hazards) else ("MEDIUM" if hazards else "CLEAN")
    return {"severity": severity, "hazards_count": len(hazards), "hazards": hazards, "pyyaml_safe_load_ok": parsed_ok, "parse_error": parse_err}


_CACHE = {"ts": 0.0, "data": None}


@app.get("/v1/market/regime-hyperliquid")
def market_regime_hyperliquid():
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["ts"]) < 60.0:
        return _CACHE["data"]
    r = requests.post(HL_URL, json={"type": "metaAndAssetCtxs"}, timeout=12)
    r.raise_for_status()
    meta, ctxs = r.json()
    traps = []
    for u, c in zip(meta["universe"], ctxs):
        if u["name"] in TRACKED_COINS:
            f_hr = float(c.get("funding") or 0.0)
            traps.append({
                "coin": u["name"],
                "markPx": float(c.get("markPx") or 0.0),
                "funding_ann_pct": round(f_hr * 24.0 * 365.0 * 100.0, 2),
                "dayNtlVlm": round(float(c.get("dayNtlVlm") or 0.0), 1),
            })
    traps.sort(key=lambda x: abs(x["funding_ann_pct"]), reverse=True)
    payload = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "source": "hyperliquid_live", "top_funding_traps": traps[:5]}
    _CACHE["ts"], _CACHE["data"] = now, payload
    return payload


@app.post("/v1/solve/stillness-sat")
def solve_stillness_sat(req: SatRequest):
    n_vars, clauses, max_steps = req.n_vars, req.clauses, min(req.max_steps, 5000)
    if n_vars < 1 or n_vars > 500 or len(clauses) > 3000:
        return {"solved": False, "error": "Limits exceeded (max 500 vars, 3000 clauses)"}

    rng = np.random.default_rng(42)
    assign = rng.integers(0, 2, size=n_vars + 1, dtype=np.int8)

    def clause_sat(cl):
        for lit in cl:
            v = abs(lit)
            val = assign[v] == 1
            if (lit > 0 and val) or (lit < 0 and not val):
                return True
        return False

    var_clauses: List[List[int]] = [[] for _ in range(n_vars + 1)]
    for ci, cl in enumerate(clauses):
        for lit in cl:
            var_clauses[abs(lit)].append(ci)

    for step in range(1, max_steps + 1):
        unsat = [ci for ci, cl in enumerate(clauses) if not clause_sat(cl)]
        if not unsat:
            return {"solved": True, "steps": step, "unsat_clauses": 0, "assignment": {str(i): bool(assign[i]) for i in range(1, n_vars + 1)}}
        cl = clauses[unsat[int(rng.integers(0, len(unsat)))]]
        if rng.random() < 0.35:
            pick = abs(cl[int(rng.integers(0, len(cl)))])
        else:
            best_v, best_breaks = abs(cl[0]), 10**9
            for lit in cl:
                v = abs(lit)
                assign[v] ^= 1
                breaks = sum(1 for c_idx in var_clauses[v] if not clause_sat(clauses[c_idx]))
                assign[v] ^= 1
                if breaks < best_breaks:
                    best_breaks, best_v = breaks, v
            pick = best_v
        assign[pick] ^= 1

    rem = sum(1 for cl in clauses if not clause_sat(cl))
    return {"solved": rem == 0, "steps": max_steps, "unsat_clauses": rem}
