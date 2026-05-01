#!/usr/bin/env python3
"""
Tantrium RH Machine — Status API Server
========================================
Minimal stdlib HTTP server. No extra dependencies.

Usage:
    python app/server.py            # start on port 8765
    python app/server.py --check    # print status and exit (no server)
    python app/server.py --port 8080

API endpoints:
    GET /api/status          — overall machine status
    GET /api/certificates    — certificate registry
    GET /api/atlas           — atlas manifest
    GET /api/theorem-graph   — theorem graph nodes
    GET /api/proof-attempt   — proof attempt DAG
    GET /api/gap-report      — gap finder report (plain text)
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = REPO_ROOT / "results" / "certificates"
ATLAS_DIR = REPO_ROOT / "results" / "atlas"
THEOREM_GRAPH = REPO_ROOT / "tantrium" / "theorem_graph" / "theorem_graph.yaml"


def _load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"error": f"not found: {path.name}"}


def _load_text(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return f"# Not found: {path.name}\n"


def get_status() -> dict:
    manifest = _load_json(ATLAS_DIR / "manifest.json")
    registry = _load_json(CERT_DIR / "certificate_registry.json")
    latest = _load_json(CERT_DIR / "tantrium_rh_machine_latest.json")
    return {
        "closure_status": manifest.get("closure_status", "unknown"),
        "proof_attempt_status": manifest.get("proof_attempt_status", "unknown"),
        "gap_status": registry.get("gap_status", "unknown"),
        "latest_commit": manifest.get("commit_sha", "unknown"),
        "latest_rh_closure_run": manifest.get("latest_rh_closure_run"),
        "latest_rh_proof_attempt": manifest.get("latest_rh_proof_attempt"),
        "latest_certificate_registry": manifest.get("latest_certificate_registry"),
        "manuscript": "paper/TANTRIUM_RH_PROOF_v1.md",
        "machine_entrypoint": "python tools/tantrium_rh_machine.py --full",
        "machine_latest": latest,
    }


ROUTES: dict[str, str | dict] = {
    "/api/status": "status",
    "/api/certificates": str(CERT_DIR / "certificate_registry.json"),
    "/api/atlas": str(ATLAS_DIR / "manifest.json"),
    "/api/theorem-graph": str(THEOREM_GRAPH),
    "/api/proof-attempt": str(CERT_DIR / "rh_proof_attempt_dag.json"),
    "/api/gap-report": str(CERT_DIR / "rh_gap_report.md"),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence default access log

    def _send(self, code: int, body: str, content_type: str = "application/json"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._send(200, json.dumps({"tantrium": "Proof Machine API", "routes": list(ROUTES)}), "application/json")
            return
        if path not in ROUTES:
            self._send(404, json.dumps({"error": "not found"}))
            return
        target = ROUTES[path]
        if target == "status":
            self._send(200, json.dumps(get_status(), indent=2))
            return
        fp = Path(target)
        if fp.suffix == ".md":
            self._send(200, _load_text(fp), "text/plain; charset=utf-8")
        else:
            self._send(200, json.dumps(_load_json(fp), indent=2))


def check_mode():
    status = get_status()
    print("Tantrium Machine Status")
    print(f"  closure_status:       {status['closure_status']}")
    print(f"  proof_attempt_status: {status['proof_attempt_status']}")
    print(f"  gap_status:           {status['gap_status']}")
    print(f"  latest_commit:        {status['latest_commit']}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Tantrium Status API Server")
    parser.add_argument("--check", action="store_true", help="Print status and exit")
    parser.add_argument("--port", type=int, default=8765, help="Port (default 8765)")
    args = parser.parse_args()

    if args.check:
        check_mode()

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    print(f"Tantrium API server running on http://localhost:{args.port}")
    print("Routes: " + "  ".join(ROUTES.keys()))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
