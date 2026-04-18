"""Consolidated enterprise-gen handler. Dispatches: ?action=score|generate (POST)."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demos", "enterprise-gen-py"))
from core import score_demos, generate_package  # noqa: E402


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
        profile = payload.get("profile", payload)
        try:
            if action == "score":
                self._json(200, {"scored": score_demos(profile)})
            elif action == "generate":
                self._json(200, generate_package(profile))
            else:
                self._json(400, {"error": "unknown action", "available": ["score", "generate"]})
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
