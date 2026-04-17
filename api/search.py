"""
Search API proxy for demos.
Calls DuckDuckGo HTML endpoint (no API key needed) and returns JSON results.
Falls back to preset results if scraping fails.
"""
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
import re

FALLBACK_RESULTS = [
    {
        "title": "AI in Enterprise — McKinsey Report 2024",
        "url": "https://www.mckinsey.com/capabilities/quantumblack/our-insights",
        "snippet": "Enterprise AI adoption has grown 270% since 2019. Leading companies report 15-30% productivity gains across departments.",
    },
    {
        "title": "State of AI 2024 — Stanford HAI",
        "url": "https://hai.stanford.edu/research/ai-index-report",
        "snippet": "Foundation models now dominate 92% of new AI deployments. Multi-agent systems emerge as dominant paradigm.",
    },
    {
        "title": "AI Adoption Patterns — BCG 2024",
        "url": "https://www.bcg.com/publications/2024/ai-adoption",
        "snippet": "High-performers integrate AI into 6+ core workflows. Key success factors: executive sponsorship, data quality, change management.",
    },
    {
        "title": "The Economic Potential of Generative AI",
        "url": "https://example.com/genai-economics",
        "snippet": "Generative AI could add $2.6T-$4.4T annually to the global economy, with 75% of the value in four domains: customer ops, marketing, software engineering, R&D.",
    },
    {
        "title": "Industry 4.0 and Predictive Maintenance",
        "url": "https://example.com/industry-40",
        "snippet": "Manufacturers using AI-powered predictive maintenance report 30-50% reduction in downtime and 10-40% reduction in maintenance costs.",
    },
]


def search_duckduckgo(query: str, max_results: int = 8):
    """Scrape DuckDuckGo HTML results (no API key)."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Parse result cards — pattern: <a class="result__a" href="URL">TITLE</a>
        #                              <a class="result__snippet">SNIPPET</a>
        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for m in pattern.finditer(html):
            if len(results) >= max_results:
                break
            raw_url = m.group(1)
            # DuckDuckGo wraps URLs: /l/?kh=-1&uddg=<encoded>
            if "uddg=" in raw_url:
                match = re.search(r"uddg=([^&]+)", raw_url)
                real_url = urllib.parse.unquote(match.group(1)) if match else raw_url
            else:
                real_url = raw_url
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", m.group(3)).strip()
            results.append({"title": title, "url": real_url, "snippet": snippet})

        return results if results else None
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        query = (params.get("q") or [""])[0]
        max_results = int((params.get("n") or ["8"])[0])

        if not query:
            self._json(400, {"error": "missing q param"})
            return

        results = search_duckduckgo(query, max_results)
        if not results:
            # Fallback: filter preset results by query relevance
            q_lower = query.lower()
            results = [r for r in FALLBACK_RESULTS if any(
                w in (r["title"] + r["snippet"]).lower()
                for w in q_lower.split() if len(w) > 2
            )] or FALLBACK_RESULTS[:3]

        self._json(200, {"query": query, "results": results, "count": len(results)})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
