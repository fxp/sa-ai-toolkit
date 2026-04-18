"""Consolidated SA toolkit handler. ?action=gen|customize|present (POST)."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demos", "sa-toolkit-py"))
from core import (  # noqa: E402
    generate_package,
    search_company,
    deepen_demo,
    replace_terms,
    switch_audience,
    export_email,
    rehearse,
)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            payload = json.loads(body or b"{}")
        except Exception:
            self._json(400, {"error": "invalid JSON"})
            return
        action = (params.get("action") or [""])[0] or payload.get("action") or ""
        try:
            if action == "gen":
                name = payload.get("company") or payload.get("name") or "Acme"
                info = search_company(name)
                for k in ("pain_points", "audience", "minutes", "size"):
                    if k in payload:
                        info[k] = payload[k]
                pkg = generate_package(info)
                pkg["info"] = info
                self._json(200, pkg)
            elif action == "customize":
                pkg = payload.get("package") or {}
                sub = payload.get("action_type") or payload.get("op")  # inner action: replace/deepen/audience
                # Backward-compat: when caller used old "action" field inside body for inner operation,
                # and top-level action is "customize" via query-string.
                if not sub:
                    sub = payload.get("sub_action") or payload.get("mode")
                # If payload.action is inner op (legacy), then top-level action came from query string.
                legacy_inner = payload.get("action")
                if sub is None and legacy_inner in ("replace", "deepen", "audience"):
                    sub = legacy_inner
                p = payload.get("params") or {}
                if sub == "replace":
                    out = replace_terms(pkg, p.get("mapping") or {})
                elif sub == "deepen":
                    out = deepen_demo(pkg, p.get("demo_id") or p.get("name") or "")
                elif sub == "audience":
                    out = switch_audience(pkg, p.get("audience") or "executives")
                else:
                    raise ValueError(f"Unknown customize op: {sub!r}")
                self._json(200, {"package": out, "action": sub})
            elif action == "present":
                pkg = payload.get("package") or {}
                mode = payload.get("mode", "rehearse")
                if mode == "rehearse":
                    self._json(200, {"plays": rehearse(pkg)})
                elif mode == "email":
                    self._json(200, {"email": export_email(pkg)})
                else:
                    self._json(400, {"error": f"Unknown mode: {mode!r}"})
            else:
                self._json(400, {"error": "unknown action",
                                 "available": ["gen", "customize", "present"]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
