from http.server import BaseHTTPRequestHandler
import base64
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demos", "ppt-gen-py"))
from core import generate_pptx  # noqa: E402


def _safe_filename(title: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", title or "deck").strip("_") or "deck"
    return stem[:60] + ".pptx"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            payload = json.loads(body or b"{}")
            title = payload.get("title", "Deck")
            subtitle = payload.get("subtitle", "")
            slides = payload.get("slides") or []
            theme = payload.get("theme", "blue-orange")
            data = generate_pptx(title, subtitle, slides, theme)
            self._json(200, {
                "pptx_base64": base64.b64encode(data).decode("ascii"),
                "filename": _safe_filename(title),
                "bytes": len(data),
            })
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
