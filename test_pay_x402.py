"""
Cliente de prueba real x402 (Solana Mainnet USDC) para disparar la 1ra llamada paga ($0.005 USDC)
que indexa automáticamente tu servidor en x402 Bazaar.

Uso:
  1) Verificación gratuita (HTTP 402 + headers):
       python test_pay_x402.py --url https://TU_URL_PUBLICA
  2) Pago real de $0.005 USDC en Solana (requiere clave privada de una wallet con >= $0.01 USDC):
       set SOLANA_PAYER_SECRET=<base58_private_key>
       python test_pay_x402.py --url https://TU_URL_PUBLICA --pay
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Base URL of deployed x402 server (e.g. https://genesis-x402-oracle.onrender.com)")
    ap.add_argument("--pay", action="store_true", help="Execute a real $0.005 USDC payment on Solana using SOLANA_PAYER_SECRET")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    print(f"[1/3] Checking {base}/health ...")
    r = requests.get(f"{base}/health", timeout=15)
    print("      ", r.status_code, r.json())

    print(f"[2/3] Checking {base}/.well-known/agent-card.json ...")
    rc = requests.get(f"{base}/.well-known/agent-card.json", timeout=15)
    print("      ", rc.status_code, rc.json().get("schema"), "capabilities:", len(rc.json().get("capabilities", [])))

    print(f"[3/3] Probing unpaid POST {base}/v1/audit/url-boundary (expecting HTTP 402)...")
    r402 = requests.post(f"{base}/v1/audit/url-boundary", json={"url": r"https://trusted.com\@evil.com/path"}, timeout=15)
    print("      HTTP status:", r402.status_code)
    hdr = r402.headers.get("payment-required") or r402.headers.get("PAYMENT-REQUIRED")
    if hdr:
        decoded = json.loads(base64.b64decode(hdr))
        acc = decoded.get("accepts", [{}])[0]
        print(f"      Verified 402 challenge -> network={acc.get('network')} | amount={acc.get('amount')} | payTo={acc.get('payTo')}")
    else:
        print("      Body:", r402.text[:300])

    if args.pay:
        secret = os.getenv("SOLANA_PAYER_SECRET", "").strip()
        if not secret:
            raise SystemExit("Set SOLANA_PAYER_SECRET env var (base58 private key with >= $0.01 USDC on Solana) to execute --pay.")
        from x402 import x402Client
        from x402.http.clients import x402HttpxClient
        from x402.mechanisms.svm import KeypairSigner
        from x402.mechanisms.svm.exact import ExactSvmClientScheme
        import asyncio

        async def _do_pay():
            signer = KeypairSigner.from_base58(secret)
            client = x402Client()
            client.register("solana:*", ExactSvmClientScheme(signer))
            async with x402HttpxClient(client) as http:
                resp = await http.post(
                    f"{base}/v1/audit/url-boundary",
                    json={"url": r"https://trusted.com\@evil.com/path"},
                )
                print("      PAID CALL STATUS:", resp.status_code)
                print("      RESPONSE:", resp.text[:400])

        asyncio.run(_do_pay())


if __name__ == "__main__":
    main()
