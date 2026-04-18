# Tests

## Python unit tests (pytest)

Each `demos/*-py/` demo has a `tests/test_core.py`. Run them all from the repo root:

    pytest

Or run tests for a single demo:

    pytest demos/autoresearch-py
    pytest demos/org-uplift-py
    pytest demos/industrial-ai-py
    pytest demos/playwright-py

Pytest discovery is configured in `pytest.ini` (testpaths = demos).

## CLI smoke tests

`scripts/batch_test.sh` runs each demo's CLI with sample input and checks the
exit code + expected output token.

    ./scripts/batch_test.sh              # list demos
    ./scripts/batch_test.sh --all        # run every demo, print pass/fail
    ./scripts/batch_test.sh autoresearch-py

## Frontend → API check (manual)

After Vercel deploy (or `vercel dev`), hit each endpoint:

    curl -s -X POST /api/research_stage -d '{"topic":"AI","stage_idx":0}'
    curl -s -X POST /api/uplift_execute -d '{"task":"demo"}'
    curl -s -X POST /api/uplift_stats   -d '{"tasks":[]}'
    curl -s /api/playwright_simulate?scenario=bing
