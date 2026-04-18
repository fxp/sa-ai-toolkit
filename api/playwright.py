"""GET /api/playwright?scenario=bing — deterministic trace."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import importlib.util as _ilu

_CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'demos', 'playwright-py', 'core.py')
_spec = _ilu.spec_from_file_location("playwright_demo_core", _CORE_PATH)
_mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
simulate_run = _mod.simulate_run
SCENARIOS = _mod.SCENARIOS


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        scenario = (params.get("scenario") or ["bing"])[0]
        if scenario not in SCENARIOS:
            self._json(400, {"error": f"unknown scenario {scenario!r}",
                             "available": sorted(SCENARIOS.keys())})
            return
        try:
            trace = simulate_run(scenario)
            sc = SCENARIOS[scenario]
            self._json(200, {
                "scenario": scenario,
                "title": sc["title"],
                "script": sc["script"],
                "trace": trace,
            })
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
