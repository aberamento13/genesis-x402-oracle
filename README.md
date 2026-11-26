# GENESIS x402 Boundary Micro-Oracle (Solana Mainnet USDC)

Pay-per-call algorithmic oracles for autonomous AI agents via **x402 v2** (`solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp`) + **ERC-8004 Agent Card** (`/.well-known/agent-card.json`).

## Endpoints
- `GET /health` (free)
- `GET /.well-known/x402.json` (free)
- `GET /.well-known/agent-card.json` (free — ERC-8004 Agent Card)
- `POST /v1/audit/url-boundary` (`$0.005 USDC`) — Detects `HOST_SPLIT` / SSRF parser discrepancies across `urllib`, `httpx`, `yarl`, `pydantic_core`.
- `POST /v1/audit/yaml-boundary` (`$0.005 USDC`) — Detects duplicate mapping keys, YAML 1.1/1.2 boolean traps, and alias bombs.
- `GET /v1/market/regime-hyperliquid` (`$0.003 USDC`) — Live Hyperliquid perpetual funding-rate traps.
- `POST /v1/solve/stillness-sat` (`$0.004 USDC`) — Differential Stillness CNF-SAT constraint solver with verified assignment.

## One-Click Deploy on Render (Free Tier)
1. Push this directory to GitHub.
2. On Render.com: **New → Blueprint** → select this repository (`render.yaml` configures Docker + env vars automatically).
