"""AutoResearch-for-VRP Vercel handler.

POST ?action=iterate  — run one solver variant {iter_idx, lang}
POST ?action=full     — run all variants
GET  ?action=instance — benchmark + program.md
GET  ?action=meta     — variant catalog
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import importlib.util as _ilu

_CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'demos', 'autoresearch-vrp-py', 'core.py')
_spec = _ilu.spec_from_file_location("autoresearch_vrp_core", _CORE_PATH)
_mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        action = (params.get("action") or ["instance"])[0]
        lang = (params.get("lang") or ["en"])[0]
        if action == "instance":
            self._json(200, {
                "instance": _mod.get_instance_payload(),
                "program_md": _mod.get_program_md(lang=lang),
                "num_iterations": _mod.NUM_ITERATIONS,
            })
        elif action == "meta":
            self._json(200, {
                "num_iterations": _mod.NUM_ITERATIONS,
                "variants": [
                    {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                     "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                    for v in _mod.VARIANTS
                ],
            })
        else:
            self._json(400, {"error": "unknown action", "available": ["instance", "meta"]})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception:
            self._json(400, {"error": "invalid JSON"})
            return
        action = (params.get("action") or [""])[0] or body.get("action") or "iterate"
        lang = body.get("lang") or "en"
        try:
            if action == "iterate":
                self._json(200, _mod.run_iteration(int(body.get("iter_idx", 0)), lang=lang))
            elif action == "full":
                self._json(200, _mod.run_full(lang=lang))
            else:
                self._json(400, {"error": "unknown action", "available": ["iterate", "full"]})
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
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
