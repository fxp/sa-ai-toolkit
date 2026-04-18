# Playwright demo — browser test simulator

`simulate_run(scenario)` returns a deterministic trace (no browser) for UI
playback. `run_real(scenario, url=None)` drives real Chromium via playwright
if installed.

## Usage

    python cli.py scenarios
    python cli.py simulate --scenario bing
    # Real execution (local only):
    pip install playwright && playwright install chromium
    python cli.py real --scenario bing --url https://www.bing.com

## Tests

    pytest tests/
